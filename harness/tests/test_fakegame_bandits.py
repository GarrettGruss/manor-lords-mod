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
    bandit_tag = function(request)
        TAGS = (TAGS or 0) + 1
        return { ok = true }
    end,
    bandit_letter = function(_, raw)
        if LETTER_OK ~= false then LETTERS = (LETTERS or 0) + 1 end
        LAST_LETTER = raw
        return { ok = LETTER_OK ~= false }
    end,
}
TELEMETRY = {}
package.loaded["HarnessTelemetry"] = { register = function(name, fn) TELEMETRY[name] = fn end }
package.loaded["HarnessUnits"] = {
    counts = function() return { by_side = { bandit = BANDIT_UNITS or 0 } } end,
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
        self.banners = []
        self.game.method(self.pawn, "playEventMessage", lambda _self, _kind, text, sub: self.banners.append((text, sub)))
        self.game.method(self.pawn, "K2_GetActorLocation", lambda _self: self.game.struct(X=0.0, Y=0.0, Z=0.0))
        self.game.method(self.pawn, "GetAddress", lambda _self: 1)
        self.calendar = self.game.obj("TemporalComponent", daysTotal=61, daysUntilNextRaid=730, Season=1)
        self.region = self.game.obj("Region", ownerPawn=self.pawn, publicOrder=100, Approval=65)
        self.families = 10
        self.slots = 4
        self.homeless = 0
        self.pawn.silver = 83
        self.game.method(self.region, "getTotalNumFamilies", lambda _self: self.families)
        self.game.method(self.region, "getNumHomelessFamilies", lambda _self: self.homeless)
        self.game.method(self.region, "getAvailableLivingSpace", lambda _self: self.game.struct(constructed=self.slots, unconstructed=0))
        self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn, TemporalComponent=self.calendar,
                                    regions=self.game.array([self.region]), debugLog_AI_general=self.game.array([]))
        self.clock = 1000.0
        self.game.method(self.engine, "getGameTimeAdjusted", lambda _self: self.clock)
        self.game.load_mod(self.mod_name)
        self.game.advance(3)
        self.counter = 0
        self.game.exec('require("ManorCore").remove_families = function(_region, count) REMOVED_TOTAL = (REMOVED_TOTAL or 0) + count; return count, count end')

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


class OrderTests(BanditsTestCase):
    def test_a_new_game_starts_at_100_and_the_mod_writes_it(self):
        self.region.publicOrder = 60  # the game's own value
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 100)
        self.assertEqual(self.state()["mod_order"], 100)

    def test_the_game_value_is_overwritten_again(self):
        self.game.advance(3)
        self.region.publicOrder = 40  # the game recalculates
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 100)
        self.assertGreaterEqual(self.state()["overwrites"], 1)

    def test_set_order_writes_the_game_value(self):
        self.ask("bandits_set_order", value=70)
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 70)

    def test_a_reload_keeps_the_order_and_the_tick_day(self):
        self.ask("bandits_set_order", value=70)
        self.calendar.daysTotal = 80
        self.game.advance(3)
        before = self.state()
        self.game.load_mod(self.mod_name)  # ModState keeps the saved values
        self.game.advance(5)
        after = self.state()
        self.assertEqual((after["mod_order"], after["last_tick_day"]), (70, before["last_tick_day"]))


