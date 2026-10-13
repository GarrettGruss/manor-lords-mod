"""Tests for the zip layout and the zip scan (spec 19)."""

import tempfile
import unittest
import zipfile
from pathlib import Path

import runlib_path  # noqa: F401
from releaselib import build, scan

KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

MANIFEST = {
    "name": "Demo", "version": "1.2.3", "description": "A demo.", "shared": ["Core"], "pak": None,
    "tested": {"game": "0.8.111", "game_build": "77", "ue4ss": "4.0.0-rc1"}, "gate_scenarios": ["demo"],
}


class ZipTestCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.mod_root = self.root / "mod"
        self.write("mod/Demo/Scripts/main.lua", 'local core = require("Core")')
        self.write("mod/Demo/mod.json", "{}")
        self.write("mod/shared/Core/Core.lua", "return {}")
        self.out = self.root / "dist"

    def write(self, name, text, binary=False):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text if binary else text.encode("utf-8"))

    def build(self, manifest=None, **kwargs):
        return build.build_zip(manifest or MANIFEST, self.mod_root, ["Core"], self.out, self.root, **kwargs)

    def names(self, zip_path):
        with zipfile.ZipFile(zip_path) as archive:
            return sorted(archive.namelist())


class BuildTests(ZipTestCase):
    def test_the_layout_follows_the_game_folder(self):
        names = self.names(self.build())
        prefix = "ManorLords/Binaries/Win64/ue4ss/Mods"
        self.assertEqual(names, sorted([f"{prefix}/Demo/Scripts/main.lua", f"{prefix}/Demo/mod.json", f"{prefix}/Demo/enabled.txt",
                                        f"{prefix}/shared/Core/Core.lua", "README.txt"]))

    def test_the_zip_is_named_after_the_mod_and_the_version(self):
        self.assertEqual(self.build().name, "Demo-v1.2.3.zip")
        self.assertEqual(build.tag_name(MANIFEST), "demo-v1.2.3")

    def test_the_readme_has_install_uninstall_and_tested_versions(self):
        with zipfile.ZipFile(self.build()) as archive:
            readme = archive.read("README.txt").decode("utf-8")
        for text in ("Install", "Uninstall", "0.8.111", "build 77", "4.0.0-rc1", "Mods\\Demo\\", "Mods\\shared\\Core\\"):
            self.assertIn(text, readme)

    def test_the_same_files_give_the_same_zip(self):
        first = self.build().read_bytes()
        self.assertEqual(self.build().read_bytes(), first)

    def test_a_pak_from_a_committed_file_goes_to_the_mods_folder(self):
        self.write("paks/demo_P.pak", b"PAKDATA", binary=True)
        manifest = dict(MANIFEST, pak={"name": "demo", "source": "file", "path": "paks/demo_P.pak"})
        names = self.names(self.build(manifest))
        self.assertIn("ManorLords/Content/Paks/~mods/demo_P.pak", names)

    def test_a_committed_pak_at_the_default_place_is_found_and_stays_out_of_the_lua_folder(self):
        self.write("mod/Demo/paks/demo_P.pak", b"PAKDATA", binary=True)
        manifest = dict(MANIFEST, pak={"name": "demo", "source": "file"})
        names = self.names(self.build(manifest))
        self.assertIn("ManorLords/Content/Paks/~mods/demo_P.pak", names)
        self.assertFalse([n for n in names if "/Mods/Demo/paks" in n])

    def test_the_key_in_a_committed_pak_is_found(self):
        self.write("mod/Demo/paks/demo_P.pak", b"x" + KEY.encode("utf-8"), binary=True)
        self.assertEqual(scan.scan_bytes("demo_P.pak", (self.mod_root / "Demo/paks/demo_P.pak").read_bytes(), KEY),
                         ["the AES key text is in demo_P.pak"])

    def test_a_pak_over_the_limit_gets_a_warning_with_name_size_and_lfs(self):
        self.assertIsNone(build.pak_size_warning("a_P.pak", build.PAK_SIZE_WARNING_BYTES))
        warning = build.pak_size_warning("big_P.pak", build.PAK_SIZE_WARNING_BYTES + 1024 * 1024)
        self.assertIn("big_P.pak", warning)
        self.assertIn("11.0 MB", warning)
        self.assertIn("Git LFS", warning)

    def test_a_pak_from_a_build_folder_is_found_by_name(self):
        self.write("work/demo/out/demo_P.pak", b"PAKDATA", binary=True)
        manifest = dict(MANIFEST, pak={"name": "demo", "source": "build"})
        names = self.names(self.build(manifest, pak_dir=self.root / "work"))
        self.assertIn("ManorLords/Content/Paks/~mods/demo_P.pak", names)

    def test_a_missing_pak_fails_with_a_clear_message(self):
        manifest = dict(MANIFEST, pak={"name": "demo", "source": "build"})
        with self.assertRaises(build.BuildError) as caught:
            self.build(manifest)
        self.assertIn("--pak-dir", str(caught.exception))
        with self.assertRaises(build.BuildError) as caught:
            self.build(manifest, pak_dir=self.root / "work")
        self.assertIn("demo_P.pak not found", str(caught.exception))
        manifest = dict(MANIFEST, pak={"name": "demo", "source": "file", "path": "nope_P.pak"})
        with self.assertRaises(build.BuildError):
            self.build(manifest)
        self.assertFalse(list(self.out.glob("*.tmp")), "no temporary file stays behind")


