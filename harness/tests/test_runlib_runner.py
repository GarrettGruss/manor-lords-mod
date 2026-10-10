import _thread
import json
import tempfile
import time
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib.fake_phases import OUTCOMES, build_fake_phases
from runlib.runfolder import create_run_folder
from runlib.runner import Phase, PhaseFailed, execute_run

EXPECTED = {
    "pass": ("pass", ["ok"] * 7),
    "fail": ("fail", ["ok", "ok", "ok", "ok", "failed", "ok", "ok"]),
    "crash": ("crash", ["ok", "ok", "ok", "ok", "error", "ok", "ok"]),
    "timeout": ("timeout", ["ok", "ok", "ok", "ok", "timeout", "ok", "ok"]),
    "harness_error": ("harness_error", ["error", "skipped", "skipped", "skipped", "skipped", "ok", "ok"]),
}


class RunnerCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.runs_root = Path(temp.name)
        self.run_folder = create_run_folder(self.runs_root, "test-run")

    def read_summary(self):
        return json.loads(self.run_folder.summary_path.read_text())


class FakeOutcomeTest(RunnerCase):
    def test_every_outcome(self):
        self.assertEqual(set(EXPECTED), set(OUTCOMES))
        for outcome, (verdict, statuses) in EXPECTED.items():
            with self.subTest(outcome=outcome):
                run = create_run_folder(self.runs_root, f"run-{outcome}")
                summary = execute_run(run, {"scenario": f"fake-{outcome}"}, build_fake_phases(outcome))
                self.assertEqual(summary.verdict, verdict)
                self.assertEqual([phase.status for phase in summary.phases], statuses)
                on_disk = json.loads(run.summary_path.read_text())
                self.assertEqual(on_disk["verdict"], verdict)
                self.assertEqual([p["name"] for p in on_disk["phases"]][-2:], ["collect", "teardown"])
                self.assertEqual(list(run.path.glob("*.tmp")), [])

    def test_pass_lists_artifacts_and_files(self):
        summary = execute_run(self.run_folder, {"scenario": "s"}, build_fake_phases("pass"))
        self.assertEqual(summary.artifacts["screenshots"], ["screenshots/start.png.txt"])
        self.assertEqual(summary.artifacts["logs"], ["mod.log"])
        self.assertEqual(summary.boot["state"], "READY")
        self.assertTrue((self.run_folder.path / "scenario.json").exists())
        self.assertEqual(summary.notes, [])

    def test_crash_collects_crash_folder(self):
        summary = execute_run(self.run_folder, {}, build_fake_phases("crash"))
        self.assertIsNotNone(summary.crash)
        self.assertTrue((self.run_folder.crash_dir / "crash.txt").exists())

    def test_skipped_phases_are_noted(self):
        summary = execute_run(self.run_folder, {}, build_fake_phases("harness_error"))
        self.assertIn("phase boot was skipped", summary.notes)
        self.assertIn("no scenario result", summary.notes)

    def test_start_notes_reach_the_summary(self):
        config = {"start_notes": ["took over a lock"]}
        summary = execute_run(self.run_folder, config, build_fake_phases("pass"))
        self.assertIn("took over a lock", summary.notes)


class PhaseBehaviourTest(RunnerCase):
    def test_exception_text_is_recorded(self):
        def boom(ctx):
            raise ValueError("bad thing")

        summary = execute_run(self.run_folder, {}, [Phase("preflight", boom, 5)])
        self.assertEqual(summary.phases[0].status, "error")
        self.assertIn("bad thing", summary.phases[0].detail)
        self.assertTrue(self.run_folder.summary_path.exists())

    def test_phase_failed_gives_failed_status(self):
        def fail(ctx):
            raise PhaseFailed("nope")

        summary = execute_run(self.run_folder, {}, [Phase("deploy", fail, 5)])
        self.assertEqual((summary.phases[0].status, summary.phases[0].detail), ("failed", "nope"))

    def test_timeout_abandons_a_daemon_thread_and_goes_on(self):
        finished = []

        def slow(ctx):
            time.sleep(0.6)
            finished.append(True)

        phases = [
            Phase("boot", slow, 0.1),
            Phase("scenario", lambda ctx: None, 5),
            Phase("teardown", lambda ctx: None, 5, always_run=True),
        ]
        started = time.monotonic()
        summary = execute_run(self.run_folder, {}, phases)
        self.assertLess(time.monotonic() - started, 0.5, "the runner must not wait for the slow phase")
        self.assertEqual([p.status for p in summary.phases], ["timeout", "skipped", "ok"])
        self.assertEqual(summary.verdict, "timeout")
        time.sleep(0.8)
        self.assertEqual(finished, [True], "the abandoned thread keeps running")

    def test_always_run_phases_run_after_failure(self):
        order = []

        def boom(ctx):
            raise RuntimeError("x")

        phases = [
            Phase("a", boom, 5),
            Phase("b", lambda ctx: order.append("b"), 5),
            Phase("collect", lambda ctx: order.append("collect"), 5, always_run=True),
            Phase("teardown", lambda ctx: order.append("teardown"), 5, always_run=True),
        ]
        execute_run(self.run_folder, {}, phases)
        self.assertEqual(order, ["collect", "teardown"])

    def test_seconds_are_recorded(self):
        summary = execute_run(self.run_folder, {}, [Phase("a", lambda ctx: time.sleep(0.2), 5)])
        self.assertGreaterEqual(summary.phases[0].seconds, 0.2)

    def test_keyboard_interrupt_still_writes_summary_and_runs_teardown(self):
        torn_down = []

        def interrupt(ctx):
            _thread.interrupt_main()  # raises KeyboardInterrupt in the main thread
            time.sleep(0.3)

        phases = [
            Phase("scenario", interrupt, 5),
            Phase("teardown", lambda ctx: torn_down.append(1), 5, always_run=True),
        ]
        with self.assertRaises(KeyboardInterrupt):
            execute_run(self.run_folder, {}, phases)
        data = self.read_summary()
        self.assertEqual(data["verdict"], "harness_error")
        self.assertIn("KeyboardInterrupt", json.dumps(data["phases"]))
        self.assertEqual(torn_down, [1])

    def test_summary_written_when_the_runner_itself_raises(self):
        class BadPhases(list):
            def __iter__(self):
                raise RuntimeError("runner broke")

        with self.assertRaises(RuntimeError):
            execute_run(self.run_folder, {}, BadPhases([Phase("a", lambda ctx: None, 5)]))
        data = self.read_summary()
        self.assertEqual(data["verdict"], "harness_error")
        self.assertIn("runner broke", data["phases"][-1]["detail"])

    def test_summary_stays_under_4kb_with_huge_exception_text(self):
        def boom(ctx):
            raise RuntimeError("y" * 50000)

        execute_run(self.run_folder, {}, [Phase("a", boom, 5)])
        self.assertLess(self.run_folder.summary_path.stat().st_size, 4096)


if __name__ == "__main__":
    unittest.main()
