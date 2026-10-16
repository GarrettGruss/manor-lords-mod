"""Tests for the guarded harness save (spec 24). A temp folder is the save folder. A fake function plays the game. No real save."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401
from runlib import fixtures, harness_save, phases, saveslots
from runlib.actions import ActionError, ActionNotPossible, Actions
from runlib.commands import CommandRefused
from runlib.harness_save import SaveGuardError

NEW_FILES = {".sav": b"new save", "_descr.sav": b"new descr", ".png": b"new png"}


class FakeGame:
    """Plays the mod. `mode` chooses what the fake save does to the folder."""

    def __init__(self, save_dir: Path, mode: str = "good"):
        self.save_dir, self.mode, self.calls = save_dir, mode, []

    def send(self, command: str, **fields) -> dict:
        self.calls.append((command, fields))
        slot = fields["save_slot"]
        if self.mode == "refuse":
            raise CommandRefused(command, "refused: slot exists")
        if self.mode == "silent":
            return {"ok": True}
        for suffix, data in NEW_FILES.items():
            (self.save_dir / f"{slot}{suffix}").write_bytes(data)
        if self.mode == "change_old":
            (self.save_dir / "saveGame_0.sav").write_bytes(b"CHANGED")
        if self.mode == "remove_old":
            (self.save_dir / "saveGame_0_descr.sav").unlink()
        if self.mode == "stray":
            (self.save_dir / "other.sav").write_bytes(b"stray")
        return {"ok": True}


class Clock:
    def __init__(self):
        self.now = 0.0
        self.saves = 0

    def sleep(self, seconds):
        self.now += seconds

    def monotonic(self):
        return self.now

    def wall(self):
        self.saves += 1  # a new second for each backup, so the backup folder names differ
        return 1_700_000_000 + self.saves


class SaveGameTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        root = Path(self._temp.name)
        self.save_dir, self.backups, self.ledger = root / "SaveGames", root / "backups", root / "ledger.json"
        self.save_dir.mkdir()
        self.originals = {"saveGame_0.sav": b"zero", "saveGame_0_descr.sav": b"zero descr", "saveGame_2.sav": b"two",
                          "saveGame_2_descr.sav": b"two descr", "rtsSettings.sav": b"settings"}
        for name, data in self.originals.items():
            (self.save_dir / name).write_bytes(data)
        self.clock = Clock()

    def save(self, mode="good", keep=False, label="probe", timeout_s=5.0, game=None):
        game = game or FakeGame(self.save_dir, mode)
        result = harness_save.save_game(self.save_dir, game.send, label, keep, self.backups, self.ledger, timeout_s,
                                        self.clock.sleep, self.clock.monotonic, now=self.clock.wall)
        return game, result

    def assert_originals_intact(self):
        for name, data in self.originals.items():
            self.assertEqual((self.save_dir / name).read_bytes(), data, name)

    def test_the_slot_is_the_next_free_number_above_the_highest(self):
        game, result = self.save()
        self.assertEqual(result["slot"], "saveGame_3")
        self.assertEqual(game.calls, [("save_game", {"save_slot": "saveGame_3", "save_name": "harness probe"})])

    def test_an_existing_file_of_the_slot_refuses_before_any_call(self):
        (self.save_dir / "saveGame_3_coat_1.png").write_bytes(b"png")  # not seen by the slot numbers, but it is a slot file
        with mock.patch.object(saveslots, "next_free_slot", return_value="saveGame_3"):
            game = FakeGame(self.save_dir)
            with self.assertRaisesRegex(SaveGuardError, "exist already"):
                self.save(game=game)
        self.assertEqual(game.calls, [])
        self.assertFalse(self.backups.exists())

    def test_a_backup_of_the_whole_folder_is_made_first(self):
        _, result = self.save()
        backup = Path(result["backup"])
        self.assertEqual(sorted(p.name for p in backup.iterdir()), sorted(self.originals))
        self.assertEqual((backup / "saveGame_2.sav").read_bytes(), b"two")
        self.assertFalse(backup.is_relative_to(self.save_dir))

    def test_only_the_newest_backups_are_kept(self):
        for _ in range(harness_save.KEPT_BACKUPS + 3):
            self.save(keep=True)
        self.assertEqual(len(list(self.backups.iterdir())), harness_save.KEPT_BACKUPS)

    def test_new_slot_files_pass_and_are_hashed(self):
        _, result = self.save()
        self.assertEqual(sorted(result["files"]), ["saveGame_3.png", "saveGame_3.sav", "saveGame_3_descr.sav"])
        self.assertEqual(result["files"]["saveGame_3.sav"], fixtures.snapshot_user_files(self.save_dir)["saveGame_3.sav"])
        self.assert_originals_intact()

    def test_a_changed_existing_file_is_restored_and_raises(self):
        with self.assertRaisesRegex(SaveGuardError, r"changed or removed: \['saveGame_0.sav'\]; restored"):
            self.save("change_old")
        self.assert_originals_intact()

    def test_a_removed_existing_file_is_restored_and_raises(self):
        with self.assertRaisesRegex(SaveGuardError, "saveGame_0_descr.sav"):
            self.save("remove_old")
        self.assert_originals_intact()

    def test_an_unexpected_new_file_raises(self):
        with self.assertRaisesRegex(SaveGuardError, "Unexpected new files.*other.sav"):
            self.save("stray")

    def test_a_missing_file_times_out_and_raises(self):
        with self.assertRaisesRegex(SaveGuardError, "timeout"):
            self.save("silent", timeout_s=2.0)
        self.assertGreater(self.clock.now, 2.0)

    def test_a_refused_command_raises_and_leaves_the_folder_unchanged(self):
        with self.assertRaises(CommandRefused):
            self.save("refuse")
        self.assert_originals_intact()
        self.assertEqual(saveslots.read_ledger(self.ledger), [])

    def test_a_bad_label_is_refused(self):
        for label in ("", "a/b", "x" * 41, "a;b"):
            with self.assertRaises(SaveGuardError):
                self.save(label=label)

    def test_a_saved_slot_goes_into_the_ledger_and_is_deleted_at_the_run_end(self):
        _, result = self.save()
        self.assertEqual([entry["slot"] for entry in saveslots.read_ledger(self.ledger)], [result["slot"]])
        removed = saveslots.uninstall_all(self.save_dir, self.ledger)
        self.assertEqual(sorted(removed[0]["removed"]), sorted(result["files"]))
        self.assertEqual(sorted(p.name for p in self.save_dir.iterdir()), sorted(self.originals))
        self.assertEqual(saveslots.read_ledger(self.ledger), [])

    def test_a_kept_save_stays_and_is_not_in_the_ledger(self):
        _, result = self.save(keep=True)
        self.assertTrue(result["kept"])
        self.assertEqual(saveslots.read_ledger(self.ledger), [])
        self.assertEqual(saveslots.uninstall_all(self.save_dir, self.ledger), [])
        self.assertTrue((self.save_dir / f"{result['slot']}.sav").is_file())


class RunEndTests(unittest.TestCase):
    def test_kept_files_are_expected_and_others_are_not(self):
        ctx = mock.Mock(state={"user_saves_snapshot": {"a.sav": "1"}, "kept_save_files": {"saveGame_3.sav": "2"}})
        expected = phases._expected_user_files(ctx)
        self.assertEqual(expected, {"a.sav": "1", "saveGame_3.sav": "2"})
        after = {"a.sav": "1", "saveGame_3.sav": "2", "b.sav": "9"}
        self.assertEqual(fixtures.describe_difference(expected, after), ["new: b.sav"])


class ActionTests(unittest.TestCase):
    class Bridge:
        def engine_path(self):
            return "engine"

    def test_the_action_returns_the_slot_and_notes_it(self):
        notes = []
        saver = lambda label, keep: {"slot": "saveGame_3", "files": {"saveGame_3.sav": "h"}, "backup": "b", "kept": keep, "user_files": 5}  # noqa: E731
        record = Actions(self.Bridge(), notes=notes, saver=saver).save_game("x", keep=True)
        self.assertEqual((record["slot"], record["kept"], record["before"], record["after"]), ("saveGame_3", True, 5, 6))
        self.assertTrue(notes)

    def test_a_guard_error_becomes_an_action_error(self):
        def saver(label, keep):
            raise SaveGuardError("restored")
        with self.assertRaisesRegex(ActionError, "restored"):
            Actions(self.Bridge(), saver=saver).save_game("x")

    def test_without_a_saver_the_action_is_not_possible(self):
        with self.assertRaises(ActionNotPossible):
            Actions(self.Bridge()).save_game("x")

    def test_save_state_is_gone_and_save_game_is_listed(self):
        self.assertIn("save_game", Actions(self.Bridge()).available())
        with self.assertRaises(ActionNotPossible):
            Actions(self.Bridge()).save_state("x")


if __name__ == "__main__":
    unittest.main()
