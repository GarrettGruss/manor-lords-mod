import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import runlib_path  # noqa: F401
from suitelib import baselines, history, report
from suitelib.baselines import Baseline
from suitelib.runner import run_suite
from suitelib_fakes import FakeClock, FakeRunOne, entry, make_suite, result, summary


def outcome_for(entries, script, retries=1, budget=1000.0, cost_s=1.0):
    clock = FakeClock()
    fake = FakeRunOne(script, clock=clock, cost_s=cost_s)
    return run_suite(make_suite(entries, budget, retries), fake, "sid", clock=clock)


class ReportTest(unittest.TestCase):
    def build(self, outcome, findings=None, rates=None):
        return report.build_report(outcome, findings or {}, rates)

    def test_pass_report_of_10_scenarios_is_under_4_kb(self):
        entries = [entry(f"scenario-number-{i}", 2) for i in range(10)]
        data = self.build(outcome_for(entries, {}), rates={f"scenario-number-{i}": 0.0 for i in range(10)})
        self.assertEqual((data["verdict"], data["exit_code"]), ("pass", 0))
        self.assertLess(len(report.render_json(data).encode()), 4096)

    def test_soak_with_many_durations_stays_small(self):
        data = self.build(outcome_for([entry("smoke", 10)], {}))
        self.assertLess(len(report.render_json(data).encode()), 4096)
        self.assertEqual(data["totals"]["runs"], 10)

    def test_same_failed_assertion_in_a_retry_is_listed_once(self):
        same = [{"name": "ticks", "value": 0}]
        script = {"a": [result("r1", "fail", failed=same), result("r2", "fail", failed=same)]}
        data = self.build(outcome_for([entry("a")], script, retries=1))
        self.assertEqual(data["scenarios"][0]["failed"], [{"name": "ticks", "value": 0}])

    def test_long_failure_text_is_truncated(self):
        long_name, long_value = "n" * 500, "v" * 500
        bad = result("r", "fail", failed=[{"name": str(i) + long_name, "value": long_value} for i in range(20)])
        data = self.build(outcome_for([entry("a")], {"a": [bad]}, retries=0))
        item = data["scenarios"][0]
        self.assertEqual(len(item["failed"]), report.MAX_FAILED_ASSERTS)
        self.assertLessEqual(len(item["failed"][0]["name"]), report.MAX_TEXT_CHARS)
        self.assertLessEqual(len(item["failed"][0]["value"]), report.MAX_TEXT_CHARS)
        self.assertLess(len(report.render_json(data).encode()), 4096)

    def test_fail_report_names_run_and_exit_code(self):
        bad = result("r1", "fail", failed=[{"name": "clock moves", "value": 0}])
        data = self.build(outcome_for([entry("a"), entry("b")], {"a": [bad]}, retries=0))
        self.assertEqual((data["verdict"], data["exit_code"]), ("fail", 1))
        self.assertEqual(data["scenarios"][0]["failed"], [{"name": "clock moves", "value": 0}])
        self.assertEqual(data["scenarios"][0]["failed_runs"], ["r1"])
        self.assertIn("clock moves = 0", report.render_markdown(data))

    def test_flaky_pass_exits_zero_and_is_listed(self):
        data = self.build(outcome_for([entry("a")], {"a": ["fail", "pass"]}))
        self.assertEqual(data["exit_code"], 0)
        self.assertEqual(data["totals"]["flaky"], 1)
        self.assertEqual(data["scenarios"][0]["stability"], "flaky")
        self.assertEqual(len(data["scenarios"][0]["failed_runs"]), 1)

    def test_crash_exit_code_and_others_still_reported(self):
        data = self.build(outcome_for([entry("a"), entry("b")], {"a": ["crash"]}, retries=0))
        self.assertEqual(data["exit_code"], 2)
        self.assertEqual([s["verdict"] for s in data["scenarios"]], ["crash", "pass"])

    def test_budget_exit_code_and_text(self):
        data = self.build(outcome_for([entry("a"), entry("b")], {}, budget=0.5))
        self.assertEqual((data["exit_code"], data["verdict"]), (3, "incomplete"))
        self.assertIn("time budget", data["stopped"])
        self.assertEqual(data["not_run"], ["b"])
        self.assertIn("Stopped", report.render_markdown(data))

    def test_iteration_cap_text(self):
        capped = result("x", "harness_error", iteration_cap=True)
        data = self.build(outcome_for([entry("a"), entry("b")], {"b": [capped]}))
        self.assertEqual(data["exit_code"], 3)
        self.assertIn("iteration cap", data["stopped"])

    def test_harness_error_exit_code(self):
        data = self.build(outcome_for([entry("a")], {"a": ["harness_error"]}))
        self.assertEqual(data["exit_code"], 4)

    def test_skipped_optional_is_noted_and_does_not_fail(self):
        unknown = result("x", "harness_error", unknown_scenario=True)
        data = self.build(outcome_for([entry("a"), entry("later", optional=True)], {"later": [unknown]}))
        self.assertEqual(data["exit_code"], 0)
        self.assertEqual(data["scenarios"][1]["verdict"], "skipped")
        self.assertIn("later", data["skipped"][0])

    def test_write_report_makes_both_files(self):
        data = self.build(outcome_for([entry("a")], {}))
        with tempfile.TemporaryDirectory() as temp:
            json_path, markdown_path = report.write_report(data, Path(temp) / "suite-x")
            self.assertEqual(json.loads(json_path.read_text())["suite_id"], "sid")
            self.assertIn("| a | pass |", markdown_path.read_text())


