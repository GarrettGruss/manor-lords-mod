"""Tests for save fixtures, the fixture store and the private appdata folder (spec 06, parts C and D). Temp folders only."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401
from runlib import fixtures, phases, saveslots
from runlib.game import GameInstall, build_game_environment
from runlib.runfolder import create_run_folder
from runlib.runner import PhaseContext, PhaseFailed
from runlib.summary import condense_environment
from saveslot_support import descriptor

TOOL = Path(__file__).resolve().parent.parent / "tools" / "fixtures.py"


class UserSavesCase(unittest.TestCase):
    """A fake user folder: Saved/SaveGames with slots, and Saved/Config."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.saved = self.root / "user" / "ManorLords" / "Saved"
        self.saves = self.saved / "SaveGames"
        self.saves.mkdir(parents=True)
        (self.saved / "Config" / "Windows").mkdir(parents=True)
        (self.saved / "Config" / "Windows" / "GameUserSettings.ini").write_text("res=1")
        for name, data in {"saveGame_3.sav": b"world", "saveGame_3_descr.sav": descriptor("saveGame_3"), "saveGame_3.png": b"png",
                           "saveGame_3_coat_0.png": b"coat", "saveGame_1.sav": b"other", "menu.sav": b"menu"}.items():
            (self.saves / name).write_bytes(data)
        self.manifest_path = self.root / "fixtures.json"
        fixtures.record_fixture(self.saves, self.manifest_path, "base", "saveGame_3", "test", ["a"])
        self.manifest = fixtures.load_manifest(self.manifest_path)
        self.appdata = self.root / "run" / "appdata"
        self.store = self.root / "store"
        self.ledger = self.root / "runs" / ".installed-slots.json"
        patch = mock.patch.object(saveslots, "LEDGER_PATH", self.ledger)  # never the real ledger
        patch.start()
        self.addCleanup(patch.stop)

    def import_base(self, name="stored"):
        sources = fixtures.files_of_save(self.saves / "saveGame_3.sav")
        fixtures.import_fixture(sources, self.manifest_path, name, "stored test", ["s"], "user slot saveGame_3", self.store)
        self.manifest = fixtures.load_manifest(self.manifest_path)


class NamesAndManifestTest(UserSavesCase):
    def test_bad_names(self):
        for name in ("", "a_b", "../x", "a b", "a/b"):
            with self.assertRaises(fixtures.FixtureError, msg=name):
                fixtures.check_name(name)
        self.assertEqual(fixtures.check_name("two-words"), "two-words")

    def test_record_needs_the_world_and_descriptor(self):
        (self.saves / "saveGame_3_descr.sav").unlink()
        with self.assertRaisesRegex(fixtures.FixtureError, "has no saveGame_3_descr.sav"):
            fixtures.record_fixture(self.saves, self.manifest_path, "x", "saveGame_3", "", [])

    def test_manifest_has_hashes_and_no_save_data(self):
        entry = json.loads(self.manifest_path.read_text())["fixtures"]["base"]
        self.assertEqual(set(entry["sha256"]), {".sav", "_descr.sav", ".png", "_coat_0.png"})
        self.assertEqual(len(entry["sha256"][".sav"]), 64)

    def test_list(self):
        self.assertEqual(fixtures.list_fixtures(self.manifest)[0]["name"], "base")

    def test_import_copies_the_slot_into_the_store_under_the_stem_slot(self):
        self.import_base()
        entry = self.manifest["fixtures"]["stored"]
        self.assertTrue(fixtures.is_stored(entry))
        self.assertEqual((self.store / "stored" / "slot.sav").read_bytes(), b"world")
        self.assertEqual(set(entry["sha256"]), {".sav", "_descr.sav", ".png", "_coat_0.png"})
        files = fixtures.fixture_files(entry, "stored", self.saves, self.store)
        self.assertEqual(files[".sav"], self.store / "stored" / "slot.sav")

    def test_a_changed_stored_file_is_refused(self):
        self.import_base()
        (self.store / "stored" / "slot.sav").write_bytes(b"other")
        with self.assertRaisesRegex(fixtures.FixtureError, "differ from the manifest"):
            fixtures.fixture_files(self.manifest["fixtures"]["stored"], "stored", self.saves, self.store)

    def test_files_of_save_needs_the_main_file_and_the_descriptor(self):
        self.assertEqual(set(fixtures.files_of_save(self.saves / "saveGame_3.sav")), {".sav", "_descr.sav", ".png", "_coat_0.png"})
        with self.assertRaisesRegex(fixtures.FixtureError, "main save file"):
            fixtures.files_of_save(self.saves / "saveGame_3_descr.sav")
        with self.assertRaisesRegex(fixtures.FixtureError, "has no saveGame_1_descr.sav"):
            fixtures.files_of_save(self.saves / "saveGame_1.sav")

    def test_repo_manifest_is_valid(self):
        manifest = fixtures.load_manifest()
        self.assertIn(fixtures.DEFAULT_FIXTURE, manifest["fixtures"])


