"""Mock tests for HarnessWalls (spec 14): free walls made from a committed road, in the fake game kit.

The fake world copies what the real game did (spec 14 notes, free-walls.md):
- the road tool commits a plain `Road` (roadType 0, wallType 0, no meshes) from the points the player placed;
- writing roadType 3 and wallType, then `cleanSplineMeshes` and `spawnRoadMeshes`, makes wall meshes (wooden: 7, stone: 14);
- `PawnCPP:removeRoad` empties the road (spline length 0, no meshes) and leaves the actor in the world.
"""

import json
import unittest

import fakegame_path  # noqa: F401
import runlib_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import sleep_in
from runlib.actions import Actions, ActionError
from runlib.commands import CommandChannel, CommandRefused
from runlib.expectations import Expectations

WORLD = """
function(fg)
    local world = { points = 0, roads = {} }
    local player = fg.object("MyPawnCPP_BP3_C", { roadmode = false, wallMode = false }, "/Game/Fake/Player")
    fg.set_method(player, "setRoadMode", function(self, mode) self.roadmode = mode end)

    local function new_road(length, wall_type, road_type)
        local spline = fg.object("SplineComponent", {})
        local road = fg.object("Road", { roadType = road_type or 0, wallType = wall_type or 0, isBlueprint = false,
                                         StaticMeshes = fg.array({}, { wrap = false }), Spline = spline })
        fg.set_method(spline, "GetSplineLength", function() return road.removed and 0 or length end)
        fg.set_method(spline, "GetLocationAtDistanceAlongSpline", function() return { X = 15000.5, Y = -52000.5, Z = 2500.5 } end)
        fg.set_method(road, "cleanSplineMeshes", function(self) self.StaticMeshes = fg.array({}, { wrap = false }) end)
        fg.set_method(road, "spawnRoadMeshes", function(self)
            local count = ({ [2] = 7, [3] = 14, [4] = 14 })[self.wallType] or 0
            local items = {}
            for i = 1, count do items[i] = "mesh" end
            self.StaticMeshes = fg.array(items, { wrap = false })
        end)
        world.roads[#world.roads + 1] = road
        return road
    end
    world.new_road = new_road
    fg.set_method(player, "commitRoad", function()
        if world.points < 2 then return nil end
        world.points = 0
        return new_road(1700)
    end)
    fg.set_method(player, "removeRoad", function(self, road)
        road.removed = true
        road.StaticMeshes = fg.array({}, { wrap = false })
    end)
    -- A wall that the planner made: a blueprint road with wall markers.
    world.planner_wall = new_road(7900, 2, 3)
    world.planner_wall.isBlueprint = true
    return world
end
"""


def start(env=None):
    game = FakeGame(env=env)
    game.start()
    world = game.lua.eval(WORLD)(game.fg)
    game.load_mod("HarnessActions")
    game.advance(1)
    return game, world


def run_command(game, command, **fields):
    folder = game.run_dir / "commands"
    folder.mkdir(exist_ok=True)
    number = len(list(folder.glob("*.json"))) // 2 + 1
    (folder / f"{number:04d}.json").write_text(json.dumps({"id": f"{number:04d}", "command": command, **fields}), encoding="utf-8")
    game.advance(1)
    return json.loads((folder / f"{number:04d}.result.json").read_text(encoding="utf-8"))


class WallTestCase(unittest.TestCase):
    def setUp(self):
        self.game, self.world = start()
        self.addCleanup(self.game.close)

    def send(self, command, **fields):
        return run_command(self.game, command, **fields)

    def commit_road(self):
        self.world.points = 2
        return self.send("road_commit")


class StateTests(WallTestCase):
    def test_the_planner_wall_is_listed_with_its_markers_and_a_plain_road_is_not(self):
        self.world.new_road(500)
        answer = self.send("wall_state")
        self.assertEqual((answer["ok"], answer["total"], answer["counts"]["wooden"]), (True, 1, 1))
        wall = answer["walls"][0]
        self.assertEqual((wall["road_type"], wall["wall_name"], wall["blueprint"], wall["length"]), (3, "wooden", True, 7900))
        self.assertEqual(wall["middle"], {"x": 15000, "y": -52001, "z": 2500})