class BaselineTest(unittest.TestCase):
    def test_proposal_math(self):
        summaries = [
            summary(duration=10, asserts=[{"name": "n", "ok": True, "value": 1}]),
            summary(duration=50, asserts=[{"name": "n", "ok": True, "value": 1}, {"name": "text", "ok": True, "value": "x"}]),
        ]
        proposal = baselines.propose_baseline(summaries, margin=0.2, scenario="smoke")
        # duration: spread 40, margin 8, floor 0.1*50 = 5, so the padding is 8.
        self.assertEqual(proposal["metrics"]["duration_s"], [2.0, 58.0])
        # constant metric: spread 0, so the floor 0.1 * 1 is used.
        self.assertEqual(proposal["metrics"]["n"], [0.9, 1.1])
        self.assertNotIn("text", proposal["metrics"])

    def test_floor_wins_for_small_spread(self):
        proposal = baselines.propose_baseline([summary(duration=100), summary(duration=102)])
        self.assertEqual(proposal["metrics"]["duration_s"], [89.8, 112.2])  # spread 2, margin 0.4, floor 10.2

    def test_proposal_without_metrics_is_refused(self):
        with self.assertRaises(baselines.BaselineError):
            baselines.propose_baseline([{"verdict": "pass"}])

    def test_compare_inside_below_above_missing_and_strict(self):
        base = Baseline("s", {"a": (10, 20), "b": (0, 1), "c": (5, 6)}, frozenset({"b"}))
        self.assertEqual(baselines.compare(base, {"a": 10, "b": 1, "c": 5.5}), [])
        findings = baselines.compare(base, {"a": 9.9, "b": 1.5})
        by_metric = {f.metric: f for f in findings}
        self.assertEqual(by_metric["a"].direction, "below")
        self.assertEqual(by_metric["b"].direction, "above")
        self.assertTrue(by_metric["b"].strict)
        self.assertFalse(by_metric["a"].strict)
        self.assertEqual(by_metric["c"].direction, "missing")
        self.assertEqual(baselines.compare(base, {"a": 21, "b": 0, "c": 6})[0].direction, "above")

    def test_malformed_baseline_is_refused(self):
        for data in ({}, {"metrics": {"a": [2, 1]}}, {"metrics": {"a": [1, 2]}, "strict": ["b"]}, {"metrics": {"a": 1}}):
            with self.assertRaises(baselines.BaselineError, msg=data):
                baselines.parse_baseline(data, "s")

    def test_write_and_load_keep_strict_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            path = baselines.baseline_path("s", Path(temp))
            path.write_text(json.dumps({"metrics": {"duration_s": [1, 2]}, "strict": ["duration_s"]}))
            baselines.write_baseline("s", baselines.propose_baseline([summary()]), Path(temp))
            loaded = baselines.load_baseline("s", Path(temp))
            self.assertEqual(loaded.strict, frozenset({"duration_s"}))
            self.assertIsNone(baselines.load_baseline("none", Path(temp)))


