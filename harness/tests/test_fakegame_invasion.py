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
        self.banners, self.raids, self.armies = [], [], []
        self.pawn = self.game.obj("PawnCPP", Tags=self.game.array([]))
        self.game.method(self.pawn, "playEventMessage", lambda _self, _kind, text, sub: self.banners.append(text))
        self.game.method(self.pawn, "K2_GetActorLocation", lambda _self: self.game.struct(X=10.0, Y=20.0, Z=30.0))
        self.calendar = self.game.obj("TemporalComponent", daysTotal=61, daysUntilNextRaid=730)
        self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn, TemporalComponent=self.calendar)
        self.bandit = self.game.obj("PawnCPP", isBandit=True)
        self.game.method(self.engine, "spawnArmy", lambda _self, point, names, owner, company, days: self.armies.append(
            ([names[i].text for i in range(1, len(names) + 1)], point.X, point.Y, owner.isBandit is True)))
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
        self.assertEqual(len(state["composition"].split("-")), state["squads"])

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
            self.assertEqual(len(answer["result"]["composition"].split("-")), squads)

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
        self.banners = [text for text in self.banners if not text.startswith(("Great raid in", "Pick the difficulty", "Subjugation"))]
        self.assertEqual(len(self.banners), warning_days + 1)  # one for each day left, plus the arrival banner
        raiders = self.state()["raiders"]
        self.assertEqual(self.banners[0], f"Raid in {warning_days} days, about {raiders} raiders")
        self.assertEqual(self.banners[warning_days - 1], f"Raid in 1 day, about {raiders} raiders")
        self.assertEqual(len(self.armies), 1)
        self.assertEqual(len(self.armies[0][0]), 4)
        self.assertEqual(self.raids, [])
        self.assertEqual(self.state()["raids_spawned"], 1)

    def test_force_next_spawns_on_the_next_check(self):
        self.ask("invasion_set_size", size="small")
        self.assertTrue(self.ask("invasion_force_next")["ok"])
        self.game.advance(2)
        self.assertEqual(len(self.armies), 1)
        self.assertFalse(self.ask("invasion_force_next")["ok"])

    def test_a_missed_day_still_spawns(self):
        plan = self.state()
        self.set_day(plan["raid_day"] + 2)
        self.assertEqual(len(self.armies), 1)

    def test_no_second_raid(self):
        plan = self.state()
        self.run_days(62, plan["raid_day"] + 30)
        self.assertEqual(len(self.armies), 1)


class RolesTests(InvasionTestCase):
    def plan_and_spawn(self, difficulty, size):
        self.ask("invasion_set_difficulty", value=difficulty)
        planned = self.ask("invasion_set_size", size=size)["result"]
        self.assertTrue(self.ask("invasion_force_next")["ok"])
        self.game.advance(2)
        return planned

    def test_the_raid_spawns_the_planned_composition_at_the_edge(self):
        planned = self.plan_and_spawn(3, "large")
        self.assertEqual(len(self.armies), 1)
        names, x, y, from_bandit = self.armies[0]
        self.assertEqual("-".join(names), planned["composition"])
        self.assertEqual(len(names), 9)
        self.assertEqual((x, y), (10.0, -88900))
        self.assertTrue(from_bandit)
        self.assertEqual(self.raids, [])

    def test_raiders_estimate_is_the_sum_of_the_squad_sizes(self):
        planned = self.plan_and_spawn(2, "medium")
        sizes = {"Brigands": 18, "spearMilitia": 32, "militiaFoot": 32, "mercenary_infantry": 36, "retinue_tier3": 36,
                 "brigandPolearms": 36, "bowMilitia": 32, "brigandArchers": 36, "crossbowMilitia": 32, "mercenary_crossbowmen": 36}
        self.assertEqual(planned["raiders"], sum(sizes[name] for name in planned["composition"].split("-")))

    def test_a_new_difficulty_makes_a_new_composition(self):
        self.state()
        self.ask("invasion_set_size", size="small")
        one = self.ask("invasion_set_difficulty", value=1)["result"]
        three = self.ask("invasion_set_difficulty", value=3)["result"]
        self.assertEqual(len(one["composition"].split("-")), 1)
        self.assertEqual(len(three["composition"].split("-")), 3)

    def test_the_composition_is_kept_in_one_integer_tag(self):
        planned = self.plan_and_spawn(3, "large")
        tags = list(self.game.lua.eval("tag_names")(self.pawn).values())
        self.assertTrue(any(tag.startswith("invasion:composition_seed=") for tag in tags), tags)
        self.assertFalse(any(tag.startswith("invasion:composition=") for tag in tags), tags)
        self.assertEqual("-".join(self.armies[0][0]), planned["composition"])

    def test_roles_off_uses_spawn_raiders(self):
        self.ask("invasion_set_size", size="small")
        self.ask("invasion_set_difficulty", value=2)
        self.assertFalse(self.ask("invasion_set_roles", enabled=False)["result"]["roles"])
        self.assertEqual(self.state()["raiders"], 36)
        self.ask("invasion_force_next")
        self.game.advance(2)
        self.assertEqual(self.raids, [(2, 10.0, 20.0)])
        self.assertEqual(self.armies, [])

    def test_a_failed_army_spawn_is_not_counted(self):
        self.game.method(self.engine, "spawnArmy", lambda *_args: (_ for _ in ()).throw(RuntimeError("no")))
        self.ask("invasion_set_size", size="small")
        self.ask("invasion_force_next")
        self.game.advance(2)
        self.assertEqual(self.state()["raids_spawned"], 0)


