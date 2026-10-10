"""Tests for harness/tools/pakmod.py with a fake packer and temp folders. No real pak tool, no real game folder."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

HARNESS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HARNESS_DIR / "tools"))
import pakmod  # noqa: E402

UNINSTALL = HARNESS_DIR / "uninstall.ps1"
ASSET = "ManorLords/Content/NotStronghold/Data/DT_Items.uasset"

FAKE_PACKER = textwrap.dedent('''
    import json, os, sys, time
    args = sys.argv[1:]
    record = os.environ["FAKE_PACKER_RECORD"]
    open(record, "w").write(json.dumps(args))
    mode = os.environ.get("FAKE_PACKER_MODE", "ok")
    if mode == "fail":
        print("boom")
        sys.exit(3)
    if mode == "sleep":
        time.sleep(30)
    if mode == "nofile":
        sys.exit(0)
    open(args[-1], "wb").write(b"FAKE PAK " + open(args[0].split("=", 1)[1]).read().encode())
''')


class PakTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.work = self.tmp / "work"
        self.work.mkdir()
        self.game = self.tmp / "game"
        (self.game / "ManorLords").mkdir(parents=True)
        self.record = self.tmp / "record.json"
        script = self.tmp / "fake_packer.py"
        script.write_text(FAKE_PACKER, encoding="utf-8")
        self.config_path = self.tmp / "pakmod.local.json"
        self.write_config(packer=sys.executable, packer_args=[str(script), "-Create={response}", "{output}"])
        env = mock.patch.dict(os.environ, {"FAKE_PACKER_RECORD": str(self.record), "FAKE_PACKER_MODE": "ok"})
        env.start()
        self.addCleanup(env.stop)

    def write_config(self, **overrides):
        config = {"packer": sys.executable, "packer_args": ["-Create={response}", "{output}"], "work_dir": str(self.work)}
        config.update(overrides)
        self.config_path.write_text(json.dumps(config), encoding="utf-8")

    def make_assets(self, name="demo", content=b"x"):
        path = self.work / name / ASSET
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def config(self):
        return pakmod.load_config(self.config_path)

    def build_and_install(self, name="demo"):
        self.make_assets(name)
        pakmod.build(self.config(), name)
        return pakmod.install(self.work, self.game, name)

    @property
    def mods(self):
        return pakmod.mods_dir_of(self.game)


class ConfigTests(PakTestCase):
    def test_valid_config_loads(self):
        self.assertEqual(self.config()["work_dir"], self.work)

    def test_missing_file_is_reported_with_an_example(self):
        self.assertIn("config file missing", pakmod.config_problems(self.tmp / "none.json")[0])

    def test_each_problem_is_reported(self):
        self.write_config(packer=str(self.tmp / "nope.exe"), packer_args=["-x"], work_dir=str(self.tmp / "nodir"))
        text = " ".join(pakmod.config_problems(self.config_path))
        self.assertIn("packer not found", text)
        self.assertIn("{response}", text)
        self.assertIn("work_dir is not a folder", text)

    def test_broken_json_is_reported(self):
        self.config_path.write_text("{", encoding="utf-8")
        with self.assertRaises(pakmod.PakModError):
            pakmod.load_config(self.config_path)

    def test_check_command_exit_codes(self):
        self.assertEqual(pakmod.main(["--config", str(self.config_path), "--game-dir", str(self.game), "check"]), 0)
        self.assertEqual(pakmod.main(["--config", str(self.tmp / "none.json"), "--game-dir", str(self.game), "check"]), 1)
        self.assertEqual(pakmod.main(["--config", str(self.config_path), "--game-dir", str(self.tmp / "nogame"), "check"]), 1)


class GuardTests(PakTestCase):
    def test_bad_names_are_refused(self):
        for name in ["", "..", "a/b", "a\\b", "x" * 41, "a b", "C:\\x", "../evil", "a.b"]:
            with self.subTest(name=name), self.assertRaises(pakmod.PakModError):
                pakmod.check_name(name)

    def test_good_names_pass(self):
        for name in ["a", "Demo_1-x", "x" * 40]:
            self.assertEqual(pakmod.check_name(name), name)

    def test_path_outside_work_dir_is_refused(self):
        with self.assertRaises(pakmod.PakModError):
            pakmod.require_inside(self.tmp / "other", self.work, "x")
        with self.assertRaises(pakmod.PakModError):
            pakmod.require_inside(self.work / ".." / "other", self.work, "x")

    def test_symlink_in_assets_is_refused(self):
        self.make_assets()
        link = self.work / "demo" / "link.uasset"
        try:
            link.symlink_to(self.record)
        except OSError:
            self.skipTest("symlinks need a privilege on this system")
        with self.assertRaises(pakmod.PakModError):
            pakmod.build(self.config(), "demo")

    def test_missing_or_empty_asset_folder_is_refused(self):
        with self.assertRaises(pakmod.PakModError):
            pakmod.build(self.config(), "demo")
        (self.work / "demo").mkdir()
        with self.assertRaises(pakmod.PakModError):
            pakmod.build(self.config(), "demo")


class BuildTests(PakTestCase):
    def test_response_file_lists_each_file_with_its_mount_path(self):
        asset = self.make_assets()
        pakmod.build(self.config(), "demo")
        text = (self.work / "out" / "demo.response.txt").read_text(encoding="utf-8")
        self.assertEqual(text, f'"{asset.resolve()}" "../../../{ASSET}"\n')

    def test_command_is_a_list_with_placeholders_replaced(self):
        self.make_assets()
        pakmod.build(self.config(), "demo")
        args = json.loads(self.record.read_text())
        self.assertEqual(args[0], f"-Create={self.work / 'out' / 'demo.response.txt'}")
        self.assertEqual(args[1], str(self.work / "out" / "demo_P.pak"))

    def test_build_writes_the_pak(self):
        self.make_assets()
        output = pakmod.build(self.config(), "demo")
        self.assertEqual(output, self.work / "out" / "demo_P.pak")
        self.assertTrue(output.read_bytes().startswith(b"FAKE PAK"))

    def test_packer_runs_without_a_shell(self):
        self.make_assets()
        with mock.patch.object(pakmod.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run:
            with self.assertRaises(pakmod.PakModError):  # the mock writes no pak
                pakmod.build(self.config(), "demo")
        self.assertIsInstance(run.call_args.args[0], list)
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertGreater(run.call_args.kwargs["timeout"], 0)

    def test_packer_failure_is_reported(self):
        self.make_assets()
        os.environ["FAKE_PACKER_MODE"] = "fail"
        with self.assertRaisesRegex(pakmod.PakModError, "exit code 3.*boom"):
            pakmod.build(self.config(), "demo")

    def test_packer_timeout_is_reported(self):
        self.make_assets()
        os.environ["FAKE_PACKER_MODE"] = "sleep"
        with self.assertRaisesRegex(pakmod.PakModError, "did not finish"):
            pakmod.build(self.config(), "demo", timeout_s=1)

    def test_packer_without_output_is_an_error(self):
        self.make_assets()
        os.environ["FAKE_PACKER_MODE"] = "nofile"
        with self.assertRaisesRegex(pakmod.PakModError, "wrote no pak"):
            pakmod.build(self.config(), "demo")

    def test_dry_run_changes_nothing(self):
        self.make_assets()
        pakmod.build(self.config(), "demo", dry_run=True)
        self.assertFalse((self.work / "out").exists())
        self.assertFalse(self.record.exists())


class InstallRemoveTests(PakTestCase):
    def test_install_copies_and_records_the_hash(self):
        target = self.build_and_install()
        self.assertEqual(target, self.mods / "demo_P.pak")
        manifest = json.loads((self.mods / pakmod.MANIFEST_NAME).read_text())
        self.assertEqual(manifest["files"], {"demo_P.pak": pakmod.sha256_of(target)})
        self.assertTrue(manifest["created_dir"])

    def test_install_dry_run_changes_nothing(self):
        self.make_assets()
        pakmod.build(self.config(), "demo")
        pakmod.install(self.work, self.game, "demo", dry_run=True)
        self.assertFalse(self.mods.exists())

    def test_install_before_build_is_refused(self):
        with self.assertRaisesRegex(pakmod.PakModError, "not built"):
            pakmod.install(self.work, self.game, "demo")

    def test_install_refuses_to_overwrite_a_foreign_pak(self):
        self.make_assets()
        pakmod.build(self.config(), "demo")
        self.mods.mkdir(parents=True)
        foreign = self.mods / "demo_P.pak"
        foreign.write_bytes(b"user file")
        with self.assertRaisesRegex(pakmod.PakModError, "not in the harness manifest"):
            pakmod.install(self.work, self.game, "demo")
        self.assertEqual(foreign.read_bytes(), b"user file")

    def test_install_can_replace_its_own_pak(self):
        self.build_and_install()
        self.make_assets(content=b"changed")
        pakmod.build(self.config(), "demo")
        target = pakmod.install(self.work, self.game, "demo")
        manifest = pakmod.read_manifest(self.mods)
        self.assertEqual(manifest["files"]["demo_P.pak"], pakmod.sha256_of(target))

    def test_remove_deletes_only_manifest_files_and_the_empty_folder(self):
        self.build_and_install()
        self.assertEqual(pakmod.remove(self.game, ["demo"]), 0)
        self.assertFalse(self.mods.exists())

    def test_remove_keeps_other_files_and_a_folder_the_user_made(self):
        self.mods.mkdir(parents=True)
        other = self.mods / "other_P.pak"
        other.write_bytes(b"user")
        self.build_and_install()
        pakmod.remove(self.game, None)
        self.assertEqual(other.read_bytes(), b"user")
        self.assertEqual(sorted(p.name for p in self.mods.iterdir()), ["other_P.pak"])

    def test_remove_all_with_two_paks(self):
        self.build_and_install("one")
        self.build_and_install("two")
        pakmod.remove(self.game, None)
        self.assertFalse(self.mods.exists())

    def test_remove_refuses_a_name_that_is_not_in_the_manifest(self):
        self.mods.mkdir(parents=True)
        other = self.mods / "other_P.pak"
        other.write_bytes(b"user")
        with self.assertRaisesRegex(pakmod.PakModError, "not in the harness manifest"):
            pakmod.remove(self.game, ["other"])
        self.assertTrue(other.exists())

    def test_remove_skips_a_changed_file(self):
        target = self.build_and_install()
        target.write_bytes(b"edited by hand")
        self.assertEqual(pakmod.remove(self.game, ["demo"]), 1)
        self.assertTrue(target.exists())
        self.assertIn("demo_P.pak", pakmod.read_manifest(self.mods)["files"])

    def test_remove_refuses_a_manifest_entry_with_a_path(self):
        self.mods.mkdir(parents=True)
        victim = self.tmp / "victim.pak"
        victim.write_bytes(b"keep")
        manifest = {"version": 1, "created_dir": False, "files": {"../../victim.pak": pakmod.sha256_of(victim)}}
        pakmod.write_manifest(self.mods, manifest)
        with self.assertRaises(pakmod.PakModError):
            pakmod.remove(self.game, None)
        self.assertTrue(victim.exists())

    def test_remove_dry_run_changes_nothing(self):
        target = self.build_and_install()
        pakmod.remove(self.game, None, dry_run=True)
        self.assertTrue(target.exists())
        self.assertIn("demo_P.pak", pakmod.read_manifest(self.mods)["files"])

    def test_remove_command_needs_name_or_all(self):
        self.assertEqual(pakmod.main(["--game-dir", str(self.game), "remove"]), 1)

    def test_list_reports_the_state(self):
        target = self.build_and_install()
        self.assertIn(" ok ", pakmod.list_paks(self.game)[0])
        target.write_bytes(b"other")
        self.assertIn("CHANGED", pakmod.list_paks(self.game)[0])

    def test_broken_manifest_stops_the_command(self):
        self.mods.mkdir(parents=True)
        (self.mods / pakmod.MANIFEST_NAME).write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(pakmod.PakModError, "manifest is broken"):
            pakmod.list_paks(self.game)


@unittest.skipUnless(shutil.which("powershell"), "needs Windows PowerShell")
class UninstallIntegrationTests(PakTestCase):
    def setUp(self):
        super().setUp()
        mods = self.game / "ManorLords" / "Binaries" / "Win64" / "ue4ss" / "Mods"
        mods.mkdir(parents=True)
        (mods / "mods.txt").write_text("Keybinds : 1\n", encoding="utf-8")

    def uninstall(self, *flags):
        command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(UNINSTALL), "-GameDir", str(self.game), *flags]
        return subprocess.run(command, capture_output=True, text=True, timeout=120)

    def test_remove_deletes_the_harness_pak_and_keeps_others(self):
        self.mods.mkdir(parents=True)
        other = self.mods / "other_P.pak"
        other.write_bytes(b"user")
        self.build_and_install()
        done = self.uninstall("-Remove")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertFalse((self.mods / "demo_P.pak").exists())
        self.assertFalse((self.mods / pakmod.MANIFEST_NAME).exists())
        self.assertEqual(other.read_bytes(), b"user")

    def test_remove_deletes_the_folder_that_the_harness_made(self):
        self.build_and_install()
        self.assertEqual(self.uninstall("-Remove").returncode, 0)
        self.assertFalse(self.mods.exists())

    def test_dry_run_and_default_mode_keep_the_pak(self):
        target = self.build_and_install()
        self.assertEqual(self.uninstall("-Remove", "-DryRun").returncode, 0)
        self.assertEqual(self.uninstall().returncode, 0)
        self.assertTrue(target.exists())
        self.assertTrue((self.mods / pakmod.MANIFEST_NAME).exists())

    def test_changed_pak_is_kept(self):
        target = self.build_and_install()
        target.write_bytes(b"edited")
        self.assertEqual(self.uninstall("-Remove").returncode, 0)
        self.assertTrue(target.exists())
        self.assertTrue((self.mods / pakmod.MANIFEST_NAME).exists())

    def test_manifest_entry_with_a_path_is_refused(self):
        self.mods.mkdir(parents=True)
        victim = self.tmp / "victim.pak"
        victim.write_bytes(b"keep")
        manifest = {"version": 1, "created_dir": False, "files": {"..\\..\\..\\..\\victim.pak": pakmod.sha256_of(victim)}}
        pakmod.write_manifest(self.mods, manifest)
        done = self.uninstall("-Remove")
        self.assertNotEqual(done.returncode, 0)
        self.assertTrue(victim.exists())

    def test_no_pak_manifest_is_fine(self):
        self.assertEqual(self.uninstall("-Remove").returncode, 0)


if __name__ == "__main__":
    unittest.main()