class RoadModeTests(WallTestCase):
    def test_road_mode_follows_the_request(self):
        self.assertTrue(self.send("road_mode", on=1)["road_mode"])
        self.assertFalse(self.send("road_mode", on=0)["road_mode"])
        self.assertTrue(self.send("road_mode", on=True)["road_mode"])

    def test_a_bad_value_is_refused(self):
        self.assertIn("on must be", self.send("road_mode", on="maybe")["error"])
        self.assertIn("on must be", self.send("road_mode")["error"])


class MakeWallTests(WallTestCase):
    def test_a_committed_road_becomes_a_wooden_wall_with_meshes(self):
        committed = self.commit_road()
        self.assertEqual((committed["ok"], committed["wall"]["wall_name"], committed["wall"]["meshes"]), (True, "none", 0))
        made = self.send("wall_make", road=committed["road"], wall_type=2)
        self.assertTrue(made["ok"], made)
        self.assertEqual((made["before"]["road_type"], made["after"]["road_type"], made["after"]["wall_name"]), (0, 3, "wooden"))
        self.assertEqual((made["before"]["meshes"], made["after"]["meshes"]), (0, 7))
        self.assertEqual(self.send("wall_state")["total"], 2)

    def test_stone_walls_have_more_meshes(self):
        road = self.commit_road()["road"]
        made = self.send("wall_make", road=road, wall_type=4)
        self.assertEqual((made["after"]["wall_name"], made["after"]["meshes"]), ("stone_high", 14))

    def test_commit_without_points_is_refused(self):
        self.assertIn("place at least 2 points", self.send("road_commit")["error"])

    def test_bad_inputs_are_refused(self):
        road = self.commit_road()["road"]
        self.assertIn("road must be", self.send("wall_make", wall_type=2)["error"])
        self.assertIn("wall_type must be", self.send("wall_make", road=road, wall_type=1)["error"])
        self.assertIn("wall_type must be", self.send("wall_make", road=road, wall_type=9)["error"])
        self.assertIn("no road with id 999999", self.send("wall_make", road=999999, wall_type=2)["error"])
        self.assertEqual(self.send("wall_state")["total"], 1)


class RemoveTests(WallTestCase):
    def test_a_removed_wall_is_no_longer_listed(self):
        road = self.commit_road()["road"]
        self.send("wall_make", road=road, wall_type=2)
        removed = self.send("wall_remove", road=road)
        self.assertEqual((removed["ok"], removed["empty"]), (True, True))
        self.assertEqual(self.send("wall_state")["total"], 1)

    def test_a_plain_road_cannot_be_removed_as_a_wall(self):
        road = self.commit_road()["road"]
        self.assertIn("is not a wall", self.send("wall_remove", road=road)["error"])


class StubBridge:
    def engine_path(self):
        return "engine"


class BuildingHealthTests(WallTestCase):
    def add_building(self, hp):
        return self.game.lua.eval("""
        function(fg, hp)
            local b = fg.object("SMBuildingMaster", { Data = { bType = 98, hp = hp, maxHp = 100 }, onFire = true, fireAmt = 0.5 },
                nil)
            fg.set_method(b, "IsRubble", function() return false end)
            fg.set_method(b, "IsConstructed", function() return true end)
            fg.set_method(b, "GetCollapseChance", function() return 0.25 end)
            return fg.counter
        end""")(self.game.fg, hp)

    def test_health_of_one_building_is_read(self):
        number = self.add_building(60)
        answer = self.send("building_health", building=number)
        self.assertEqual((answer["ok"], answer["type"], answer["hp"], answer["max_hp"]), (True, 98, 60, 100))
        self.assertEqual((answer["on_fire"], answer["rubble"], answer["built"], answer["collapse_chance"]), (True, False, True, 0.25))

    def test_a_missing_building_is_refused(self):
        self.assertIn("no building", self.send("building_health", building=5)["error"])
        self.assertIn("building must be", self.send("building_health")["error"])


