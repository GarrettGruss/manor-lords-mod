"""Fake tests for genmesh.py. No network, no key."""
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import genmesh  # noqa: E402


class GenmeshTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.log = self.dir / "log.jsonl"
        self.image = self.dir / "a.png"
        self.image.write_bytes(b"png")

    def fake_call(self, status="SUCCEEDED", credits=30):
        calls = []

        def call(method, path, body=None):
            calls.append((method, path))
            if method == "POST":
                return {"result": "t1"}
            return {"id": "t1", "status": status, "consumed_credits": credits,
                    "model_urls": {"fbx": "u/m.fbx", "glb": "u/m.glb"},
                    "texture_urls": [{"base_color": "u/b.png"}]}
        return call, calls

    def test_success_logs_credits_and_downloads(self):
        call, _ = self.fake_call()
        fetched = []
        genmesh.run_multi([self.image], self.dir / "o", 2000, "meshy-6", call,
                          lambda url, target: (fetched.append(url), target.write_bytes(b"x")), lambda s: None, self.log)
        self.assertEqual(json.loads(self.log.read_text())["credits"], 30)
        self.assertEqual(len(fetched), 3)

    def test_day_cap_refuses(self):
        genmesh.log_call({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "credits": 190}, self.log)
        call, calls = self.fake_call()
        with self.assertRaises(SystemExit):
            genmesh.run_multi([self.image], self.dir / "o", 2000, "meshy-6", call, None, lambda s: None, self.log)
        self.assertEqual(calls, [])

    def test_failed_task_raises_and_logs(self):
        call, _ = self.fake_call("FAILED", 0)
        with self.assertRaises(SystemExit):
            genmesh.run_multi([self.image], self.dir / "o", 2000, "meshy-6", call, None, lambda s: None, self.log)
        self.assertEqual(json.loads(self.log.read_text())["status"], "FAILED")

    def test_image_count_checked(self):
        with self.assertRaises(SystemExit):
            genmesh.build_payload([], 2000, "meshy-6")


if __name__ == "__main__":
    unittest.main()
