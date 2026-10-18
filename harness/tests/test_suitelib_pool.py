"""The parallel suite pool (spec 11, step 4): slots, exclusive scenarios, a broken slot, separate run folders."""

import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from suitelib.pool import build_jobs, run_suite_parallel
from suitelib.runner import STOP_ITERATION_CAP, STOP_NO_SLOTS, run_suite
from suitelib.suitefile import SuiteEntry, Variant
from suitelib_fakes import FakeRunOne, entry, make_suite, result

RUN_S = 0.05


class SlotRecorder:
    """Shared by the fake launchers of all slots: who ran where, and how many ran at the same time."""

    def __init__(self, runs_root: Path | None = None):
        self.lock = threading.Lock()
        self.active: set[str] = set()
        self.max_active = 0
        self.overlaps: list[tuple[str, set[str]]] = []  # (scenario, the other scenarios that ran at its start)
        self.calls: list[tuple[int, str, str]] = []  # (slot, scenario, run_id)
        self.runs_root = runs_root

    def launcher(self, slot: int, script: dict | None = None, broken: bool = False):
        script = dict(script or {})

        def run_one(scenario, run_id, fixture, variant=None):
            if broken:
                return result(run_id, "harness_error", reason=f"slot {slot} is not installed", start_failed=True)
            with self.lock:
                self.overlaps.append((scenario, set(self.active)))
                self.active.add(run_id)
                self.max_active = max(self.max_active, len(self.active))
                self.calls.append((slot, scenario, run_id))
            try:
                if self.runs_root:
                    self._write_run_folder(run_id)
                time.sleep(RUN_S)
                item = script.get(scenario, "pass")
                return item(run_id) if callable(item) else result(run_id, item)
            finally:
                with self.lock:
                    self.active.discard(run_id)

        return run_one

    def _write_run_folder(self, run_id: str) -> None:
        folder = self.runs_root / run_id
        folder.mkdir(parents=True)  # raises if another run used the same folder
        (folder / "summary.json").write_text(run_id)


