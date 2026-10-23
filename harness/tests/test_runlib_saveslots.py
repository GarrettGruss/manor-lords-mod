"""Tests for installing a save under a free slot name and removing it (spec 06, part D). Temp folders only."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401
from runlib import saveslots
from saveslot_support import descriptor


class DescriptorTest(unittest.TestCase):
    def test_rewrite_changes_only_the_value_and_fixes_the_size(self):
        data = descriptor("saveGame_28")
        longer = saveslots.rewrite_str_property(data, "saveSlot", "saveGame_100")
        self.assertEqual(saveslots.read_str_property(longer, "saveSlot"), "saveGame_100")
        self.assertEqual(saveslots.read_str_property(longer, "saveName"), "saveGame_28")
        self.assertEqual(saveslots.read_str_property(longer, "LevelName"), "Jagged_Cliffs")
        self.assertEqual(saveslots.rewrite_str_property(longer, "saveSlot", "saveGame_28"), data)

    def test_a_missing_or_doubled_property_is_refused(self):
        with self.assertRaisesRegex(saveslots.SlotError, "exactly one"):
            saveslots.rewrite_str_property(b"nothing here", "saveSlot", "x")
        with self.assertRaisesRegex(saveslots.SlotError, "exactly one"):
            saveslots.rewrite_str_property(descriptor("a") + descriptor("b"), "saveSlot", "x")


class InstallTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.saves = root / "SaveGames"
        self.saves.mkdir()
        for name in ("saveGame_0.sav", "saveGame_7_descr.sav", "autosave.sav", "menu.sav"):
            (self.saves / name).write_bytes(b"user")
        source = root / "store"
        source.mkdir()
        (source / "slot.sav").write_bytes(b"world")
        (source / "slot_descr.sav").write_bytes(descriptor("saveGame_28"))
        (source / "slot.png").write_bytes(b"png")
        self.sources = {".sav": source / "slot.sav", "_descr.sav": source / "slot_descr.sav", ".png": source / "slot.png"}
        self.ledger = root / "runs" / ".installed-slots.json"

    def test_next_free_slot_is_one_above_the_highest(self):
        self.assertEqual(saveslots.next_free_slot(self.saves), "saveGame_8")

    def test_install_writes_new_files_and_the_ledger(self):
        installed = saveslots.install(self.saves, self.sources, "manor", self.ledger)
        self.assertEqual(installed.slot, "saveGame_8")
        self.assertEqual((self.saves / "saveGame_8.sav").read_bytes(), b"world")
        descr = (self.saves / "saveGame_8_descr.sav").read_bytes()
        self.assertEqual(saveslots.read_str_property(descr, "saveSlot"), "saveGame_8")
        self.assertEqual(saveslots.read_str_property(descr, "saveName"), "harness manor")
        entry = saveslots.read_ledger(self.ledger)[0]
        self.assertEqual(sorted(entry["files"]), ["saveGame_8.png", "saveGame_8.sav", "saveGame_8_descr.sav"])

    def test_install_never_overwrites(self):
        # A file of the chosen name can appear between the choice and the copy (the game saves at that moment).
        (self.saves / "saveGame_7.png").write_bytes(b"the user's file")
        with mock.patch.object(saveslots, "next_free_slot", return_value="saveGame_7"):
            with self.assertRaisesRegex(saveslots.SlotError, "exist already"):
                saveslots.install(self.saves, self.sources, "manor", self.ledger)
        self.assertEqual((self.saves / "saveGame_7.png").read_bytes(), b"the user's file")

    def test_a_new_user_slot_moves_the_free_name_up(self):
        (self.saves / "saveGame_8.png").write_bytes(b"the user's file")
        self.assertEqual(saveslots.install(self.saves, self.sources, "manor", self.ledger).slot, "saveGame_9")

    def test_uninstall_deletes_only_unchanged_ledger_files(self):
        installed = saveslots.install(self.saves, self.sources, "manor", self.ledger)
        (self.saves / "saveGame_8.png").write_bytes(b"changed")
        result = saveslots.uninstall_slot(installed.slot, self.ledger)
        self.assertEqual(sorted(result["removed"]), ["saveGame_8.sav", "saveGame_8_descr.sav"])
        self.assertEqual(result["kept"], ["saveGame_8.png (changed, not deleted)"])
        self.assertTrue((self.saves / "saveGame_8.png").exists())
        self.assertTrue((self.saves / "saveGame_0.sav").exists())
        self.assertEqual(saveslots.read_ledger(self.ledger), [])

    def test_uninstall_all_touches_only_its_own_save_folder(self):
        saveslots.install(self.saves, self.sources, "manor", self.ledger)
        other = self.saves.parent / "OtherSaves"
        other.mkdir()
        saveslots.install(other, self.sources, "elsewhere", self.ledger)
        results = saveslots.uninstall_all(self.saves, self.ledger)
        self.assertEqual([r["slot"] for r in results], ["saveGame_8"])
        self.assertEqual([e["label"] for e in saveslots.read_ledger(self.ledger)], ["elsewhere"])
        self.assertTrue((other / "saveGame_0.sav").exists())

    def _entry(self, label, **kw):
        installed = saveslots.install(self.saves, self.sources, label, self.ledger, **kw)
        entries = saveslots.read_ledger(self.ledger)
        return installed, entries

    def _live_owner(self, alive=True):
        return mock.patch.object(saveslots, "has_live_owner", return_value=alive)

    def test_install_records_the_game_slot_and_root(self):
        self._entry("a", game_slot=2, game_root=Path("C:/g2"))
        entry = saveslots.read_ledger(self.ledger)[0]
        self.assertEqual((entry["game_slot"], entry["game_root"]), (2, str(Path("C:/g2"))))

    def test_a_kept_open_run_on_another_slot_stays(self):
        installed, _ = self._entry("a", game_slot=0, game_root=Path("C:/g0"))
        with self._live_owner(False), mock.patch("runlib.game.find_game_processes", return_value=[object()]) as find:
            self.assertEqual(saveslots.uninstall_all(self.saves, self.ledger, game_slot=1), [])
        find.assert_called_once_with(Path("C:/g0"))
        self.assertTrue((self.saves / f"{installed.slot}.sav").exists())
        self.assertEqual(len(saveslots.read_ledger(self.ledger)), 1)

    def test_a_leftover_of_the_same_game_slot_is_removed(self):
        installed, _ = self._entry("a", game_slot=1, game_root=Path("C:/g1"))
        with self._live_owner(False), mock.patch("runlib.game.find_game_processes", return_value=[object()]):
            results = saveslots.uninstall_all(self.saves, self.ledger, game_slot=1)
        self.assertEqual([r["slot"] for r in results], [installed.slot])
        self.assertFalse((self.saves / f"{installed.slot}.sav").exists())

    def test_an_entry_whose_game_is_gone_is_removed(self):
        installed, _ = self._entry("a", game_slot=0, game_root=Path("C:/g0"))
        with self._live_owner(False), mock.patch("runlib.game.find_game_processes", return_value=[]):
            results = saveslots.uninstall_all(self.saves, self.ledger, game_slot=1)
        self.assertEqual([r["slot"] for r in results], [installed.slot])
        self.assertEqual(saveslots.read_ledger(self.ledger), [])

    def test_an_entry_without_a_game_slot_is_removed(self):
        installed, _ = self._entry("a")
        self.assertNotIn("game_slot", saveslots.read_ledger(self.ledger)[0])
        with self._live_owner(False):
            results = saveslots.uninstall_all(self.saves, self.ledger, game_slot=1)
        self.assertEqual([r["slot"] for r in results], [installed.slot])

    def test_an_entry_without_a_game_slot_stays_while_its_owner_lives(self):
        self._entry("a")
        with self._live_owner(True):
            self.assertEqual(saveslots.uninstall_all(self.saves, self.ledger, game_slot=1), [])

    def test_a_removed_run_leaves_the_ledger_even_if_its_files_are_gone(self):
        installed, _ = self._entry("a", game_slot=0, game_root=Path("C:/g0"))
        (self.saves / f"{installed.slot}.sav").unlink()
        with self._live_owner(False), mock.patch("runlib.game.find_game_processes", return_value=[]):
            results = saveslots.uninstall_all(self.saves, self.ledger, game_slot=1)
        self.assertIn(f"{installed.slot}.sav (missing)", results[0]["kept"])
        self.assertEqual(saveslots.read_ledger(self.ledger), [])

    def test_a_save_without_descriptor_is_refused(self):
        with self.assertRaisesRegex(saveslots.SlotError, "_descr.sav"):
            saveslots.install(self.saves, {".sav": self.sources[".sav"]}, "x", self.ledger)


if __name__ == "__main__":
    unittest.main()
