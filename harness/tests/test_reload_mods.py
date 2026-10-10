"""Unit tests for harness/tools/reload_mods.py. No game: a thread plays the part of HarnessReload."""

import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import reload_mods  # noqa: E402


class TempCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.mod_dir = self.root / "mod"
        self.run_dir = self.root / "run"
        self.run_dir.mkdir()
        (self.run_dir / "mod.log").write_text("", encoding="utf-8")

    def make_mod(self, name, text="", folder="Scripts"):
        script = self.mod_dir / name / folder / "main.lua"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(text, encoding="utf-8")

    def fake_game(self, version="7", ok=True, error=None, delay=0.05):
        """Answer one request like HarnessReload does."""
        def work():
            request_file = self.run_dir / "reload.json"
            for _ in range(200):
                if request_file.exists():
                    request = json.loads(request_file.read_text(encoding="utf-8"))
                    request_file.unlink()
                    time.sleep(delay)
                    answer = {"id": request["id"], "mod": request["mod"], "ok": ok, "version": version if ok else None,
                              "error": error}
                    (self.run_dir / "reload.result.json").write_text(json.dumps(answer), encoding="utf-8")
                    return
                time.sleep(0.01)

        thread = threading.Thread(target=work)
        thread.start()
        self.addCleanup(thread.join)


class VersionTest(TempCase):
    def test_version_is_read_from_the_repo_file(self):
        self.make_mod("A", 'local log = 1\nlocal VERSION = "3.1"\n')
        self.make_mod("B", "-- no version here\n")
        self.make_mod("C", '  local VERSION = "9"', folder="scripts")
        self.assertEqual(reload_mods.read_repo_version(self.mod_dir, "A"), "3.1")
        self.assertIsNone(reload_mods.read_repo_version(self.mod_dir, "B"))
        self.assertEqual(reload_mods.read_repo_version(self.mod_dir, "C"), "9")
        self.assertIsNone(reload_mods.read_repo_version(self.mod_dir, "Missing"))


class ChangedModsTest(TempCase):
    def test_copied_lines_are_parsed(self):
        output = "unchanged  A\Scripts\main.lua\ncopied     B\Scripts\main.lua\ncopied     shared\X\X.lua\n"
        self.assertEqual(reload_mods.parse_copied_files(output), ["B\Scripts\main.lua", "shared\X\X.lua"])

    def test_mods_and_shared_users(self):
        self.make_mod("Uses", 'local x = require("Shared1")')
        self.make_mod("Other", "-- nothing")
        self.make_mod("HarnessBoot", 'require("Shared1")')
        mods, notes = reload_mods.mods_to_reload(
            ["Other\Scripts\main.lua", "shared\Shared1\Shared1.lua", "HarnessReload\Scripts\main.lua"], self.mod_dir)
        self.assertEqual(mods, ["Other", "Uses"])
        self.assertTrue(any("shared module Shared1 changed" in n for n in notes))
        self.assertTrue(any("HarnessBoot is not restarted by default" in n for n in notes))
        self.assertTrue(any("HarnessReload is not restarted by default" in n for n in notes))

    def test_nothing_changed_nothing_to_reload(self):
        self.assertEqual(reload_mods.mods_to_reload([], self.mod_dir), ([], []))


class ReloadOneTest(TempCase):
    def test_success_with_matching_version(self):
        self.fake_game(version="7")
        report = reload_mods.reload_one(self.run_dir, "A", "7", timeout_s=5)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["version"], "7")

    def test_wrong_version_fails_with_both_versions(self):
        self.fake_game(version="6")
        report = reload_mods.reload_one(self.run_dir, "A", "7", timeout_s=5)
        self.assertFalse(report["ok"])
        self.assertIn("runs version 6", report["error"])
        self.assertIn("repository has 7", report["error"])

    def test_no_repo_version_accepts_any_version(self):
        self.fake_game(version="1")
        self.assertTrue(reload_mods.reload_one(self.run_dir, "A", None, timeout_s=5)["ok"])

    def test_game_error_is_passed_on(self):
        self.fake_game(ok=False, error="no mod folder")
        report = reload_mods.reload_one(self.run_dir, "A", "1", timeout_s=5)
        self.assertEqual((report["ok"], report["error"]), (False, "no mod folder"))

    def test_stale_result_is_not_taken_for_the_answer(self):
        (self.run_dir / "reload.result.json").write_text(json.dumps({"id": "old", "ok": True, "version": "7"}), encoding="utf-8")
        report = reload_mods.reload_one(self.run_dir, "A", "7", timeout_s=0.3)
        self.assertFalse(report["ok"])
        self.assertIn("no answer", report["error"])

    def test_request_file_is_written_atomically_with_a_unique_id(self):
        reload_mods.write_request(self.run_dir, "A", "id-1")
        self.assertEqual(json.loads((self.run_dir / "reload.json").read_text()), {"mod": "A", "id": "id-1"})
        self.assertFalse((self.run_dir / "reload.json.tmp").exists())
        ids = {reload_mods.uuid.uuid4().hex[:12] for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_half_written_result_is_ignored(self):
        (self.run_dir / "reload.result.json").write_text('{"id": "x", "o', encoding="utf-8")
        self.assertIsNone(reload_mods.read_result(self.run_dir, "x"))


class MainTest(TempCase):
    def test_bad_mod_name_is_a_harness_error(self):
        self.assertEqual(reload_mods.main(["--mod", "bad name", "--run-dir", str(self.run_dir), "--no-deploy"]), 2)

    def test_run_dir_without_a_log_is_refused(self):
        empty = self.root / "empty"
        empty.mkdir()
        with self.assertRaisesRegex(reload_mods.ReloadError, "mod.log"):
            reload_mods.reload_mods(["HarnessLogTest"], empty)

    def test_no_deploy_needs_a_mod(self):
        self.assertEqual(reload_mods.main(["--no-deploy", "--run-dir", str(self.run_dir)]), 2)

    def test_full_flow_with_a_fake_deploy(self):
        self.make_mod("HarnessLogTest", 'local VERSION = "7"')
        self.fake_game(version="7")
        with mock.patch.object(reload_mods, "REPO_ROOT", self.root), \
                mock.patch.object(reload_mods, "run_deploy", return_value="copied     HarnessLogTest\Scripts\main.lua\n"), \
                mock.patch("builtins.print") as printed:
            code = reload_mods.main(["--run-dir", str(self.run_dir)])
        self.assertEqual(code, 0)
        report = json.loads(printed.call_args.args[0])
        self.assertEqual([m["mod"] for m in report["mods"]], ["HarnessLogTest"])
        self.assertTrue(report["ok"])


if __name__ == "__main__":
    unittest.main()