class ManorBlueprintTests(WallTestCase):
    def test_missing_fields_are_refused(self):
        self.assertIn("type, x, y and z are required", self.send("manor_blueprint_add", type=58)["error"])
        self.assertIn("type, x, y and z are required", self.send("manor_blueprint_add", x=1, y=2, z=3)["error"])

    def test_without_a_matching_manor_blueprint_nothing_is_spawned(self):
        answer = self.send("manor_blueprint_add", type=58, x=-100, y=200, z=3, commit=True)
        self.assertFalse(answer["ok"])
        self.assertRegex(answer["error"], "no manor|no blueprint of type 58")


    def test_a_mesh_path_does_not_skip_the_manor_check(self):
        answer = self.send("manor_blueprint_add", type=123, x=1, y=2, z=3, mesh="/Game/ManorLords/Buildings/Merged/SM_Test")
        self.assertFalse(answer["ok"])
        self.assertRegex(answer["error"], "no manor|mesh not found")


UNSAFE_COMMANDS = ("path_obstacles_clear", "building_stat_write", "construction_complete")


class UnsafeCommandTests(WallTestCase):
    def test_unsafe_commands_are_refused_without_the_env(self):
        for name in UNSAFE_COMMANDS:
            answer = self.send(name)
            self.assertFalse(answer["ok"], name)
            self.assertIn("HARNESS_ALLOW_UNSAFE=1", answer["error"], name)


class UnsafeCommandsAllowedTests(unittest.TestCase):
    def setUp(self):
        self.game, self.world = start(env={"HARNESS_ALLOW_UNSAFE": "1"})
        self.addCleanup(self.game.close)

    def test_unsafe_commands_run_their_own_checks_with_the_env(self):
        self.assertIn("building must be", run_command(self.game, "construction_complete")["error"])
        self.assertIn("kind must be", run_command(self.game, "building_stat_write")["error"])
        self.assertNotIn("HARNESS_ALLOW_UNSAFE", str(run_command(self.game, "path_obstacles_clear").get("error")))


class WallActionTests(unittest.TestCase):
    def setUp(self):
        self.game, self.world = start()
        self.addCleanup(self.game.close)
        sleep = sleep_in(self.game)
        channel = CommandChannel(self.game.run_dir / "commands", sleep=sleep, monotonic=self.game.now)
        self.actions = Actions(StubBridge(), Expectations(sleep=sleep, monotonic=self.game.now), [], commands=channel)

    def test_the_wrappers_build_and_remove_a_free_wall(self):
        self.assertTrue(self.actions.road_mode(True)["road_mode"])
        self.world.points = 3
        road = self.actions.road_commit()["road"]
        made = self.actions.wall_make(road, 3)
        self.assertEqual(made["after"]["wall_name"], "stone_low")
        self.assertEqual(self.actions.wall_state()["counts"]["stone_low"], 1)
        self.assertTrue(self.actions.wall_remove(road)["empty"])
        self.assertEqual(self.actions.wall_state()["counts"]["stone_low"], 0)

    def test_the_wrappers_check_their_inputs(self):
        with self.assertRaises(ActionError):
            self.actions.road_mode("yes")
        with self.assertRaises(ActionError):
            self.actions.wall_make(0, 2)
        with self.assertRaises(ActionError):
            self.actions.wall_make(5, 1)
        with self.assertRaises(ActionError):
            self.actions.wall_remove(-1)

    def test_a_refused_command_raises(self):
        with self.assertRaises(CommandRefused):
            self.actions.wall_make(999999, 2)


if __name__ == "__main__":
    unittest.main()
