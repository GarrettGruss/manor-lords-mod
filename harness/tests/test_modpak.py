"""Tests for harness/tools/modpak.py (the logic of `pakmod.py buildmod`) with fake tools and temp folders.

No game, no repak, no UAssetGUI. The fake table JSON has the same shape as the UAssetGUI output (Exports[0].Table.Data).
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HARNESS_DIR / "tools"))
import modpak  # noqa: E402

MANIFEST = {
    "name": "TestMod",
    "features": [
        {"name": "alpha", "requires": [], "ids": {"buildingStats": [1000, 1099], "DT_Upgrades": [117, 126]}},
        {"name": "beta", "requires": [], "ids": {"buildingStats": [1100, 1199]}},
    ],
}


def fake_table(names):
    rows = [{"Name": n, "Value": [{"Name": "stableSpace", "Value": 1, "IsZero": True},
                                  {"Name": "upgrades", "Value": [{"Name": "0", "Value": 5}]}]} for n in names]
    return {"NameMap": list(names), "Exports": [{"Table": {"Data": rows}}]}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


class ModTestCase(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)
        self.mod = self.root / "mod" / "TestMod"
        self.work = self.root / "work"
        self.manifest = json.loads(json.dumps(MANIFEST))
        write_json(self.mod / "mod.json", self.manifest)

    def patch(self, feature, name, **changes):
        data = {"table": "buildingStats", "row": "1000", "op": "add", "from": "30"}
        data.update(changes)
        data = {key: value for key, value in data.items() if value is not None}
        write_json(self.mod / "data" / feature / "patches" / name, data)

    def build(self, calls=None):
        calls = calls if calls is not None else []
        tables = {"buildingStats": fake_table(["30", "31"]), "DT_Upgrades": fake_table(["2"])}
        folder = self.work / "TestMod"
        folder.mkdir(parents=True, exist_ok=True)

        def fetch(asset):
            calls.append(("fetch", asset))
            path = self.work / "json" / (asset.rsplit("/", 1)[1] + ".json")
            write_json(path, tables[[t for t, a in modpak.TABLES.items() if a == asset][0]])
            return path

        def pack(json_file):
            calls.append(("pack", json_file.name))
            (folder / (json_file.stem + ".uasset")).write_bytes(b"asset")

        def build_pak():
            calls.append(("build", None))
            pak = self.work / "out" / "TestMod_P.pak"
            pak.parent.mkdir(exist_ok=True)
            pak.write_bytes(b"pak")
            return pak

        return modpak.build_mod(self.mod, folder, fetch, pack, build_pak)

    def assert_build_refused(self, *texts):
        with self.assertRaises(modpak.ModPakError) as caught:
            self.build()
        for text in texts:
            self.assertIn(text, str(caught.exception))


class PatchFormatTests(ModTestCase):
    def test_unknown_table_names_the_file(self):
        self.patch("alpha", "bad.json", table="nope")
        self.assert_build_refused("data/alpha/patches/bad.json", "'table'")

    def test_unknown_op_and_key_are_refused(self):
        self.patch("alpha", "bad.json", op="remove")
        self.assert_build_refused("bad.json", "'op'")
        self.patch("alpha", "bad.json", extra=1)
        self.assert_build_refused("bad.json", "unknown keys")

    def test_add_needs_from_and_set_needs_fields(self):
        self.patch("alpha", "bad.json", **{"from": None})
        self.assert_build_refused("bad.json", "needs 'from'")
        self.patch("alpha", "bad.json", op="set", **{"from": None})
        self.assert_build_refused("bad.json", "non-empty")

    def test_invalid_json_names_the_file(self):
        path = self.mod / "data" / "alpha" / "patches" / "broken.json"
        path.parent.mkdir(parents=True)
        path.write_text("{", encoding="utf-8")
        self.assert_build_refused("broken.json", "not valid JSON")


class OrderTests(ModTestCase):
    def test_order_is_feature_order_then_file_name(self):
        self.patch("beta", "a.json", row="1100")
        self.patch("alpha", "b.json", row="1001")
        self.patch("alpha", "a.json", row="1000")
        patches = modpak.load_patches(self.mod, self.manifest)
        self.assertEqual([p.file for p in patches], [
            "data/alpha/patches/a.json", "data/alpha/patches/b.json", "data/beta/patches/a.json"])


class CheckTests(ModTestCase):
    def test_same_row_added_twice_names_both_files(self):
        self.patch("alpha", "a.json", row="1050")
        self.patch("beta", "b.json", row="1050")
        self.assert_build_refused("data/alpha/patches/a.json", "data/beta/patches/b.json", "added")

    def test_same_field_set_by_two_features_names_both_files(self):
        self.patch("alpha", "a.json", op="set", row="31", set={"stableSpace": 2}, **{"from": None})
        self.patch("beta", "b.json", op="set", row="31", set={"stableSpace": 3}, **{"from": None})
        self.assert_build_refused("data/alpha/patches/a.json", "data/beta/patches/b.json", "stableSpace")

    def test_different_fields_of_one_row_do_not_conflict(self):
        self.patch("alpha", "x.json", op="set", row="31", set={"stableSpace": 2}, **{"from": None})
        self.patch("beta", "x.json", op="set", row="31", set={"other": 2}, **{"from": None})
        modpak.check_conflicts(modpak.load_patches(self.mod, self.manifest))

    def test_id_outside_the_range_fails(self):
        self.patch("alpha", "a.json", row="1100")
        self.assert_build_refused("data/alpha/patches/a.json", "[1000, 1099]")

    def test_table_without_a_range_fails(self):
        self.patch("beta", "a.json", table="DT_Upgrades", row="117", **{"from": "2"})
        self.assert_build_refused("no 'ids' range")


class ApplyTests(ModTestCase):
    def apply(self, names=("30",)):
        tables = {"buildingStats": fake_table(list(names))}
        modpak.apply_patches(tables, modpak.load_patches(self.mod, self.manifest))
        return tables

    def test_add_clones_a_row_and_sets_fields(self):
        self.patch("alpha", "a.json", set={"stableSpace": 4, "upgrades": [7, 8]})
        tables = self.apply()
        rows = modpak.table_rows(tables["buildingStats"])
        new = rows[-1]
        self.assertEqual(new["Name"], "1000")
        self.assertEqual(new["Value"][0]["Value"], 4)
        self.assertFalse(new["Value"][0]["IsZero"])
        self.assertEqual([e["Value"] for e in new["Value"][1]["Value"]], [7, 8])
        self.assertIn("1000", tables["buildingStats"]["NameMap"])
        self.assertTrue(rows[0]["Value"][0]["IsZero"], "the source row must stay unchanged")

    def test_missing_field_fails(self):
        self.patch("alpha", "a.json", set={"nope": 1})
        with self.assertRaises(modpak.ModPakError):
            self.apply()

    def test_missing_source_row_fails(self):
        self.patch("alpha", "a.json", **{"from": "99"})
        with self.assertRaises(modpak.ModPakError):
            self.apply()

    def test_existing_row_cannot_be_added(self):
        self.patch("alpha", "a.json")
        with self.assertRaises(modpak.ModPakError):
            self.apply(("30", "1000"))


class AssetTests(ModTestCase):
    def test_assets_are_copied_with_their_folders(self):
        asset = self.mod / "data" / "alpha" / "assets" / "ManorLords" / "Content" / "BM_x.uasset"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b"x")
        target = self.root / "pakdir"
        names = modpak.copy_assets(self.mod, self.manifest, target)
        self.assertEqual(names, ["ManorLords/Content/BM_x.uasset"])
        self.assertEqual((target / names[0]).read_bytes(), b"x")

    def test_same_asset_in_two_features_fails(self):
        for feature in ("alpha", "beta"):
            path = self.mod / "data" / feature / "assets" / "a.bin"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"x")
        with self.assertRaises(modpak.ModPakError) as caught:
            modpak.copy_assets(self.mod, self.manifest, self.root / "pakdir")
        self.assertIn("alpha", str(caught.exception))
        self.assertIn("beta", str(caught.exception))


class BuildTests(ModTestCase):
    def test_end_to_end_fake_build(self):
        self.patch("alpha", "a.json", set={"stableSpace": 4})
        self.patch("beta", "b.json", table="DT_Upgrades", op="set", row="2", set={"stableSpace": 9}, **{"from": None})
        asset = self.mod / "data" / "beta" / "assets" / "ManorLords" / "m.uasset"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b"m")
        calls = []
        pak = self.build(calls)
        self.assertEqual(pak, self.mod / "paks" / "TestMod_P.pak")
        self.assertEqual(pak.read_bytes(), b"pak")
        self.assertEqual([c[0] for c in calls], ["fetch", "fetch", "pack", "pack", "build"])
        edited = json.loads((self.work / "json" / "buildingStats.json").read_text())
        self.assertEqual(modpak.table_rows(edited)[-1]["Name"], "1000")
        self.assertTrue((self.work / "TestMod" / "ManorLords" / "m.uasset").is_file())

    def test_a_failed_check_builds_nothing(self):
        self.patch("alpha", "a.json", row="5")
        calls = []
        with self.assertRaises(modpak.ModPakError):
            self.build(calls)
        self.assertEqual(calls, [])
        self.assertFalse((self.mod / "paks").exists())


class RepoModsTests(unittest.TestCase):
    def test_every_patch_of_the_repo_mods_passes_the_checks(self):
        for manifest_path in sorted((HARNESS_DIR.parent / "mod").glob("*/mod.json")):
            mod_dir = manifest_path.parent
            manifest = modpak.read_manifest(mod_dir)
            if "features" not in manifest:
                continue
            patches = modpak.load_patches(mod_dir, manifest)
            modpak.check_conflicts(patches)
            modpak.check_id_ranges(patches, manifest)


if __name__ == "__main__":
    unittest.main()
