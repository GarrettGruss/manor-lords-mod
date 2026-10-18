"""Tests for the fallback capital of the feature sack_and_terms (M06 iteration 03) in the fake game.

They run the real Lua files. The game calls (take the region back, settle, the stores) are stubs.
They do not prove how the real game behaves (see the real-game runs in the iteration file).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_vassals import HandoverBase

STUB = """
CALLS = {}
CONSUMED = 0
local lords = package.loaded["HarnessLords"]
lords.region_clear_owner = function(request)
    CALLS[#CALLS + 1] = "clear:" .. request.region
    if FAIL_CLEAR then return { ok = false, error = "no" } end
    return { ok = true }
end
local old_claim = lords.claim_region
lords.claim_region = function(request)
    CALLS[#CALLS + 1] = "claim:" .. request.region
    return old_claim(request)
end
local core = require("ManorCore")
core.settle_region = function(request)
    CALLS[#CALLS + 1] = "settle:" .. request.region
    return { ok = true }
end
local rw = require("features.raid_behavior.world")
local store = { by_good = { [30] = 50 }, building = { consumeGoodNoCheck = function() CONSUMED = CONSUMED + 1 end } }
rw.stores = function() return { store } end
"""


class FallbackTests(HandoverBase):
    def setUp(self):
        super().setUp()
        self.game.exec(STUB)
        self.region = self.add_region("Eichenhau", True, 12)
        self.game.exec("REGIONS[2].buildings = 12; REGIONS[2].owner = 'Lord'")
        self.deposits = []
        building = self.game.obj("Building")
        self.game.method(building, "IsRubble", lambda _self: False)
        self.game.method(building, "addToInventory", lambda _self, good: self.deposits.append(good))
        self.game.method(self.region, "GetBuildings", lambda _self: self.game.array([building]))
        self.game.advance(10)  # the handover
        self.pawn.silver = 1000
        self.ask("fallback_set_take_back", mode="clear")

    def move(self, slot=1):
        return self.ask("fallback_move", slot=slot)

    def calls(self):
        return list(self.game.exec("return table.concat(CALLS, ',')").split(","))

    def test_the_move_takes_the_region_back_pays_and_moves_grain(self):
        answer = self.move()
        self.assertTrue(answer["ok"], answer)
        result = answer["result"]
        self.assertEqual(result["slot"], 1)
        self.assertEqual(self.pawn.silver, 850)
        self.assertEqual(result["last"]["grain_taken"], 20)
        self.assertEqual(self.game.exec("return CONSUMED"), 20)
        self.assertEqual(len(self.deposits), 1)
        self.assertEqual(self.calls(), ["clear:Eichenhau", "claim:Eichenhau", "settle:Eichenhau"])

    def test_the_vassal_slot_becomes_the_capital_and_is_not_handed_over_again(self):
        self.move()
        self.game.advance(20)
        row = self.state()["vassals"][0]
        self.assertTrue(row["capital"])
        self.assertEqual(row["lord"], "none")
        self.assertEqual(self.game.exec("return #SPAWNED"), 1)

    def test_a_vassal_below_the_fortified_size_is_refused(self):
        self.game.exec("REGIONS[2].buildings = 5")
        answer = self.move()
        self.assertFalse(answer["ok"])
        self.assertIn("fortified", answer["error"])
        self.assertEqual(self.pawn.silver, 1000)

    def test_not_enough_silver_is_refused(self):
        self.pawn.silver = 100
        answer = self.move()
        self.assertFalse(answer["ok"])
        self.assertIn("silver", answer["error"])

    def test_an_empty_slot_is_refused(self):
        self.assertFalse(self.move(slot=2)["ok"])

    def test_a_second_fallback_capital_is_refused(self):
        self.move()
        answer = self.move()
        self.assertFalse(answer["ok"])

    def test_nothing_is_paid_when_the_region_cannot_be_taken_back(self):
        self.game.exec("FAIL_CLEAR = true")
        answer = self.move()
        self.assertFalse(answer["ok"])
        self.assertEqual(self.pawn.silver, 1000)
        self.assertEqual(self.game.exec("return CONSUMED"), 0)

    def test_the_cost_grows_with_the_difficulty(self):
        self.ask("invasion_set_difficulty", value=3)
        self.move()
        self.assertEqual(self.pawn.silver, 1000 - 450)

    def test_the_default_variant_writes_the_owner_and_makes_no_claim_calls(self):
        self.ask("fallback_set_take_back", mode="write")
        self.region.ownerPawn = None
        answer = self.move()
        self.assertTrue(answer["ok"], answer)
        self.assertIsNotNone(self.region.ownerPawn)
        self.assertEqual(self.game.exec("return CALLS[1]"), "settle:Eichenhau")
        self.assertEqual(self.calls(), ["settle:Eichenhau"])


if __name__ == "__main__":
    unittest.main()
