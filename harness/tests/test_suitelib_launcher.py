import json
import sys
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from suitelib.launcher import SubprocessLauncher

STUB = Path(__file__).resolve().parent / "stub_launcher.py"


class TimeoutCleanupTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        plan = self.root / "plan.json"
        plan.write_text(json.dumps({"a": [{"mode": "hang"}]}))
        self.env_patch = {"HARNESS_STUB_PLAN": str(plan), "HARNESS_STUB_STATE": str(self.root / "state.json")}

    def launch(self, on_timeout):
        import os
        os.environ.update(self.env_patch)
        self.addCleanup(lambda: [os.environ.pop(key, None) for key in self.env_patch])
        launcher = SubprocessLauncher(self.root / "runs", [sys.executable, str(STUB)], run_timeout_s=2, on_timeout=on_timeout)
        return launcher("a", "run-1")

    def test_timeout_kills_the_run_and_calls_the_cleanup_once(self):
        calls = []
        result = self.launch(lambda: calls.append("closed"))
        self.assertEqual(result.verdict, "timeout")
        self.assertEqual(calls, ["closed"])
        self.assertLess(result.duration_s, 30)

    def test_no_cleanup_is_needed_without_a_hook(self):
        self.assertEqual(self.launch(None).verdict, "timeout")


if __name__ == "__main__":
    unittest.main()