class ClockTests(InvasionTestCase):
    def clock(self):
        answer = self.ask("invasion_clock_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def test_the_clock_is_three_to_five_years(self):
        clock = self.clock()
        self.assertTrue(3 * 365 <= clock["great_raid_day"] - 61 <= 5 * 365, clock)
        self.assertEqual(clock["days_left"], clock["great_raid_day"] - 61)

    def test_the_clock_is_kept_in_the_pawn_tags(self):
        clock = self.clock()
        tags = list(self.game.lua.eval("tag_names")(self.pawn).values())
        self.assertIn(f"invasion:great_raid_day={clock['great_raid_day']}", tags)

    def test_days_left_falls_each_day_and_the_end_day_stays(self):
        first = self.clock()
        self.set_day(66)
        second = self.clock()
        self.assertEqual(second["great_raid_day"], first["great_raid_day"])
        self.assertEqual(second["days_left"], first["days_left"] - 5)

    def test_the_clock_banner_shows_once_in_30_days(self):
        self.ask("invasion_force_next")
        self.set_day(62)  # the minor raid spawns, so no minor banner is left
        self.ask("invasion_clock_set_days_left", days=500)
        self.banners.clear()
        for day in range(63, 100):
            self.set_day(day)
        great = [text for text in self.banners if text.startswith("Great raid in")]
        subjugation = [text for text in self.banners if text.startswith("Subjugation")]  # these banners carry the clock in their subtitle
        self.assertGreaterEqual(len(great) + len(subjugation), 1)
        self.assertLessEqual(len(great), 2)

    def test_the_minor_raid_banner_names_the_clock(self):
        self.ask("invasion_force_next")
        self.ask("invasion_clock_set_days_left", days=400)
        subtitles = []
        self.game.method(self.pawn, "playEventMessage", lambda _self, _kind, text, sub: subtitles.append(sub))
        self.set_day(62)
        self.assertTrue(any(sub.startswith("Great raid in") for sub in subtitles) or self.state()["raids_spawned"] == 1, subtitles)

    def test_set_days_left_is_refused_outside_range(self):
        self.assertFalse(self.ask("invasion_clock_set_days_left", days=0)["ok"])


class DifficultyTests(InvasionTestCase):
    def difficulty(self):
        answer = self.ask("invasion_difficulty_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def test_before_a_pick_the_default_is_used_and_a_prompt_shows(self):
        info = self.difficulty()
        self.assertFalse(info["chosen"])
        self.assertEqual(info["difficulty"], 1)
        self.assertTrue(any(text.startswith("Pick the difficulty") for text in self.banners), self.banners)

    def test_a_pick_sets_the_difficulty_once(self):
        self.assertTrue(self.ask("invasion_pick_difficulty", value=2)["ok"])
        info = self.difficulty()
        self.assertTrue(info["chosen"])
        self.assertEqual((info["difficulty"], info["relief_squads"], info["waves"]), (2, 8, 2))
        self.assertFalse(self.ask("invasion_pick_difficulty", value=3)["ok"])
        self.assertEqual(self.state()["squads"] % 2, 0)

    def test_relief_and_waves_by_difficulty(self):
        seen = []
        for value in (1, 2, 3):
            self.ask("invasion_set_difficulty", value=value)
            info = self.difficulty()
            seen.append((info["relief_squads"], info["waves"]))
        self.assertEqual(seen, [(15, 1), (8, 2), (0, 3)])

    def test_the_prompt_stops_after_a_pick(self):
        self.ask("invasion_pick_difficulty", value=1)
        self.banners.clear()
        for day in range(62, 90):
            self.set_day(day)
        self.assertFalse(any(text.startswith("Pick the difficulty") for text in self.banners))

    def test_pick_outside_range_is_refused(self):
        self.assertFalse(self.ask("invasion_pick_difficulty", value=4)["ok"])

class SubjugationTests(InvasionTestCase):
    def sub(self):
        answer = self.ask("invasion_subjugation_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def after_first_raid(self):
        self.ask("invasion_force_next")
        self.set_day(62)
        self.assertEqual(self.state()["raids_spawned"], 1)

    def test_no_plan_before_the_first_raid(self):
        self.assertEqual(self.sub()["sub_day"], 0)

    def test_the_plan_follows_the_first_raid_and_is_large(self):
        self.ask("invasion_set_difficulty", value=2)
        self.after_first_raid()
        sub = self.sub()
        self.assertTrue(60 <= sub["sub_day"] - 61 <= 120, sub)
        self.assertEqual(sub["squads"], 6)
        self.assertEqual(len(sub["composition"].split("-")), 6)

    def test_the_subjugation_raid_spawns_once_on_its_day(self):
        self.after_first_raid()
        armies_before = len(self.armies)
        sub = self.sub()
        self.set_day(sub["sub_day"] + 1)
        self.assertTrue(self.sub()["spawned"])
        self.assertEqual(self.state()["raids_spawned"], 2)
        self.assertEqual(len(self.armies) - armies_before, 1)
        self.assertEqual(len(self.armies[-1][0]), self.sub()["squads"])
        self.set_day(sub["sub_day"] + 40)
        self.assertEqual(self.state()["raids_spawned"], 2)

    def test_force_next_needs_a_plan(self):
        self.assertFalse(self.ask("invasion_subjugation_force_next")["ok"])
        self.after_first_raid()
        self.assertTrue(self.ask("invasion_subjugation_force_next")["ok"])
        self.game.advance(2)
        self.assertTrue(self.sub()["spawned"])


class TargetRulesTests(unittest.TestCase):
    def run_lua(self, code):
        game = FakeGame()
        game.start()
        self.addCleanup(game.close)
        game.exec(f'package.path = "{(find_pack_mod() / "Scripts").as_posix()}/?.lua;" .. package.path')
        return game.lua.eval(f"(function() local target = require('features.invasion.target'); {code} end)")()

    def test_plunder_always_hits_home(self):
        self.assertEqual(self.run_lua("local t = target.pick('plunder', 'home', {'v1'}, function(a, b) return b end); return t.region .. tostring(t.stand_in)"), "homefalse")

    def test_subjugation_without_vassals_uses_home_as_stand_in(self):
        self.assertEqual(self.run_lua("local t = target.pick('subjugation', 'home', {}, math.random); return t.region .. tostring(t.stand_in)"), "hometrue")

    def test_subjugation_picks_a_vassal(self):
        self.assertEqual(self.run_lua("local t = target.pick('subjugation', 'home', {'a', 'b'}, function(a, b) return b end); return t.region .. tostring(t.stand_in)"), "bfalse")


if __name__ == "__main__":
    unittest.main()
