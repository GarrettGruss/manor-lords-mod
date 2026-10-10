"""Tests for run_until and the stall detector (runlib/waiting.py), and the scenario limit rules. No game."""

import unittest

import runlib_path  # noqa: F401
from runlib.scenario import (
    get_limit_s,
    LONG_LIMIT_S, MAX_LIMIT_S, SCENARIO_INFO, check_limit, list_scenarios, register, run_timeout_s,
)
from runlib.timectl import TimeControlError
from runlib.waiting import GameStalled, ScenarioFailure, WaitTimeout, run_until


class FakeTime:
    """A fake wall clock and game clock. Each sleep moves the wall clock. The game clock moves by `rate` while `running`."""

    def __init__(self, rate=1.0, running=True):
        self.wall, self.game, self.rate, self.running = 0.0, 100.0, rate, running

    def sleep(self, seconds):
        self.wall += seconds
        if self.running:
            self.game += seconds * self.rate

    def monotonic(self):
        return self.wall

    def read_clock(self):
        return self.game

    def options(self, **extra):
        return dict(sleep=self.sleep, monotonic=self.monotonic, read_clock=self.read_clock, **extra)


class RunUntilTest(unittest.TestCase):
    def test_returns_when_true(self):
        fake = FakeTime(rate=8)
        result = run_until(lambda: fake.game >= 140, 60, what="5 game seconds", **fake.options())
        self.assertGreaterEqual(result.game_s, 40)
        self.assertEqual(result.stalls, 0)
        self.assertGreater(result.polls, 1)

    def test_value_of_the_predicate_is_returned(self):
        fake = FakeTime()
        result = run_until(lambda: {"day": 3} if fake.wall >= 2 else None, 10, **fake.options())
        self.assertEqual(result.value, {"day": 3})

    def test_wall_timeout_message(self):
        fake = FakeTime()
        with self.assertRaisesRegex(WaitTimeout, r"timeout: the raid arrives was not true within 5 wall seconds"):
            run_until(lambda: False, 5, what="the raid arrives", **fake.options())

    def test_game_time_timeout_counts_game_seconds(self):
        fake = FakeTime(rate=8)
        with self.assertRaisesRegex(WaitTimeout, "within 40 game seconds") as caught:
            run_until(lambda: False, 40, what="never", clock="game", **fake.options())
        self.assertLess(fake.wall, 10)  # 40 game seconds at 8x are about 5 wall seconds
        self.assertIn("polls", str(caught.exception))

    def test_game_clock_needs_a_reader(self):
        with self.assertRaises(ValueError):
            run_until(lambda: True, 5, clock="game")
        with self.assertRaises(ValueError):
            run_until(lambda: True, 5, stall_s=3)
        with self.assertRaises(ValueError):
            run_until(lambda: True, 0)
        with self.assertRaises(ValueError):
            run_until(lambda: True, 5, clock="moon")

    def test_check_alive_error_passes_through(self):
        fake = FakeTime()

        def dead():
            raise RuntimeError("game ended")

        with self.assertRaisesRegex(RuntimeError, "game ended"):
            run_until(lambda: False, 5, check_alive=dead, **fake.options())

    def test_on_poll_runs_after_each_false_poll(self):
        fake, seen = FakeTime(), []
        run_until(lambda: fake.wall >= 3, 10, on_poll=lambda: seen.append(fake.wall), **fake.options())
        self.assertEqual(seen, [0.0, 1.0, 2.0])


class StallTest(unittest.TestCase):
    def test_stall_without_repair_raises(self):
        fake = FakeTime(running=False)
        with self.assertRaisesRegex(GameStalled, "stood still at 100.0 for 5 s while waiting for the days") as caught:
            run_until(lambda: False, 600, what="the days", stall_s=5, **fake.options())
        self.assertIn("close_popups", str(caught.exception))
        self.assertLess(fake.wall, 10)

    def test_repair_that_helps_keeps_the_wait_going(self):
        fake, repairs = FakeTime(running=False), []

        def repair():
            repairs.append(fake.wall)
            fake.running = True

        result = run_until(lambda: fake.game >= 130, 600, stall_s=5, on_stall=repair, **fake.options())
        self.assertEqual(result.stalls, 1)
        self.assertEqual(len(repairs), 1)
        self.assertEqual(len(result.stall_log), 1)

    def test_repair_that_does_not_help_raises_after_a_second_window(self):
        fake, repairs = FakeTime(running=False), []
        with self.assertRaisesRegex(GameStalled, "after a repair"):
            run_until(lambda: False, 600, stall_s=5, on_stall=lambda: repairs.append(1), **fake.options())
        self.assertEqual(len(repairs), 1)
        self.assertLess(fake.wall, 15)

    def test_a_second_stall_gets_a_second_repair(self):
        fake, repairs = FakeTime(running=True), []

        def repair():
            repairs.append(fake.wall)
            fake.running = True

        def predicate():
            # Stop the game twice, 20 wall seconds apart.
            if fake.wall in (10.0, 30.0):
                fake.running = False
            return fake.wall >= 50

        result = run_until(predicate, 600, stall_s=4, on_stall=repair, **fake.options())
        self.assertEqual(result.stalls, 2)

    def test_slow_clock_is_not_a_stall(self):
        fake = FakeTime(rate=0.5)
        result = run_until(lambda: fake.wall >= 30, 100, stall_s=3, **fake.options())
        self.assertEqual(result.stalls, 0)


class LimitRulesTest(unittest.TestCase):
    def test_default_and_short_limits_need_no_reason(self):
        check_limit("x", 90)
        check_limit("x", LONG_LIMIT_S)

    def test_long_limit_needs_a_reason(self):
        with self.assertRaisesRegex(ValueError, "LONG_REASON"):
            check_limit("soak", 600)
        check_limit("soak", 600, "10 minutes of wall time at 8x")

    def test_limit_above_the_maximum_is_refused(self):
        with self.assertRaisesRegex(ValueError, "at most"):
            check_limit("soak", MAX_LIMIT_S + 1, "reason")
        check_limit("soak", MAX_LIMIT_S, "reason")
        for bad in (0, -5):
            with self.assertRaises(ValueError):
                check_limit("x", bad)

    def test_register_applies_the_rule(self):
        with self.assertRaises(ValueError):
            register("test-long-no-reason", 1000)(lambda ctx: {})
        self.assertNotIn("test-long-no-reason", SCENARIO_INFO)

    def test_every_real_scenario_obeys_the_rule(self):
        for name, info in list_scenarios(include_hidden=True).items():
            self.assertTrue(0 < info.limit_s <= MAX_LIMIT_S, name)
            if info.limit_s > LONG_LIMIT_S:
                self.assertTrue(info.long_reason, f"{name} has no LONG_REASON")

    def test_launcher_timeout_follows_the_scenario_limit(self):
        self.assertEqual(run_timeout_s("smoke"), 900)  # short scenario: the floor
        self.assertEqual(run_timeout_s("unknown-scenario"), 900)
        self.assertEqual(run_timeout_s("smoke", 10), get_limit_s("smoke") + 600)
        info = SCENARIO_INFO.get("soak-days")
        if info:
            self.assertGreater(run_timeout_s("soak-days"), info.limit_s)


class ErrorKindsTest(unittest.TestCase):
    def test_wait_and_time_errors_are_scenario_failures(self):
        for error in (WaitTimeout, GameStalled, TimeControlError):
            self.assertTrue(issubclass(error, ScenarioFailure))


if __name__ == "__main__":
    unittest.main()
