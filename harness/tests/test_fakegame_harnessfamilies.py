"""Mock tests for family_state, family_eject and family_add (spec 15, part 7).

The fake region records the calls. It tests the Lua module logic, not how the real game rehouses families.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

BUILD_WORLD = """
function(fg)
    local world = { set_home_calls = {}, new_families = {}, left = 0 }
    local player = fg.object("MyPawnCPP_BP3_C", { isMainPlayer = true })
    local function house(ids)
        local b = fg.object("SMBuildingMaster", { Data = { bType = 3 }, occupantFamilyIDs = fg.array(ids, { wrap = false }) })
        fg.set_method(b, "isResidentialBuilding", function() return true end)
        fg.set_method(b, "IsConstructed", function() return true end)
        fg.set_method(b, "IsRubble", function() return false end)
        fg.set_method(b, "isHomelessTent", function() return false end)
        return b
    end
    local buildings = { house({ 11, 12 }), house({ 13 }) }
    local function unit()
        local u = fg.object("SMUnit", { dead = false, role = 1 })
        fg.set_method(u, "removeFromFamilyIfHasOne", function() world.left = world.left + 1 end)
        return u
    end
    local families = {
        fg.object("Family", { familyMembers = fg.array({ unit(), unit() }, { wrap = false }) }),
        fg.object("Family", { familyMembers = fg.array({ unit() }, { wrap = false }) }),
    }
    local region = fg.object("Region", { regionName = "Riesenbuckel", Approval = 70, publicOrder = 100 })
    region.ownerPawn = player
    region.workerFamilies = fg.array(families, { wrap = false })
    player.currentRegion = region
    fg.set_method(region, "GetBuildings", function() return buildings end)
    fg.set_method(region, "getTotalNumFamilies", function() return 3 end)
    fg.set_method(region, "getNumHomelessFamilies", function() return #world.new_families end)
    fg.set_method(region, "getNumHumanResidents", function() return 6 end)
    fg.set_method(region, "getLivingSpace", function() return { constructed = 3, unconstructed = 0 } end)
    fg.set_method(region, "getAvailableLivingSpace", function() return { constructed = 0, unconstructed = 0 } end)
    fg.set_method(region, "getBuildingCount", function() return 0 end)
    fg.set_method(region, "GetMonthlyPopGrowthModifiersWithValues", function() return { [1] = 1, [3] = 2 } end)
    fg.set_method(region, "SetFamilyHome", function(self, id, home, suppress)
        world.set_home_calls[#world.set_home_calls + 1] = { id = id, home_is_nil = home == nil, suppress = suppress }
    end)
    fg.set_method(region, "AddNewFamily", function(self, members)
        world.new_families[#world.new_families + 1] = #members
        return 100 + #world.new_families
    end)
    fg.object("RTSMultiEngineCPP", { playerRef = player, regions = fg.array({ region }, { wrap = false }) })
    return world
end
"""


class FamilyTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.world = self.game.lua.eval(BUILD_WORLD)(self.game.fg)
        self.game.load_mod("HarnessActions")
        self.game.advance(1)
        self.number = 0

    def send(self, command, **fields):
        self.number += 1
        folder = self.game.run_dir / "commands"
        folder.mkdir(exist_ok=True)
        (folder / f"{self.number:04d}.json").write_text(json.dumps({"id": f"{self.number:04d}", "command": command, **fields}), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{self.number:04d}.result.json").read_text(encoding="utf-8"))


class StateTests(FamilyTestCase):
    def test_state_lists_housed_ids_and_approval(self):
        state = self.send("family_state")
        self.assertTrue(state["ok"], state)
        self.assertEqual(state["housed_ids"], [11, 12, 13])
        self.assertEqual(state["region"]["approval"], 70)

    def test_state_reads_the_monthly_growth_modifiers(self):
        growth = self.send("family_state")["growth"]
        self.assertEqual((growth["1"], growth["3"]), (1, 2))
        self.assertNotIn("error", growth)


class EjectTests(FamilyTestCase):
    def test_eject_calls_set_family_home_with_an_empty_home(self):
        answer = self.send("family_eject", count=2, suppress=True)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["ejected"], [11, 12])
        calls = self.world.set_home_calls
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[1].home_is_nil)
        self.assertTrue(calls[1].suppress)

    def test_suppress_false_is_passed_on(self):
        self.send("family_eject", count=1, suppress=False)
        self.assertFalse(self.world.set_home_calls[1].suppress)

    def test_suppress_defaults_to_true(self):
        self.send("family_eject", count=1)
        self.assertTrue(self.world.set_home_calls[1].suppress)

    def test_eject_refuses_bad_counts(self):
        for count in (0, 11):
            self.assertFalse(self.send("family_eject", count=count)["ok"])
        self.assertFalse(self.send("family_eject")["ok"])
        self.assertEqual(len(self.world.set_home_calls), 0)

    def test_eject_refuses_more_than_housed(self):
        answer = self.send("family_eject", count=4)
        self.assertFalse(answer["ok"])
        self.assertIn("housed", answer["error"])
        self.assertEqual(len(self.world.set_home_calls), 0)


    def test_eject_refuses_an_unknown_home(self):
        self.assertFalse(self.send("family_eject", count=1, home="castle")["ok"])
        self.assertEqual(len(self.world.set_home_calls), 0)

    def test_eject_into_a_tent_needs_a_tent(self):
        answer = self.send("family_eject", count=1, home="tent")
        self.assertFalse(answer["ok"])
        self.assertIn("tent", answer["error"])
        self.assertEqual(len(self.world.set_home_calls), 0)


class AddTests(FamilyTestCase):
    def test_add_takes_a_spare_member_and_makes_a_family(self):
        answer = self.send("family_add", count=1)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.world.left, 1)
        self.assertEqual(list(self.world.new_families), [1])
        self.assertEqual(answer["added"][0]["family_id"], 101)

    def test_add_refuses_a_bad_count(self):
        self.assertFalse(self.send("family_add", count=11)["ok"])
        self.assertEqual(len(self.world.new_families), 0)


if __name__ == "__main__":
    unittest.main()
