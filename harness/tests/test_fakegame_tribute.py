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


if __name__ == "__main__":
    unittest.main()
