"""Tests for collecting crash reports after a run ended (collect_crash.py)."""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib import phases
from runlib.game import GameInstall
from runlib.latecrash import LateCrashError, collect_late_crashes


class LateCrashTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.temp = Path(self._tmp.name)
        self.install = GameInstall(root=self.temp / "game", saved_dir=self.temp / "saved")
        self.run = self.temp / "runs" / "r1"
        self.run.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def write_record(self, pid=4242, started=None):
        record = {"pid": pid, "run_started_epoch": started or time.time() - 60, "appdata_dir": None}
        (self.run / phases.GAME_RECORD_FILE).write_text(json.dumps(record), encoding="utf-8")

    def make_crash(self, name, pid, age_s=-5):
        folder = self.install.crashes_dir / name
        folder.mkdir(parents=True)
        (folder / phases.CRASH_CONTEXT_FILE).write_text(f"<root><ProcessId>{pid}</ProcessId></root>", encoding="utf-8")
        stamp = time.time() - age_s
        os.utime(folder, (stamp, stamp))

    def test_missing_record_fails_loudly(self):
        with self.assertRaises(LateCrashError):
            collect_late_crashes(self.install, self.run)

    def test_crash_of_the_run_game_is_copied_once(self):
        self.write_record()
        self.make_crash("late", 4242)
        self.assertEqual(collect_late_crashes(self.install, self.run)["copied"], ["crash/late"])
        self.assertTrue((self.run / "crash" / "late" / phases.CRASH_CONTEXT_FILE).exists())
        self.assertEqual(collect_late_crashes(self.install, self.run)["copied"], [])

    def test_crash_of_another_process_or_before_the_run_is_skipped(self):
        self.write_record()
        self.make_crash("other", 1111)
        self.make_crash("old", 4242, age_s=3600)
        self.assertEqual(collect_late_crashes(self.install, self.run)["copied"], [])

    def test_ue4ss_dump_is_copied(self):
        self.write_record()
        ue4ss = self.install.win64 / "ue4ss"
        ue4ss.mkdir(parents=True)
        (ue4ss / "crash_1.dmp").write_bytes(b"d")
        self.assertEqual(collect_late_crashes(self.install, self.run)["copied"], ["crash/crash_1.dmp"])


if __name__ == "__main__":
    unittest.main()
