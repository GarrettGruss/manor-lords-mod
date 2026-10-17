"""Tests for the feature invasion of the pack mod (mod feature M02, iteration 01) in the fake game.

They run the real Lua files. The fake world has a calendar, a raid timer, a pawn with a banner function and spawnRaiders.
They do not prove how the real game behaves.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from test_fakegame_modstate import FNAME, HELPERS, find_pack_mod

PLAN_DAYS = (30, 90)
WARNING_DAYS = (14, 56)


class InvasionTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        pack = find_pack_mod()
        self.mod_name = pack.name
        self.game.exec(f'package.path = "{(pack / "Scripts").as_posix()}/?.lua;" .. package.path')
        self.game.exec(FNAME + HELPERS)
        self.banners, self.raids = [], []
        self.pawn = self.game.obj("PawnCPP", Tags=self.game.array([]))
        self.game.method(self.pawn, "playEventMessage", lambda _self, _kind, text, sub: self.banners.append(text))
        self.game.method(self.pawn, "K2_GetActorLocation", lambda _self: self.game.struct(X=10.0, Y=20.0, Z=30.0))
        self.calendar = self.game.obj("TemporalComponent", daysTotal=61, daysUntilNextRaid=730)
        self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn, TemporalComponent=self.calendar)
        self.game.method(self.engine, "spawnRaiders", lambda _self, squads, centre: self.raids.append((squads, centre.X, centre.Y)))
        self.game.load_mod(self.mod_name)
        self.game.advance(2)

    def command(self, number, name, **args):
        folder = self.game.run_dir / "modcmd" / self.mod_name
        folder.mkdir(parents=True, exist_ok=True)
        body = {"id": f"{number:04d}", "command": f"{self.mod_name}.{name}", "args": args}
        (folder / f"{number:04d}.json").write_text(json.dumps(body), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{number:04d}.result.json").read_text(encoding="utf-8"))

    def next_number(self):
        self.counter = getattr(self, "counter", 0) + 1
        return self.counter

    def state(self):
        answer = self.command(self.next_number(), "invasion_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def ask(self, name, **args):
        return self.command(self.next_number(), name, **args)

    def set_day(self, day):
        self.calendar.daysTotal = day
        self.game.advance(2)


class PlanTests(InvasionTestCase):
    def test_a_plan_is_made_within_the_ranges(self):
        state = self.state()
        self.assertEqual(state["plan_day"], 61)
        self.assertTrue(PLAN_DAYS[0] <= state["raid_day"] - 61 <= PLAN_DAYS[1], state)
        self.assertTrue(WARNING_DAYS[0] <= state["raid_day"] - state["warning_day"] <= WARNING_DAYS[1], state)
        self.assertIn(state["squads"], (1, 2, 3))
        self.assertEqual(state["raiders"], 18 * state["squads"])

    def test_the_plan_is_kept_in_the_pawn_tags(self):
        state = self.state()
        tags = list(self.game.lua.eval("tag_names")(self.pawn).values())
        self.assertIn(f"invasion:raid_day={state['raid_day']}", tags)

    def test_base_timer_is_lifted_when_low(self):
        self.calendar.daysUntilNextRaid = 5
        self.game.advance(2)
        self.assertEqual(self.calendar.daysUntilNextRaid, 700)


class CommandTests(InvasionTestCase):
    def test_size_and_difficulty_set_the_squads(self):
        self.state()
        for difficulty, size, squads in ((1, "small", 1), (2, "medium", 4), (3, "large", 9), (2, "small", 2)):
            self.assertTrue(self.ask("invasion_set_difficulty", value=difficulty)["ok"])
            answer = self.ask("invasion_set_size", size=size)
            self.assertEqual(answer["result"]["squads"], squads)
            self.assertEqual(answer["result"]["raiders"], 18 * squads)

    def test_a_difficulty_outside_one_to_three_is_refused(self):
        self.assertFalse(self.ask("invasion_set_difficulty", value=4)["ok"])
        self.assertFalse(self.ask("invasion_set_size", size="huge")["ok"])


class RaidTests(InvasionTestCase):
    def run_days(self, first, last):
        for day in range(first, last + 1):
            self.set_day(day)

    def test_daily_banner_then_one_spawn_on_the_planned_day(self):
        self.ask("invasion_set_difficulty", value=2)
        plan = self.ask("invasion_set_size", size="medium")["result"]
        self.run_days(62, plan["raid_day"] + 5)
        warning_days = plan["raid_day"] - plan["warning_day"]
        self.assertEqual(len(self.banners), warning_days + 1)  # one for each day left, plus the arrival banner
        self.assertEqual(self.banners[0], f"Raid in {warning_days} days, about 72 raiders")
        self.assertEqual(self.banners[warning_days - 1], "Raid in 1 day, about 72 raiders")
        self.assertEqual(self.raids, [(4, 10.0, 20.0)])
        self.assertEqual(self.state()["raids_spawned"], 1)

    def test_force_next_spawns_on_the_next_check(self):
        self.ask("invasion_set_size", size="small")
        self.assertTrue(self.ask("invasion_force_next")["ok"])
        self.game.advance(2)
        self.assertEqual(self.raids, [(1, 10.0, 20.0)])
        self.assertFalse(self.ask("invasion_force_next")["ok"])

    def test_a_missed_day_still_spawns(self):
        plan = self.state()
        self.set_day(plan["raid_day"] + 2)
        self.assertEqual(len(self.raids), 1)

    def test_no_second_raid(self):
        plan = self.state()
        self.run_days(62, plan["raid_day"] + 30)
        self.assertEqual(len(self.raids), 1)


if __name__ == "__main__":
    unittest.main()
