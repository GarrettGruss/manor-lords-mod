"""Tests for the real-game gate and the hash record of a run (spec 19)."""

import json
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from releaselib import gate
from runlib.environment import MOD_FILES_NAME, hash_mod_files
from runlib.summary import condense_environment

WANTED = {"Demo/Scripts/main.lua": "aaa", "shared/Core/Core.lua": "bbb"}


def run(run_id, *, scenario="demo", verdict="pass", started="2026-10-13T10:00:00Z", build="77", hashes=None):
    return gate.RunInfo(run_id, scenario, verdict, started, build, dict(WANTED if hashes is None else hashes))


class GateLogicTests(unittest.TestCase):
    def test_a_matching_passing_run_opens_the_gate(self):
        result = gate.check_scenario("demo", [run("r1")], WANTED, "77")
        self.assertEqual(result.run_id, "r1")

    def test_the_latest_matching_run_is_reported(self):
        runs = [run("old", started="2026-10-12T10:00:00Z"), run("new", started="2026-10-13T10:00:00Z")]
        self.assertEqual(gate.check_scenario("demo", runs, WANTED, None).run_id, "new")

    def test_no_run_says_which_scenario_to_run(self):
        with self.assertRaises(gate.GateError) as caught:
            gate.check_scenario("demo", [run("r1", scenario="other")], WANTED, "77")
        self.assertIn("no real run found", str(caught.exception))
        self.assertIn("--scenario demo", str(caught.exception))

    def test_only_failed_runs_do_not_open_the_gate(self):
        with self.assertRaises(gate.GateError) as caught:
            gate.check_scenario("demo", [run("r1", verdict="fail")], WANTED, "77")
        self.assertIn("none passed", str(caught.exception))

    def test_changed_mod_files_close_the_gate(self):
        stale = run("r1", hashes={"Demo/Scripts/main.lua": "zzz", "shared/Core/Core.lua": "bbb"})
        with self.assertRaises(gate.GateError) as caught:
            gate.check_scenario("demo", [stale], WANTED, "77")
        self.assertIn("other mod files", str(caught.exception))
        self.assertIn("Demo/Scripts/main.lua", str(caught.exception))

    def test_a_missing_file_in_the_run_record_closes_the_gate(self):
        with self.assertRaises(gate.GateError):
            gate.check_scenario("demo", [run("r1", hashes={"Demo/Scripts/main.lua": "aaa"})], WANTED, "77")

    def test_a_failed_new_run_does_not_hide_an_older_matching_pass(self):
        runs = [run("pass", started="2026-10-12T10:00:00Z"), run("fail", verdict="fail", started="2026-10-13T10:00:00Z")]
        self.assertEqual(gate.check_scenario("demo", runs, WANTED, "77").run_id, "pass")

    def test_another_game_build_closes_the_gate(self):
        with self.assertRaises(gate.GateError) as caught:
            gate.check_scenario("demo", [run("r1", build="99")], WANTED, "77")
        self.assertIn("game build 99", str(caught.exception))

    def test_extra_files_in_the_run_record_do_not_matter(self):
        extra = run("r1", hashes={**WANTED, "Other/main.lua": "ccc"})
        self.assertEqual(gate.check_scenario("demo", [extra], WANTED, "77").run_id, "r1")


class RunFolderTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.runs = Path(folder.name)

    def make_run(self, run_id, summary, files=None):
        path = self.runs / run_id
        path.mkdir()
        (path / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        if files is not None:
            (path / MOD_FILES_NAME).write_text(json.dumps(files), encoding="utf-8")

    def test_real_runs_need_a_hash_record(self):
        env = {"game_build": "77", "mod_files": MOD_FILES_NAME}
        self.make_run("real", {"scenario": "demo", "verdict": "pass", "started": "t", "environment": env}, WANTED)
        self.make_run("fake", {"scenario": "demo", "verdict": "pass", "started": "t", "environment": {"mods_hash": "x"}})
        self.make_run("broken", {"scenario": "demo", "verdict": "pass", "started": "t", "environment": env})
        (self.runs / "no-summary").mkdir()
        self.assertEqual([r.run_id for r in gate.real_runs(self.runs)], ["real"])

    def test_current_hashes_cover_the_mod_and_its_shared_modules(self):
        mod_root = self.runs / "mod"
        for name in ("Demo/Scripts/main.lua", "shared/Core/Core.lua", "shared/Other/Other.lua", "Demo/__pycache__/x.pyc"):
            (mod_root / name).parent.mkdir(parents=True, exist_ok=True)
            (mod_root / name).write_text(name, encoding="utf-8")
        hashes = gate.current_hashes(mod_root, "Demo", ["Core"])
        self.assertEqual(sorted(hashes), ["Demo/Scripts/main.lua", "shared/Core/Core.lua"])
        self.assertEqual(hashes, {k: v for k, v in hash_mod_files(mod_root).items() if k in hashes})

    def test_the_run_summary_names_the_hash_file(self):
        self.assertEqual(condense_environment({"mod_files": MOD_FILES_NAME})["mod_files"], MOD_FILES_NAME)


if __name__ == "__main__":
    unittest.main()
