"""Mock tests for HarnessEncampment (spec 30): find camp sites, spawn and remove a placed mesh actor.

The fake world follows the facts of docs/harness/30-wagenburg-encampment/implementation-notes (camp master type 100, SpawnActor on the world).
It tests the Lua logic, not the game.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

CLASS_PATH = "/Game/HarnessMod/BM_Wagenburg.BM_Wagenburg_C"

WORLD = """
function(fg)
    local part = fg.object("SMBuilding", {})
    fg.set_method(part, "K2_GetActorLocation", function() return { X = 10, Y = 20, Z = 30 } end)
    local camp = fg.object("SMBuildingMaster", { Data = { bType = 100 }, buildings = fg.array({ part }, { wrap = false }) })
    fg.set_method(camp, "IsConstructed", function() return true end)
    fg.set_method(camp, "K2_GetActorLocation", function() return { X = 1, Y = 2, Z = 3 } end)
    fg.object("SMBuildingMaster", { Data = { bType = 87 }, buildings = fg.array({}, { wrap = false }) })

    fg.object("Class", {}, "/Game/HarnessMod/BM_Wagenburg.BM_Wagenburg_C")
    local world = fg.object("World", {})
    fg.set_method(world, "SpawnActor", function(_, class, at)
        local actor = fg.object("BM_Wagenburg_C", {})
        fg.set_method(actor, "K2_GetActorLocation", function() return at end)
        fg.set_method(actor, "K2_DestroyActor", function(self) fg.invalidate(self) end)
        return actor
    end)
    local controller = fg.object("PlayerController", {})
    fg.set_method(controller, "GetWorld", function() return world end)
end
"""


class EncampmentTests(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame(env={})
        self.game.start()
        self.addCleanup(self.game.close)
        self.game.lua.eval(WORLD)(self.game.fg)
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

    def spawn(self, **fields):
        return self.send("encampment_spawn", **{"class": CLASS_PATH}, x=100, y=200, z=300, **fields)


class SitesTests(EncampmentTests):
    def test_lists_only_masters_of_the_asked_type(self):
        answer = self.send("encampment_sites")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual([site["type"] for site in answer["sites"]], [100])
        self.assertEqual(answer["sites"][0]["first_part_at"], {"x": 10, "y": 20, "z": 30})

    def test_a_type_without_masters_gives_an_empty_list(self):
        self.assertEqual(self.send("encampment_sites", type=999)["sites"], [])


class SpawnTests(EncampmentTests):
    def test_spawns_lists_and_removes_an_actor(self):
        answer = self.spawn(yaw=90)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["spawned"]["at"], {"x": 100, "y": 200, "z": 300})
        self.assertEqual(len(self.send("encampment_list")["spawned"]), 1)
        self.assertEqual(self.send("encampment_remove", name=answer["spawned"]["name"])["removed"], 1)
        self.assertEqual(self.send("encampment_list")["spawned"], [])

    def test_refuses_a_bad_class_path(self):
        answer = self.send("encampment_spawn", **{"class": "../evil"}, x=1, y=2, z=3)
        self.assertFalse(answer["ok"])

    def test_refuses_a_class_that_is_not_loaded(self):
        answer = self.send("encampment_spawn", **{"class": "/Game/HarnessMod/BM_None.BM_None_C"}, x=1, y=2, z=3)
        self.assertIn("not loaded", answer["error"])

    def test_refuses_a_far_coordinate(self):
        answer = self.send("encampment_spawn", **{"class": CLASS_PATH}, x=9e9, y=0, z=0)
        self.assertFalse(answer["ok"])

    def test_caps_the_number_of_actors(self):
        for _ in range(8):
            self.assertTrue(self.spawn()["ok"])
        self.assertFalse(self.spawn()["ok"])

    def test_remove_all_works_with_nothing_spawned(self):
        self.assertTrue(self.send("encampment_remove", name="all")["ok"])

    def test_remove_refuses_an_unknown_name(self):
        self.assertFalse(self.send("encampment_remove", name="Other_1")["ok"])


if __name__ == "__main__":
    unittest.main()
