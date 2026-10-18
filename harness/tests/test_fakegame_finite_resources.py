"""Tests for the feature finite_resources of the pack mod (mod feature M10) in the fake game.

They run the real Lua files. A fake mine reports its production through ProductionTrackerComponent:getGoodsProducedOver.
They do not prove how the real game behaves (see the real-game runs in the iteration files).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_tech_tree import TechTreeTestCase

IRON = 14

WORLD = """
function(fg, region)
    local world = { produced = {}, limits = {}, calls = {} }
    local mine = fg.object("SMBuildingMaster", { Data = { bType = 99 } }, "/Game/Fake/Map.Map:PersistentLevel.SMBuildingMaster_400")
    local tracker = fg.object("ProductionTrackerComponent", {}, "/Game/Fake/Map.Map:PersistentLevel.SMBuildingMaster_400.Tracker")
    fg.set_method(tracker, "getGoodsProducedOver", function(self, days) return world.produced end)
    mine.ProductionTrackerComponent = tracker
    world.mine = mine
    fg.set_method(region, "GetBuildings", function() return { mine } end)
    fg.set_method(region, "setProductionLimit", function(self, good, amount) world.limits[good] = amount end)
    fg.set_method(region, "setProductionUnlimited", function(self, good) world.limits[good] = nil end)
    fg.set_method(region, "isProductionLimited", function(self, good) return world.limits[good] ~= nil end)
    fg.set_method(region, "getProductionLimit", function(self, good, default) return world.limits[good] or default end)
    return world
end
"""


class FiniteResourcesTestCase(TechTreeTestCase):
    def setUp(self):
        super().setUp()
        self.world = self.game.lua.eval(WORLD)(self.game.fg, self.region)

    def produce(self, amount):
        self.world.produced[IRON] = (self.world.produced[IRON] or 0) + amount
        self.game.advance(12)

    def row(self):
        answer = self.ask("finite_resources_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]["resources"][0]

    def limit(self):
        return self.world.limits[IRON]


class DepositTests(FiniteResourcesTestCase):
    def test_the_start_holds_the_full_stock_and_no_limit(self):
        row = self.row()
        self.assertEqual((row["name"], row["size"], row["mined"], row["remaining"], row["empty"]), ("iron", 400, 0, 400, False))
        self.assertIsNone(self.limit())

    def test_production_that_existed_before_the_first_look_is_not_counted(self):
        self.produce(50)
        self.assertEqual(self.row()["mined"], 0)

    def test_new_production_counts_down_the_stock(self):
        self.game.advance(12)
        self.produce(30)
        self.produce(20)
        row = self.row()
        self.assertEqual((row["mined"], row["remaining"]), (50, 350))
        self.assertIsNone(self.limit())

    def test_an_empty_deposit_limits_the_production_to_zero(self):
        self.game.advance(12)
        self.produce(400)
        row = self.row()
        self.assertEqual((row["remaining"], row["empty"]), (0, True))
        self.assertEqual(self.limit(), 0)

    def test_a_fall_of_the_total_does_not_count(self):
        self.game.advance(12)
        self.produce(40)
        self.world.produced[IRON] = 10
        self.game.advance(12)
        self.produce(5)
        self.assertEqual(self.row()["mined"], 45)

    def test_the_test_command_changes_the_good_and_the_size(self):
        answer = self.ask("finite_resources_test_set", resource="iron", good=16, size=5)
        self.assertEqual((answer["result"]["resources"][0]["good"], answer["result"]["resources"][0]["size"]), (16, 5))
        self.assertFalse(self.ask("finite_resources_test_set", resource="gold", good=16, size=5)["ok"])

    def test_the_stock_is_kept_in_the_pawn_tags(self):
        self.game.advance(12)
        self.produce(7)
        tags = list(self.game.lua.eval("tag_names")(self.pawn).values())
        self.assertIn("invasion:fin_iron_mined=7", tags)


if __name__ == "__main__":
    unittest.main()
