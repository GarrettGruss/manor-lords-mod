"""Tests for the feature manor_stronghold of the pack mod (mod feature M13) in the fake game.

They run the real Lua files, with a fake manor module that works like the real one in spec 12:
`addToInventory(Good)` adds goods to the building and to the region stock, `consumeGoodNoCheck(good)` removes one unit.
They do not prove how the real game behaves (see the real-game runs in the iteration files).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_tech_tree import TechTreeTestCase

MANOR = """
function(fg, region, built)
    local world = { stock = {}, buildings = {} }
    local function add_stock(kind, amount) world.stock[kind] = (world.stock[kind] or 0) + amount end
    local b = fg.object("SMBuildingMaster", { Data = { bType = 98, constructed = built }, Inventory = fg.array({}, { wrap = false }) },
                        "/Game/Fake/Map.Map:PersistentLevel.SMBuildingMaster_300")
    fg.set_method(b, "IsConstructed", function(self) return self.Data.constructed end)
    fg.set_method(b, "addToInventory", function(self, good)
        local found
        for i = 1, #self.Inventory do if self.Inventory[i].Type == good.Type then found = self.Inventory[i] end end
        if found then found.amt = found.amt + good.amt else fg.array_add(self.Inventory, { Type = good.Type, amt = good.amt }) end
        add_stock(good.Type, good.amt)
    end)
    fg.set_method(b, "consumeGoodNoCheck", function(self, kind)
        for i = 1, #self.Inventory do
            local entry = self.Inventory[i]
            if entry.Type == kind and entry.amt > 0 then entry.amt = entry.amt - 1; add_stock(kind, -1); return end
        end
        error("nothing to consume")
    end)
    world.buildings[1] = b
    fg.set_method(region, "GetBuildings", function() return world.buildings end)
    fg.set_method(region, "getStockOfGood", function(self, kind) return world.stock[kind] or 0 end)
    return world
end
"""

STONE = 27


class ManorStorageTestCase(TechTreeTestCase):
    def setUp(self):
        super().setUp()
        self.world = self.game.lua.eval(MANOR)(self.game.fg, self.region, True)

    def manor(self, name, **args):
        return self.ask(name, **args)

    def prosperity_upgrade(self):
        self.choose("prosperity")
        self.grant(1)
        self.assertTrue(self.unlock("fair_courts")["ok"])
        self.assertTrue(self.unlock("amnesty")["ok"])
        self.game.advance(4)


class CapacityTests(ManorStorageTestCase):
    def test_the_base_capacity_is_200_and_more_is_refused(self):
        self.assertTrue(self.manor("manor_put", good=STONE, amount=200)["ok"])
        answer = self.manor("manor_put", good=STONE, amount=1)
        self.assertFalse(answer["ok"])
        self.assertIn("200", answer["error"])

    def test_the_state_shows_the_capacity_and_the_bonus(self):
        state = self.manor("manor_state")["result"]
        self.assertEqual((state["capacity"], state["storage_bonus"]), (200, 0))

    def test_a_prosperity_node_raises_the_capacity_to_400(self):
        self.prosperity_upgrade()
        self.assertEqual(self.manor("manor_state")["result"]["capacity"], 400)
        self.assertTrue(self.manor("manor_put", good=STONE, amount=300)["ok"])
        self.assertFalse(self.manor("manor_put", good=STONE, amount=101)["ok"])
        self.assertTrue(self.manor("manor_put", good=STONE, amount=100)["ok"])

    def test_an_oppression_node_raises_the_capacity_too(self):
        self.choose("oppression")
        self.grant(1)
        self.unlock("martial_law")
        self.assertTrue(self.unlock("iron_hand")["ok"])
        self.game.advance(4)
        self.assertEqual(self.manor("manor_state")["result"]["capacity"], 400)

    def test_a_first_node_does_not_change_the_capacity(self):
        self.choose("prosperity")
        self.unlock("fair_courts")
        self.game.advance(4)
        self.assertEqual(self.manor("manor_state")["result"]["capacity"], 200)

    def test_the_tree_text_names_the_storage(self):
        self.prosperity_upgrade()
        self.assertIn("Manor storage +200", self.game.lua.eval(
            "function() return require('features.tech_tree.rules').describe_totals({order_bonus=0,approval_bonus=0,buy_back_multiplier=1,"
            "militia_attack_multiplier=1,militia_defence_multiplier=1,manor_storage_bonus=200}) end")())


class PutAndTakeTests(ManorStorageTestCase):
    def test_put_and_take_follow_the_region_stock(self):
        put = self.manor("manor_put", good=STONE, amount=20)["result"]
        self.assertEqual((put["before"], put["after"], put["stock_after"] - put["stock_before"]), (0, 20, 20))
        take = self.manor("manor_take", good=STONE, amount=5)["result"]
        self.assertEqual((take["after"], take["stock_after"] - take["stock_before"]), (15, -5))

    def test_a_take_of_more_than_the_manor_holds_is_refused(self):
        self.manor("manor_put", good=STONE, amount=3)
        self.assertFalse(self.manor("manor_take", good=STONE, amount=4)["ok"])

    def test_without_a_built_manor_a_put_is_refused(self):
        self.world.buildings[1].Data.constructed = False
        answer = self.manor("manor_put", good=STONE, amount=1)
        self.assertFalse(answer["ok"])

    def test_the_goods_stay_after_game_time(self):
        self.manor("manor_put", good=STONE, amount=15)
        self.game.advance(60)
        self.assertEqual(self.manor("manor_state")["result"]["modules"][0]["total"], 15)


class RetinueTests(ManorStorageTestCase):
    def unlock_militia_rights(self, path, nodes):
        self.choose(path)
        self.grant(len(nodes) - 1)
        for node in nodes:
            self.assertTrue(self.unlock(node)["ok"], node)
        self.game.advance(4)

    def test_militia_rights_gives_the_retinue_bonus(self):
        self.unlock_militia_rights("prosperity", ["fair_courts", "amnesty", "militia_rights"])
        self.assertTrue(any("retinue_bonus=12" in line for line in self.game.log_lines()))

    def test_veteran_levies_gives_the_retinue_bonus_on_the_other_path(self):
        self.unlock_militia_rights("oppression", ["martial_law", "iron_hand", "veteran_levies"])
        self.assertTrue(any("retinue_bonus=12" in line for line in self.game.log_lines()))

    def test_no_bonus_before_the_node(self):
        self.unlock_militia_rights("prosperity", ["fair_courts"])
        self.assertFalse(any("retinue_bonus=12" in line for line in self.game.log_lines()))

    def test_the_retinue_hooks_are_registered(self):
        self.assertTrue(any("manor_stronghold" in line and "loaded" in line for line in self.game.log_lines()))


if __name__ == "__main__":
    unittest.main()
