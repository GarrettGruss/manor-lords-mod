"""Tests for the manor-lords-mod changes to sn-motion-html: key lookup, spend cap,
spend log, and the export timeline. No network, no browser, no paid request.

Run: uv run python -m unittest discover -s .claude/skills/sn-motion-html/tests
"""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import export_video  # noqa: E402
import seedance_pipeline as pipeline  # noqa: E402

FAKE_KEY = "sk-test-secret-value"


def make_project(root: Path, dive_count: int = 2) -> dict:
    dives = [
        {"id": f"d{i}", "prompt": f"prompts/d{i}.txt", "still": f"stills/d{i}.png", "output": f"out/d{i}.mp4"}
        for i in range(dive_count)
    ]
    manifest = {
        "model": "m", "duration": 4, "resolution": "720p", "ratio": "16:9",
        "dives": dives, "connectors": [],
    }
    (root / "prompts").mkdir(parents=True)
    (root / "stills").mkdir()
    for dive in dives:
        (root / dive["prompt"]).write_text("prompt", encoding="utf-8")
        (root / dive["still"]).write_bytes(b"png")
    (root / "prompts" / "video-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


def run_args(**overrides) -> argparse.Namespace:
    values = dict(phase="dives", limit=0, force=False, attempts=2, poll_seconds=0, timeout_seconds=5, workers=1)
    values.update(overrides)
    return argparse.Namespace(**values)


class KeyLookupTest(unittest.TestCase):
    def test_seedance_name_wins(self):
        with mock.patch.dict(os.environ, {"SEEDANCE_API_KEY": "a", "ARK_API_KEY": "b"}, clear=True):
            self.assertEqual(pipeline.find_api_key(), "a")

    def test_old_name_still_works(self):
        with mock.patch.dict(os.environ, {"ARK_API_KEY": "b"}, clear=True):
            self.assertEqual(pipeline.find_api_key(), "b")

    def test_windows_registry_fallback(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(pipeline, "windows_user_variable", side_effect=lambda n: "w" if n == "SEEDANCE_API_KEY" else ""):
            self.assertEqual(pipeline.find_api_key(), "w")

    def test_missing_key_message_has_no_value(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(pipeline, "windows_user_variable", return_value=""):
            with self.assertRaises(SystemExit) as caught:
                pipeline.find_api_key()
        self.assertIn("SEEDANCE_API_KEY", str(caught.exception))


class SpendCapTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manifest = make_project(self.root, dive_count=3)

    def tearDown(self):
        self.temp.cleanup()

    def test_pending_counts_missing_outputs(self):
        (self.root / "out").mkdir()
        (self.root / "out" / "d0.mp4").write_bytes(b"x")
        self.assertEqual(pipeline.pending_clips(self.root, self.manifest, run_args()), 2)
        self.assertEqual(pipeline.pending_clips(self.root, self.manifest, run_args(force=True)), 3)

    def test_main_refuses_batch_above_cap_without_network(self):
        argv = ["seedance_pipeline.py", str(self.root), "dives", "--max-clips", "2"]
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(pipeline, "ArkClient") as client, \
             mock.patch("sys.stdout", io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                pipeline.main()
        self.assertIn("--max-clips is 2", str(caught.exception))
        client.assert_not_called()

    def test_default_cap_is_zero(self):
        argv = ["seedance_pipeline.py", str(self.root), "dives"]
        with mock.patch.object(sys, "argv", argv), mock.patch("sys.stdout", io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                pipeline.main()
        self.assertIn("--max-clips is 0", str(caught.exception))

    def test_guard_stops_retries_at_cap(self):
        guard = pipeline.SpendGuard(1, self.root / "logs" / "spend.jsonl")
        guard.reserve("a")
        with self.assertRaises(pipeline.SpendCapReached):
            guard.reserve("b")


class FakeClient:
    def __init__(self, fail_with: Exception | None = None):
        self.fail_with = fail_with
        self.created = 0

    def create(self, payload):
        self.created += 1
        if self.fail_with:
            raise self.fail_with
        return f"task-{self.created}"

    def wait(self, task_id, poll, timeout):
        return {"status": "succeeded", "content": {"video_url": "https://example.invalid/v.mp4"}, "usage": {"tokens": 1}}


class GenerateClipTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manifest = make_project(self.root, dive_count=1)
        self.log = self.root / "logs" / "spend.jsonl"
        self.item = self.manifest["dives"][0]

    def tearDown(self):
        self.temp.cleanup()

    def generate(self, client, guard):
        with mock.patch.object(pipeline, "download"), mock.patch.object(pipeline, "normalize_video"), \
             mock.patch("sys.stdout", io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
            pipeline.generate_clip(self.root, client, guard, self.manifest, "dives", self.item,
                                   self.root / self.item["still"], None, run_args())

    def test_success_logs_one_line_without_secrets(self):
        with mock.patch.dict(os.environ, {"SEEDANCE_API_KEY": FAKE_KEY}):
            self.generate(FakeClient(), pipeline.SpendGuard(5, self.log))
        lines = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual((record["clip_id"], record["status"], record["task_id"]), ("d0", "succeeded", "task-1"))
        self.assertNotIn(FAKE_KEY, lines[0])
        self.assertNotIn("data:", lines[0])

    def test_billing_error_is_not_retried(self):
        client = FakeClient()
        client.create = mock.Mock(side_effect=pipeline.NonRetryableArkError("Ark HTTP 402"))
        with self.assertRaises(pipeline.NonRetryableArkError):
            self.generate(client, pipeline.SpendGuard(5, self.log))
        self.assertEqual(client.create.call_count, 1)

    def test_http_402_maps_to_non_retryable(self):
        ark = pipeline.ArkClient(FAKE_KEY, "https://example.invalid")
        error = HTTPError("u", 402, "Payment Required", {}, io.BytesIO(b"{}"))
        with mock.patch.object(pipeline, "urlopen", side_effect=error):
            with self.assertRaises(pipeline.NonRetryableArkError) as caught:
                ark.request("POST", "/x", {})
        self.assertNotIn(FAKE_KEY, str(caught.exception))

    def test_transient_error_retries_within_cap(self):
        client = FakeClient(fail_with=RuntimeError("network"))
        with self.assertRaises(RuntimeError):
            self.generate(client, pipeline.SpendGuard(5, self.log))
        self.assertEqual(client.created, 2)
        self.assertEqual(len(self.log.read_text(encoding="utf-8").splitlines()), 2)


class ExportScheduleTest(unittest.TestCase):
    SEGMENTS = [
        {"id": "a", "kind": "scene", "units": 4.0},
        {"id": "connector-0", "kind": "connector", "units": 1.0},
        {"id": "b", "kind": "scene", "units": 4.0},
    ]

    def timing(self, **overrides):
        timing = dict(export_video.DEFAULT_TIMING, seconds={})
        timing.update(overrides)
        return timing

    def test_defaults_and_overrides(self):
        schedule = export_video.build_schedule(self.SEGMENTS, self.timing(seconds={"a": 6}))
        self.assertEqual([s.seconds for s in schedule], [6, 1.5, 4.0])
        self.assertEqual(export_video.total_seconds(schedule, self.timing()), 12.5)

    def test_unknown_id_fails(self):
        with self.assertRaises(SystemExit):
            export_video.build_schedule(self.SEGMENTS, self.timing(seconds={"typo": 3}))

    def test_time_maps_into_route_units(self):
        schedule = export_video.build_schedule(self.SEGMENTS, self.timing(head_seconds=1))
        self.assertEqual(export_video.route_units_at(schedule, 0.5), 0.0)
        self.assertAlmostEqual(export_video.route_units_at(schedule, 3.0), 2.0)
        self.assertAlmostEqual(export_video.route_units_at(schedule, 5.75), 4.5)
        self.assertLess(export_video.route_units_at(schedule, 99), 9.0)
        self.assertGreater(export_video.route_units_at(schedule, 99), 8.9)


if __name__ == "__main__":
    unittest.main()