class TickTests(BanditsTestCase):
    def test_no_tick_before_30_days(self):
        self.ask("bandits_set_order", value=50)
        self.calendar.daysTotal = 61 + 29
        self.game.advance(5)
        state = self.state()
        self.assertEqual((state["ticks"], state["mod_order"]), (0, 50))

    def test_a_tick_every_30_days(self):
        self.ask("bandits_set_order", value=50)
        self.game.advance(3)
        self.calendar.daysTotal = 61 + 30
        self.game.advance(3)
        self.calendar.daysTotal = 61 + 59
        self.game.advance(3)
        self.assertEqual(self.state()["ticks"], 1)
        self.calendar.daysTotal = 61 + 61
        self.game.advance(3)
        state = self.state()
        self.assertEqual((state["ticks"], state["mod_order"]), (2, 70))

    def test_a_tick_with_homeless_villagers_is_recorded(self):
        self.homeless = 4
        self.ask("bandits_set_order", value=50)
        tick = self.ask("bandits_tick_now")["result"]["last_tick"]
        self.assertEqual(
            {key: tick[key] for key in ("order_before", "manor_term", "homeless_count", "homeless_term", "order_after")},
            {"order_before": 50, "manor_term": 10, "homeless_count": 4, "homeless_term": 20, "order_after": 40},
        )
        self.assertEqual(self.region.publicOrder, 40)

    def test_the_tick_is_logged(self):
        self.ask("bandits_tick_now")
        self.assertTrue(any("BANDITS tick day=" in line for line in self.game.log_lines()))

    def test_the_tech_tree_order_bonus_adds_to_the_manor_term(self):
        self.game.exec('require("features.bandits.init").set_modifiers({ order_bonus = 5 })')
        self.ask("bandits_set_order", value=50)
        self.assertEqual(self.ask("bandits_tick_now")["result"]["last_tick"]["manor_term"], 15)

    def test_the_telemetry_metric_holds_the_last_tick(self):
        self.ask("bandits_tick_now")
        self.assertEqual(self.game.exec("return TELEMETRY.bandits_order().last_tick.order_after"), 100)


class TimerTests(BanditsTestCase):
    def setUp(self):
        super().setUp()
        self.game.exec('require("config").bandits.tick_days = 100000')  # no tick moves the order in these tests

    def test_low_order_starts_the_timer_with_a_banner(self):
        self.ask("bandits_set_order", value=20)
        state = self.state()
        self.assertTrue(state["timer"]["active"])
        self.assertEqual(state["timer"]["days_left"], 90)
        self.assertEqual(len(self.banners), 1)
        self.assertIn("unrest", self.banners[0][0].lower())

    def test_the_timer_resets_when_order_reaches_25(self):
        self.families = 40
        self.ask("bandits_set_order", value=20)
        self.ask("bandits_set_order", value=25)
        self.assertFalse(self.state()["timer"]["active"])
        self.calendar.daysTotal = 61 + 200
        self.game.advance(5)
        self.assertEqual(self.state()["converted_families"], 0)

    def test_the_warning_shows_once_30_days_before(self):
        self.ask("bandits_set_order", value=20)
        self.calendar.daysTotal = 61 + 59
        self.game.advance(3)
        self.assertEqual(len(self.banners), 1)
        self.calendar.daysTotal = 61 + 60
        self.game.advance(3)
        self.calendar.daysTotal = 61 + 70
        self.game.advance(3)
        self.assertEqual(len(self.banners), 2)
        self.assertIn("about to leave", self.banners[1][0])

    def test_the_villagers_leave_when_the_timer_expires(self):
        self.families = 40
        self.ask("bandits_set_order", value=20)
        self.calendar.daysTotal = 61 + 90
        self.game.advance(3)
        state = self.state()
        self.assertEqual(state["converted_families"], 18)
        self.assertEqual(state["mod_order"], 45)  # 20 + 25
        self.assertFalse(state["timer"]["active"])  # order 45 is not under 25
        self.assertEqual(self.banners[-1][0], "Families have turned to banditry")
        self.assertEqual(self.game.exec("return REMOVED_TOTAL"), 18)

    def test_the_timer_restarts_after_a_leave_when_order_stays_under_25(self):
        self.families = 40
        self.ask("bandits_set_order", value=0)
        self.game.exec('require("config").bandits.order_gain = 10')
        self.calendar.daysTotal = 61 + 90
        self.game.advance(3)
        state = self.state()
        self.assertEqual(state["mod_order"], 10)
        self.assertTrue(state["timer"]["active"])
        self.assertEqual(state["timer"]["days_left"], 90)

    def test_the_last_family_stays(self):
        self.families = 1
        self.ask("bandits_set_order", value=20)
        self.calendar.daysTotal = 61 + 90
        self.game.advance(3)
        self.assertEqual(self.state()["converted_families"], 0)
        self.assertEqual(self.game.exec("return REMOVED_TOTAL or 0"), 0)

    def test_fewer_families_than_18_all_but_one_leave(self):
        self.families = 10
        self.ask("bandits_set_order", value=20)
        self.calendar.daysTotal = 61 + 90
        self.game.advance(3)
        self.assertEqual(self.state()["converted_families"], 9)


