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

    def test_a_save_without_descriptor_is_refused(self):
        with self.assertRaisesRegex(saveslots.SlotError, "_descr.sav"):
            saveslots.install(self.saves, {".sav": self.sources[".sav"]}, "x", self.ledger)


if __name__ == "__main__":
    unittest.main()
