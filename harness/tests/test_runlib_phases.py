"""Tests for the real phases that need no game: mocks, fakes and temp folders."""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401
from runlib import phases
from runlib.environment import hash_mods, read_build_id, sha256_of_folder
from runlib.game import (
    GameInstall,
    build_game_environment,
    count_pause_calls,
    ensure_game_alive,
    read_boot_file,
    stop_processes,
)
from runlib.runfolder import create_run_folder
from runlib.runner import PhaseContext, PhaseFailed
from runlib.scenario import SCENARIOS, get_scenario
from runlib.scenario_context import ScenarioContext


class FakePopen:
    def __init__(self, exit_code=None):
        self.exit_code = exit_code
        self.pid = 1234

    def poll(self):
        return self.exit_code


class FakeProcess:
    def __init__(self, pid):
        self.pid = pid
        self.terminated = False

    def terminate(self):
        self.terminated = True


class TempTestCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.run_folder = create_run_folder(self.temp / "runs", "r1")
        self.ctx = PhaseContext(run=self.run_folder, config={})


class BootFileTest(TempTestCase):
    def test_read_boot_file(self):
        path = self.temp / "boot.json"
        self.assertIsNone(read_boot_file(path))
        path.write_text('{"state": "REA', encoding="utf-8")  # half written
        self.assertIsNone(read_boot_file(path))
        path.write_text('{"state": "READY", "reason": null}', encoding="utf-8")
        self.assertEqual(read_boot_file(path)["state"], "READY")

    def test_count_pause_calls(self):
        log = self.temp / "mod.log"
        self.assertEqual(count_pause_calls(log), 0)
        log.write_text(
            "1 1 INFO [HarnessBoot] game clock is moving; calling pauseGame (call 1)\n"
            "2 2 INFO [HarnessBoot] state -> READY\n"
            "3 3 INFO [HarnessBoot] game clock is moving; calling pauseGame (call 2)\n",
            encoding="utf-8",
        )
        self.assertEqual(count_pause_calls(log), 2)


class EnvironmentTest(TempTestCase):
    def test_game_environment(self):
        env = build_game_environment(self.run_folder.path, "saveGame_0", base_env={"KEEP": "yes"})
        self.assertEqual(env["KEEP"], "yes")
        self.assertEqual(env["HARNESS_AUTOBOOT"], "1")
        self.assertEqual(env["HARNESS_TEST_SAVE"], "saveGame_0")
        self.assertEqual(env["HARNESS_RUN_DIR"], str(self.run_folder.path.resolve()))
        self.assertTrue(os.path.isabs(env["HARNESS_RUN_DIR"]))

    def test_telemetry_interval_default_and_off(self):
        default = build_game_environment(self.run_folder.path, "s", base_env={})
        self.assertEqual(default["HARNESS_TELEMETRY_INTERVAL_S"], "5")
        off = build_game_environment(self.run_folder.path, "s", base_env={}, telemetry_interval_s=0)
        self.assertEqual(off["HARNESS_TELEMETRY_INTERVAL_S"], "0")

    def test_describe_telemetry(self):
        self.assertIsNone(phases.describe_telemetry(self.temp))
        (self.temp / "telemetry.jsonl").write_text('{"n":1}\n{"n":2}\n', encoding="utf-8")
        self.assertEqual(phases.describe_telemetry(self.temp), "telemetry.jsonl (2 samples)")

    def test_launch_passes_environment_and_working_folder(self):
        install = GameInstall(root=self.temp / "game", saved_dir=self.temp / "saved")
        with mock.patch.object(phases.subprocess, "Popen", return_value=FakePopen()) as popen, mock.patch.object(
            phases.time, "sleep"
        ):
            phases._launch(install, "saveGame_0", 2.5)(self.ctx)
        args, kwargs = popen.call_args
        self.assertEqual(args[0], [str(install.exe)])
        self.assertEqual(kwargs["cwd"], install.win64)
        self.assertEqual(kwargs["env"]["HARNESS_RUN_DIR"], str(self.run_folder.path.resolve()))
        self.assertEqual(kwargs["env"]["HARNESS_TELEMETRY_INTERVAL_S"], "2.5")
        self.assertIn("game_popen", self.ctx.state)

    def test_hash_mods_changes_with_content(self):
        mod_dir = self.temp / "mod"
        (mod_dir / "A").mkdir(parents=True)
        (mod_dir / "A" / "x.lua").write_text("one")
        first = hash_mods(mod_dir)
        self.assertEqual(list(first), ["A"])
        (mod_dir / "A" / "x.lua").write_text("two")
        self.assertNotEqual(hash_mods(mod_dir), first)
        self.assertEqual(sha256_of_folder(mod_dir / "A"), hash_mods(mod_dir)["A"])

    def test_read_build_id(self):
        manifest = self.temp / "app.acf"
        manifest.write_text('"AppState"\n{\n\t"buildid"\t\t"12345"\n}\n')
        self.assertEqual(read_build_id(manifest), "12345")