class ScanTests(ZipTestCase):
    def test_a_clean_zip_passes(self):
        self.assertEqual(scan.scan_zip(self.build(), KEY), [])

    def test_a_harness_only_module_file_fails(self):
        self.write("mod/shared/Core/HarnessLog.lua", "return {}")
        problems = scan.scan_zip(self.build(), KEY)
        self.assertTrue(any("harness-only module HarnessLog" in problem for problem in problems), problems)

    def test_a_harness_only_mod_folder_fails(self):
        self.write("mod/shared/HarnessActions/main.lua", "return {}")
        with zipfile.ZipFile(self.build()) as archive:
            self.assertEqual(archive.testzip(), None)
        build.build_zip(MANIFEST, self.mod_root, ["Core", "HarnessActions"], self.out, self.root)
        problems = scan.scan_zip(self.out / "Demo-v1.2.3.zip", KEY)
        self.assertTrue(any("HarnessActions" in problem for problem in problems), problems)

    def test_a_hard_require_of_a_harness_module_fails(self):
        self.write("mod/Demo/Scripts/main.lua", 'local log = require("HarnessLog")')
        problems = scan.scan_zip(self.build(), KEY)
        self.assertTrue(any("requires the harness-only module HarnessLog" in problem for problem in problems), problems)

    def test_an_optional_require_passes(self):
        self.write("mod/Demo/Scripts/main.lua", 'local ok, log = pcall(require, "HarnessLog")')
        self.assertEqual(scan.scan_zip(self.build(), KEY), [])

    def test_the_key_in_text_or_in_a_binary_file_fails_and_is_not_printed(self):
        self.write("mod/Demo/Scripts/main.lua", f'local k = "{KEY.upper()}"')
        problems = scan.scan_zip(self.build(), KEY)
        self.assertTrue(any("AES key" in problem for problem in problems), problems)
        self.assertFalse(any(KEY in problem.lower() for problem in problems))
        self.write("mod/Demo/Scripts/main.lua", "ok")
        self.write("paks/demo_P.pak", b"\x00\x01" + KEY.encode("utf-16-le") + b"\x02", binary=True)
        manifest = dict(MANIFEST, pak={"name": "demo", "source": "file", "path": "paks/demo_P.pak"})
        problems = scan.scan_zip(self.build(manifest), KEY)
        self.assertTrue(any("AES key" in problem and "demo_P.pak" in problem for problem in problems), problems)

    def test_the_key_file_is_checked(self):
        with self.assertRaises(FileNotFoundError):
            scan.read_key(self.root / "missing.txt")
        self.write("short.txt", "abc")
        with self.assertRaises(ValueError):
            scan.read_key(self.root / "short.txt")
        self.write("key.txt", KEY + "\n")
        self.assertEqual(scan.read_key(self.root / "key.txt"), KEY)


if __name__ == "__main__":
    unittest.main()
