"""Tests for --pak and --env of run.py (spec 10, U4). Temp game folders and fake paks only. No game is started."""

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401
import run as run_module
from runlib import paks, phases
from runlib.extra_env import EnvOptionError, masked_for_config, parse_env_options
from runlib.game import GameInstall, build_game_environment
from runlib.pak_phases import PAK_PHASE_NAME, install_paks, remove_paks_phase
from runlib.runfolder import create_run_folder
from runlib.scenario_context import ScenarioContext
from runlib.runner import Phase, PhaseContext, PhaseFailed, run_phases
from runlib.summary import condense_environment


class EnvOptionTest(unittest.TestCase):
    def test_valid_options_are_parsed(self):
        self.assertEqual(parse_env_options(["A_1=x", "B=a b=c"]), {"A_1": "x", "B": "a b=c"})

    def test_bad_names_are_refused(self):
        for option in ("a=1", "1A=1", "A-B=1", "=1", "A" * 65 + "=1", "NOEQUALS"):
            with self.subTest(option=option), self.assertRaises(EnvOptionError):
                parse_env_options([option])

    def test_reserved_names_are_refused(self):
        for name in ("PATH", "PATHEXT", "LOCALAPPDATA", "HARNESS_RUN_DIR", "HARNESS_RUN_DIR2", "UE4SS_BRIDGE_PORT",
                     "HARNESS_AUTOBOOT", "HARNESS_TEST_SAVE"):
            with self.subTest(name=name), self.assertRaises(EnvOptionError):
                parse_env_options([f"{name}=1"])

    def test_other_harness_names_are_allowed(self):
        self.assertEqual(parse_env_options(["HARNESS_EXPECT_ITEM_ROWS=1"]), {"HARNESS_EXPECT_ITEM_ROWS": "1"})

    def test_bad_values_are_refused(self):
        for value in ("a\nb", "a\x00b", "x" * 257):
            with self.subTest(value=value[:5]), self.assertRaises(EnvOptionError):
                parse_env_options([f"A={value}"])

    def test_duplicate_name_is_refused(self):
        with self.assertRaises(EnvOptionError):
            parse_env_options(["A=1", "A=2"])

    def test_secret_values_are_masked_in_config(self):
        masked = masked_for_config({"MY_TOKEN": "abc", "API_KEY": "k", "DB_PASSWORD": "p", "THE_SECRET": "s", "MODE": "fast"})
        self.assertEqual(masked, {"MY_TOKEN": "***", "API_KEY": "***", "DB_PASSWORD": "***", "THE_SECRET": "***", "MODE": "fast"})

    def test_game_environment_gets_extra_values_but_the_harness_wins(self):
        env = build_game_environment(Path("run"), "slot", base_env={"X": "base"}, extra_env={"MODE": "fast", "X": "extra"})
        self.assertEqual((env["MODE"], env["X"]), ("fast", "extra"))
        self.assertEqual(env["HARNESS_TEST_SAVE"], "slot")


class PakPhasesTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.install = GameInstall(root=root / "game", saved_dir=root / "saved")
        self.work = root / "work"
        (self.work / "out").mkdir(parents=True)
        for name in ("demo", "other"):
            (self.work / "out" / paks.pak_file_name(name)).write_bytes(f"fake pak {name}".encode())
        self.mods = paks.mods_dir_of(self.install.root)
        self.ctx = PhaseContext(run=create_run_folder(root / "runs", "r1"), config={})

    def pak_in_mods(self, name):
        return self.mods / paks.pak_file_name(name)

    def test_preflight_installs_and_records_the_pak(self):
        install_paks(self.install, self.ctx, ["demo", "other"], self.work)
        self.assertTrue(self.pak_in_mods("demo").is_file() and self.pak_in_mods("other").is_file())
        entries = self.ctx.config["environment"]["paks"]
        self.assertEqual([entry.split(":")[0] for entry in entries], ["demo", "other"])
        self.assertEqual(len(entries[0].split(":")[1]), 12)
        self.assertEqual(condense_environment(self.ctx.config["environment"])["paks"], entries)
        self.assertEqual(json.loads(self.ctx.run.config_path.read_text())["environment"]["paks"], entries)

    def test_cleanup_phase_removes_the_paks_and_the_empty_folder(self):
        install_paks(self.install, self.ctx, ["demo"], self.work)
        detail = remove_paks_phase(self.install).fn(self.ctx)
        self.assertFalse(self.pak_in_mods("demo").exists())
        self.assertFalse(self.mods.exists())
        self.assertIn("demo", detail)

    def test_teardown_removes_the_pak_when_an_earlier_phase_failed(self):
        def failing_preflight(ctx):
            install_paks(self.install, ctx, ["demo"], self.work)
            raise PhaseFailed("something after the install broke")

        results = run_phases([Phase("preflight", failing_preflight, 5), Phase("scenario", lambda ctx: None, 5),
                              remove_paks_phase(self.install)], self.ctx)
        self.assertEqual([result.status for result in results], ["failed", "skipped", "ok"])
        self.assertFalse(self.pak_in_mods("demo").exists())

    def test_cleanup_runs_after_a_crash_of_the_phase(self):
        def crashing(ctx):
            install_paks(self.install, ctx, ["demo"], self.work)
            raise RuntimeError("boom")

        results = run_phases([Phase("preflight", crashing, 5), remove_paks_phase(self.install)], self.ctx)
        self.assertEqual(results[0].status, "error")
        self.assertFalse(self.pak_in_mods("demo").exists())

    def test_manifest_conflict_fails_clearly_and_keeps_the_foreign_file(self):
        self.mods.mkdir(parents=True)
        self.pak_in_mods("demo").write_bytes(b"not ours")
        with self.assertRaises(PhaseFailed) as caught:
            install_paks(self.install, self.ctx, ["demo"], self.work)
        self.assertIn("refusing to overwrite", str(caught.exception))
        self.assertIn("manifest", str(caught.exception))
        remove_paks_phase(self.install).fn(self.ctx)  # the cleanup must not delete a file that is not in the manifest
        self.assertEqual(self.pak_in_mods("demo").read_bytes(), b"not ours")

    def test_unbuilt_pak_fails_clearly(self):
        with self.assertRaises(PhaseFailed) as caught:
            install_paks(self.install, self.ctx, ["missing"], self.work)
        self.assertIn("not built", str(caught.exception))

    def test_a_changed_pak_is_kept_and_reported(self):
        install_paks(self.install, self.ctx, ["demo"], self.work)
        self.pak_in_mods("demo").write_bytes(b"changed by hand")
        with self.assertRaises(PhaseFailed) as caught:
            remove_paks_phase(self.install).fn(self.ctx)
        self.assertIn("NOT removed", str(caught.exception))
        self.assertTrue(self.pak_in_mods("demo").exists())

    def test_cleanup_without_paks_does_nothing(self):
        self.assertIsNone(remove_paks_phase(self.install).fn(self.ctx))

    def test_phase_list_has_the_cleanup_last_only_with_paks(self):
        plain = phases.build_real_phases("noop")
        self.assertNotIn(PAK_PHASE_NAME, [phase.name for phase in plain])
        with_paks = phases.build_real_phases("noop", pak_names=["demo"], pak_work_dir=self.work)
        self.assertEqual(with_paks[-1].name, PAK_PHASE_NAME)
        self.assertTrue(with_paks[-1].always_run)


class MetricTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        run = create_run_folder(Path(temp.name) / "runs", "r1")
        self.scenario_ctx = ScenarioContext(PhaseContext(run=run, config={}), mock.Mock())
        self.path = run.path / "metrics.json"

    def test_metrics_are_written_as_a_flat_file(self):
        self.scenario_ctx.metric("ticks", 12)
        self.scenario_ctx.metric("losses.left", 3.5)
        self.scenario_ctx.metric("ticks", 14)  # the second call replaces the value
        self.assertEqual(json.loads(self.path.read_text()), {"ticks": 14.0, "losses.left": 3.5})

    def test_bad_metrics_are_refused(self):
        for name, value in (("bad name", 1), ("", 1), ("x", "text"), ("x", True), ("x", float("nan")), ("x", float("inf"))):
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                self.scenario_ctx.metric(name, value)
        self.assertFalse(self.path.exists())


class RunPyOptionsTest(unittest.TestCase):
    def parse(self, *extra):
        return run_module.parse_args(["--scenario", "smoke", *extra])

    def test_options_are_checked_and_stored(self):
        args = self.parse("--pak", "demo", "--env", "MODE=fast", "--env", "API_KEY=abc")
        run_module.check_variant_options(args)
        self.assertEqual(args.pak_names, ["demo"])
        self.assertEqual(args.extra_env, {"MODE": "fast", "API_KEY": "abc"})

    def test_config_has_masked_values_and_keys_only_in_the_environment(self):
        args = self.parse("--env", "MODE=fast", "--env", "API_KEY=abc")
        run_module.check_variant_options(args)
        run = argparse.Namespace(run_id="r1")
        lock = argparse.Namespace(took_over_pid=None)
        config = run_module.build_config(args, run, [], lock)
        self.assertEqual(config["env"], {"MODE": "fast", "API_KEY": "***"})
        self.assertEqual(config["environment"], {"env_keys": ["API_KEY", "MODE"]})
        self.assertNotIn("abc", json.dumps(config))

    def test_bad_options_fail_before_a_run(self):
        for extra in (("--env", "PATH=x"), ("--pak", "bad name"), ("--pak", "a", "--pak", "a"), ("--env", "NOEQUALS")):
            with self.subTest(extra=extra):
                args = self.parse(*extra)
                self.assertEqual(run_module.run_one(args), 4)

    def test_fake_run_refuses_game_options(self):
        args = run_module.parse_args(["--fake", "pass", "--env", "A=1"])
        self.assertEqual(run_module.run_one(args), 4)


if __name__ == "__main__":
    unittest.main()