class StalePreflightTest(TempTestCase):
    def test_stale_process_is_stopped_and_noted(self):
        stale = FakeProcess(4242)
        with mock.patch.object(phases, "find_game_processes", return_value=[stale]), mock.patch.object(
            phases, "stop_processes"
        ) as stop:
            phases._stop_stale_game(self.ctx)
        stop.assert_called_once_with([stale])
        self.assertEqual(self.ctx.state["notes"], ["stale game process PID 4242 was stopped"])

    def test_no_stale_process_no_note(self):
        with mock.patch.object(phases, "find_game_processes", return_value=[]):
            phases._stop_stale_game(self.ctx)
        self.assertEqual(self.ctx.state["notes"], [])

    def test_steam_missing_fails(self):
        install = GameInstall(root=self.temp / "game", saved_dir=self.temp / "saved")
        with mock.patch.object(phases, "is_steam_running", return_value=False):
            with self.assertRaisesRegex(PhaseFailed, "Steam"):
                phases._preflight(install, "saveGame_0")(self.ctx)

    def test_missing_fixture_source_fails(self):
        install = GameInstall(root=self.temp / "game", saved_dir=self.temp / "saved")
        install.exe.parent.mkdir(parents=True)
        install.exe.write_text("")
        with mock.patch.object(phases, "is_steam_running", return_value=True):
            with self.assertRaisesRegex(PhaseFailed, "fixture base"):
                phases._preflight(install, "saveGame_0")(self.ctx)

    def test_stop_processes_raises_if_one_stays(self):
        with mock.patch("runlib.game.psutil.wait_procs", return_value=([], [FakeProcess(7)])):
            with self.assertRaisesRegex(RuntimeError, "still running"):
                stop_processes([FakeProcess(7)], wait_s=0)


class CrashDetectionTest(TempTestCase):
    def test_alive_game_is_fine(self):
        self.ctx.state["game_popen"] = FakePopen(None)
        ensure_game_alive(self.ctx, "boot")
        self.assertIsNone(self.ctx.state["crash"])

    def test_dead_game_is_a_crash(self):
        self.ctx.state["game_popen"] = FakePopen(1)
        with self.assertRaises(PhaseFailed):
            ensure_game_alive(self.ctx, "boot")
        self.assertEqual(self.ctx.state["crash"], {"reason": "game process ended during boot", "exit_code": 1})

    def test_dead_game_after_stop_request_is_not_a_crash(self):
        self.ctx.state["game_popen"] = FakePopen(1)
        self.ctx.state["game_stop_requested"] = True
        ensure_game_alive(self.ctx, "teardown")
        self.assertIsNone(self.ctx.state["crash"])