class DriftInReportTest(unittest.TestCase):
    """The deliberate regression: a metric moves out of its baseline range."""

    def drift_report(self, value, strict):
        base = Baseline("a", {"clock ticks": (90.0, 110.0)}, frozenset({"clock ticks"}) if strict else frozenset())
        good = result("r1", "pass", metrics={"clock ticks": value})
        outcome = outcome_for([entry("a")], {"a": [good]})
        findings = {"a": report.collect_drift(outcome.entries[0], base)}
        return report.build_report(outcome, findings)

    def test_inside_range_passes(self):
        data = self.drift_report(100, strict=False)
        self.assertEqual((data["verdict"], data["exit_code"]), ("pass", 0))
        self.assertEqual(data["scenarios"][0]["baseline"], "ok")

    def test_regression_is_reported_as_drift(self):
        data = self.drift_report(40, strict=False)
        self.assertEqual((data["verdict"], data["exit_code"]), ("drift", 0))
        self.assertEqual(data["scenarios"][0]["drift"][0]["direction"], "below")
        self.assertIn("drift clock ticks = 40", report.render_markdown(data))

    def test_regression_on_a_strict_metric_fails(self):
        data = self.drift_report(400, strict=True)
        self.assertEqual((data["verdict"], data["exit_code"]), ("fail", 1))

    def test_no_baseline_is_not_drift(self):
        outcome = outcome_for([entry("a")], {})
        self.assertIsNone(report.collect_drift(outcome.entries[0], None))

    def test_failed_runs_are_not_compared(self):
        base = Baseline("a", {"m": (1.0, 2.0)})
        outcome = outcome_for([entry("a")], {"a": [result("r", "fail", metrics={"m": 99})]}, retries=0)
        self.assertEqual(report.collect_drift(outcome.entries[0], base), [])


class HistoryTest(unittest.TestCase):
    def test_lines_and_flake_rate(self):
        outcome = outcome_for([entry("a"), entry("b")], {"a": ["fail", "pass"]})
        now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "runs" / "suite-history.jsonl"
            history.append_history(path, outcome, now)
            history.append_history(path, outcome, now)
            lines = path.read_text().splitlines()
            self.assertEqual(len(lines), 6)
            first = json.loads(lines[0])
            self.assertEqual(
                first, {"time": "2026-01-02T03:04:05Z", "suite": "t", "scenario": "a", "verdict": "fail", "duration_s": 10.0}
            )
            rows = history.read_history(path)
            self.assertEqual(history.flake_rate(rows, "a"), 0.5)
            self.assertEqual(history.flake_rate(rows, "b"), 0.0)
            self.assertIsNone(history.flake_rate(rows, "zzz"))
            self.assertEqual(history.flake_rate(rows, "a", window=1), 0.0)

    def test_harness_errors_do_not_count(self):
        rows = [{"scenario": "a", "verdict": "harness_error"}, {"scenario": "a", "verdict": "pass"}]
        self.assertEqual(history.flake_rate(rows, "a"), 0.0)

    def test_bad_line_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "h.jsonl"
            path.write_text("{\n")
            with self.assertRaises(ValueError):
                history.read_history(path)

    def test_missing_file_is_empty(self):
        self.assertEqual(history.read_history(Path("does-not-exist.jsonl")), [])


if __name__ == "__main__":
    unittest.main()
