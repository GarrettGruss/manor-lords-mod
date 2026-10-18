"""Tests for the feature tribute of the pack mod (mod feature M08, iteration 01) in the fake game.

They run the real Lua files. The stores of the village are a stub (raid_behavior.world.stores and deposit).
They do not prove how the real game behaves (see the real-game runs in the iteration file).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_vassals import HandoverBase

STORE_STUB = """
HELD = {}
DEPOSITS = {}
local rw = require("features.raid_behavior.world")
rw.stores = function() return { { by_good = { [30] = 100 }, id = 1 } } end
rw.deposit = function(_, good, amount)
    if REFUSE then return false, "store full" end
    HELD[good] = (HELD[good] or 0) + amount
    DEPOSITS[#DEPOSITS + 1] = good .. ":" .. amount
    return true
end
"""


class TributeTests(HandoverBase):
    def setUp(self):
        super().setUp()
        self.game.exec(STORE_STUB)
        region = self.add_region("Eichenhau", True, 4)
        self.game.method(region, "getTotalNumFamilies", lambda _self: 5)
        self.game.advance(10)

    def tribute(self):
        answer = self.ask("tribute_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def change_season(self):
        self.calendar.Season = (self.calendar.Season + 1) % 4
        self.game.advance(5)

    def held(self, good):
        return self.game.exec(f"return HELD[{good}] or 0")

    def test_one_vassal_at_loyalty_50_pays_20_goods_split_over_two_goods(self):
        self.change_season()
        state = self.tribute()
        self.assertEqual((state["ticks"], state["paid_total"]), (1, 20))
        self.assertEqual((self.held(30), self.held(16)), (10, 10))
        payment = state["history"][0]["payments"][0]
        self.assertEqual((payment["families"], payment["production"], payment["amount"]), (5, 100, 20))

    def test_no_vassal_no_tribute(self):
        self.game.exec("local v = require('features.vassals.init'); v.state:set('vassal1_lord', 'none')")
        self.change_season()
        self.assertEqual(self.tribute()["paid_total"], 0)
        self.assertEqual(self.game.exec("return #DEPOSITS"), 0)

    def test_one_payment_for_one_season_change(self):
        self.change_season()
        self.game.advance(30)
        self.assertEqual(self.tribute()["ticks"], 1)
        self.change_season()
        self.assertEqual(self.tribute()["ticks"], 2)

    def test_no_tick_on_the_first_poll(self):
        self.assertEqual(self.tribute()["ticks"], 0)

    def test_loyalty_100_pays_30_and_loyalty_0_pays_10(self):
        for loyalty, want in ((100, 30), (0, 10)):
            self.ask("vassals_set_loyalty", slot=1, value=loyalty)
            before = self.tribute()["paid_total"]
            self.change_season()
            self.assertEqual(self.tribute()["paid_total"] - before, want, loyalty)

    def test_a_refused_deposit_is_counted_and_not_paid(self):
        self.game.exec("REFUSE = true")
        self.change_season()
        state = self.tribute()
        self.assertEqual(state["paid_total"], 0)
        self.assertEqual(state["failed_deposits"], 2)

    def test_the_forced_tick_pays_at_once(self):
        answer = self.ask("tribute_tick_now")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["result"]["paid_total"], 20)

    def test_the_policy_scales_the_share(self):
        for policy, factor in (("heavy", 1.5), ("light", 0.5)):
            self.ask("vassals_set_policy", slot=1, policy=policy)
            self.change_season()
            payment = self.tribute()["history"][-1]["payments"][0]
            self.assertEqual(payment["policy"], policy)
            self.assertAlmostEqual(payment["share"], (0.10 + 0.20 * payment["loyalty"] / 100) * factor)


    def test_a_submitted_vassal_pays_nothing(self):
        self.ask("vassals_set_loyalty", slot=1, value=5)
        self.ask("vassals_submission_tick_now")
        self.change_season()
        self.assertEqual(self.tribute()["paid_total"], 0)

    def raid_result(self, region, state, leave_reason=None):
        args = {"region": region, "state": state}
        if leave_reason:
            args["leave_reason"] = leave_reason
        answer = self.ask("tribute_test_raid_result", **args)
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def loyalty(self):
        return self.state()["vassals"][0]["loyalty"]

    def test_an_undefended_raid_on_a_vassal_lowers_loyalty_by_15(self):
        self.raid_result("Eichenhau", "left", "loot")
        self.assertEqual(self.loyalty(), 35)
        self.assertEqual(self.tribute()["protection_failed"], 1)

    def test_a_defended_raid_raises_loyalty_by_5(self):
        self.raid_result("Eichenhau", "left", "losses")
        self.raid_result("Eichenhau", "destroyed")
        self.assertEqual(self.loyalty(), 60)
        self.assertEqual(self.tribute()["protection_defended"], 2)

    def test_a_raid_on_the_home_region_changes_nothing(self):
        self.assertFalse(self.raid_result("Home", "left", "loot")["event"])
        self.assertEqual(self.loyalty(), 50)

    def test_three_undefended_raids_make_the_vassal_submit_at_the_next_season_and_tribute_stops(self):
        for _ in range(3):
            self.raid_result("Eichenhau", "left", "time")
        self.assertEqual(self.loyalty(), 5)
        self.change_season()
        self.assertTrue(self.state()["vassals"][0]["submitted"])
        paid = self.tribute()["paid_total"]  # the tribute tick may run before the submission in the same season change
        self.change_season()
        self.assertEqual(self.tribute()["paid_total"], paid)

    def test_loyalty_is_clamped(self):
        for _ in range(5):
            self.raid_result("Eichenhau", "left", "loot")
        self.assertEqual(self.loyalty(), 0)
        self.ask("vassals_set_loyalty", slot=1, value=98)
        self.raid_result("Eichenhau", "destroyed")
        self.assertEqual(self.loyalty(), 100)

    # -- vassal targets and siege (M02 iteration 07) ----------------------------------------

    def stub_raid(self, living=18, age=9, target="Eichenhau", kind="subjugation"):
        today = self.calendar.daysTotal
        self.game.exec(f'''require("features.raid_behavior.init").active_raids = function()
            return {{ {{ id = 7, kind = "{kind}", state = "active", target = "{target}", start_day = {today - age}, initial = 18, living = {living} }} }}
        end''')
        self.game.advance(4)

    def test_the_target_regions_are_the_handed_over_vassals(self):
        self.assertEqual(self.game.exec("local r = require('features.vassals.init').target_regions(); return table.concat(r, ',')"), "Eichenhau")

    def test_a_submitted_vassal_is_no_target(self):
        self.ask("vassals_set_loyalty", slot=1, value=5)
        self.ask("vassals_submission_tick_now")
        self.assertEqual(self.game.exec("return #require('features.vassals.init').target_regions()"), 0)

    def test_a_subjugation_raid_that_held_8_days_takes_the_vassal(self):
        self.stub_raid(living=18, age=9)
        state = self.state()
        self.assertEqual(state["lost"], 1)  # the fake region keeps its player owner, so the scan registers it again; the real region stays with its lord
        self.assertEqual(state["lost_events"][0]["reason"], "taken")
        self.assertEqual(self.tribute()["siege"], {"7": "taken"})

    def test_the_vassal_is_lost_only_once(self):
        self.stub_raid(age=9)
        self.stub_raid(age=20)
        self.assertEqual(self.state()["lost"], 1)

    def test_a_raid_younger_than_8_days_takes_nothing(self):
        self.stub_raid(age=5)
        self.assertEqual(self.state()["lost"], 0)

    def test_a_beaten_raid_fails_and_the_vassal_stays(self):
        self.stub_raid(living=8, age=9)
        self.assertEqual(self.state()["lost"], 0)
        self.assertEqual(self.tribute()["siege"], {"7": "failed"})

    def test_a_plunder_raid_or_a_raid_on_home_takes_nothing(self):
        self.stub_raid(age=9, kind="plunder")
        self.stub_raid(age=9, target="Home")
        self.assertEqual(self.state()["lost"], 0)


if __name__ == "__main__":
    unittest.main()
