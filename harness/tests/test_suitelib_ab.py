"""A/B variants: suite file, interleaved runner, statistics in the report, expectations and the launcher (spec 10, U4).

The stochastic runs are simulated by a seeded stand-in. No game and no run.py are started.
"""

import json
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
import suite as suite_cli
from suitelib import report
from suitelib.launcher import SubprocessLauncher, variant_arguments
from suitelib.runner import run_suite
from suitelib.suitefile import Expectation, SuiteFileError, Variant, load_suite, parse_suite
from suitelib_fakes import FakeClock, make_suite, result

STUB = Path(__file__).resolve().parent / "stub_launcher.py"
SUITES_DIR = Path(__file__).resolve().parent.parent / "suites"


class StochasticRunOne:
    """A seeded stand-in for run.py. Each variant has its own mean for the metric `ticks`."""

    def __init__(self, means, spread=2.0, seed=7):
        self.means, self.spread = means, spread
        self.generator = random.Random(seed)
        self.calls = []

    def __call__(self, scenario, run_id, fixture, variant=None):
        name = variant.name if variant else "default"
        self.calls.append((name, run_id))
        ticks = self.generator.gauss(self.means[name], self.spread)
        losses = self.generator.gauss(50, 5)  # the same for all variants
        return result(run_id, "pass", 40.0 + self.generator.random(), metrics={"ticks": ticks, "losses": losses})


def ab_entry(repeat, expect=None, names=("A", "B")):
    from suitelib.suitefile import SuiteEntry
    return SuiteEntry("smoke", repeat, variants=tuple(Variant(name) for name in names), expect=expect)


def run_ab(means, repeat=8, expect=None, names=("A", "B"), seed=7):
    fake = StochasticRunOne(means, seed=seed)
    clock = FakeClock()
    outcome = run_suite(make_suite([ab_entry(repeat, expect, names)], retries=0), fake, "sid", clock=clock)
    return outcome, fake, report.build_report(outcome, {})


def comparison_of(data, metric):
    return next(item for item in data["ab"][0]["compared"] if item["metric"] == metric)


class SuiteFileVariantTest(unittest.TestCase):
    def parse(self, entry):
        return parse_suite({"name": "t", "scenarios": [entry], "time_budget_s": 10})

    def test_variants_and_expect_are_parsed(self):
        suite = self.parse({"scenario": "s", "repeat": 3, "variants": [{"name": "a"}, {"name": "b", "paks": ["demo"], "env": {"X": "1"}}],
                            "expect": {"metric": "ticks", "direction": "lower", "min_rel_diff": 0.2}})
        entry = suite.entries[0]
        self.assertEqual(entry.variants[1], Variant("b", ("demo",), {"X": "1"}))
        self.assertEqual(entry.expect, Expectation("ticks", "lower", 0.2))

    def test_no_variants_is_the_old_format(self):
        entry = self.parse({"scenario": "s"}).entries[0]
        self.assertEqual((entry.variants, entry.has_variants, entry.run_variants), ((), False, (None,)))

    def test_bad_files_are_refused(self):
        bad = [
            {"scenario": "s", "variants": []},
            {"scenario": "s", "variants": [{"name": "a"}, {"name": "a"}]},
            {"scenario": "s", "variants": [{"name": "bad name"}]},
            {"scenario": "s", "variants": [{"name": "a", "env": {"PATH": "x"}}]},
            {"scenario": "s", "variants": [{"name": "a", "env": {"X": 1}}]},
            {"scenario": "s", "variants": [{"name": "a", "paks": ["../x"]}]},
            {"scenario": "s", "variants": [{"name": "a", "color": 1}]},
            {"scenario": "s", "variants": [{"name": "a"}], "expect": {"metric": "m", "direction": "lower"}},
            {"scenario": "s", "variants": [{"name": "a"}, {"name": "b"}], "expect": {"metric": "m", "direction": "sideways"}},
            {"scenario": "s", "variants": [{"name": "a"}, {"name": "b"}], "expect": {"metric": "m", "direction": "lower", "min_rel_diff": -1}},
        ]
        for entry in bad:
            with self.subTest(entry=entry), self.assertRaises(SuiteFileError):
                self.parse(entry)

    def test_the_example_suite_is_valid_and_has_env_only(self):
        suite = load_suite("ab-example", SUITES_DIR)
        variants = suite.entries[0].variants
        self.assertEqual([v.name for v in variants], ["baseline", "flag-on"])
        self.assertTrue(all(not v.paks for v in variants))
        self.assertTrue(variants[1].env)