class BootPhaseTest(TempTestCase):
    def setUp(self):
        super().setUp()
        self.ctx.state["launch_monotonic"] = time.monotonic()
        self.ctx.state["game_popen"] = FakePopen(None)
        self.patch = mock.patch.object(phases, "BOOT_POLL_S", 0.01)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def write_boot(self, state, reason=None):
        self.run_folder.boot_path.write_text(json.dumps({"state": state, "reason": reason}))

    def test_ready(self):
        (self.run_folder.path / "mod.log").write_text("1 1 INFO [HarnessBoot] calling pauseGame (call 1)\n")
        self.write_boot("READY")
        phases._boot(self.ctx)
        boot = self.ctx.state["boot"]
        self.assertEqual((boot["state"], boot["pause_calls"], boot["reason"]), ("READY", 1, None))

    def test_failed_keeps_reason(self):
        self.write_boot("FAILED", "slot missing")
        with self.assertRaisesRegex(PhaseFailed, "slot missing"):
            phases._boot(self.ctx)
        self.assertEqual(self.ctx.state["boot"]["reason"], "slot missing")

    def test_game_dies_during_boot(self):
        self.ctx.state["game_popen"] = FakePopen(-1)
        with self.assertRaises(PhaseFailed):
            phases._boot(self.ctx)
        self.assertEqual(self.ctx.state["crash"]["reason"], "game process ended during boot")

    def test_timeout_names_last_state(self):
        self.write_boot("LOADING_SAVE")
        with mock.patch.object(phases, "BOOT_DEADLINE_S", 0.1):
            with self.assertRaisesRegex(PhaseFailed, "LOADING_SAVE"):
                phases._boot(self.ctx)


class ScenarioTest(TempTestCase):
    def test_registry(self):
        self.assertIn("noop", SCENARIOS)
        with self.assertRaisesRegex(ValueError, "Unknown scenario"):
            get_scenario("nope")

    def noop_result(self, clock):
        self.ctx.state["game_popen"] = FakePopen(None)
        scenario_ctx = ScenarioContext(self.ctx, mock.Mock())
        scenario_ctx.bridge.measure_clock.return_value = clock
        return get_scenario("noop")(scenario_ctx)

    def test_noop_passes_when_paused(self):
        clock = {"clock": 1.0, "change": 0.0, "seconds": 3, "paused": True}
        self.assertTrue(self.noop_result(clock)["passed"])

    def test_noop_fails_when_not_paused(self):
        clock = {"clock": 4.0, "change": 3.0, "seconds": 3, "paused": False}
        self.assertFalse(self.noop_result(clock)["passed"])

    def test_bridge_error_with_dead_game_is_a_crash(self):
        self.ctx.state["game_popen"] = FakePopen(1)
        install = GameInstall(root=self.temp / "game", saved_dir=self.temp / "saved")
        with mock.patch.dict(SCENARIOS, {"boom": mock.Mock(side_effect=ConnectionError("lost"))}):
            with mock.patch.object(phases, "configure_bridge_client"):
                with self.assertRaises(PhaseFailed):
                    phases._scenario(install, "boom")(self.ctx)
        self.assertEqual(self.ctx.state["crash"]["reason"], "game process ended during scenario")


