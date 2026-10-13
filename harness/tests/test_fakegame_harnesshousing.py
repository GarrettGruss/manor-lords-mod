"""Mock tests for HarnessHousing (spec 15): housing numbers, homeless tents and the tent spot finder.

The fake world follows the game facts of implementation-notes/tent-placement.md:
  - a tent is an SMBuildingMaster with Data.bType 87 and isHomelessTent true;
  - RTSMultiEngineCPP:pointCollidesWithBuildingBorder is true near a building and false far from it.
It tests the Lua module logic. It does NOT prove how the real game decides.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

BUILD_WORLD = """
function(fg)
    local world = { accommodate_calls = 0 }
    local player = fg.object("MyPawnCPP_BP3_C", { isMainPlayer = true })
    local buildings = {}
    local function add(kind, x, y, tent)
        local b = fg.object("SMBuildingMaster", { Data = { bType = kind }, x = x, y = y, occupantFamilyIDs = fg.array({}, { wrap = false }) })
        fg.set_method(b, "IsConstructed", function() return true end)
        fg.set_method(b, "IsRubble", function() return false end)
        fg.set_method(b, "isHomelessTent", function() return tent end)
        fg.set_method(b, "isResidentialBuilding", function() return kind == 3 end)
        fg.set_method(b, "K2_GetActorLocation", function(self) return { X = self.x, Y = self.y, Z = 100 } end)
        buildings[#buildings + 1] = b
        return b
    end
    add(3, 0, 0, false)
    add(3, 1000, 0, false)
    world.add = add
    world.buildings = buildings
    local region = fg.object("Region", { regionName = "Riesenbuckel" })
    region.ownerPawn = player
    player.currentRegion = region
    fg.set_method(region, "GetBuildings", function() return buildings end)
    fg.set_method(region, "getSettledRegionCenter", function() return { X = 0, Y = 0, Z = 0 } end)
    fg.set_method(region, "getTotalNumFamilies", function() return 2 end)
    fg.set_method(region, "getNumHomelessFamilies", function() return 0 end)
    fg.set_method(region, "getNumHumanResidents", function() return 6 end)
    fg.set_method(region, "getLivingSpace", function() return { constructed = 3, unconstructed = 0 } end)
    fg.set_method(region, "getAvailableLivingSpace", function() return { constructed = 1, unconstructed = 0 } end)
    fg.set_method(region, "getBuildingCount", function(self, kind)
        local n = 0
        for _, b in ipairs(buildings) do if b.Data.bType == kind then n = n + 1 end end
        return n
    end)
    fg.set_method(region, "accomodateHomelessFamilies", function() world.accommodate_calls = world.accommodate_calls + 1 end)
    local engine = fg.object("RTSMultiEngineCPP", { playerRef = player, regions = fg.array({ region }, { wrap = false }) })
    fg.set_method(engine, "pointCollidesWithBuildingBorder", function(self, point)
        for _, b in ipairs(buildings) do
            if math.sqrt((b.x - point.X) ^ 2 + (b.y - point.Y) ^ 2) < 600 then return true end
        end
        return false
    end)
    return world
end
"""


class HousingTestCase(unittest.TestCase):
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


class StateTests(HousingTestCase):
    def test_state_shows_slots_and_residential_buildings(self):
        state = self.send("housing_state")
        self.assertTrue(state["ok"], state)
        self.assertEqual(state["region"]["vacant"]["constructed"], 1)
        self.assertEqual((state["residential_total"], len(state["tents"]), state["world_tents"]), (2, 0, []))

    def test_a_tent_is_listed(self):
        self.world.add(87, 3000, 0, True)
        state = self.send("housing_state")
        self.assertEqual(len(state["tents"]), 1)
        self.assertEqual(state["region"]["tents_by_count"], 1)
        self.assertEqual(len(state["world_tents"]), 1)

    def test_accommodate_homeless_calls_the_game_and_reports_before_and_after(self):
        answer = self.send("accommodate_homeless")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.world.accommodate_calls, 1)
        self.assertEqual(answer["before"]["homeless"], 0)

    def test_building_stat_refuses_a_type_above_the_limit(self):
        self.assertFalse(self.send("building_stat", type=999)["ok"])
        self.assertFalse(self.send("building_stat")["ok"])

    def test_plot_upgrade_checks_the_id_and_needs_a_building_under_the_mouse(self):
        self.assertIn("upgrade must be", self.send("plot_upgrade")["error"])
        self.assertIn("upgrade must be", self.send("plot_upgrade", upgrade=5000)["error"])
        answer = self.send("plot_upgrade", upgrade=12)
        self.assertFalse(answer["ok"])
        self.assertRegex(answer["error"], "no building under the mouse|no player pawn")


class SpotTests(HousingTestCase):
    def test_spots_are_clear_of_buildings(self):
        answer = self.send("tent_find_spot")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(len(answer["spots"]), 5)
        for spot in answer["spots"]:
            for x, y in ((0, 0), (1000, 0)):
                self.assertGreaterEqual(((spot["x"] - x) ** 2 + (spot["y"] - y) ** 2) ** 0.5, 600)
            self.assertGreaterEqual(spot["gap"], 900)

    def test_no_spot_when_the_game_check_does_not_run(self):
        self.game.exec("fg_engine = FindFirstOf('RTSMultiEngineCPP')")
        self.game.lua.eval("function(fg) fg.set_method(FindFirstOf('RTSMultiEngineCPP'), 'pointCollidesWithBuildingBorder', function() error('broken') end) end")(self.game.fg)
        answer = self.send("tent_find_spot")
        self.assertFalse(answer["ok"])
        self.assertEqual(answer["spots"], [])


FOLIAGE_WORLD = """
function(fg, region, spec)
    -- spec: list of { mesh = name, outer = region or other, trees = { {x, y}, ... } }
    for _, row in ipairs(spec) do
        local mesh = fg.object("StaticMesh", {})
        fg.set_method(mesh, "GetFName", function() return fg.fstring(row.mesh) end)
        local component = fg.object("FoliageInstancedStaticMeshComponent", { StaticMesh = mesh })
        fg.set_method(component, "GetOuter", function() return row.outer or region end)
        fg.set_method(component, "GetInstanceCount", function() return #row.trees end)
        fg.set_method(component, "GetInstanceTransform", function(self, index, out)
            local tree = row.trees[index + 1]
            out.Translation = { X = tree[1], Y = tree[2], Z = 50 }
            return true
        end)
    end
end
"""


class ForestTests(HousingTestCase):
    def grove(self, centre_x, centre_y, count=12):
        return [[centre_x + (i % 4) * 100, centre_y + (i // 4) * 100] for i in range(count)]

    def add_foliage(self, spec):
        region = self.game.lua.eval("function() return FindFirstOf('Region') end")()
        self.game.lua.eval(FOLIAGE_WORLD)(self.game.fg, region, self.game.lua.table_from(spec, recursive=True))

    def test_a_dense_grove_far_from_the_buildings_is_found(self):
        self.add_foliage([{"mesh": "stc_oak_test", "trees": self.grove(20000, 0)}])
        answer = self.send("forest_spot")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["found"], 1)
        spot = answer["spots"][0]
        self.assertEqual(spot["trees"], 12)
        self.assertGreaterEqual(spot["dist"], 15000)
        self.assertLessEqual(spot["dist"], 40000)
        self.assertEqual(answer["tree_meshes"], {"stc_oak_test": 12})

    def test_shrubs_other_regions_and_far_groves_are_ignored(self):
        other = self.game.lua.eval("function(fg) return fg.object('Region', { regionName = 'Other' }) end")(self.game.fg)
        self.add_foliage([
            {"mesh": "OakYoungShrubReduced", "trees": self.grove(20000, 0)},
            {"mesh": "stc_oak_test", "outer": other, "trees": self.grove(20000, 5000)},
            {"mesh": "fir_stc_Small_01", "trees": self.grove(90000, 0)},
        ])
        answer = self.send("forest_spot")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["found"], 0)

    def test_the_distance_window_is_a_request_field(self):
        self.add_foliage([{"mesh": "fir_stc_Small_01", "trees": self.grove(5000, 0)}])
        self.assertEqual(self.send("forest_spot")["found"], 0)
        self.assertEqual(self.send("forest_spot", min_dist=3000, max_dist=9000)["found"], 1)
        self.assertFalse(self.send("forest_spot", min_dist=9000, max_dist=3000)["ok"])


STATS_WORLD = """
function(fg)
    local row = fg.object("BuildingStatsRow", { occupantTypes = { X = 0, Y = 0, Z = 0, W = 0 }, workerTypes = { X = 1, Y = 2, Z = 3, W = 4 } })
    local table = fg.object("DataTable", {}, "/Game/NotStronghold/Data/buildingStats.buildingStats")
    fg.set_method(table, "FindRow", function(self, name) if name == "87" then return row end return nil end)
    return row
end
"""

FIELD_WORLD = """
function(fg)
    local function points() return fg.array({ { X = 100, Y = 200, Z = 5 }, { X = 300, Y = 400, Z = 5 } }, { wrap = false }) end
    local pawn = FindFirstOf("MyPawnCPP_BP3_C")
    pawn.fieldClosed = true
    pawn.fieldSmoothPoints = points()
    pawn.fieldSmoothPointsClosed = points()
    pawn.fieldCenter = { X = 10, Y = 20, Z = 0 }
    pawn.commit_calls = 0
    fg.set_method(pawn, "addCommitFieldRequest", function(self) self.commit_calls = self.commit_calls + 1 end)
    return pawn
end
"""


class VectorWriteRefusedTests(HousingTestCase):
    def test_refused_without_the_env_variable(self):
        answer = self.send("building_stat_vector_write", type=87, field="occupantTypes", component="Y", value=5)
        self.assertFalse(answer["ok"])
        self.assertIn("HARNESS_ALLOW_UNSAFE=1", answer["error"])


class VectorWriteTests(HousingTestCase):
    def setUp(self):
        self.game = FakeGame(env={"HARNESS_ALLOW_UNSAFE": "1"})
        self.game.start()
        self.addCleanup(self.game.close)
        self.game.lua.eval(BUILD_WORLD)(self.game.fg)
        self.row = self.game.lua.eval(STATS_WORLD)(self.game.fg)
        self.game.load_mod("HarnessActions")
        self.game.advance(1)
        self.number = 0

    def write(self, **fields):
        body = {"type": 87, "field": "occupantTypes", "component": "Y", "value": 5}
        body.update(fields)
        return self.send("building_stat_vector_write", **body)

    def test_writes_one_component_and_returns_before_and_after(self):
        answer = self.write()
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["before"]["y"], 0)
        self.assertEqual(answer["after"], {"x": 0, "y": 5, "z": 0, "w": 0})
        self.assertEqual(self.row.occupantTypes.Y, 5)

    def test_can_write_the_value_back_to_zero(self):
        self.write()
        self.assertEqual(self.write(value=0)["after"]["y"], 0)

    def test_worker_types_can_be_written(self):
        answer = self.write(field="workerTypes", component="W", value=9)
        self.assertEqual(answer["after"], {"x": 1, "y": 2, "z": 3, "w": 9})

    def test_bad_input_is_refused_and_nothing_is_written(self):
        for bad in ({"field": "maxHp"}, {"component": "Q"}, {"component": "YY"}, {"value": -1}, {"value": 1000}, {"type": 999}):
            self.assertFalse(self.write(**bad)["ok"], bad)
        self.assertEqual(self.row.occupantTypes.Y, 0)
        self.assertFalse(self.send("building_stat_vector_write")["ok"])

    def test_an_unknown_row_is_refused(self):
        self.assertIn("no buildingStats row 88", self.write(type=88)["error"])


class PlotFieldShiftTests(HousingTestCase):
    def setUp(self):
        super().setUp()
        self.pawn = self.game.lua.eval(FIELD_WORLD)(self.game.fg)

    def test_moves_the_outline_and_the_centre(self):
        answer = self.send("plot_field_shift", dx=50, dy=-20)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.pawn.fieldSmoothPoints[1].X, 150)
        self.assertEqual(self.pawn.fieldSmoothPointsClosed[2].Y, 380)
        self.assertEqual((answer["center"]["x"], answer["center"]["y"]), (60, 0))
        self.assertEqual((answer["moved"]["smooth"], answer["moved"]["closed"], answer["committed"]), (2, 2, False))
        self.assertEqual(self.pawn.commit_calls, 0)

    def test_commit_flag_calls_the_commit(self):
        answer = self.send("plot_field_shift", dx=1, dy=1, commit=True)
        self.assertTrue(answer["committed"], answer)
        self.assertEqual(self.pawn.commit_calls, 1)

    def test_bad_numbers_are_refused(self):
        for fields in ({}, {"dx": 1}, {"dx": 20000, "dy": 0}, {"dx": 0, "dy": -20000}):
            self.assertIn("dx and dy", self.send("plot_field_shift", **fields).get("error", ""), fields)
        self.assertEqual(self.pawn.fieldSmoothPoints[1].X, 100)

    def test_an_open_field_is_refused(self):
        self.pawn.fieldClosed = False
        self.assertIn("no closed plot field", self.send("plot_field_shift", dx=1, dy=1)["error"])


# The real game makes a full ExtractedPlot struct when Lua writes the index after the last element. The fake list does the same.
PLOT_LIST_WORLD = """
function(fg)
    local function vectors() return fg.array({}, { wrap = false }) end
    local function transform() return { Translation = { X = 0, Y = 0, Z = 0 }, Rotation = { X = 0, Y = 0, Z = 0, W = 1 }, Scale3D = { X = 1, Y = 1, Z = 1 } } end
    local items = {}
    local list = setmetatable({}, {
        __index = function(_, key)
            if key == "Empty" then return function() items = {} end end
            if key == "GetArrayNum" then return function() return #items end end
            return items[key]
        end,
        __newindex = function(_, index)
            items[index] = { SmoothBorder = vectors(), Corners = vectors(), extensionSmoothBorder = vectors(), extensionCorners = vectors(),
                             primaryBuildingTransform = transform(), secondaryBuildingTransform = transform(), extensionTransform = transform(),
                             backFacade = { A = { X = 0, Y = 0, Z = 0 }, B = { X = 0, Y = 0, Z = 0 } } }
        end })
    local p = FindFirstOf('MyPawnCPP_BP3_C')
    p.extractedPlots = list
    return p
end
"""


def one_plot():
    return {"corners": [[0, 0, 0], [1, 0, 0]], "border": [[0, 0, 0]], "ext_corners": [], "ext_border": [],
            "primary": [10, 20, 30, 0, 0, 0, 1], "extension": [0, 0, 0, 0, 0, 0, 1], "facade": [[1, 2, 3], [4, 5, 6]]}


class PlotFieldPlaceTests(HousingTestCase):
    def setUp(self):
        super().setUp()
        self.pawn = self.game.lua.eval(PLOT_LIST_WORLD)(self.game.fg)

    def test_bad_requests_are_refused(self):
        bad_plots = [None, [], [one_plot()] * 13, [{**one_plot(), "primary": [1, 2]}], [{**one_plot(), "facade": [[1, 2, 3]]}],
                     [{**one_plot(), "corners": "x"}], [{**one_plot(), "extension": None}]]
        for plots in bad_plots:
            self.assertFalse(self.send("plot_field_place", plots=plots)["ok"], plots)
        self.assertEqual(self.pawn.extractedPlots.GetArrayNum(), 0)

    def test_writes_a_plot_and_closes_the_field(self):
        answer = self.send("plot_field_place", plots=[one_plot()])
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["steps"]["count"], 1)
        self.assertEqual(answer["steps"]["plot1"]["corners"], 2)
        self.assertTrue(self.pawn.fieldClosed)
        self.assertEqual(self.pawn.expectedNumPlots, 1)


if __name__ == "__main__":
    unittest.main()
