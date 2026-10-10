import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401

HARNESS_DIR = Path(__file__).resolve().parent.parent
SUITE_PY = HARNESS_DIR / "suite.py"
STUB = Path(__file__).resolve().parent / "stub_launcher.py"

SUITE = {
    "name": "t",
    "scenarios": [{"scenario": "a"}, {"scenario": "b", "repeat": 2}, {"scenario": "later", "optional": True}],
    "time_budget_s": 600,
    "flake_retries": 1,
}


def metric_step(value, duration=50.0, verdict="pass"):
    return {"verdict": verdict, "duration_s": duration, "asserts": [{"name": "ticks", "ok": True, "value": value}]}


class SuiteCliTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.runs_root = self.root / "runs"
        self.suites_dir = self.root / "suites"
        self.baselines_dir = self.root / "baselines"
        self.suites_dir.mkdir()
        self.set_suite(SUITE)

    def set_suite(self, suite):
        (self.suites_dir / f"{suite['name']}.json").write_text(json.dumps(suite))

    def run_cli(self, plan, *args, timeout=120):
        plan_path = self.root / "plan.json"
        plan_path.write_text(json.dumps(plan))
        state_path = self.root / "state.json"
        state_path.unlink(missing_ok=True)
        env = {**os.environ, "HARNESS_STUB_PLAN": str(plan_path), "HARNESS_STUB_STATE": str(state_path)}
        env["HARNESS_SUITE_LAUNCHER"] = f'"{sys.executable}" "{STUB}"'
        command = [
            sys.executable, str(SUITE_PY), "--runs-root", str(self.runs_root), "--suites-dir", str(self.suites_dir),
            "--baselines-dir", str(self.baselines_dir), *args,
        ]
        return subprocess.run(command, capture_output=True, text=True, env=env, timeout=timeout)

    def report(self):
        # Folder names only have a one second time stamp and a random suffix, so two suites started in the
        # same second would sort in a random order. Pick the newest by file time instead.
        folder = max(self.runs_root.glob("suite-2*"), key=lambda f: (f / "report.json").stat().st_mtime_ns)
        return json.loads((folder / "report.json").read_text()), folder

    def test_all_pass(self):
        done = self.run_cli({"later": [{"mode": "unknown"}]}, "--suite", "t")
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
        data, folder = self.report()
        self.assertEqual(data["verdict"], "pass")
        self.assertEqual(data["totals"]["runs"], 3)
        self.assertEqual(data["scenarios"][2]["verdict"], "skipped")
        self.assertTrue((folder / "report.md").is_file())
        history_lines = (self.runs_root / "suite-history.jsonl").read_text().splitlines()
        self.assertEqual(len(history_lines), 3)

    def test_fail_gives_exit_1_and_retry_is_visible(self):
        done = self.run_cli({"a": [{"verdict": "fail"}], "later": [{"mode": "unknown"}]}, "--suite", "t")
        self.assertEqual(done.returncode, 1)
        data, _ = self.report()
        self.assertEqual(data["scenarios"][0]["attempts"], 2)

    def test_flaky_passes_with_exit_0(self):
        done = self.run_cli({"a": [{"verdict": "fail"}, {"verdict": "pass"}], "later": [{"mode": "unknown"}]}, "--suite", "t")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(self.report()[0]["totals"]["flaky"], 1)

    def test_crash_does_not_stop_the_suite(self):
        done = self.run_cli({"a": [{"verdict": "crash"}], "later": [{"mode": "unknown"}]}, "--suite", "t")
        self.assertEqual(done.returncode, 2)
        verdicts = [s["verdict"] for s in self.report()[0]["scenarios"]]
        self.assertEqual(verdicts, ["crash", "pass", "skipped"])

    def test_missing_summary_is_harness_error(self):
        done = self.run_cli({"a": [{"mode": "no_summary", "verdict": "harness_error"}]}, "--suite", "t")
        self.assertEqual(done.returncode, 4)
        self.assertIn("no summary.json", self.report()[0]["scenarios"][0]["reason"])

    def test_iteration_cap_exit_3(self):
        done = self.run_cli({"b": [{"mode": "iteration_cap"}]}, "--suite", "t")
        self.assertEqual(done.returncode, 3)
        data, _ = self.report()
        self.assertIn("iteration cap", data["stopped"])
        self.assertEqual(data["not_run"], ["b", "later"])

    def test_run_time_limit_is_a_timeout_and_suite_goes_on(self):
        done = self.run_cli({"a": [{"mode": "hang"}], "later": [{"mode": "unknown"}]}, "--suite", "t", "--run-timeout-s", "1")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(self.report()[0]["scenarios"][0]["verdict"], "timeout")

    def test_deliberate_regression_is_caught_and_baseline_untouched(self):
        plan = {"a": [metric_step(100)], "b": [{"verdict": "pass"}], "later": [{"mode": "unknown"}]}
        self.assertEqual(self.run_cli(plan, "--suite", "t").returncode, 0)
        proposal = self.run_cli(plan, "--update-baseline", "a")
        self.assertEqual(proposal.returncode, 0, proposal.stderr)
        baseline_file = self.baselines_dir / "a.json"
        data = json.loads(baseline_file.read_text())
        self.assertEqual(data["metrics"]["ticks"], [90.0, 110.0])
        data["strict"] = []
        baseline_file.write_text(json.dumps(data))
        before = baseline_file.read_text()

        regress = {**plan, "a": [metric_step(10)]}
        done = self.run_cli(regress, "--suite", "t")
        self.assertEqual(done.returncode, 0, "non-strict drift does not fail")
        report_data, _ = self.report()
        self.assertEqual(report_data["verdict"], "drift")
        self.assertEqual(report_data["scenarios"][0]["drift"][0]["direction"], "below")
        self.assertEqual(baseline_file.read_text(), before, "a normal run never writes a baseline")

    def test_strict_regression_fails(self):
        self.baselines_dir.mkdir()
        (self.baselines_dir / "a.json").write_text(json.dumps({"metrics": {"ticks": [90, 110]}, "strict": ["ticks"]}))
        done = self.run_cli({"a": [metric_step(10)], "later": [{"mode": "unknown"}]}, "--suite", "t")
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.report()[0]["verdict"], "fail")

    def test_update_baseline_without_runs_is_an_error(self):
        done = self.run_cli({}, "--update-baseline", "a")
        self.assertEqual(done.returncode, 4)
        self.assertFalse((self.baselines_dir / "a.json").exists())

    def test_update_baseline_uses_last_n_passing_runs(self):
        for index, (verdict, value) in enumerate([("pass", 1), ("fail", 500), ("pass", 3), ("pass", 5)]):
            folder = self.runs_root / f"r{index}"
            folder.mkdir(parents=True)
            data = {"scenario": "a", "verdict": verdict, "started": f"2026-01-0{index + 1}T00:00:00Z", "duration_s": 10,
                    "scenario_result": {"asserts": [{"name": "v", "ok": True, "value": value}]}}
            (folder / "summary.json").write_text(json.dumps(data))
        done = self.run_cli({}, "--update-baseline", "a", "--from-last", "2")
        self.assertEqual(done.returncode, 0, done.stderr)
        metrics = json.loads((self.baselines_dir / "a.json").read_text())["metrics"]
        # last 2 passing runs have values 5 and 3: spread 2, margin 0.4, floor 0.5.
        self.assertEqual(metrics["v"], [2.5, 5.5])

    def test_list_and_bad_arguments(self):
        listed = self.run_cli({}, "--list")
        self.assertEqual(listed.returncode, 0)
        self.assertIn("later", listed.stdout)
        self.assertEqual(self.run_cli({}).returncode, 4)
        missing = self.run_cli({}, "--suite", "nope")
        self.assertEqual(missing.returncode, 4)
        self.assertIn("nope", missing.stderr)


if __name__ == "__main__":
    unittest.main()