class PoolTest(unittest.TestCase):
    def test_jobs_keep_the_sequential_order_with_interleaved_variants(self):
        ab = SuiteEntry("raid", 2, None, False, variants=[Variant("A"), Variant("B")])
        jobs = build_jobs(make_suite([entry("smoke"), ab]))
        self.assertEqual([(job.entry.scenario, job.variant_name) for job in jobs],
                         [("smoke", "default"), ("raid", "A"), ("raid", "B"), ("raid", "A"), ("raid", "B")])

    def test_three_slots_run_at_the_same_time_with_the_same_verdicts(self):
        recorder = SlotRecorder()
        suite = make_suite([entry("a", 3), entry("b", 3)])
        outcome = run_suite_parallel(suite, {n: recorder.launcher(n) for n in range(3)}, "sid")
        self.assertEqual(recorder.max_active, 3)
        self.assertEqual({call[0] for call in recorder.calls}, {0, 1, 2})
        sequential = run_suite(suite, FakeRunOne({}), "sid")
        self.assertEqual([e.verdict for e in outcome.entries], [e.verdict for e in sequential.entries])
        self.assertEqual([len(e.repeats) for e in outcome.entries], [3, 3])
        self.assertIsNone(outcome.stop_reason)

    def test_variant_repeats_are_reported_in_job_order(self):
        recorder = SlotRecorder()
        ab = SuiteEntry("raid", 3, None, False, variants=[Variant("A"), Variant("B")])
        outcome = run_suite_parallel(make_suite([ab]), {n: recorder.launcher(n) for n in range(2)}, "sid")
        self.assertEqual(outcome.entries[0].variant_names, ["A", "B", "A", "B", "A", "B"])
        self.assertEqual(len(outcome.entries[0].repeats_of("B")), 3)

    def test_failure_is_retried_on_the_same_job(self):
        recorder = SlotRecorder()
        verdicts = iter(["fail", "pass"])
        script = {"a": lambda run_id: result(run_id, next(verdicts))}
        outcome = run_suite_parallel(make_suite([entry("a")], retries=1), {0: recorder.launcher(0, script)}, "sid")
        self.assertEqual(outcome.entries[0].verdict, "pass")
        self.assertTrue(outcome.entries[0].flaky)

    def test_an_exclusive_scenario_never_runs_with_another_game(self):
        recorder = SlotRecorder()
        suite = make_suite([entry("a", 3), entry("mouse", 2), entry("b", 3)])
        outcome = run_suite_parallel(suite, {n: recorder.launcher(n) for n in range(3)}, "sid",
                                     is_exclusive=lambda scenario: scenario == "mouse")
        self.assertEqual([e.verdict for e in outcome.entries], ["pass"] * 3)
        for scenario, others in recorder.overlaps:
            if scenario == "mouse":
                self.assertEqual(others, set(), "the exclusive run started while another game ran")
        mouse_ids = {run_id for _, scenario, run_id in recorder.calls if scenario == "mouse"}
        for scenario, others in recorder.overlaps:
            self.assertFalse(others & mouse_ids, f"{scenario} started while the exclusive run ran")
        self.assertEqual(recorder.max_active, 3, "the other scenarios still ran in parallel")

    def test_a_slot_that_fails_to_start_is_dropped_and_the_suite_goes_on(self):
        recorder = SlotRecorder()
        launchers = {0: recorder.launcher(0), 1: recorder.launcher(1, broken=True), 2: recorder.launcher(2)}
        outcome = run_suite_parallel(make_suite([entry("a", 4)]), launchers, "sid")
        self.assertEqual(outcome.entries[0].verdict, "pass")
        self.assertEqual(len(outcome.entries[0].repeats), 4, "the job of the broken slot ran on another slot")
        self.assertEqual(set(outcome.bad_slots), {1})
        self.assertIn("not installed", outcome.bad_slots[1])
        self.assertNotIn(1, {call[0] for call in recorder.calls})
        self.assertIsNone(outcome.stop_reason)

    def test_no_working_slot_stops_the_suite_and_names_what_did_not_run(self):
        recorder = SlotRecorder()
        launchers = {n: recorder.launcher(n, broken=True) for n in range(2)}
        outcome = run_suite_parallel(make_suite([entry("a"), entry("b")]), launchers, "sid")
        self.assertEqual(outcome.stop_reason, STOP_NO_SLOTS)
        self.assertEqual(outcome.not_run, ["a", "b"])
        self.assertEqual(set(outcome.bad_slots), {0, 1})

    def test_unknown_optional_scenario_is_skipped(self):
        recorder = SlotRecorder()
        script = {"later": lambda run_id: result(run_id, "harness_error", unknown_scenario=True)}
        suite = make_suite([entry("a"), entry("later", 3, optional=True)])
        outcome = run_suite_parallel(suite, {n: recorder.launcher(n, script) for n in range(2)}, "sid")
        self.assertEqual([e.verdict for e in outcome.entries], ["pass", "skipped"])

    def test_iteration_cap_stops_new_runs(self):
        recorder = SlotRecorder()
        script = {"b": lambda run_id: result(run_id, "harness_error", iteration_cap=True)}
        outcome = run_suite_parallel(make_suite([entry("b"), entry("c", 3)]), {0: recorder.launcher(0, script)}, "sid")
        self.assertEqual(outcome.stop_reason, STOP_ITERATION_CAP)
        self.assertEqual(outcome.not_run, ["b", "c"])

    def test_parallel_runs_never_share_a_run_folder(self):
        runs_root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, runs_root, True)
        recorder = SlotRecorder(runs_root)
        outcome = run_suite_parallel(make_suite([entry("a", 6)]), {n: recorder.launcher(n) for n in range(3)}, "sid")
        run_ids = [run_id for _, _, run_id in recorder.calls]
        self.assertEqual(len(set(run_ids)), 6)
        for run_id in run_ids:
            self.assertEqual((runs_root / run_id / "summary.json").read_text(), run_id)
        self.assertEqual(outcome.entries[0].verdict, "pass")

    def test_mouse_scenarios_are_exclusive(self):
        from runlib.scenario import is_exclusive
        self.assertTrue(is_exclusive("place-building"))
        self.assertTrue(is_exclusive("probe-steer"))
        self.assertFalse(is_exclusive("smoke"))
        self.assertFalse(is_exclusive("no-such-scenario"))

    def test_no_slot_is_a_clear_error(self):
        with self.assertRaisesRegex(ValueError, "at least one game slot"):
            run_suite_parallel(make_suite([entry("a")]), {}, "sid")


if __name__ == "__main__":
    unittest.main()
