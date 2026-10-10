import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib.summary import EXIT_CODES

RUN_PY = Path(__file__).resolve().parent.parent / "run.py"
OUTCOMES = ("pass", "fail", "crash", "timeout", "harness_error")


class CliTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.runs_root = Path(temp.name) / "runs"

    def run_cli(self, *args):
        command = [sys.executable, str(RUN_PY), "--runs-root", str(self.runs_root), *args]
        return subprocess.run(command, capture_output=True, text=True, timeout=60)

    def test_each_fake_outcome(self):
        for outcome in OUTCOMES:
            with self.subTest(outcome=outcome):
                result = self.run_cli("--fake", outcome, "--run-id", f"id-{outcome}")
                self.assertEqual(result.returncode, EXIT_CODES[outcome], result.stderr)
                lines = result.stdout.strip().splitlines()
                self.assertEqual(len(lines), 1)
                self.assertIn(f"id-{outcome} {outcome}", lines[0])
                summary_path = self.runs_root / f"id-{outcome}" / "summary.json"
                self.assertIn(str(summary_path), lines[0])
                data = json.loads(summary_path.read_text())
                self.assertEqual((data["run_id"], data["verdict"]), (f"id-{outcome}", outcome))
                self.assertTrue((summary_path.parent / "config.json").exists())
        self.assertFalse((self.runs_root / ".lock").exists(), "the lock must be released")
        self.assertEqual((self.runs_root / ".iterations").read_text(), str(len(OUTCOMES)))

    def test_fake_is_required(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 4)
        self.assertIn("--fake", result.stderr)

    def test_iteration_limit(self):
        self.assertEqual(self.run_cli("--fake", "pass", "--max-runs", "1").returncode, 0)
        result = self.run_cli("--fake", "pass", "--max-runs", "1")
        self.assertEqual(result.returncode, 4)
        self.assertIn("Iteration limit", result.stderr)

    def test_live_lock_holder(self):
        holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        self.addCleanup(lambda: (holder.kill(), holder.wait()))
        self.runs_root.mkdir()
        (self.runs_root / ".lock").write_text(str(holder.pid))
        result = self.run_cli("--fake", "pass")
        self.assertEqual(result.returncode, 4)
        self.assertIn(str(holder.pid), result.stderr)

    def test_stale_lock_is_reported_in_summary(self):
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        self.runs_root.mkdir()
        (self.runs_root / ".lock").write_text(str(dead.pid))
        result = self.run_cli("--fake", "pass", "--run-id", "x")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((self.runs_root / "x" / "summary.json").read_text())
        self.assertTrue(any(str(dead.pid) in note for note in data["notes"]))

    def test_duplicate_run_id(self):
        self.run_cli("--fake", "pass", "--run-id", "dup")
        result = self.run_cli("--fake", "pass", "--run-id", "dup")
        self.assertEqual(result.returncode, 4)


if __name__ == "__main__":
    unittest.main()