class LeaveTests(BanditsTestCase):
    def install_camp_engine(self):
        """The fake engine plays spawnBanditCamp: it makes the bandit pawn when missing and adds 18 bandit units."""
        def spawn(_self):
            self.camp_calls += 1
            if not self.bandit_pawns:
                self.bandit_pawns.append(self.game.obj("PawnCPP", isBandit=True))
            self.game.exec(f"BANDIT_UNITS = (BANDIT_UNITS or 0) + 18")
        self.camp_calls = 0
        self.bandit_pawns = []
        self.relation_calls = []
        self.game.method(self.engine, "spawnBanditCamp", spawn)
        self.game.method(self.engine, "addPawnRelations", lambda _self, pawn: self.relation_calls.append(pawn))

    def test_with_a_bandit_pawn_one_camp_spawns_for_18_families(self):
        self.install_camp_engine()
        self.bandit_pawns.append(self.game.obj("PawnCPP", isBandit=True))
        self.families = 40
        result = self.ask("bandits_leave_now")["result"]
        self.assertEqual(self.camp_calls, 1)  # one camp, not 3 squads
        self.assertEqual(self.rebel_calls(), 0)
        self.assertEqual(self.game.exec("return REMOVED_TOTAL"), 18)
        self.assertEqual(self.relation_calls, [])  # the pawn is not new
        self.assertTrue(result["last_leave"]["spawned"])
        self.assertEqual(result["last_leave"]["removed"], 18)
        self.assertEqual(result["last_leave"]["camps"], 1)
        self.assertEqual(result["last_leave"]["bandit_units"], 18)
        self.assertFalse(result["last_leave"]["pawn_created"])

    def test_without_a_bandit_pawn_the_camp_call_makes_the_pawn(self):
        self.install_camp_engine()
        self.families = 40
        result = self.ask("bandits_leave_now")["result"]
        self.assertEqual(self.camp_calls, 1)
        self.assertEqual(len(self.bandit_pawns), 1)
        self.assertEqual(len(self.relation_calls), 1)  # addPawnRelations for the new pawn
        self.assertTrue(result["last_leave"]["pawn_created"])
        self.assertTrue(result["last_leave"]["spawned"])
        self.assertEqual(result["last_leave"]["removed"], 18)
        self.assertEqual(result["mod_order"], 100)  # clamped
        self.assertEqual(self.game.exec("return REMOVED_TOTAL"), 18)

    def test_the_last_family_stays_and_no_camp_spawns(self):
        self.install_camp_engine()
        self.families = 1
        result = self.ask("bandits_leave_now")["result"]
        self.assertEqual(self.camp_calls, 0)
        self.assertEqual(result["last_leave"]["removed"], 0)

    def test_a_failed_camp_call_is_logged_and_the_families_still_left(self):
        self.install_camp_engine()
        self.game.method(self.engine, "spawnBanditCamp", lambda _self: (_ for _ in ()).throw(RuntimeError("boom")))
        self.families = 40
        result = self.ask("bandits_leave_now")["result"]
        self.assertFalse(result["last_leave"]["spawned"])
        self.assertEqual(result["last_leave"]["removed"], 18)
        self.assertTrue(any("camp failed" in line for line in self.game.log_lines()))


