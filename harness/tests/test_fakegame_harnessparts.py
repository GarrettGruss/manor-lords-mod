"""Mock tests for HarnessParts (spec 18): list, add and remove the parts of a building master.

The fake master follows the facts of implementation-notes/part-edit-test.md. It tests the Lua logic, not the game.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

BUILD_WORLD = """
function(fg)
    local parts = {}
    for i = 1, 3 do
        local part = fg.object("SMBuilding", { x = i * 100 })
        fg.set_method(part, "K2_GetActorLocation", function(self) return { X = self.x, Y = 0, Z = 0 } end)
        fg.set_method(part, "IsHidden", function(self) return self.hid == true end)
        fg.set_method(part, "SetActorHiddenInGame", function(self, value) self.hid = value end)
        parts[i] = part
    end
    local master = fg.object("SMBuildingMaster", { Data = { bType = 87 }, buildings = fg.array(parts, { wrap = false }), Extensions = fg.array({}, { wrap = false }) })
    fg.set_method(master, "IsConstructed", function() return true end)
end
"""


class PartsTests(unittest.TestCase):
    env = {}

    def setUp(self):
        self.game = FakeGame(env=self.env)
        self.game.start()
        self.addCleanup(self.game.close)
        self.game.lua.eval(BUILD_WORLD)(self.game.fg)
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


class ReadTests(PartsTests):
    def test_lists_the_parts_of_a_master_by_type(self):
        answer = self.send("master_parts", type=87, limit=2)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["parts"], len(answer["rows"])), (3, 2))

    def test_needs_an_id_or_a_type(self):
        self.assertFalse(self.send("master_parts")["ok"])

    def test_artisan_state_is_read_without_the_env_variable(self):
        answer = self.send("master_artisan", type=87)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["type"], answer["extension_types"]), (87, []))


class RefusedTests(PartsTests):
    def test_remove_and_add_are_refused_without_the_env_variable(self):
        for name in ("master_part_remove", "master_part_add"):
            answer = self.send(name, type=87, index=1)
            self.assertFalse(answer["ok"], name)
            self.assertIn("HARNESS_ALLOW_UNSAFE=1", answer["error"])


    def test_artisan_set_is_refused_without_the_env_variable(self):
        answer = self.send("master_artisan_set", type=87, job=14)
        self.assertFalse(answer["ok"])
        self.assertIn("HARNESS_ALLOW_UNSAFE=1", answer["error"])


class HideTests(PartsTests):
    env = {"HARNESS_ALLOW_UNSAFE": "1"}

    def test_hide_keeps_the_part_in_the_list(self):
        answer = self.send("master_part_remove", type=87, index=2, mode="hide")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["after"]["parts"], 3)

    def test_artisan_set_writes_the_job_and_reads_it_back(self):
        answer = self.send("master_artisan_set", type=87, job=14)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["after"], 14)

    def test_artisan_set_needs_a_change(self):
        self.assertIn("give job", self.send("master_artisan_set", type=87)["error"])

    def test_index_and_mode_are_checked(self):
        self.assertIn("index must be", self.send("master_part_remove", type=87, index=9)["error"])
        self.assertIn("mode must be", self.send("master_part_remove", type=87, index=1, mode="boom")["error"])


SITE_WORLD = """
function(fg)
    local region = fg.object("BP_Region_C", {})
    fg.object("MyPawnCPP_BP3_C", { currentRegion = region })
    local site = fg.object("SMBuildingMaster", { Data = { bType = 483, constructed = false }, buildings = fg.array({}, { wrap = false }),
                                                  Resources = fg.array({}, { wrap = false }), constructionGoods = fg.array({}, { wrap = false }) })
    fg.set_method(site, "IsConstructed", function(self) return self.Data.constructed == true end)
end
"""


class SiteTests(PartsTests):
    def setUp(self):
        super().setUp()
        self.game.lua.eval(SITE_WORLD)(self.game.fg)

    def test_site_is_read_while_unbuilt(self):
        answer = self.send("master_site", type=483)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["type"], answer["constructed"], answer["region"]), (483, False, "<invalid>"))

    def test_region_write_is_read_back(self):
        answer = self.send("master_set_region", type=483)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["before"], "<invalid>")
        self.assertNotEqual(answer["after"], "<invalid>")

    def test_finish_writes_constructed(self):
        answer = self.send("master_finish", type=483)
        self.assertTrue(answer["ok"], answer)
        self.assertTrue(self.send("master_site", type=483)["constructed"])

    def test_a_site_needs_an_id_or_a_type(self):
        self.assertFalse(self.send("master_set_region")["ok"])


if __name__ == "__main__":
    unittest.main()