class InterleaveTest(unittest.TestCase):
    def test_variants_alternate_and_run_ids_name_the_variant(self):
        _, fake, _ = run_ab({"A": 100, "B": 100}, repeat=3)
        self.assertEqual([name for name, _ in fake.calls], ["A", "B", "A", "B", "A", "B"])
        self.assertIn("-smoke-B", fake.calls[1][1])

    def test_old_three_argument_callable_still_works_without_variants(self):
        from suitelib_fakes import FakeRunOne, entry
        outcome = run_suite(make_suite([entry("a", 2)]), FakeRunOne({}), "sid")
        self.assertEqual(outcome.entries[0].variant_names, ["default", "default"])


class AbStatisticsTest(unittest.TestCase):
    def test_identical_distributions_are_same(self):
        _, _, data = run_ab({"A": 100, "B": 100})
        self.assertEqual(comparison_of(data, "ticks")["verdict"], "same")
        self.assertEqual(data["notes"], ["ab: different on 0 metrics"])
        self.assertEqual(data["exit_code"], 0)

    def test_shifted_distributions_are_different(self):
        _, _, data = run_ab({"A": 100, "B": 120})
        self.assertEqual(comparison_of(data, "ticks")["verdict"], "different")
        self.assertEqual(comparison_of(data, "losses")["verdict"], "same")
        self.assertEqual(data["notes"], ["ab: different on 1 metrics"])
        self.assertEqual(data["exit_code"], 0, "a difference alone does not change pass or fail")

    def test_two_runs_per_variant_are_inconclusive(self):
        _, _, data = run_ab({"A": 100, "B": 200}, repeat=2)
        self.assertEqual(comparison_of(data, "ticks")["verdict"], "inconclusive")

    def test_report_lists_variants_and_stays_small(self):
        _, _, data = run_ab({"A": 100, "B": 120}, repeat=10)
        self.assertEqual([item["name"] for item in data["scenarios"][0]["variants"]], ["A", "B"])
        self.assertEqual(data["scenarios"][0]["variants"][0]["runs"], 10)
        self.assertLess(len(report.render_json(data).encode()), report.MAX_AB_REPORT_JSON_BYTES)

    def test_only_the_eight_strongest_metrics_are_reported(self):
        from suitelib.runresult import RunResult
        generator = random.Random(3)

        def many_metrics(scenario, run_id, fixture, variant=None):
            shift = 5.0 if variant.name == "B" else 0.0
            metrics = {f"m{i}": generator.gauss(10 * i + shift * i, 1.0) for i in range(12)}
            return RunResult(run_id, "pass", 40.0, metrics=metrics)

        outcome = run_suite(make_suite([ab_entry(6)], retries=0), many_metrics, "sid")
        data = report.build_report(outcome, {})
        self.assertEqual(len(data["ab"][0]["compared"]), 8)
        self.assertLess(len(report.render_json(data).encode()), report.MAX_AB_REPORT_JSON_BYTES)
        self.assertEqual(data["notes"], ["ab: different on 11 metrics"], "the note counts all metrics, not only the 8 shown")

    def test_markdown_has_an_ab_table(self):
        _, _, data = run_ab({"A": 100, "B": 120})
        text = report.render_markdown(data)
        self.assertIn("## A/B: smoke (reference: A)", text)
        self.assertIn("| B | ticks | different |", text)
        self.assertIn("heuristics for small samples", text)

    def test_a_failed_run_gives_no_values(self):
        fake = StochasticRunOne({"A": 100, "B": 100})

        def sometimes_fail(scenario, run_id, fixture, variant=None):
            outcome = fake(scenario, run_id, fixture, variant)
            return result(run_id, "fail", 40.0, metrics={"ticks": 9999}) if len(fake.calls) == 2 else outcome

        outcome = run_suite(make_suite([ab_entry(5)], retries=0), sometimes_fail, "sid")
        data = report.build_report(outcome, {})
        self.assertEqual(comparison_of(data, "ticks")["n"], [5, 4])
        self.assertEqual(data["exit_code"], 1)


