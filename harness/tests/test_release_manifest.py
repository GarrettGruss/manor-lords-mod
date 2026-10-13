"""Tests for the manifest check, the changelog reader and the module closure (spec 19)."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from releaselib import changelog
from releaselib.files import ClosureError, hard_requires, shared_closure
from releaselib.manifest import ManifestError, check_manifest, load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]

GOOD = {
    "name": "Demo", "version": "1.2.3", "description": "A demo.", "shared": ["Core"], "pak": None,
    "tested": {"game": "0.8.111", "game_build": "1", "ue4ss": "4.0.0-rc1"}, "gate_scenarios": ["demo-scenario"],
}


def changed(**fields):
    manifest = copy.deepcopy(GOOD)
    manifest.update(fields)
    return manifest


class ManifestCheckTests(unittest.TestCase):
    def test_a_good_manifest_has_no_problem(self):
        self.assertEqual(check_manifest(GOOD, "Demo"), [])

    def test_a_pak_by_build_or_by_file_is_valid(self):
        self.assertEqual(check_manifest(changed(pak={"name": "demo_pak", "source": "build"}), "Demo"), [])
        self.assertEqual(check_manifest(changed(pak={"name": "demo_pak", "source": "file", "path": "paks/demo_pak_P.pak"}), "Demo"), [])

    def test_a_bad_pak_is_refused(self):
        self.assertEqual(check_manifest(changed(pak={"name": "x", "source": "file"}), "Demo"), [])  # default path
        self.assertIn("pak.path must be", " ".join(check_manifest(changed(pak={"name": "x", "source": "file", "path": ""}), "Demo")))
        self.assertIn("pak.path must not be set", " ".join(check_manifest(changed(pak={"name": "x", "source": "build", "path": "a"}), "Demo")))
        self.assertIn("pak.source", " ".join(check_manifest(changed(pak={"name": "x", "source": "web"}), "Demo")))
        self.assertIn("pak.name", " ".join(check_manifest(changed(pak={"name": "a b", "source": "build"}), "Demo")))

    def test_a_bad_version_is_refused(self):
        for version in ("1", "1.2", "v1.2.3", "01.2.3", 3):
            self.assertIn("version must be semver", " ".join(check_manifest(changed(version=version), "Demo")), version)

    def test_a_prerelease_version_is_valid(self):
        self.assertEqual(check_manifest(changed(version="1.0.0-rc.1"), "Demo"), [])

    def test_the_name_must_match_the_folder(self):
        self.assertIn("must equal the folder name", " ".join(check_manifest(GOOD, "Other")))

    def test_missing_and_unknown_fields_are_listed(self):
        manifest = copy.deepcopy(GOOD)
        del manifest["description"]
        manifest["colour"] = "red"
        problems = " ".join(check_manifest(manifest, "Demo"))
        self.assertIn("description is missing", problems)
        self.assertIn("colour is not a known field", problems)

    def test_gate_scenarios_must_not_be_empty(self):
        self.assertIn("gate_scenarios must not be empty", " ".join(check_manifest(changed(gate_scenarios=[]), "Demo")))

    def test_tested_versions_are_required(self):
        problems = " ".join(check_manifest(changed(tested={"game": "1"}), "Demo"))
        self.assertIn("tested.game_build is missing", problems)
        self.assertIn("tested.ue4ss is missing", problems)

    def test_a_manifest_that_is_not_an_object_is_refused(self):
        self.assertEqual(check_manifest([], "Demo"), ["the manifest must be a JSON object"])

    def test_load_reports_all_problems_in_one_error(self):
        with tempfile.TemporaryDirectory() as folder:
            mod_dir = Path(folder) / "Demo"
            mod_dir.mkdir()
            (mod_dir / "mod.json").write_text(json.dumps(changed(version="x", shared="Core")), encoding="utf-8")
            with self.assertRaises(ManifestError) as caught:
                load_manifest(mod_dir)
        self.assertIn("version must be semver", str(caught.exception))
        self.assertIn("shared must be a list", str(caught.exception))

    def test_load_reports_a_missing_file_and_bad_json(self):
        with tempfile.TemporaryDirectory() as folder:
            mod_dir = Path(folder) / "Demo"
            mod_dir.mkdir()
            with self.assertRaises(ManifestError) as caught:
                load_manifest(mod_dir)
            self.assertIn("does not exist", str(caught.exception))
            (mod_dir / "mod.json").write_text("{", encoding="utf-8")
            with self.assertRaises(ManifestError) as caught:
                load_manifest(mod_dir)
            self.assertIn("not valid JSON", str(caught.exception))

    def test_the_manifest_of_every_releasable_mod_is_valid(self):
        for manifest_file in sorted((REPO_ROOT / "mod").glob("*/mod.json")):
            load_manifest(manifest_file.parent)


class ChangelogTests(unittest.TestCase):
    TEXT = "# Changelog\n\n## [Unreleased]\n\n## [0.2.0] - 2026-10-14\n\n### Fixed\n- a fix\n\n## [0.1.0] - 2026-10-13\n\n### Added\n- first\n"

    def test_the_section_of_a_version_is_found(self):
        self.assertEqual(changelog.section_for(self.TEXT, "0.2.0"), "### Fixed\n- a fix")
        self.assertEqual(changelog.section_for(self.TEXT, "0.1.0"), "### Added\n- first")

    def test_a_missing_or_empty_section_is_none(self):
        self.assertIsNone(changelog.section_for(self.TEXT, "0.3.0"))
        self.assertIsNone(changelog.section_for(self.TEXT, "Unreleased"))

    def test_release_notes_fail_with_a_clear_message(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "CHANGELOG.md"
            with self.assertRaises(changelog.ChangelogError) as caught:
                changelog.release_notes(path, "0.1.0")
            self.assertIn("does not exist", str(caught.exception))
            path.write_text(self.TEXT, encoding="utf-8")
            with self.assertRaises(changelog.ChangelogError) as caught:
                changelog.release_notes(path, "9.9.9")
            self.assertIn("## [9.9.9]", str(caught.exception))
            self.assertIn("first", changelog.release_notes(path, "0.1.0"))


class ClosureTests(unittest.TestCase):
    def make_tree(self, files):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return root

    def test_requires_are_found_and_comments_and_optional_ones_are_not(self):
        text = 'local a = require("A")\nlocal ok, b = pcall(require, "B")\n-- local c = require("C")\nlocal d = require( \'D\' )\n'
        self.assertEqual(hard_requires(text), {"A", "D"})

    def test_the_closure_follows_requires_between_shared_modules(self):
        root = self.make_tree({"Demo/Scripts/main.lua": 'require("Core")', "shared/Core/Core.lua": 'require("Util")',
                               "shared/Util/Util.lua": "return {}"})
        self.assertEqual(shared_closure(root / "Demo", root / "shared", ["Core"]), ["Core", "Util"])

    def test_a_harness_only_module_is_refused_in_the_mod_and_in_shared(self):
        root = self.make_tree({"Demo/Scripts/main.lua": 'require("HarnessLog")', "shared/Core/Core.lua": ""})
        with self.assertRaises(ClosureError) as caught:
            shared_closure(root / "Demo", root / "shared", ["Core"])
        self.assertIn("harness-only module HarnessLog", str(caught.exception))
        root = self.make_tree({"Demo/Scripts/main.lua": 'require("Core")', "shared/Core/Core.lua": 'require("HarnessCommands")'})
        with self.assertRaises(ClosureError) as caught:
            shared_closure(root / "Demo", root / "shared", ["Core"])
        self.assertIn("Core requires the harness-only module HarnessCommands", str(caught.exception))

    def test_an_undeclared_or_missing_shared_module_is_refused(self):
        root = self.make_tree({"Demo/Scripts/main.lua": 'require("Core")', "shared/Core/Core.lua": ""})
        with self.assertRaises(ClosureError) as caught:
            shared_closure(root / "Demo", root / "shared", [])
        self.assertIn("does not list it", str(caught.exception))
        root = self.make_tree({"Demo/Scripts/main.lua": "ok"})
        with self.assertRaises(ClosureError) as caught:
            shared_closure(root / "Demo", root / "shared", ["Nope"])
        self.assertIn("does not exist", str(caught.exception))

    def test_refugee_waves_needs_no_harness_module(self):
        mod_dir = REPO_ROOT / "mod" / "RefugeeWaves"
        manifest = load_manifest(mod_dir)
        closure = shared_closure(mod_dir, REPO_ROOT / "mod" / "shared", manifest["shared"])
        self.assertEqual(closure, ["ManorCore"])


if __name__ == "__main__":
    unittest.main()