class BuyBackTests(BanditsTestCase):
    """C1, C4 to C7 in the fake game. The stub plays the game: it records the letter, the test moves silver, units and families."""

    def convert(self):
        self.game.obj("PawnCPP", isBandit=True)
        self.ask("bandits_leave_now", count=2)
        self.game.exec("BANDIT_UNITS = 18")
        self.families -= 2

    def letter(self):
        return self.game.exec("return LAST_LETTER"), self.game.exec("return LETTERS or 0")

    def test_a_conversion_adds_outstanding_families(self):
        self.convert()
        self.assertEqual(self.state()["outstanding_families"], 2)

    def test_buy_back_sends_the_letter_with_the_price(self):
        self.convert()
        answer = self.ask("bandits_buy_back")["result"]
        self.assertTrue(answer["accepted"], answer)
        self.assertEqual((answer["price"], answer["expected_families"]), (20, 2))
        raw, count = self.letter()
        self.assertEqual(count, 1)
        self.assertIn("raider_suggestSettle+20", raw)
        self.assertEqual(self.game.exec("return TAGS"), 1)
        self.assertEqual(self.state()["outstanding_families"], 0)

    def test_the_result_is_recorded_when_the_bandits_are_gone(self):
        self.convert()
        self.ask("bandits_buy_back")
        self.game.exec("BANDIT_UNITS = 0")
        self.pawn.silver = 63
        self.families += 2
        self.game.advance(8)
        state = self.state()
        self.assertFalse(state["buy_back_pending"])
        self.assertEqual(state["returned_families"], 2)
        self.assertEqual((state["buy_backs"][0]["silver_paid"], state["buy_backs"][0]["family_gain"]), (20, 2))

    def test_a_failed_deal_gives_the_silver_back_and_keeps_the_families_outstanding(self):
        self.pawn.silver = 100
        self.convert()
        self.ask("bandits_buy_back")
        self.game.exec("BANDIT_UNITS = 0")
        self.pawn.silver = 80  # the game took the price, no family came
        self.clock += 130
        self.game.advance(8)
        state = self.state()
        self.assertFalse(state["buy_back_pending"])
        self.assertEqual(self.pawn.silver, 100)
        self.assertEqual(state["outstanding_families"], 2)
        self.assertEqual(state["returned_families"], 0)
        self.assertEqual((state["buy_backs"][0]["refunded"], state["buy_backs"][0]["family_gain"]), (20, 0))

    def test_the_mod_waits_in_game_time_for_a_late_family(self):
        self.convert()
        self.ask("bandits_buy_back")
        self.game.exec("BANDIT_UNITS = 0")
        self.game.advance(10)  # real time passes, the game clock stands still
        self.assertTrue(self.state()["buy_back_pending"])

    def test_the_price_follows_the_free_slots(self):
        self.convert()
        self.slots = 1
        answer = self.ask("bandits_buy_back")["result"]
        self.assertEqual((answer["price"], answer["expected_families"]), (10, 1))
        self.assertEqual(self.state()["outstanding_families"], 1)

    def refused(self, reason_part):
        before = self.state()["outstanding_families"], self.letter()[1]
        answer = self.ask("bandits_buy_back")["result"]
        self.assertFalse(answer["accepted"], answer)
        self.assertIn(reason_part, answer["reason"])
        self.assertEqual((self.state()["outstanding_families"], self.letter()[1]), before)

    def test_refused_when_silver_is_short(self):
        self.convert()
        self.pawn.silver = 19
        self.refused("silver")

    def test_refused_without_free_homes(self):
        self.convert()
        self.slots = 0
        self.refused("free home")

    def test_refused_when_nothing_is_outstanding(self):
        self.game.exec("BANDIT_UNITS = 18")
        self.refused("no families")

    def test_refused_without_bandit_units(self):
        self.convert()
        self.game.exec("BANDIT_UNITS = 0")
        self.refused("no bandit units")

    def test_a_failed_letter_changes_nothing(self):
        self.convert()
        self.game.exec("LETTER_OK = false")
        self.refused("letter failed")

    def test_a_second_buy_back_waits_for_the_first(self):
        self.convert()
        self.ask("bandits_buy_back")
        self.refused("still running")


if __name__ == "__main__":
    unittest.main()