class ExpectationTest(unittest.TestCase):
    def test_met_expectation_passes(self):
        expect = Expectation("ticks", "lower", 0.1)
        _, _, data = run_ab({"A": 100, "B": 80}, expect=expect)
        self.assertTrue(data["ab"][0]["expect"]["met"])
        self.assertEqual(data["exit_code"], 0)

    def test_wrong_direction_fails_with_exit_code_1(self):
        _, _, data = run_ab({"A": 100, "B": 120}, expect=Expectation("ticks", "lower", 0.1))
        self.assertFalse(data["ab"][0]["expect"]["met"])
        self.assertIn("went up", data["ab"][0]["expect"]["reason"])
        self.assertEqual((data["exit_code"], data["verdict"]), (1, "fail"))

    def test_too_small_a_difference_fails(self):
        _, _, data = run_ab({"A": 100, "B": 90}, expect=Expectation("ticks", "lower", 0.5))
        self.assertIn("smaller than", data["ab"][0]["expect"]["reason"])
        self.assertEqual(data["exit_code"], 1)

    def test_no_difference_fails(self):
        _, _, data = run_ab({"A": 100, "B": 100}, expect=Expectation("ticks", "lower", 0.1))
        self.assertEqual(data["exit_code"], 1)

    def test_inconclusive_fails(self):
        _, _, data = run_ab({"A": 100, "B": 50}, repeat=2, expect=Expectation("ticks", "lower", 0.1))
        self.assertIn("inconclusive", data["ab"][0]["expect"]["reason"])
        self.assertEqual(data["exit_code"], 1)

    def test_missing_metric_fails(self):
        _, _, data = run_ab({"A": 100, "B": 80}, expect=Expectation("nothing", "lower", 0.1))
        self.assertIn("missing", data["ab"][0]["expect"]["reason"])
        self.assertEqual(data["exit_code"], 1)

    def test_markdown_shows_the_expectation(self):
        _, _, data = run_ab({"A": 100, "B": 120}, expect=Expectation("ticks", "lower", 0.1))
        self.assertIn("NOT MET", report.render_markdown(data))


class LauncherVariantTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        plan = {"smoke": [{"duration_s": 12.0, "asserts": [{"name": "kills", "ok": True, "value": 3}], "metrics": {"ticks": 77, "kills": 5, "bad": "x"}}]}
        (self.root / "plan.json").write_text(json.dumps(plan))
        patch = {"HARNESS_STUB_PLAN": str(self.root / "plan.json"), "HARNESS_STUB_STATE": str(self.root / "state.json")}
        os.environ.update(patch)
        self.addCleanup(lambda: [os.environ.pop(key, None) for key in patch])

    def test_arguments_of_a_variant(self):
        self.assertEqual(variant_arguments(None), [])
        variant = Variant("v", ("demo", "other"), {"X": "a b", "Y": "2"})
        self.assertEqual(variant_arguments(variant), ["--pak", "demo", "--pak", "other", "--env", "X=a b", "--env", "Y=2"])

    def test_launcher_passes_options_and_reads_metrics_json(self):
        launcher = SubprocessLauncher(self.root / "runs", [sys.executable, str(STUB)], run_timeout_s=30)
        found = launcher("smoke", "run-1", None, Variant("v", ("demo",), {"X": "1"}))
        sent = json.loads((self.root / "runs" / "run-1" / "summary.json").read_text())["stub_args"]
        self.assertEqual(sent, {"pak": ["demo"], "env": ["X=1"]})
        self.assertEqual(found.metrics["ticks"], 77.0)
        self.assertEqual(found.metrics["kills"], 5.0, "metrics.json wins over an assert of the same name")
        self.assertEqual(found.metrics["duration_s"], 12.0)
        self.assertNotIn("bad", found.metrics)

    def test_launcher_without_a_variant_sends_no_options(self):
        launcher = SubprocessLauncher(self.root / "runs", [sys.executable, str(STUB)], run_timeout_s=30)
        launcher("smoke", "run-2")
        sent = json.loads((self.root / "runs" / "run-2" / "summary.json").read_text())["stub_args"]
        self.assertEqual(sent, {"pak": [], "env": []})


class SuiteCliAbTest(unittest.TestCase):
    def test_a_suite_with_a_missed_expectation_exits_with_1(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            suites = root / "suites"
            suites.mkdir()
            suite = {"name": "abx", "time_budget_s": 600, "flake_retries": 0, "scenarios": [
                {"scenario": "smoke", "repeat": 4, "variants": [{"name": "a"}, {"name": "b", "env": {"X": "1"}}],
                 "expect": {"metric": "ticks", "direction": "lower", "min_rel_diff": 0.1}}]}
            (suites / "abx.json").write_text(json.dumps(suite))
            # The stub gives every run the same value, so the variants cannot differ.
            plan = {"smoke": [{"duration_s": 10.0, "metrics": {"ticks": 100}}]}
            (root / "plan.json").write_text(json.dumps(plan))
            os.environ.update({"HARNESS_STUB_PLAN": str(root / "plan.json"), "HARNESS_STUB_STATE": str(root / "state.json")})
            self.addCleanup(lambda: [os.environ.pop(key, None) for key in ("HARNESS_STUB_PLAN", "HARNESS_STUB_STATE")])
            code = suite_cli.main(["--suite", "abx", "--suites-dir", str(suites), "--runs-root", str(root / "runs"),
                                   "--baselines-dir", str(root / "baselines"), "--launcher-command", f'"{sys.executable}" "{STUB}"'])
            self.assertEqual(code, 1)
            data = json.loads(next((root / "runs").glob("suite-*/report.json")).read_text())
            self.assertFalse(data["ab"][0]["expect"]["met"])


if __name__ == "__main__":
    unittest.main()
