"""Tests for time control, assertions, snapshots and the telemetry reader. No game."""

import json
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib.bridge_client import Bridge
from runlib.expectations import Expectations
from runlib.snapshot import snapshot
from runlib.telemetry import TelemetryReader
from runlib.timectl import CLOCK_SECONDS_PER_DAY, SPEED_FACTOR, TimeControl, TimeControlError, absolute_day

ENGINE = "Map:PersistentLevel.Engine"
PLAYER = "Map:PersistentLevel.Pawn"
CALENDAR = ENGINE + ".TemporalComponent"


class FakeGame:
    """A fake game. `sleep` moves wall time. The clock runs at the speed factor while the game is not paused."""

    def __init__(self, blocked=False, ignores_pause=False):
        self.wall = 0.0
        self.clock = 100.0
        self.factor = 0.0
        self.year, self.day = 1, 364
        self.days_total = 0
        self.blocked = blocked  # a pop-up holds the pause
        self.ignores_pause = ignores_pause
        self.pause_calls = 0
        self.player_paused_flag = True  # set by the pause of HarnessBoot. Only unPauseGame clears it.
        self.flag_set_at = 0.0
        self.reset_once = False

    def sleep(self, seconds):
        self.wall += seconds
        if self.player_paused_flag and self.factor > 1 and self.wall - self.flag_set_at > 2.5:
            self.factor = 1.0  # the real game does this when the flag is still set
        if self.reset_once and self.factor > 1 and self.wall - self.flag_set_at > 2.5:
            self.factor, self.reset_once = 1.0, False
        if self.factor and not self.blocked:
            self._advance(seconds * self.factor)

    def monotonic(self):
        return self.wall

    def _advance(self, game_seconds):
        old_days = int(self.clock // CLOCK_SECONDS_PER_DAY)
        self.clock += game_seconds
        for _ in range(int(self.clock // CLOCK_SECONDS_PER_DAY) - old_days):
            self.days_total += 1
            self.day += 1
            if self.day > 365:
                self.day, self.year = 1, self.year + 1

    def one(self, op, **args):
        if op == "objects":
            return {"result": {"objects": [f"Engine {ENGINE}"]}}
        if op == "get":
            return {"result": self._get(args["ref"], args["name"])}
        return {"result": self._call(args["function"], args.get("args", []))}

    def _get(self, ref, name):
        if name == "TemporalComponent":
            return {"__object": f"TemporalComponent {CALENDAR}"}
        if name == "playerRef":
            return {"__object": f"Pawn {PLAYER}"}
        if name == "gameSpeed":
            return self.factor
        return {"day": self.day, "Year": self.year, "daysTotal": self.days_total}[name]

    def _call(self, function, args):
        if function == "getGameTimeAdjusted":
            return self.clock
        if function == "changeGameSpeed":
            self.flag_set_at = self.wall
            self.factor = SPEED_FACTOR[args[0]]
        if function == "unPauseGame":
            self.player_paused_flag = False
            self.factor = self.factor or 1.0
        if function == "pauseGame":
            self.pause_calls += 1
            if not self.ignores_pause:
                self.factor = 0.0
        return None


def make_time(game):
    return TimeControl(Bridge(game.one, sleep=game.sleep), sleep=game.sleep, monotonic=game.monotonic)


class SetSpeedTest(unittest.TestCase):
    def test_speeds_1_2_3(self):
        for speed, factor in SPEED_FACTOR.items():
            self.assertEqual(make_time(FakeGame()).set_speed(speed), {"speed": speed, "game_speed": factor, "attempts": 1})

    def test_speed_holds_when_the_player_paused_flag_was_set(self):
        game = FakeGame()
        self.assertEqual(make_time(game).set_speed(3)["game_speed"], 8.0)
        self.assertEqual(game.factor, 8.0)

    def test_a_one_time_reset_to_1x_is_retried(self):
        game = FakeGame()
        game.player_paused_flag = False
        game.reset_once = True  # the real game dropped to 1x once after the first change
        record = make_time(game).set_speed(3)
        self.assertEqual((record["game_speed"], record["attempts"]), (8.0, 2))

    def test_unknown_speed_is_refused(self):
        with self.assertRaisesRegex(TimeControlError, "unknown speed"):
            make_time(FakeGame()).set_speed(4)

    def test_blocked_clock_gives_a_clear_error(self):
        with self.assertRaisesRegex(TimeControlError, "pop-up"):
            make_time(FakeGame(blocked=True)).set_speed(1)


class RunTest(unittest.TestCase):
    def test_the_guard_closes_a_pop_up_that_opens_during_a_run(self):
        game = FakeGame()
        game.player_paused_flag = False
        calls = []

        def guard():
            calls.append(game.wall)
            game.blocked = False  # the guard closed the pop-up

        control = TimeControl(Bridge(game.one, sleep=game.sleep), sleep=game.sleep, monotonic=game.monotonic, guard=guard)
        real_sleep = game.sleep

        def sleep_and_block(seconds):
            real_sleep(seconds)
            if 3.0 < game.wall < 3.3:
                game.blocked = True  # a pop-up opens

        game.sleep = sleep_and_block
        control = TimeControl(Bridge(game.one, sleep=sleep_and_block), sleep=sleep_and_block, monotonic=game.monotonic, guard=guard)
        record = control.run_game_seconds(80, speed=3)
        self.assertTrue(calls)
        self.assertTrue(record["paused_at_end"])

    def test_run_game_seconds_pauses_at_the_end(self):
        game = FakeGame()
        record = make_time(game).run_game_seconds(20, speed=3)
        moved = record["clock_end"] - record["clock_start"]
        self.assertEqual(game.factor, 0.0)
        self.assertTrue(record["paused_at_end"])
        self.assertGreaterEqual(moved, 20)
        self.assertLess(moved, 20 + 8 * 3)  # a few polls of overshoot
        self.assertEqual(set(record), {"clock_start", "clock_end", "wall_s", "paused_at_end", "speed", "speed_resets"})
        self.assertEqual(record["speed_resets"], 0)

    def test_a_run_sets_the_speed_again_when_an_army_drops_it_to_1x(self):
        game = FakeGame()
        control = make_time(game)
        real_sleep = game.sleep

        def sleep_with_armies(seconds):
            real_sleep(seconds)
            if game.wall > 12 and game.factor > 1 and int(game.wall) % 3 == 0:
                game.factor = 1.0  # an army was spotted

        control._sleep = sleep_with_armies
        control._bridge._sleep = sleep_with_armies
        record = control.run_game_days(3, speed=3)
        self.assertGreaterEqual(record["speed_resets"], 1)
        self.assertEqual(record["days_end"] - record["days_start"], 3)
        self.assertEqual(game.factor, 0.0)

    def test_wall_time_follows_speed(self):
        slow = make_time(FakeGame()).run_game_seconds(16, 1)["wall_s"]
        fast = make_time(FakeGame()).run_game_seconds(16, 3)["wall_s"]
        self.assertGreater(slow, fast * 4)

    def test_run_game_days_counts_days(self):
        game = FakeGame()
        record = make_time(game).run_game_days(2, speed=3)
        self.assertEqual(record["days_end"] - record["days_start"], 2)
        self.assertEqual(game.factor, 0.0)

    def test_day_counter_wrap_at_year_end(self):
        game = FakeGame()  # day 364 of year 1: two days later it is day 1 of year 2
        record = make_time(game).run_game_days(2, speed=3)
        self.assertEqual((game.year, game.day), (2, 1))
        self.assertEqual(record["day_end"] - record["day_start"], 2)

    def test_timeout_pauses_and_raises(self):
        game = FakeGame()
        control = make_time(game)
        real_sleep = game.sleep

        def sleep_then_freeze(seconds):
            real_sleep(seconds)
            game.blocked = game.wall > 3  # a pop-up stops the clock after the start

        control._sleep = sleep_then_freeze
        control._bridge._sleep = sleep_then_freeze
        with self.assertRaisesRegex(TimeControlError, "timeout"):
            control.run_game_days(5, speed=3)
        self.assertGreaterEqual(game.pause_calls, 1)

    def test_pause_that_does_not_hold_raises(self):
        with self.assertRaisesRegex(TimeControlError, "still moved after pauseGame"):
            make_time(FakeGame(ignores_pause=True)).run_game_seconds(2, speed=3)

    def test_absolute_day(self):
        self.assertEqual(absolute_day({"year": 2, "day": 1}) - absolute_day({"year": 1, "day": 365}), 1)


class ExpectationsTest(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.expect = Expectations(sleep=self.sleep, monotonic=lambda: self.now)

    def sleep(self, seconds):
        self.now += seconds

    def last(self):
        return self.expect.records[-1]

    def test_in_range(self):
        self.assertTrue(self.expect.in_range("a", 5, 0, 10))
        self.assertFalse(self.expect.in_range("b", 11, 0, 10))
        self.assertFalse(self.expect.in_range("c", None, 0, 10))
        self.assertEqual(self.expect.records[0], {"name": "a", "ok": True, "value": 5, "rule": "0..10"})

    def test_at_least_and_at_most(self):
        self.assertTrue(self.expect.at_least("a", 3, 3))
        self.assertFalse(self.expect.at_least("b", 2, 3))
        self.assertTrue(self.expect.at_most("c", 3, 3))
        self.assertFalse(self.expect.at_most("d", 4, 3))
        self.assertEqual(self.expect.records[0]["rule"], ">=3")

    def test_changed(self):
        self.assertTrue(self.expect.changed("any", 1, 2))
        self.assertFalse(self.expect.changed("none", 2, 2))
        self.assertTrue(self.expect.changed("two", 10, 12, min_delta=2, max_delta=2))
        self.assertFalse(self.expect.changed("too much", 10, 15, max_delta=2))
        self.assertFalse(self.expect.changed("too little", 10, 11, min_delta=2))
        self.assertFalse(self.expect.changed("null", None, 1))
        self.assertEqual(self.expect.records[2]["value"], 2)

    def test_equals(self):
        self.assertTrue(self.expect.equals("flag", True, True))
        self.assertFalse(self.expect.equals("name", "a", "b"))

    def test_eventually_passes_when_fn_turns_true(self):
        self.assertTrue(self.expect.eventually("soon", lambda: self.now >= 2, timeout_s=10))
        self.assertTrue(self.last()["ok"])
        self.assertGreaterEqual(self.last()["value"], 2)

    def test_eventually_fails_on_timeout(self):
        self.assertFalse(self.expect.eventually("never", lambda: False, timeout_s=3))
        self.assertFalse(self.last()["ok"])

    def test_result_fails_if_one_fails(self):
        self.expect.at_least("a", 5, 1)
        self.assertTrue(self.expect.result()["passed"])
        self.expect.at_most("b", 5, 1)
        result = self.expect.result()
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["asserts"]), 2)

    def test_record_is_short(self):
        self.expect.in_range("x" * 5, 1234.5678, 0.5, 99999)
        self.assertLess(len(json.dumps(self.last())), 200)


class SnapshotFake:
    def __init__(self, fail=()):
        self.fail = fail

    def engine_path(self):
        return ENGINE

    def read_clock_value(self, engine=None):
        return 12.5

    def calendar_path(self, engine=None):
        return CALENDAR

    def read_property(self, ref, name):
        if name in self.fail:
            raise RuntimeError(f"cannot read {name}")
        if name == "regions":
            return [{"__object": "BP_Region_C /m.R1"}, {"__object": "BP_Region_C /m.R2"}]
        if name == "playerRef":
            return {"__object": f"Pawn {PLAYER}"}
        return {"regionName": "Hochweg", "isSettled": True, "Approval": 50, "publicOrder": 100, "regionalWealth": 5,
                "supplies_food": 2, "day": 61, "month": 3, "Year": 1, "Season": 1, "silver": 0, "influence": 0,
                "kingsFavour": 0}[name]

    def call_function(self, ref, function, args=None):
        return {"getNumTotalPopulation": 10, "getNumHomelessFamilies": 5}[function]


class SnapshotTest(unittest.TestCase):
    def test_shape_matches_a_telemetry_sample(self):
        shot = snapshot(SnapshotFake())
        self.assertEqual(shot["errors"], [])
        self.assertEqual(shot["date"], {"day": 61, "month": 3, "year": 1, "season": 1})
        self.assertEqual(shot["player"], {"silver": 0, "influence": 0, "kingsFavour": 0})
        self.assertEqual(len(shot["regions"]), 2)
        self.assertEqual(set(shot["regions"][0]),
                         {"name", "settled", "approval", "publicOrder", "wealth", "food", "population", "homeless"})
        self.assertEqual(shot["clock"], 12.5)

    def test_read_error_gives_null_and_an_error_entry(self):
        shot = snapshot(SnapshotFake(fail=("Approval", "silver")))
        self.assertIsNone(shot["regions"][0]["approval"])
        self.assertIsNone(shot["player"]["silver"])
        self.assertEqual(shot["regions"][0]["name"], "Hochweg")
        self.assertTrue(any(error.startswith("region1.approval") for error in shot["errors"]))
        self.assertTrue(any(error.startswith("player.silver") for error in shot["errors"]))

    def test_no_engine_gives_empty_snapshot_with_error(self):
        class NoEngine(SnapshotFake):
            def engine_path(self):
                raise RuntimeError("no engine")

        shot = snapshot(NoEngine())
        self.assertIsNone(shot["clock"])
        self.assertEqual(shot["regions"], [])
        self.assertTrue(shot["errors"][0].startswith("engine"))


class TelemetryReaderTest(unittest.TestCase):
    def test_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(TelemetryReader(Path(temp)).read(), [])

    def test_read_window_and_half_written_last_line(self):
        with tempfile.TemporaryDirectory() as temp:
            lines = [json.dumps({"n": i, "clock": i * 10.0}) for i in range(1, 5)]
            (Path(temp) / "telemetry.jsonl").write_text("\n".join(lines) + '\n{"n": 5, "clo', encoding="utf-8")
            reader = TelemetryReader(Path(temp))
            self.assertEqual(len(reader.read()), 4)
            self.assertEqual([s["n"] for s in reader.window(15, 35)], [2, 3])

    def test_bad_line_in_the_middle_raises(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "telemetry.jsonl").write_text('{"n":1}\nnot json\n{"n":3}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                TelemetryReader(Path(temp)).read()


if __name__ == "__main__":
    unittest.main()
