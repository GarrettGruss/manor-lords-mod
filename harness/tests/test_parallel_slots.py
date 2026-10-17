"""Parallel game slots (spec 11, step 3): slot list, slot locks, shared locks, ledger owners, process search by path."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import harness_tools_path  # noqa: F401
import runlib_path  # noqa: F401
import saveslot_support
from harness_tools import tools
from runlib import gameslots, phases, saveslots
from runlib.game import GameInstall, find_game_processes
from runlib.runfolder import LockTimeoutError, RunLock, RunLockedError, WaitLock, bump_iterations, run_lock_name


class TempCase(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)


def make_game(root: Path) -> Path:
    exe = GameInstall(root=root).exe
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"exe")
    return root


def write_slots_state(slots_dir: Path, entries: list[dict]) -> None:
    (slots_dir / ".install").mkdir(parents=True, exist_ok=True)
    # PowerShell writes UTF-8 without a BOM, but a BOM must not break the reader either.
    (slots_dir / ".install" / "slots.json").write_text("﻿" + json.dumps({"slots": entries}), encoding="utf-8")


class GameSlotsTest(TempCase):
    def test_slot_zero_only_without_state(self):
        slots = gameslots.installed_slots(self.temp / "slots", self.temp / "game")
        self.assertEqual([slot.number for slot in slots], [0])

    def test_installed_slots_with_an_existing_exe_are_listed_in_order(self):
        slots_dir = self.temp / "slots"
        two = make_game(slots_dir / "2" / "Manor Lords")
        one = make_game(slots_dir / "1" / "Manor Lords")
        write_slots_state(slots_dir, [{"slot": 2, "root": str(two)}, {"slot": 1, "root": str(one)},
                                      {"slot": 3, "root": str(slots_dir / "3" / "missing")}])
        slots = gameslots.installed_slots(slots_dir, self.temp / "game")
        self.assertEqual([slot.number for slot in slots], [0, 1, 2])
        self.assertEqual(gameslots.get_slot(2, slots_dir, self.temp / "game").root, two)
        self.assertEqual(gameslots.get_slot(2, slots_dir).tile, (0, 720))

    def test_unknown_slot_is_a_clear_error(self):
        with self.assertRaisesRegex(gameslots.SlotError, "slot 3 is not installed"):
            gameslots.get_slot(3, self.temp / "slots", self.temp / "game")

    def test_broken_state_file_is_a_clear_error(self):
        (self.temp / "slots" / ".install").mkdir(parents=True)
        (self.temp / "slots" / ".install" / "slots.json").write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(gameslots.SlotError, "broken"):
            gameslots.installed_slots(self.temp / "slots")


class SlotLockTest(TempCase):
    def test_each_slot_has_its_own_lock(self):
        self.assertEqual(run_lock_name(0), ".lock")
        self.assertEqual(run_lock_name(2), ".lock-2")
        with RunLock(self.temp, 0), RunLock(self.temp, 1):
            self.assertTrue((self.temp / ".lock").exists())
            self.assertTrue((self.temp / ".lock-1").exists())

    def test_acquire_then_with_does_not_take_the_lock_twice(self):
        lock = RunLock(self.temp, 1)
        lock.acquire()
        with lock:
            pass
        self.assertFalse((self.temp / ".lock-1").exists())


def hold_lock_in_child(path: Path, seconds: float) -> subprocess.Popen:
    """Another process that writes its pid into the lock file and keeps running."""
    code = (f"import os, time, pathlib; pathlib.Path({str(path)!r}).write_text(str(os.getpid())); time.sleep({seconds})")
    child = subprocess.Popen([sys.executable, "-c", code])
    deadline = time.monotonic() + 10
    while not path.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    return child


class WaitLockTest(TempCase):
    def test_waits_until_the_holder_ends(self):
        path = self.temp / ".saves.lock"
        child = hold_lock_in_child(path, 1.0)
        self.addCleanup(child.kill)
        started = time.monotonic()
        child_done = False
        with WaitLock(path, timeout_s=20):
            child_done = child.poll() is not None
        self.assertTrue(child_done, "the lock was taken while the holder was alive")
        self.assertGreater(time.monotonic() - started, 0.3)

    def test_times_out_with_a_clear_error(self):
        path = self.temp / ".saves.lock"
        child = hold_lock_in_child(path, 30)
        self.addCleanup(child.kill)
        with self.assertRaisesRegex(LockTimeoutError, "was not free"):
            with WaitLock(path, timeout_s=0.3):
                pass

    def test_iteration_counter_still_counts(self):
        self.assertEqual(bump_iterations(self.temp, 5), 1)
        self.assertEqual(bump_iterations(self.temp, 5), 2)
        self.assertFalse((self.temp / ".iterations.lock").exists())


class LedgerOwnerTest(TempCase):
    def setUp(self):
        super().setUp()
        self.saves = self.temp / "SaveGames"
        self.saves.mkdir()
        self.ledger = self.temp / "ledger.json"

    def add_entry(self, slot: str, owner_pid: int | None, owner_started: float | None) -> Path:
        path = self.saves / f"{slot}.sav"
        path.write_bytes(slot.encode())
        entry = {"slot": slot, "label": "t", "save_dir": str(self.saves), "installed": 0,
                 "files": {path.name: saveslots.sha256_of_file(path)}}
        if owner_pid is not None:
            entry.update(owner_pid=owner_pid, owner_started=owner_started)
        entries = saveslots.read_ledger(self.ledger) + [entry]
        self.ledger.write_text(json.dumps(entries), encoding="utf-8")
        return path

    def test_entries_of_a_live_run_stay_and_left_overs_go(self):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        self.addCleanup(child.kill)
        import psutil
        live = self.add_entry("saveGame_5", child.pid, psutil.Process(child.pid).create_time())
        reused = self.add_entry("saveGame_6", child.pid, 1.0)  # same pid, other start time: a reused pid
        old = self.add_entry("saveGame_7", None, None)
        results = saveslots.uninstall_all(self.saves, self.ledger)
        self.assertEqual(sorted(result["slot"] for result in results), ["saveGame_6", "saveGame_7"])
        self.assertTrue(live.exists())
        self.assertFalse(reused.exists())
        self.assertFalse(old.exists())
        self.assertEqual([entry["slot"] for entry in saveslots.read_ledger(self.ledger)], ["saveGame_5"])

    def test_new_entries_record_this_process_as_owner(self):
        (self.temp / "src.sav").write_bytes(b"s")
        (self.temp / "src_descr.sav").write_bytes(saveslot_support.descriptor("saveGame_0"))
        sources = {".sav": self.temp / "src.sav", "_descr.sav": self.temp / "src_descr.sav"}
        saveslots.install(self.saves, sources, "t", self.ledger)
        entry = saveslots.read_ledger(self.ledger)[0]
        self.assertEqual(entry["owner_pid"], os.getpid())
        self.assertFalse(saveslots.has_live_owner(entry), "the own entry is not another live run")

    def test_user_files_leave_out_every_harness_file(self):
        (self.saves / "saveGame_0.sav").write_bytes(b"user")
        self.add_entry("saveGame_9", 1, 1.0)
        install = GameInstall(root=self.temp, saved_dir=self.temp)
        with mock.patch.object(saveslots, "LEDGER_PATH", self.ledger):
            files = phases.user_files(install)
        self.assertEqual(set(files), {"saveGame_0.sav"})

    def test_the_settings_file_counts_only_without_the_install(self):
        (self.saves / "saveGame_0.sav").write_bytes(b"user")
        (self.saves / "rtsSettings.sav").write_bytes(b"settings")
        install = GameInstall(root=self.temp, saved_dir=self.temp)
        with mock.patch.object(saveslots, "LEDGER_PATH", self.ledger):
            with mock.patch.object(gameslots, "settings_installed", return_value=True):
                self.assertEqual(set(phases.user_files(install)), {"saveGame_0.sav"})
            with mock.patch.object(gameslots, "settings_installed", return_value=False):
                self.assertEqual(set(phases.user_files(install)), {"saveGame_0.sav", "rtsSettings.sav"})


class SlotInstallTest(TempCase):
    def test_a_slot_reads_the_steam_manifest_of_the_real_game(self):
        with mock.patch.object(gameslots, "_default_root", return_value=self.temp / "steamapps" / "common" / "Manor Lords"):
            install = gameslots.GameSlot(1, self.temp / "slots" / "1" / "Manor Lords").install()
        self.assertEqual(install.appmanifest, self.temp / "steamapps" / "appmanifest_1363080.acf")
        self.assertEqual(install.win64, self.temp / "slots" / "1" / "Manor Lords" / "ManorLords" / "Binaries" / "Win64")


class FakeProcess:
    def __init__(self, pid: int, exe: str):
        self.pid = pid
        self._exe = exe

    def exe(self) -> str:
        return self._exe


class ProcessByPathTest(TempCase):
    def test_only_games_of_the_slot_root_are_found(self):
        slot0 = self.temp / "game"
        slot1 = self.temp / "slots" / "1" / "Manor Lords"
        games = [FakeProcess(1, str(GameInstall(root=slot0).exe)), FakeProcess(2, str(GameInstall(root=slot1).exe))]
        with mock.patch("runlib.game.find_processes", return_value=games):
            self.assertEqual([p.pid for p in find_game_processes(slot1)], [2])
            self.assertEqual([p.pid for p in find_game_processes(slot0)], [1])
            self.assertEqual([p.pid for p in find_game_processes()], [1, 2])


class McpSlotClaimTest(TempCase):
    def setUp(self):
        super().setUp()
        self.slots = [gameslots.GameSlot(0, self.temp / "g0"), gameslots.GameSlot(1, self.temp / "g1")]
        patcher = mock.patch.object(tools.gameslots, "installed_slots", return_value=self.slots)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_auto_skips_a_locked_slot(self):
        (self.temp / ".lock").write_text(str(os.getpid()))
        number, claim = tools.claim_game_slot(self.temp, "r1", "auto")
        self.assertEqual(number, 1)
        self.assertEqual(claim.name, ".active-launcher-1.json")

    def test_auto_fails_when_all_are_busy(self):
        tools.claim_game_slot(self.temp, "r1", "auto")
        tools.claim_game_slot(self.temp, "r2", "auto")
        with self.assertRaisesRegex(tools.ToolError, "All 2 game slots are busy"):
            tools.claim_game_slot(self.temp, "r3", "auto")

    def test_explicit_busy_slot_names_the_slot(self):
        (self.temp / ".lock-1").write_text(str(os.getpid()))
        with mock.patch.object(tools.gameslots, "get_slot", return_value=self.slots[1]):
            with self.assertRaisesRegex(tools.ToolError, "active in slot 1"):
                tools.claim_game_slot(self.temp, "r1", "1")

    def test_bad_slot_text_is_refused(self):
        with self.assertRaisesRegex(tools.ToolError, "slot must be"):
            tools.claim_game_slot(self.temp, "r1", "x")


if __name__ == "__main__":
    unittest.main()
