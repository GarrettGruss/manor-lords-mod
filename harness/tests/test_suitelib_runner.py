import unittest

import runlib_path  # noqa: F401
from suitelib.runner import STOP_ITERATION_CAP, STOP_TIME_BUDGET, run_suite
from suitelib_fakes import FakeClock, FakeRunOne, entry, make_suite, result


class RunnerTest(unittest.TestCase):
    def run_it(self, entries, script, retries=1, budget=1000.0, cost_s=1.0, **kwargs):
        clock = FakeClock()
        fake = FakeRunOne(script, clock=clock, cost_s=cost_s)
        outcome = run_suite(make_suite(entries, budget, retries), fake, "sid", clock=clock, **kwargs)
        return outcome, fake

    def test_all_pass(self):
        outcome, fake = self.run_it([entry("a", 2), entry("b")], {})
        self.assertEqual([e.verdict for e in outcome.entries], ["pass", "pass"])
        self.assertEqual(len(fake.calls), 3)
        self.assertIsNone(outcome.stop_reason)
        self.assertFalse(any(e.flaky for e in outcome.entries))
        self.assertEqual(len({c[1] for c in fake.calls}), 3, "run ids are unique")

    def test_fixture_is_passed(self):
        _, fake = self.run_it([entry("a", fixture="base")], {})
        self.assertEqual(fake.calls[0][2], "base")

    def test_failure_is_retried_then_final(self):
        outcome, fake = self.run_it([entry("a")], {"a": ["fail"]}, retries=2)
        self.assertEqual(len(fake.calls), 3)
        self.assertEqual(outcome.entries[0].verdict, "fail")
        self.assertFalse(outcome.entries[0].flaky)

    def test_flaky_when_retry_passes(self):
        outcome, _ = self.run_it([entry("a")], {"a": ["fail", "pass"]})
        item = outcome.entries[0]
        self.assertEqual(item.verdict, "pass")
        self.assertTrue(item.flaky)
        self.assertEqual(len(item.attempts), 2)

    def test_no_retry_without_flake_retries(self):
        _, fake = self.run_it([entry("a")], {"a": ["fail"]}, retries=0)
        self.assertEqual(len(fake.calls), 1)

    def test_harness_error_is_not_retried(self):
        outcome, fake = self.run_it([entry("a")], {"a": ["harness_error"]})
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(outcome.entries[0].verdict, "harness_error")

    def test_crash_and_exception_do_not_stop_the_suite(self):
        script = {"a": ["crash"], "b": [RuntimeError("boom")], "c": ["pass"]}
        outcome, _ = self.run_it([entry("a"), entry("b"), entry("c")], script, retries=0)
        self.assertEqual([e.verdict for e in outcome.entries], ["crash", "harness_error", "pass"])
        self.assertIn("boom", outcome.entries[1].attempts[0].reason)

    def test_time_budget_stops_and_names_the_rest(self):
        outcome, fake = self.run_it([entry("a", 2), entry("b"), entry("c")], {}, budget=2.5)
        self.assertEqual(outcome.stop_reason, STOP_TIME_BUDGET)
        self.assertEqual(len(fake.calls), 3)
        self.assertEqual(outcome.not_run, ["c"])

    def test_max_seconds_lowers_the_budget(self):
        outcome, fake = self.run_it([entry("a", 5)], {}, max_seconds=2.0)
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual(outcome.budget_s, 2.0)
        self.assertEqual(outcome.stop_reason, STOP_TIME_BUDGET)

    def test_iteration_cap_stops_without_counting_a_result(self):
        capped = result("x", "harness_error", iteration_cap=True)
        outcome, fake = self.run_it([entry("a"), entry("b"), entry("c")], {"b": [capped]})
        self.assertEqual(outcome.stop_reason, STOP_ITERATION_CAP)
        self.assertEqual([e.entry.scenario for e in outcome.entries], ["a"])
        self.assertEqual(sorted(outcome.not_run), ["b", "c"])
        self.assertEqual(len(fake.calls), 2)

    def test_optional_missing_scenario_is_skipped(self):
        unknown = result("x", "harness_error", unknown_scenario=True)
        entries = [entry("a"), entry("later", 2, optional=True), entry("b")]
        outcome, fake = self.run_it(entries, {"later": [unknown]})
        self.assertEqual([e.verdict for e in outcome.entries], ["pass", "skipped", "pass"])
        self.assertIn("later", outcome.entries[1].skipped_note)
        self.assertEqual(len([c for c in fake.calls if c[0] == "later"]), 1)
        self.assertEqual(outcome.not_run, [])

    def test_required_missing_scenario_is_a_harness_error(self):
        unknown = result("x", "harness_error", unknown_scenario=True)
        outcome, _ = self.run_it([entry("later")], {"later": [unknown]})
        self.assertEqual(outcome.entries[0].verdict, "harness_error")


if __name__ == "__main__":
    unittest.main()