class PrepareAppdataTest(UserSavesCase):
    def test_config_is_copied_and_the_fixture_is_checked_but_not_copied(self):
        # The game never reads saves from the private folder (fixture-load-bug.md), so no slot file goes there.
        result = fixtures.prepare_appdata(self.saved, self.appdata, self.manifest, "base")
        target = fixtures.saved_dir_of(self.appdata)
        self.assertEqual(list((target / "SaveGames").iterdir()), [])
        self.assertEqual((target / "Config" / "Windows" / "GameUserSettings.ini").read_text(), "res=1")
        self.assertEqual((result.source_slot, result.stored, len(result.sources), result.user_files), ("saveGame_3", False, 4, 6))
        self.assertEqual(set(result.user_snapshot), {p.name for p in self.saves.iterdir()})

    def test_fresh_start_needs_no_fixture(self):
        result = fixtures.prepare_appdata(self.saved, self.appdata, self.manifest, None)
        self.assertEqual((result.fixture, result.stored, result.sources, result.user_files), (None, False, {}, 6))
        self.assertEqual(set(result.user_snapshot), {p.name for p in self.saves.iterdir()})
        self.assertTrue((fixtures.saved_dir_of(self.appdata) / "Config" / "Windows" / "GameUserSettings.ini").is_file())

    def test_user_files_are_not_changed(self):
        before = fixtures.snapshot_user_files(self.saves)
        fixtures.prepare_appdata(self.saved, self.appdata, self.manifest, "base")
        self.assertEqual(fixtures.snapshot_user_files(self.saves), before)

    def test_changed_source_is_refused_and_nothing_is_copied(self):
        (self.saves / "saveGame_3.sav").write_bytes(b"the user played on")
        with self.assertRaisesRegex(fixtures.FixtureError, "differ from the manifest"):
            fixtures.prepare_appdata(self.saved, self.appdata, self.manifest, "base")

    def test_unknown_fixture(self):
        with self.assertRaisesRegex(fixtures.FixtureError, "unknown fixture"):
            fixtures.prepare_appdata(self.saved, self.appdata, self.manifest, "nope")

    def test_appdata_inside_the_user_folder_is_refused(self):
        with self.assertRaisesRegex(fixtures.FixtureError, "must not be inside"):
            fixtures.prepare_appdata(self.saved, self.saved / "appdata", self.manifest, "base")

    def test_user_file_change_during_the_copy_aborts(self):
        real_copy = fixtures.shutil.copytree

        def copy_and_disturb(src, dst, *args, **kwargs):
            real_copy(src, dst, *args, **kwargs)
            (self.saves / "menu.sav").write_bytes(b"changed by the game")

        with mock.patch.object(fixtures.shutil, "copytree", side_effect=copy_and_disturb):
            with self.assertRaisesRegex(fixtures.SaveFolderChanged, "changed: menu.sav"):
                fixtures.prepare_appdata(self.saved, self.appdata, self.manifest, "base")


class GuardTest(UserSavesCase):
    def test_changed_new_and_deleted_files_abort(self):
        with self.assertRaisesRegex(fixtures.SaveFolderChanged, "changed: menu.sav"):
            with fixtures.guarded(self.saves):
                (self.saves / "menu.sav").write_bytes(b"x")
        with self.assertRaisesRegex(fixtures.SaveFolderChanged, "new: saveGame_9.sav"):
            with fixtures.guarded(self.saves):
                (self.saves / "saveGame_9.sav").write_bytes(b"x")
        with self.assertRaisesRegex(fixtures.SaveFolderChanged, "deleted: saveGame_1.sav"):
            with fixtures.guarded(self.saves):
                (self.saves / "saveGame_1.sav").unlink()


class RemoveAppdataTest(UserSavesCase):
    def test_removes_the_private_folder_only(self):
        fixtures.prepare_appdata(self.saved, self.appdata, self.manifest, "base")
        before = fixtures.snapshot_user_files(self.saves)
        self.assertGreaterEqual(fixtures.remove_appdata(self.appdata), 1)
        self.assertFalse(self.appdata.exists())
        self.assertEqual(fixtures.snapshot_user_files(self.saves), before)

    def test_missing_folder_is_fine(self):
        self.assertEqual(fixtures.remove_appdata(self.appdata), 0)

    def test_refuses_other_folders(self):
        with self.assertRaisesRegex(fixtures.FixtureError, "not named"):
            fixtures.remove_appdata(self.saved)
        other = self.root / "appdata"
        other.mkdir()
        (other / "keep.txt").write_text("x")
        with self.assertRaisesRegex(fixtures.FixtureError, "no ManorLords/Saved"):
            fixtures.remove_appdata(other)
        self.assertTrue((other / "keep.txt").exists())


