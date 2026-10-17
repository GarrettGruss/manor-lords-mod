"""install.ps1 and uninstall.ps1 with temp folders and real PowerShell (spec 11, design 10)."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent
INSTALL = HARNESS / "install.ps1"
UNINSTALL = HARNESS / "uninstall.ps1"

USER_SETTINGS = (";METADATA=(Diff=true, UseCommands=true)\r\n[Settings]\r\nML.UIScale=1.3\r\nt.MaxFps=144\r\n"
                 "r.setres=2560x1440w\r\n\r\n[/Script/AutoSettingsInput.InputMappingManager]\r\nPlayerInputOverrides=(keys)\r\n\r\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@unittest.skipUnless(shutil.which("powershell"), "needs Windows PowerShell")
class InstallScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.game = self.temp / "game"
        self.user = self.temp / "user"
        self.slots = self.temp / "slots"
        self.make_game()
        config = self.user / "Config" / "Windows"
        config.mkdir(parents=True)
        (config / "UserSettings.ini").write_bytes(USER_SETTINGS.encode())
        (self.user / "SaveGames").mkdir()
        (self.user / "SaveGames" / "rtsSettings.sav").write_bytes(b"\x01\x02user")
        self.originals = {p: sha(p) for p in self.user_files()}

    def make_game(self):
        win64 = self.game / "ManorLords" / "Binaries" / "Win64"
        (win64 / "ue4ss" / "Mods").mkdir(parents=True)
        (win64 / "ue4ss" / "Mods" / "mods.txt").write_text("Keybinds : 1\n", encoding="utf-8")
        (win64 / "game.exe").write_bytes(b"exe")
        paks = self.game / "ManorLords" / "Content" / "Paks"
        (paks / "~mods").mkdir(parents=True)
        (paks / "~mods" / "user_P.pak").write_bytes(b"user pak")
        (paks / "pakchunk0-Windows.pak").write_bytes(b"pak data")
        for relative in ("Engine", "ManorLords/Plugins", "ManorLords/Content/Movies", "ManorLords/Content/Slate"):
            (self.game / relative).mkdir(parents=True, exist_ok=True)
            (self.game / relative / "keep.txt").write_text("game file", encoding="utf-8")

    def user_files(self) -> list[Path]:
        return [self.user / "Config" / "Windows" / "UserSettings.ini", self.user / "SaveGames" / "rtsSettings.sav"]

    def run_script(self, script: Path, *flags: str) -> subprocess.CompletedProcess:
        command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-GameDir", str(self.game),
                   "-SlotsDir", str(self.slots), *flags]
        if script == INSTALL:
            command += ["-UserDir", str(self.user), "-SkipDeploy"]
        done = subprocess.run(command, capture_output=True, text=True, timeout=180)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done

    def settings_text(self) -> str:
        return (self.user / "Config" / "Windows" / "UserSettings.ini").read_bytes().decode("utf-8")

    def test_install_writes_harness_values_and_keeps_other_keys(self):
        self.run_script(INSTALL, "-SettingsOnly")
        text = self.settings_text()
        self.assertIn("t.MaxFps=30\r\n", text)
        self.assertIn("r.setres=1280x720w\r\n", text)
        self.assertNotIn("t.MaxFps=144", text)
        self.assertIn("ML.UIScale=1.3\r\n", text)
        self.assertIn("PlayerInputOverrides=(keys)", text)
        game_user = (self.user / "Config" / "Windows" / "GameUserSettings.ini").read_text(encoding="utf-8")
        self.assertIn("FullscreenMode=2", game_user)

    def test_uninstall_restores_files_bit_for_bit_after_the_game_changed_them(self):
        self.run_script(INSTALL, "-SettingsOnly")
        (self.user / "SaveGames" / "rtsSettings.sav").write_bytes(b"changed by the game")
        self.run_script(UNINSTALL)
        self.assertEqual({p: sha(p) for p in self.user_files()}, self.originals)
        self.assertFalse((self.user / "Config" / "Windows" / "GameUserSettings.ini").exists(), "it did not exist before")
        self.assertFalse((self.slots / ".install" / "settings.json").exists())

    def test_second_install_keeps_the_first_backup(self):
        self.run_script(INSTALL, "-SettingsOnly")
        self.run_script(INSTALL, "-SettingsOnly")
        self.run_script(UNINSTALL)
        self.assertEqual({p: sha(p) for p in self.user_files()}, self.originals)

    def test_slots_have_own_win64_and_mods_and_remove_never_touches_the_game(self):
        self.run_script(INSTALL, "-Slots", "2")
        slot = self.slots / "1" / "Manor Lords"
        self.assertEqual((slot / "ManorLords" / "Binaries" / "Win64" / "game.exe").read_bytes(), b"exe")
        self.assertEqual((slot / "ManorLords" / "Content" / "Paks" / "pakchunk0-Windows.pak").read_bytes(), b"pak data")
        self.assertFalse((slot / "ManorLords" / "Content" / "Paks" / "~mods").exists(), "~mods is per slot")
        self.assertTrue((slot / "Engine" / "keep.txt").exists(), "junction to the game")
        self.run_script(UNINSTALL, "-Remove")
        self.assertFalse((self.slots / "1").exists())
        self.assertFalse((self.slots / "2").exists())
        for relative in ("Engine", "ManorLords/Plugins", "ManorLords/Content/Movies", "ManorLords/Content/Slate"):
            self.assertTrue((self.game / relative / "keep.txt").exists(), relative)
        self.assertEqual((self.game / "ManorLords" / "Content" / "Paks" / "pakchunk0-Windows.pak").read_bytes(), b"pak data")
        self.assertTrue((self.game / "ManorLords" / "Content" / "Paks" / "~mods" / "user_P.pak").exists())


if __name__ == "__main__":
    unittest.main()
