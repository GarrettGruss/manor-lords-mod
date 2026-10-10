"""Unit tests for harness/tools/coverage.py. Fake scenario files and run folders in temp folders."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import coverage  # noqa: E402


def make_criterion(cid, mark="A", **changes):
    item = {"id": cid, "title": f"title {cid}", "pillar": "threat", "mark": mark, "method": "do it",
            "blocked_by": None, "spikes": [], "upgrades": [], "method_verified": False,
            "verified_by": [], "reason_human": "people judge it" if mark == "H" else ""}
    item.update(changes)
    return item


class TempCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.scenarios = self.root / "scenarios"
        self.scenarios.mkdir()
        self.runs = self.root / "runs"
        self.runs.mkdir()

    def write_scenario(self, filename, text):
        (self.scenarios / filename).write_text(text, encoding="utf-8")

    def write_run(self, folder, scenario, verdict, started):
        run_dir = self.runs / folder
        run_dir.mkdir()
        summary = {"run_id": folder, "scenario": scenario, "verdict": verdict, "started": started}
        (run_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")

    def write_criteria(self, items):
        path = self.root / "criteria.json"
        path.write_text(json.dumps(items), encoding="utf-8")
        return path

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = coverage.main([str(a) for a in args])
        return code, out.getvalue(), err.getvalue()

    def common_args(self, criteria_path):
        return ["--criteria", criteria_path, "--scenarios", self.scenarios, "--runs-root", self.runs]


class ArithmeticTest(unittest.TestCase):
    def test_shares_and_blocked(self):
        criteria = [make_criterion("T1"), make_criterion("T2", method_verified=True),
                    make_criterion("O1", blocked_by="no outposts"), make_criterion("T4", "P"),
                    make_criterion("Q3", "H")]
        result = coverage.compute(criteria, [], {})
        self.assertEqual(result["total"], 5)
        self.assertEqual(result["by_mark"], {"A": 3, "P": 1, "H": 1})
        self.assertAlmostEqual(result["automatable_share"], 0.8)
        self.assertEqual(result["verified"], 1)
        self.assertAlmostEqual(result["verified_share"], 0.25)
        self.assertEqual([b["id"] for b in result["blocked"]], ["O1"])
        self.assertEqual(result["gaps"], ["T1", "O1", "T4"])
        self.assertEqual(result["human"][0]["id"], "Q3")

    def test_no_automatable_criteria_gives_zero_share(self):
        result = coverage.compute([make_criterion("Q3", "H")], [], {})
        self.assertEqual(result["verified_share"], 0.0)

    def test_scenario_without_passing_run_is_not_verified_but_not_a_gap(self):
        scenarios = [{"name": "s", "file": "s.py", "covers": ["T1"]}]
        result = coverage.compute([make_criterion("T1")], scenarios, {})
        self.assertEqual(result["verified"], 0)
        self.assertEqual(result["gaps"], [])

    def test_scenario_with_passing_run_verifies(self):
        scenarios = [{"name": "s", "file": "s.py", "covers": ["T1"]}]
        result = coverage.compute([make_criterion("T1")], scenarios, {"s": "run1"})
        self.assertEqual(result["verified_ids"], ["T1"])
        self.assertEqual(result["scenarios"][0]["last_passing_run"], "run1")

    def test_unknown_cover_id_is_reported(self):
        scenarios = [{"name": "s", "file": "s.py", "covers": ["X9"]}]
        result = coverage.compute([make_criterion("T1")], scenarios, {"s": "run1"})
        self.assertEqual(result["unknown_covers"], [{"scenario": "s.py", "id": "X9"}])
        self.assertEqual(result["verified"], 0)


class ValidationTest(unittest.TestCase):
    def test_human_needs_reason(self):
        problems = coverage.validate_criteria([make_criterion("Q3", "H", reason_human="")])
        self.assertTrue(any("reason_human" in p for p in problems))

    def test_automatable_needs_method(self):
        problems = coverage.validate_criteria([make_criterion("T1", method="")])
        self.assertTrue(any("method" in p for p in problems))

    def test_bad_mark_duplicate_and_missing_field(self):
        broken = make_criterion("T2")
        del broken["spikes"]
        problems = coverage.validate_criteria([make_criterion("T1", "Z"), make_criterion("T1"), broken])
        text = "\n".join(problems)
        self.assertIn("mark must be", text)
        self.assertIn("duplicate id", text)
        self.assertIn("missing fields", text)


class ScenarioParsingTest(TempCase):
    def test_covers_and_name_are_read(self):
        self.write_scenario("a.py", 'NAME = "alpha"\nCOVERS = ["T1", "T2"]\n')
        self.assertEqual(coverage.read_scenarios(self.scenarios),
                         [{"name": "alpha", "covers": ["T1", "T2"], "file": "a.py"}])

    def test_module_without_covers_is_ignored(self):
        self.write_scenario("b.py", "def run(ctx):\n    return 1\n")
        info = coverage.read_scenarios(self.scenarios)[0]
        self.assertEqual(info["covers"], [])
        self.assertEqual(info["name"], "b")

    def test_module_is_never_executed(self):
        marker = self.root / "executed.txt"
        self.write_scenario("c.py", f'open({str(marker)!r}, "w").write("x")\nCOVERS = ["T1"]\n')
        coverage.read_scenarios(self.scenarios)
        self.assertFalse(marker.exists())

    def test_syntax_error_gives_clear_error(self):
        self.write_scenario("d.py", "def broken(:\n")
        with self.assertRaises(coverage.InputError) as caught:
            coverage.read_scenarios(self.scenarios)
        self.assertIn("d.py", str(caught.exception))

    def test_covers_that_is_not_a_literal_list_is_an_error(self):
        self.write_scenario("e.py", "COVERS = make_list()\n")
        with self.assertRaises(coverage.InputError):
            coverage.read_scenarios(self.scenarios)


class LastPassingRunTest(TempCase):
    def test_only_pass_counts_and_newest_wins(self):
        self.write_run("r1", "s", "pass", "2026-01-01T00:00:00Z")
        self.write_run("r2", "s", "pass", "2026-02-01T00:00:00Z")
        self.write_run("r3", "s", "fail", "2026-03-01T00:00:00Z")
        self.write_run("r4", "other", "crash", "2026-03-01T00:00:00Z")
        self.assertEqual(coverage.last_passing_runs(self.runs), {"s": "r2"})

    def test_broken_summary_is_skipped(self):
        (self.runs / "bad").mkdir()
        (self.runs / "bad" / "summary.json").write_text("{not json", encoding="utf-8")
        self.write_run("r1", "s", "pass", "2026-01-01T00:00:00Z")
        self.assertEqual(coverage.last_passing_runs(self.runs), {"s": "r1"})

    def test_missing_runs_folder_is_empty(self):
        self.assertEqual(coverage.last_passing_runs(self.root / "nothing"), {})


class CommandLineTest(TempCase):
    def setUp(self):
        super().setUp()
        self.criteria = self.write_criteria([make_criterion("T1"), make_criterion("T2"), make_criterion("Q3", "H")])
        self.write_scenario("a.py", 'NAME = "alpha"\nCOVERS = ["T1"]\n')
        self.write_run("r1", "alpha", "pass", "2026-01-01T00:00:00Z")

    def test_report_headline(self):
        code, out, _ = self.run_main(*self.common_args(self.criteria))
        self.assertEqual(code, 0)
        self.assertIn("verified share of A and P criteria = 50% (target 90%)", out)
        self.assertIn("blocked criteria count against the target: 0", out)

    def test_json_shape(self):
        code, out, _ = self.run_main(*self.common_args(self.criteria), "--json")
        data = json.loads(out)
        self.assertEqual(code, 0)
        for key in ("total", "by_mark", "automatable_share", "verified", "verified_share", "blocked",
                    "human", "unknown_covers", "gaps", "scenarios", "target"):
            self.assertIn(key, data)
        self.assertEqual(data["verified_ids"], ["T1"])

    def test_min_verified_exit_codes(self):
        self.assertEqual(self.run_main(*self.common_args(self.criteria), "--min-verified", "0.5")[0], 0)
        self.assertEqual(self.run_main(*self.common_args(self.criteria), "--min-verified", "0.9")[0], 1)

    def test_unknown_id_exits_with_2(self):
        self.write_scenario("b.py", 'COVERS = ["X9"]\n')
        code, out, _ = self.run_main(*self.common_args(self.criteria))
        self.assertEqual(code, 2)
        self.assertIn("unknown id X9", out)

    def test_bad_criteria_file_exits_with_2(self):
        bad = self.root / "bad.json"
        bad.write_text("[{}]", encoding="utf-8")
        code, _, err = self.run_main(*self.common_args(bad))
        self.assertEqual(code, 2)
        self.assertIn("missing fields", err)

    def test_unparsable_scenario_exits_with_2(self):
        self.write_scenario("bad.py", "def (:\n")
        code, _, err = self.run_main(*self.common_args(self.criteria))
        self.assertEqual(code, 2)
        self.assertIn("bad.py", err)


class RealCriteriaTest(TempCase):
    def test_real_file_is_valid(self):
        criteria = json.loads(coverage.DEFAULT_CRITERIA.read_text(encoding="utf-8"))
        self.assertEqual(coverage.validate_criteria(criteria), [])
        ids = [c["id"] for c in criteria]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(c["mark"] in coverage.MARKS for c in criteria))

    def test_real_file_agrees_with_real_spec(self):
        code, out, _ = self.run_main("--check-spec")
        self.assertEqual(code, 0, out)

    def test_broken_spec_copy_is_detected(self):
        text = coverage.DEFAULT_SPEC.read_text(encoding="utf-8")
        text = text.replace("| T2 | ", "| T9 | ", 1)  # an id that criteria.json lacks
        text = text.replace("| A | count units by side |", "| H | count units by side |", 1)  # another mark
        broken = self.root / "broken.md"
        broken.write_text(text, encoding="utf-8")
        code, out, _ = self.run_main("--check-spec", "--spec", broken)
        self.assertEqual(code, 1)
        self.assertIn("T9: in the spec but not in criteria.json", out)
        self.assertIn("T2: in criteria.json but not in the spec", out)

    def test_changed_mark_is_detected(self):
        text = coverage.DEFAULT_SPEC.read_text(encoding="utf-8")
        text = text.replace("| P | screenshot, plus", "| A | screenshot, plus", 1)
        broken = self.root / "broken.md"
        broken.write_text(text, encoding="utf-8")
        code, out, _ = self.run_main("--check-spec", "--spec", broken)
        self.assertEqual(code, 1)
        self.assertIn("T4: mark is P in criteria.json but A in the spec", out)


if __name__ == "__main__":
    unittest.main()