class EnvironmentTest(unittest.TestCase):
    def test_game_gets_its_own_localappdata_only_when_asked(self):
        env = build_game_environment(Path("run"), "saveGame_0", base_env={"LOCALAPPDATA": "C:/user"})
        self.assertEqual(env["LOCALAPPDATA"], "C:/user")
        env = build_game_environment(Path("run"), "saveGame_0", base_env={"LOCALAPPDATA": "C:/user"},
                                     appdata_dir=Path("run/appdata"))
        self.assertEqual(Path(env["LOCALAPPDATA"]), Path("run/appdata").resolve())


class ToolCliTest(UserSavesCase):
    def run_tool(self, *args):
        base = [sys.executable, str(TOOL), "--user-saved-dir", str(self.saved), "--manifest", str(self.manifest_path),
                "--store", str(self.store)]
        return subprocess.run(base + list(args), capture_output=True, text=True, timeout=60)

    def test_list_and_import_from_a_slot_and_from_a_file(self):
        self.assertEqual(json.loads(self.run_tool("list").stdout)["fixtures"][0]["name"], "base")
        from_slot = self.run_tool("import", "one", "--source-slot", "saveGame_3", "--tags", "a,b")
        self.assertEqual(from_slot.returncode, 0, from_slot.stderr)
        self.assertEqual(json.loads(from_slot.stdout)["tags"], ["a", "b"])
        from_file = self.run_tool("import", "two", "--from", str(self.saves / "saveGame_3.sav"))
        self.assertEqual(from_file.returncode, 0, from_file.stderr)
        self.assertTrue((self.store / "two" / "slot_descr.sav").is_file())
        listed = {row["name"]: row["stored"] for row in json.loads(self.run_tool("list").stdout)["fixtures"]}
        self.assertEqual(listed, {"base": False, "one": True, "two": True})

    def test_errors_have_exit_codes(self):
        self.assertEqual(self.run_tool("import", "x", "--source-slot", "saveGame_1").returncode, 1)
        self.assertEqual(self.run_tool("remove", "--appdata", str(self.saved)).returncode, 1)