class CollectTest(TempTestCase):
    def make_install(self):
        install = GameInstall(root=self.temp / "game", saved_dir=self.temp / "saved")
        install.ue4ss_log.parent.mkdir(parents=True)
        install.ue4ss_log.write_text("log text")
        return install

    def make_crash(self, install, name, age_s, size=10):
        folder = install.crashes_dir / name
        folder.mkdir(parents=True)
        (folder / "report.txt").write_bytes(b"x" * size)
        old = time.time() - age_s
        os.utime(folder, (old, old))
        return folder

    def test_collect_copies_log_and_new_crashes_only(self):
        install = self.make_install()
        self.make_crash(install, "old", age_s=3600)
        self.make_crash(install, "new", age_s=-5)
        self.ctx.state["run_started_epoch"] = time.time() - 60
        phases._collect(install)(self.ctx)
        artifacts = self.ctx.state["artifacts"]
        self.assertEqual(artifacts["crash"], ["crash/new"])
        self.assertIn("UE4SS.log", artifacts["logs"])
        self.assertTrue((self.run_folder.crash_dir / "new" / "report.txt").exists())
        self.assertFalse((self.run_folder.crash_dir / "old").exists())

    def test_big_crash_dir_is_skipped_with_note(self):
        install = self.make_install()
        self.make_crash(install, "big", age_s=-5, size=2048)
        self.ctx.state["run_started_epoch"] = time.time() - 60
        with mock.patch.object(phases, "MAX_CRASH_DIR_BYTES", 1024):
            phases._collect(install)(self.ctx)
        self.assertEqual(self.ctx.state["artifacts"]["crash"], [])
        self.assertTrue(any("big" in note for note in self.ctx.state["notes"]))

    def test_missing_log_and_crash_folder_are_fine(self):
        install = GameInstall(root=self.temp / "none", saved_dir=self.temp / "none")
        phases._collect(install)(self.ctx)
        self.assertEqual(self.ctx.state["artifacts"]["logs"], [])


class TeardownTest(TempTestCase):
    def install(self):
        return GameInstall(root=self.temp / "game", saved_dir=self.temp / "saved")

    def test_stop_flag_is_set_before_terminate(self):
        order = []
        game = FakeProcess(99)
        self.ctx.state["artifacts"] = {}

        def fake_stop(processes):
            order.append(self.ctx.state["game_stop_requested"])

        with mock.patch.object(phases, "find_game_processes", side_effect=[[game], []]), mock.patch.object(
            phases, "stop_processes", side_effect=fake_stop
        ):
            detail = phases._teardown(self.install(), keep_open=False)(self.ctx)
        self.assertEqual(order, [True])
        self.assertIn("game stopped", detail)

    def test_process_remaining_fails(self):
        self.ctx.state["artifacts"] = {}
        with mock.patch.object(phases, "find_game_processes", return_value=[FakeProcess(1)]), mock.patch.object(
            phases, "stop_processes"
        ):
            with self.assertRaisesRegex(PhaseFailed, "remains"):
                phases._teardown(self.install(), keep_open=False)(self.ctx)

    def test_keep_open_does_not_stop(self):
        with mock.patch.object(phases, "stop_processes") as stop:
            phases._teardown(self.install(), keep_open=True)(self.ctx)
        stop.assert_not_called()
        self.assertTrue(any("keep-open" in note for note in self.ctx.state["notes"]))
        self.assertTrue(self.ctx.state["game_stop_requested"])


class BuildPhasesTest(unittest.TestCase):
    def test_order_and_always_run(self):
        built = phases.build_real_phases("noop")
        self.assertEqual(
            [p.name for p in built], ["preflight", "deploy", "launch", "boot", "scenario", "collect", "teardown"]
        )
        self.assertEqual([p.name for p in built if p.always_run], ["collect", "teardown"])

    def test_unknown_scenario(self):
        with self.assertRaises(ValueError):
            phases.build_real_phases("nope")


class CliArgumentsTest(unittest.TestCase):
    def run_cli(self, *args):
        import subprocess
        import sys

        run_py = Path(__file__).resolve().parent.parent / "run.py"
        return subprocess.run([sys.executable, str(run_py), *args], capture_output=True, text=True, timeout=60)

    def test_both_or_none_is_refused(self):
        for args in ([], ["--fake", "pass", "--scenario", "noop"]):
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 4)
            self.assertIn("exactly one", result.stderr)

    def test_unknown_scenario_is_refused_before_any_run(self):
        result = self.run_cli("--scenario", "nope")
        self.assertEqual(result.returncode, 4)
        self.assertIn("Unknown scenario", result.stderr)


if __name__ == "__main__":
    unittest.main()
