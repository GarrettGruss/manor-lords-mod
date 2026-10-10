import json
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from suitelib.suitefile import SUITES_DIR, SuiteFileError, load_suite, parse_suite

GOOD = {
    "name": "core",
    "scenarios": [{"scenario": "smoke", "repeat": 2}, {"scenario": "time-advance", "fixture": "base", "optional": True}],
    "time_budget_s": 1800,
    "flake_retries": 1,
}


class ParseSuiteTest(unittest.TestCase):
    def test_good_file(self):
        suite = parse_suite(GOOD, "core")
        self.assertEqual(suite.name, "core")
        self.assertEqual(
            [(e.scenario, e.repeat, e.fixture, e.optional) for e in suite.entries],
            [("smoke", 2, None, False), ("time-advance", 1, "base", True)],
        )
        self.assertEqual((suite.time_budget_s, suite.flake_retries), (1800.0, 1))

    def test_retries_default_to_zero(self):
        data = {k: v for k, v in GOOD.items() if k != "flake_retries"}
        self.assertEqual(parse_suite(data).flake_retries, 0)

    def assert_error(self, change, text):
        data = json.loads(json.dumps(GOOD))
        change(data)
        with self.assertRaises(SuiteFileError) as caught:
            parse_suite(data)
        self.assertIn(text, str(caught.exception))

    def test_errors_are_clear(self):
        self.assert_error(lambda d: d.update(scenarios=[]), "non-empty list")
        self.assert_error(lambda d: d.update(time_budget_s=0), "time_budget_s")
        self.assert_error(lambda d: d.update(flake_retries=-1), "flake_retries")
        self.assert_error(lambda d: d.update(extra=1), "unknown key")
        self.assert_error(lambda d: d["scenarios"][0].update(repeat=0), "repeat")
        self.assert_error(lambda d: d["scenarios"][0].update(repeat=True), "repeat")
        self.assert_error(lambda d: d["scenarios"][0].update(scenario=""), "scenario")
        self.assert_error(lambda d: d["scenarios"][0].update(optional="yes"), "optional")
        self.assert_error(lambda d: d["scenarios"][1].update(fixture=3), "fixture")
        self.assert_error(lambda d: d["scenarios"].append(5), "must be an object")

    def test_name_must_match_file(self):
        with self.assertRaises(SuiteFileError):
            parse_suite(GOOD, "other")


class LoadSuiteTest(unittest.TestCase):
    def test_missing_file_lists_known_suites(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "a.json").write_text(json.dumps({**GOOD, "name": "a"}))
            with self.assertRaises(SuiteFileError) as caught:
                load_suite("b", Path(temp))
            self.assertIn("['a']", str(caught.exception))

    def test_bad_json(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "a.json").write_text("{")
            with self.assertRaises(SuiteFileError):
                load_suite("a", Path(temp))

    def test_shipped_suites_are_valid(self):
        for name, repeats in (("smoke", 1), ("core", 2), ("soak", 10)):
            self.assertEqual(load_suite(name, SUITES_DIR).entries[0].repeat, repeats)
        self.assertEqual([e.optional for e in load_suite("core").entries], [False, False, False])


if __name__ == "__main__":
    unittest.main()