class RunPhasesTest(UserSavesCase):
    """Preflight builds the private appdata. Teardown compares the user files and deletes it."""

    def setUp(self):
        super().setUp()
        self.install = GameInstall(root=self.root / "game", saved_dir=self.saved)
        self.ctx = PhaseContext(run=create_run_folder(self.root / "runs", "r1"), config={})
        patch = mock.patch.object(fixtures, "load_manifest", return_value=self.manifest)
        patch.start()
        self.addCleanup(patch.stop)

    def test_prepare_fills_state_and_config(self):
        phases._prepare_appdata(self.install, self.ctx, "base")
        self.assertEqual(self.ctx.state["appdata_dir"], self.ctx.run.path / "appdata")
        self.assertEqual(self.ctx.config["environment"]["fixture"]["source_slot"], "saveGame_3")
        private = phases._private_install(self.install, self.ctx)
        self.assertEqual(private.crashes_dir, self.ctx.run.path / "appdata" / "ManorLords" / "Saved" / "Crashes")

    def test_an_old_fixture_loads_its_source_slot_without_an_install(self):
        appdata = phases._prepare_appdata(self.install, self.ctx, "base")
        self.assertEqual(phases._choose_slot(self.install, self.ctx, appdata, None), "saveGame_3")
        self.assertNotIn("installed_slot", self.ctx.state)

    def test_a_stored_fixture_is_installed_loaded_and_removed_in_teardown(self):
        self.import_base()
        fixtures.load_manifest.return_value = self.manifest
        with mock.patch.object(fixtures, "STORE_DIR", self.store):
            appdata = phases._prepare_appdata(self.install, self.ctx, "stored")
        slot = phases._choose_slot(self.install, self.ctx, appdata, None)
        self.assertEqual(slot, "saveGame_4")
        self.assertEqual(saveslots.read_str_property((self.saves / "saveGame_4_descr.sav").read_bytes(), "saveSlot"), "saveGame_4")
        detail = phases._finish_appdata(self.install, self.ctx)
        self.assertIn("user saves unchanged", detail)
        self.assertFalse((self.saves / "saveGame_4.sav").exists())
        self.assertTrue(any("installed slot saveGame_4 removed (4 files)" in note for note in self.ctx.state["notes"]))
        self.assertEqual(saveslots.read_ledger(), [])

    def test_a_save_file_is_installed_under_its_own_label(self):
        appdata = phases._prepare_appdata(self.install, self.ctx, "base")
        slot = phases._choose_slot(self.install, self.ctx, appdata, self.saves / "saveGame_3.sav")
        self.assertEqual(self.ctx.config["environment"]["installed_slot"]["label"], "saveGame_3")
        self.assertEqual(saveslots.read_str_property((self.saves / f"{slot}_descr.sav").read_bytes(), "saveName"),
                         "harness saveGame_3")
        phases._finish_appdata(self.install, self.ctx)
        self.assertFalse((self.saves / f"{slot}.sav").exists())

    def test_preflight_removes_a_slot_left_by_an_earlier_run(self):
        sources = fixtures.files_of_save(self.saves / "saveGame_3.sav")
        left = saveslots.install(self.saves, sources, "left")
        phases._remove_stale_slots(self.install, self.ctx)
        self.assertFalse((self.saves / f"{left.slot}.sav").exists())
        self.assertTrue(any(f"removed the slot {left.slot}" in note for note in self.ctx.state["notes"]))

    def test_bad_source_fails_the_phase(self):
        (self.saves / "saveGame_3.sav").write_bytes(b"changed")
        with self.assertRaisesRegex(PhaseFailed, "fixture base"):
            phases._prepare_appdata(self.install, self.ctx, "base")

    def test_teardown_part_removes_appdata_and_notes_unchanged_saves(self):
        phases._prepare_appdata(self.install, self.ctx, "base")
        detail = phases._finish_appdata(self.install, self.ctx)
        self.assertIn("appdata removed", detail)
        self.assertFalse((self.ctx.run.path / "appdata").exists())
        self.assertTrue(any("did not change" in note for note in self.ctx.state["notes"]))

    def test_teardown_fails_loudly_when_a_user_file_changed_but_still_removes_appdata(self):
        phases._prepare_appdata(self.install, self.ctx, "base")
        (self.saves / "autosave.sav").write_bytes(b"new autosave")
        with self.assertRaisesRegex(PhaseFailed, "new: autosave.sav"):
            phases._finish_appdata(self.install, self.ctx)
        self.assertFalse((self.ctx.run.path / "appdata").exists())

    def test_no_appdata_no_work(self):
        self.assertIsNone(phases._finish_appdata(self.install, self.ctx))

    def test_collect_reads_crashes_from_the_private_appdata(self):
        phases._prepare_appdata(self.install, self.ctx, "base")
        private = phases._private_install(self.install, self.ctx)
        (private.crashes_dir / "UECC-1").mkdir(parents=True)
        (private.crashes_dir / "UECC-1" / "report.txt").write_text("crash")
        (self.install.crashes_dir / "UECC-user").mkdir(parents=True)  # a crash report of another process must be ignored
        (self.install.crashes_dir / "UECC-user" / phases.CRASH_CONTEXT_FILE).write_text("<ProcessId>1111</ProcessId>")
        self.ctx.state.update(run_started_epoch=0, game_pid=4242)
        phases._collect(self.install)(self.ctx)
        self.assertEqual(self.ctx.state["artifacts"]["crash"], ["crash/UECC-1"])

    def test_summary_environment_is_short(self):
        phases._prepare_appdata(self.install, self.ctx, "base")
        short = condense_environment(self.ctx.config["environment"])
        self.assertEqual(short["fixture"], "base")
        self.assertEqual(len(short["fixture_sav_sha256"]), 12)
        self.assertEqual(len(short["user_saves_sha256"]), 12)

    def test_build_phases_default_and_bad_fixture(self):
        with mock.patch.object(phases, "_preflight") as preflight:
            phases.build_real_phases("noop")
            self.assertEqual(preflight.call_args.args[2], "base")
            phases.build_real_phases("noop", fixture="other")
            self.assertEqual(preflight.call_args.args[2], "other")
        with self.assertRaises(fixtures.FixtureError):
            phases.build_real_phases("noop", fixture="bad_name")


class GameLaunchArgsTest(unittest.TestCase):
    def test_empty_gives_no_args(self):
        from runlib.game import game_launch_args
        self.assertEqual(game_launch_args({}), [])

    def test_allowed_args_pass(self):
        from runlib.game import game_launch_args
        self.assertEqual(game_launch_args({"HARNESS_GAME_ARGS": "-faketouches -windowed"}), ["-faketouches", "-windowed"])

    def test_unknown_arg_is_an_error(self):
        from runlib.game import game_launch_args
        with self.assertRaises(ValueError):
            game_launch_args({"HARNESS_GAME_ARGS": "-exec=evil"})


if __name__ == "__main__":
    unittest.main()
