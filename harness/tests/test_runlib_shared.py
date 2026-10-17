"""State shared by the main checkout and its git worktrees (spec 11): slots, locks, counter, ledger."""

import shutil
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib import gameslots, harness_save, saveslots, scenario_context, shared
from runlib.runfolder import RunLock


class MainCheckoutTest(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.main = self.temp / "repo"
        (self.main / ".git" / "worktrees" / "feature").mkdir(parents=True)
        self.worktree = self.main / ".claude" / "worktrees" / "feature"
        self.worktree.mkdir(parents=True)

    def test_a_worktree_maps_to_its_main_checkout(self):
        (self.worktree / ".git").write_text(f"gitdir: {self.main / '.git' / 'worktrees' / 'feature'}\n", encoding="utf-8")
        self.assertEqual(shared.main_checkout(self.worktree), self.main)

    def test_the_main_checkout_maps_to_itself(self):
        self.assertEqual(shared.main_checkout(self.main), self.main)

    def test_a_folder_without_git_maps_to_itself(self):
        self.assertEqual(shared.main_checkout(self.temp), self.temp)

    def test_a_strange_git_file_is_a_clear_error(self):
        (self.worktree / ".git").write_text("gitdir: C:/somewhere/else\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "not <main>/.git/worktrees"):
            shared.main_checkout(self.worktree)
        (self.worktree / ".git").write_text("not a git file\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "not a git worktree file"):
            shared.main_checkout(self.worktree)


class SharedPathsTest(unittest.TestCase):
    def test_the_default_runs_folder_maps_to_the_shared_one(self):
        self.assertEqual(shared.lock_root(shared.REPO_ROOT / "runs"), shared.SHARED_RUNS)

    def test_another_runs_folder_keeps_its_own_locks(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp, True)
        self.assertEqual(shared.lock_root(temp), temp)
        self.assertEqual(RunLock(temp, 2).lock_path, temp / ".lock-2")

    def test_all_shared_state_lives_in_the_shared_root(self):
        self.assertEqual(RunLock(shared.REPO_ROOT / "runs", 1).lock_path, shared.SHARED_RUNS / ".lock-1")
        self.assertEqual(gameslots.SLOTS_DIR, shared.SHARED_ROOT / "slots")
        self.assertEqual(saveslots.LEDGER_PATH.parent, shared.SHARED_RUNS)
        self.assertEqual(saveslots.saves_lock().lock_path.parent, shared.SHARED_RUNS)
        self.assertEqual(scenario_context.INPUT_LOCK_PATH.parent, shared.SHARED_RUNS)
        self.assertEqual(harness_save.BACKUP_ROOT.parent, shared.SHARED_RUNS)


if __name__ == "__main__":
    unittest.main()
