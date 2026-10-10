import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import runlib_path  # noqa: F401
from runlib.runfolder import (
    IterationLimitError,
    RunLock,
    RunLockedError,
    bump_iterations,
    create_run_folder,
    new_run_id,
    write_config,
)


class TempRootCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)


class RunIdAndFolderTest(TempRootCase):
    def test_run_id_format(self):
        run_id = new_run_id(datetime(2026, 10, 9, 23, 30, 0, tzinfo=timezone.utc))
        self.assertRegex(run_id, r"^20261009-233000-[0-9a-f]{4}$")

    def test_folder_has_sub_folders_and_paths(self):
        run = create_run_folder(self.root, "abc")
        for sub_dir in (run.screenshots_dir, run.crash_dir, run.bridge_dir):
            self.assertTrue(sub_dir.is_dir())
        self.assertEqual(run.summary_path, self.root / "abc" / "summary.json")
        self.assertEqual(run.config_path.name, "config.json")
        self.assertEqual(run.boot_path.name, "boot.json")

    def test_duplicate_id_is_refused(self):
        create_run_folder(self.root, "abc")
        with self.assertRaises(FileExistsError):
            create_run_folder(self.root, "abc")

    def test_config_is_written_atomically(self):
        run = create_run_folder(self.root, "abc")
        write_config(run, {"scenario": "x"})
        self.assertEqual(json.loads(run.config_path.read_text()), {"scenario": "x"})
        self.assertEqual(list(run.path.glob("*.tmp")), [])


class RunLockTest(TempRootCase):
    def test_free_lock_is_taken_and_released(self):
        with RunLock(self.root) as lock:
            self.assertTrue(lock.lock_path.exists())
            self.assertIsNone(lock.took_over_pid)
        self.assertFalse(lock.lock_path.exists())

    def test_live_holder_blocks(self):
        holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        self.addCleanup(lambda: (holder.kill(), holder.wait()))
        (self.root / ".lock").write_text(str(holder.pid))
        with self.assertRaises(RunLockedError) as caught:
            with RunLock(self.root):
                pass
        self.assertEqual(caught.exception.holder_pid, holder.pid)
        self.assertIn(str(holder.pid), str(caught.exception))
        self.assertTrue((self.root / ".lock").exists(), "the lock of the other process must stay")

    def test_stale_lock_is_taken_over_and_reported(self):
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        (self.root / ".lock").write_text(str(dead.pid))
        with RunLock(self.root) as lock:
            self.assertEqual(lock.took_over_pid, dead.pid)
        self.assertFalse(lock.lock_path.exists())

    def test_unreadable_lock_is_refused(self):
        (self.root / ".lock").write_text("not a pid")
        with self.assertRaises(RunLockedError):
            with RunLock(self.root):
                pass


class IterationTest(TempRootCase):
    def test_counts_up_to_the_limit_then_refuses(self):
        self.assertEqual(bump_iterations(self.root, 2), 1)
        self.assertEqual(bump_iterations(self.root, 2), 2)
        with self.assertRaises(IterationLimitError):
            bump_iterations(self.root, 2)
        self.assertEqual((self.root / ".iterations").read_text(), "2")
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_bad_counter_file_fails_loudly(self):
        (self.root / ".iterations").write_text("abc")
        with self.assertRaises(ValueError):
            bump_iterations(self.root, 5)


if __name__ == "__main__":
    unittest.main()
