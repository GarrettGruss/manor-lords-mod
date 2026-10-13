"""Mock tests for the reverse direction of spec 15: families become bandits (homeless_rebel, bandit_spawn_at, bandit_turn).

The fake world follows the facts of implementation-notes/homeless-rebellion.md:
  - sack_people kills every member of a family; the family leaves the count of the region at once and is not homeless;
  - RTSMultiEngineCPP:spawnArmy(position, names, owner, 0, 0) makes one squad of maxSize units per name (Brigands: 18) for the owner pawn;
  - SMUnit:turnToBandit takes the unit out of its family and gives it the role Soldier.
It tests the Lua module logic. It does NOT prove how the real game decides.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

BUILD_WORLD = """
function(fg)
    local world = { spawn_positions = {}, next_squad = 20, turned = 0 }
    local player = fg.object("PawnCPP", { isMainPlayer = true, isBandit = false, isAI = false, commandedSquads = fg.array({}, { wrap = false }) }, "/Game/Fake/Player")
    fg.set_method(player, "GetAddress", function() return 1 end)
    fg.set_method(player, "K2_GetActorLocation", function() return { X = 1000.0, Y = 2000.0, Z = 30.0 } end)
    local bandit = fg.object("PawnCPP", { isMainPlayer = false, isBandit = true, isAI = true, commandedSquads = fg.array({}, { wrap = false }) }, "/Game/Fake/Bandit")

    local rows, names = {}, {}
    for _, row in ipairs({ { "spearMilitia", 32 }, { "Brigands", 18 } }) do
        rows[row[1]] = fg.object("UnitTemplateRow", { cost = 0.0, maxSize = row[2], minMeleeTraining = 0.0, minArcheryTraining = 0.0, minHouseLv = 1,
                                                      combatExperience = 5.0, Name = row[1] })
        names[#names + 1] = row[1]
    end
    local dataTable = fg.object("DataTable", {}, "/Game/NotStronghold/Data/DT_UnitTemplates.DT_UnitTemplates")
    fg.set_method(dataTable, "GetRowNames", function() return names end)
    fg.set_method(dataTable, "GetRowStruct", function() return fg.object("ScriptStruct", {}, "/Script/ManorLords.UnitTemplate") end)
    fg.set_method(dataTable, "FindRow", function(self, name) return rows[name] end)

    local families = {}
    local function add_family(x, y, members)
        local home = fg.object("SMBuildingMaster", {})
        fg.set_method(home, "K2_GetActorLocation", function() return { X = x, Y = y, Z = 50.0 } end)
        local list = {}
        for _ = 1, members do
            local unit = fg.object("SMUnit", { dead = false, currentUnitRole = 0, assignedSquadID = { Value = 3 }, realPos = { X = x, Y = y, Z = 50.0 }, family = true })
            fg.set_method(unit, "just_die", function(self) self.dead = true end)
            fg.set_method(unit, "hasValidFamily", function(self) return self.family end)
            fg.set_method(unit, "turnToBandit", function(self) self.family = false self.currentUnitRole = 5 world.turned = world.turned + 1 end)
            list[#list + 1] = unit
        end
        families[#families + 1] = { familyHome = home, familyMembers = fg.array(list, { wrap = false }), list = list }
    end
    add_family(100.0, 200.0, 3)
    add_family(300.0, 400.0, 2)
    add_family(500.0, 600.0, 4)
    local function living(family)
        local count = 0
        for _, unit in ipairs(family.list) do if not unit.dead then count = count + 1 end end
        return count
    end
    local region = fg.object("Region", { ownerPawn = player, regionName = fg.text("Test Village"), workerFamilies = fg.array(families, { wrap = false }) })
    fg.set_method(region, "getTotalNumFamilies", function()
        local count = 0
        for _, family in ipairs(families) do if living(family) > 0 then count = count + 1 end end
        return count
    end)
    fg.set_method(region, "getNumHomelessFamilies", function() return 0 end)
    fg.set_method(region, "getNumHumanResidents", function()
        local count = 0
        for _, family in ipairs(families) do count = count + living(family) end
        return count
    end)
    fg.set_method(region, "getAvailableLivingSpace", function() return { constructed = 1, unconstructed = 0 } end)
    fg.set_method(region, "GetBuildings", function() return {} end)
    fg.set_method(region, "getSettledRegionCenter", function() return { X = 1.0, Y = 1.0, Z = 0.0 } end)

    local engine = fg.object("RTSMultiEngineCPP", { playerRef = player, regions = fg.array({ region }, { wrap = false }) })
    fg.set_method(engine, "spawnArmy", function(self, position, template_names, owner, company, days)
        local ids = {}
        for _, name in ipairs(template_names) do
            local id = world.next_squad
            world.next_squad = id + 1
            world.spawn_positions[#world.spawn_positions + 1] = { x = position.X, y = position.Y, owner = owner.isBandit and "bandit" or "player" }
            fg.array_add(owner.commandedSquads, { Value = id })
            for _ = 1, rows[name.fname].maxSize do
                local unit = fg.object("SMUnit", { dead = false, assignedSquadID = { Value = id }, currentUnitRole = 5, ItemsLooted = 0, morale = 1.0,
                                                   combatExperience = 0.0, realPos = { X = position.X, Y = position.Y, Z = position.Z }, family = false })
                fg.set_method(unit, "hasValidFamily", function(self) return self.family end)
                fg.set_method(unit, "turnToBandit", function(self) world.turned = world.turned + 1 end)
                fg.set_method(unit, "just_die", function(self) self.dead = true end)
            end
            ids[#ids + 1] = { Value = id }
        end
        return ids
    end)
    -- A real raid appears at the map edge; the target only sets where. The fake keeps the target and makes one squad of 18 units.
    world.raid_targets = {}
    fg.set_method(engine, "spawnRaiders", function(self, squads, center)
        world.raid_targets[#world.raid_targets + 1] = { x = center.X, y = center.Y }
        for _ = 1, squads do
            local id = world.next_squad
            world.next_squad = id + 1
            fg.array_add(bandit.commandedSquads, { Value = id })
            for _ = 1, 18 do
                fg.object("SMUnit", { dead = false, assignedSquadID = { Value = id }, currentUnitRole = 5, ItemsLooted = 0, morale = 1.0,
                                      combatExperience = 0.0, realPos = { X = 0.0, Y = -88000.0, Z = 0.0 }, family = false })
            end
        end
    end)
    world.families = families
    return world
end
"""


class RebelTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.game.exec("FName = function(text) return { fname = text } end")
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


FOLIAGE_WORLD = """
function(fg, region, spec)
    for _, row in ipairs(spec) do
        local mesh = fg.object("StaticMesh", {})
        fg.set_method(mesh, "GetFName", function() return fg.fstring(row.mesh) end)
        local component = fg.object("FoliageInstancedStaticMeshComponent", { StaticMesh = mesh })
        fg.set_method(component, "GetOuter", function() return region end)
        fg.set_method(component, "GetInstanceCount", function() return #row.trees end)
        fg.set_method(component, "GetInstanceTransform", function(self, index, out)
            local tree = row.trees[index + 1]
            out.Translation = { X = tree[1], Y = tree[2], Z = 50 }
            return true
        end)
    end
end
"""


class RebelRaidRallyTests(RebelTestCase):
    def add_groves(self, centres):
        region = self.game.lua.eval("function() return FindFirstOf('Region') end")()
        groves = [{"mesh": "stc_oak_test", "trees": [[x + (i % 4) * 100, y + (i // 4) * 100] for i in range(12)]} for x, y in centres]
        self.game.lua.eval(FOLIAGE_WORLD)(self.game.fg, region, self.game.lua.table_from(groves, recursive=True))

    def test_families_leave_and_one_raid_is_aimed_at_the_forest_nearest_to_the_waypoint(self):
        self.add_groves([(-35000, -66000), (-26000, -26000)])
        answer = self.send("rebel_raid_rally", count=2)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["before"]["families"], answer["after"]["families"]), (3, 1))
        self.assertEqual(answer["families_removed"], 2)
        self.assertLess(abs(answer["spot"]["x"] - -26000), 1000)
        self.assertEqual(len(self.world.raid_targets), 1)
        self.assertEqual(answer["squads"], [20])
        self.assertEqual(answer["bandit_units_after"] - answer["bandit_units_before"], 18)

    def test_no_forest_spot_fails_before_any_family_is_removed(self):
        answer = self.send("rebel_raid_rally", count=2)
        self.assertFalse(answer["ok"])
        self.assertIn("no forest spot", answer["error"])
        self.assertEqual(len(self.world.raid_targets), 0)
        self.assertFalse(any(unit.dead for family in self.world.families.values() for unit in family.list.values()))

    def test_bad_counts_are_refused(self):
        self.add_groves([(-26000, -26000)])
        for count in (0, 7):
            self.assertFalse(self.send("rebel_raid_rally", count=count)["ok"], count)
        self.assertEqual(len(self.world.raid_targets), 0)


class HomelessRebelTests(RebelTestCase):
    def test_removed_families_leave_bandit_squads_at_their_homes(self):
        answer = self.send("homeless_rebel", count=2)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["before"]["families"], answer["after"]["families"]), (3, 1))
        self.assertEqual((answer["before"]["residents"], answer["after"]["residents"]), (9, 4))
        self.assertEqual(answer["families_removed"], 2)
        self.assertEqual(answer["people_removed"], 5)
        self.assertEqual([(squad["x"], squad["y"]) for squad in answer["squads"]], [(100, 200), (300, 400)])
        self.assertEqual(answer["bandit_units_spawned"], 36)
        self.assertEqual(answer["bandit_units_after"] - answer["bandit_units_before"], 36)
        self.assertEqual([row["owner"] for row in self.world.spawn_positions.values()], ["bandit", "bandit"])

    def test_families_per_squad_groups_families_into_one_squad(self):
        answer = self.send("homeless_rebel", count=2, families_per_squad=2)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(len(answer["squads"]), 1)
        self.assertEqual((answer["squads"][0]["x"], answer["squads"][0]["y"]), (100, 200))

    def test_bad_inputs_are_refused_and_nothing_is_removed(self):
        for fields in ({"count": 0}, {"count": 7}, {"count": 1, "families_per_squad": 0}, {"count": 1, "template": "NoSuchUnit"}):
            self.assertFalse(self.send("homeless_rebel", **fields)["ok"], fields)
        self.assertFalse(any(unit.dead for family in self.world.families.values() for unit in family.list.values()))


class KillSquadsTests(RebelTestCase):
    def test_only_the_named_squads_die(self):
        self.assertTrue(self.send("bandit_spawn_at", x=1, y=2, count=3)["ok"])
        answer = self.send("bandit_kill_squads", squad=21, count=2)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["killed"], 36)
        self.assertEqual(self.send("bandit_kill_squads", squad=21, count=2)["killed"], 0)
        self.assertEqual(self.send("bandit_kill_squads", squad=20)["killed"], 18)

    def test_bad_inputs_are_refused(self):
        for fields in ({}, {"squad": 0}, {"squad": 5, "count": 0}, {"squad": 5, "count": 11}):
            self.assertFalse(self.send("bandit_kill_squads", **fields)["ok"], fields)


class SpawnAtTests(RebelTestCase):
    def test_a_bandit_squad_appears_at_the_point(self):
        answer = self.send("bandit_spawn_at", x=-22873, y=-50789, z=3003, template="Brigands")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["units"], 18)
        self.assertEqual((self.world.spawn_positions[1]["x"], self.world.spawn_positions[1]["y"]), (-22873, -50789))

    def test_missing_or_far_coordinates_are_refused(self):
        self.assertFalse(self.send("bandit_spawn_at", y=5)["ok"])
        self.assertFalse(self.send("bandit_spawn_at", x=9999999, y=5)["ok"])
        self.assertFalse(self.send("bandit_spawn_at", x=1, y=5, template="NoSuchUnit")["ok"])


class TurnTests(RebelTestCase):
    def test_family_members_are_turned_and_leave_the_family(self):
        answer = self.send("bandit_turn", count=2, source="family")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.world.turned, 2)
        self.assertTrue(answer["turned"][0]["before"]["family"])
        self.assertFalse(answer["turned"][0]["after"]["family"])
        self.assertEqual(answer["turned"][0]["after"]["role"], 5)

    def test_squad_source_needs_units_made_by_spawn_units(self):
        self.assertFalse(self.send("bandit_turn", count=1)["ok"])
        self.assertTrue(self.send("spawn_units", side="player", template="spearMilitia", count=1)["ok"])
        answer = self.send("bandit_turn", count=3)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.world.turned, 3)

    def test_count_and_source_are_checked(self):
        self.assertFalse(self.send("bandit_turn", count=0)["ok"])
        self.assertFalse(self.send("bandit_turn", count=99)["ok"])
        self.assertFalse(self.send("bandit_turn", count=1, source="sky")["ok"])


if __name__ == "__main__":
    unittest.main()
