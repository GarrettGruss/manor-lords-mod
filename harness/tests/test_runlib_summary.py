import json
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib.summary import EXIT_CODES, PhaseResult, Summary, decide_verdict, write_summary

PASSED = {"passed": True}


def ok_phases(*extra):
    names = ["preflight", "deploy", "launch", "boot", "scenario", "collect", "teardown"]
    return [PhaseResult(name, "ok") for name in names] + list(extra)


def state(**overrides):
    base = {"boot": {"state": "READY"}, "scenario_result": PASSED, "crash": None}
    base.update(overrides)
    return base


class VerdictTest(unittest.TestCase):
    def verdict(self, phases, st):
        return decide_verdict(phases, st)[0]

    def test_pass(self):
        self.assertEqual(decide_verdict(ok_phases(), state()), ("pass", None))

    def test_pass_from_asserts_list(self):
        result = {"asserts": [{"name": "a", "ok": True}]}
        self.assertEqual(self.verdict(ok_phases(), state(scenario_result=result)), "pass")

    def test_failed_assert_is_fail(self):
        result = {"asserts": [{"name": "a", "ok": True}, {"name": "b", "ok": False}]}
        self.assertEqual(self.verdict(ok_phases(), state(scenario_result=result)), "fail")

    def test_boot_failed_is_fail(self):
        st = state(boot={"state": "FAILED", "reason": "slot missing"}, scenario_result=None)
        verdict, reason = decide_verdict(ok_phases(), st)
        self.assertEqual(verdict, "fail")
        self.assertIn("slot missing", reason)

    def test_crash(self):
        self.assertEqual(self.verdict(ok_phases(), state(crash={"reason": "died"})), "crash")

    def test_timeout(self):
        phases = [PhaseResult("boot", "timeout", 300, "slow")]
        self.assertEqual(self.verdict(phases, state(scenario_result=None)), "timeout")

    def test_error_is_harness_error(self):
        phases = [PhaseResult("preflight", "error", 0, "boom")]
        verdict, reason = decide_verdict(phases, state(boot=None, scenario_result=None))
        self.assertEqual(verdict, "harness_error")
        self.assertIn("boom", reason)

    def test_failed_deploy_is_harness_error(self):
        phases = [PhaseResult("deploy", "failed", 1, "hash mismatch")]
        self.assertEqual(self.verdict(phases, state(scenario_result=None)), "harness_error")

    def test_never_pass_with_skipped_phase(self):
        phases = ok_phases(PhaseResult("extra", "skipped"))
        self.assertEqual(self.verdict(phases, state()), "harness_error")

    def test_never_pass_without_scenario_result(self):
        for missing in (None, {}, {"asserts": []}):
            self.assertEqual(self.verdict(ok_phases(), state(scenario_result=missing)), "harness_error")

    def test_no_phases_is_harness_error(self):
        self.assertEqual(self.verdict([], state()), "harness_error")

    def test_precedence_crash_beats_timeout_and_error(self):
        phases = [PhaseResult("scenario", "error", 1, "lost"), PhaseResult("collect", "timeout", 9)]
        self.assertEqual(self.verdict(phases, state(crash={"reason": "died"})), "crash")

    def test_precedence_timeout_beats_fail_and_error(self):
        phases = [PhaseResult("scenario", "timeout", 9), PhaseResult("teardown", "error", 1)]
        st = state(scenario_result={"passed": False})
        self.assertEqual(self.verdict(phases, st), "timeout")

    def test_precedence_fail_beats_harness_error(self):
        phases = [PhaseResult("scenario", "failed", 1), PhaseResult("teardown", "error", 1)]
        self.assertEqual(self.verdict(phases, state(scenario_result={"passed": False})), "fail")

    def test_exit_codes(self):
        self.assertEqual(EXIT_CODES, {"pass": 0, "fail": 1, "crash": 2, "timeout": 3, "harness_error": 4})

    def test_bad_phase_status_is_refused(self):
        with self.assertRaises(ValueError):
            PhaseResult("x", "weird")


class WriteSummaryTest(unittest.TestCase):
    def make_summary(self, detail=None):
        phases = [PhaseResult("boot", "ok", 1, detail)]
        return Summary("id", "pass", None, "smoke", "2026-10-09T23:30:00Z", 1.0, phases)

    def test_atomic_write_leaves_no_tmp(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "summary.json"
            write_summary(path, self.make_summary())
            self.assertEqual(json.loads(path.read_text())["run_id"], "id")
            self.assertEqual(list(Path(temp).glob("*.tmp")), [])

    def test_long_detail_is_cut_under_4kb_with_a_note(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "summary.json"
            write_summary(path, self.make_summary("x" * 20000))
            data = json.loads(path.read_text())
            self.assertLess(path.stat().st_size, 4096)
            self.assertTrue(any("WARNING" in note for note in data["notes"]))
            self.assertIn("[cut]", data["phases"][0]["detail"])

    def test_small_summary_has_no_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "summary.json"
            write_summary(path, self.make_summary("short"))
            self.assertEqual(json.loads(path.read_text())["notes"], [])


if __name__ == "__main__":
    unittest.main()
