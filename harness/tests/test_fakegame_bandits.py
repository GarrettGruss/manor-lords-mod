"""Tests for the feature bandits of the pack mod (mod feature M04, iteration 01) in the fake game.

They run the real Lua files. HarnessBandits is replaced by a stub that records the call.
They do not prove how the real game behaves (see the real-game runs in the iteration file).
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from test_fakegame_modstate import FNAME, HELPERS, find_pack_mod

STUB = """
package.loaded["HarnessBandits"] = {
    homeless_rebel = function(request)
        REBEL_CALLS = (REBEL_CALLS or 0) + 1
        LAST_REBEL = request
        return { ok = true, families_removed = request.count, squads = { {} }, bandit_units_spawned = 18 }
    end,
}
"""


class BanditsTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        pack = find_pack_mod()
        self.mod_name = pack.name
        self.game.exec(f'package.path = "{(pack / "Scripts").as_posix()}/?.lua;" .. package.path')
        self.game.exec(FNAME + HELPERS + STUB)
        self.pawn = self.game.obj("PawnCPP", Tags=self.game.array([]))
        self.game.method(self.pawn, "playEventMessage", lambda _self, _kind, _text, _sub: None)
        self.game.method(self.pawn, "K2_GetActorLocation", lambda _self: self.game.struct(X=0.0, Y=0.0, Z=0.0))
        self.game.method(self.pawn, "GetAddress", lambda _self: 1)
        self.calendar = self.game.obj("TemporalComponent", daysTotal=61, daysUntilNextRaid=730, Season=1)
        self.region = self.game.obj("Region", ownerPawn=self.pawn, publicOrder=100, Approval=65)
        self.families = 10
        self.game.method(self.region, "getTotalNumFamilies", lambda _self: self.families)
        self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn, TemporalComponent=self.calendar,
                                    regions=self.game.array([self.region]), debugLog_AI_general=self.game.array([]))
        self.game.load_mod(self.mod_name)
        self.game.advance(3)
        self.counter = 0

    def ask(self, name, **args):
        self.counter += 1
        folder = self.game.run_dir / "modcmd" / self.mod_name
        folder.mkdir(parents=True, exist_ok=True)
        body = {"id": f"{self.counter:04d}", "command": f"{self.mod_name}.{name}", "args": args}
        (folder / f"{self.counter:04d}.json").write_text(json.dumps(body), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{self.counter:04d}.result.json").read_text(encoding="utf-8"))

    def state(self):
        answer = self.ask("bandits_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def rebel_calls(self):
        return self.game.exec("return REBEL_CALLS or 0")


class DebuffTests(BanditsTestCase):
    def test_order_is_natural_minus_debuff(self):
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 65)  # approval 65, difficulty 1

    def test_the_debuff_does_not_stack(self):
        self.game.advance(10)
        self.assertEqual(self.region.publicOrder, 65)
        self.assertEqual(self.state()["natural_order"], 100)

    def test_the_game_value_is_taken_as_natural(self):
        self.game.advance(3)
        self.region.publicOrder = 90  # the game recalculates
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 55)
        self.assertEqual(self.state()["natural_order"], 90)

    def test_full_approval_gives_back_the_natural_value(self):
        self.game.advance(3)
        self.assertTrue(self.ask("bandits_set_approval", value=100)["ok"])
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 100)

    def test_difficulty_two_doubles_the_debuff_and_stops_at_zero(self):
        self.ask("invasion_set_difficulty", value=2)
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 30)
        self.ask("bandits_set_approval", value=20)
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 0)


class ConversionTests(BanditsTestCase):
    def low_order(self):
        self.ask("bandits_set_approval", value=0)
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 0)

    def test_low_order_and_a_winning_roll_convert_families(self):
        self.low_order()
        result = self.ask("bandits_tick_now", roll=0.0)["result"]
        self.assertEqual(result["converted_families"], 2)
        self.assertEqual(self.rebel_calls(), 1)
        self.assertEqual(self.game.exec("return LAST_REBEL.mode"), "home")

    def test_a_losing_roll_converts_nothing(self):
        self.low_order()
        self.assertEqual(self.ask("bandits_tick_now", roll=0.99)["result"]["converted_families"], 0)
        self.assertEqual(self.rebel_calls(), 0)

    def test_high_order_never_converts(self):
        self.ask("bandits_set_approval", value=100)
        self.game.advance(3)
        self.assertEqual(self.ask("bandits_tick_now", roll=0.0)["result"]["converted_families"], 0)
        self.assertEqual(self.rebel_calls(), 0)

    def test_the_last_family_stays(self):
        self.families = 2
        self.low_order()
        self.assertEqual(self.ask("bandits_tick_now", roll=0.0)["result"]["converted_families"], 1)

    def test_no_roll_on_the_first_poll_or_in_the_same_season(self):
        self.low_order()
        self.calendar.daysTotal = 61 + 40
        self.game.advance(5)
        self.assertEqual(self.state()["rolls"], 0)
        self.assertEqual(self.state()["last_season"], 1)


class SeasonTickTests(BanditsTestCase):
    def change_season(self, season):
        self.calendar.Season = season
        self.game.advance(3)

    def test_one_roll_per_season_change(self):
        self.change_season(2)
        self.change_season(3)
        self.game.advance(10)
        state = self.state()
        self.assertEqual(state["rolls"], 2)
        self.assertEqual(state["last_season"], 3)

    def test_winter_rolls_once_when_the_year_changes(self):
        self.change_season(3)
        self.change_season(0)
        self.calendar.Year = 2
        self.game.advance(5)
        self.assertEqual(self.state()["rolls"], 2)

    def test_a_season_change_converts_with_a_winning_roll(self):
        self.ask("bandits_set_approval", value=0)
        self.game.advance(3)
        self.game.exec("math.random = function() return 0.0 end")
        self.change_season(2)
        self.assertEqual(self.state()["converted_families"], 2)
        self.assertEqual(self.rebel_calls(), 1)

    def test_a_reload_in_the_same_season_does_not_roll(self):
        self.change_season(2)
        self.assertEqual(self.state()["rolls"], 1)
        self.game.load_mod(self.mod_name)  # ModState keeps the saved season
        self.game.advance(5)
        self.assertEqual(self.state()["rolls"], 1)


class DistributionTests(BanditsTestCase):
    def test_the_conversion_rate_matches_the_chance_bands(self):
        rules = self.game.exec('return require("features.bandits.rules")')
        bands = self.game.exec('return require("config").bandits.bands')
        random = __import__("random").Random(7)
        for order, chance in ((80, 0.0), (60, 0.10), (40, 0.25), (10, 0.50)):
            hits = sum(1 for _ in range(20000) if rules.should_convert(order, bands, random.random()))
            self.assertAlmostEqual(hits / 20000, chance, delta=0.015, msg=f"order {order}")


if __name__ == "__main__":
    unittest.main()
