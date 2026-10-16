"""Tests for scenario discovery in mod/<Name>/scenarios (spec 22)."""

import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib import scenario

SCENARIO_TEXT = '''"""A test scenario of a mod."""
NAME = "{name}"
LIMIT_S = 30


def run(ctx):
    return ctx.result()
'''


class ModScenarioTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.mod_root = Path(folder.name)
        self.before = (dict(scenario.SCENARIOS), dict(scenario.SCENARIO_INFO), dict(scenario.SCENARIO_SOURCE))
        self.addCleanup(self.restore)

    def restore(self):
        for registry, saved in zip((scenario.SCENARIOS, scenario.SCENARIO_INFO, scenario.SCENARIO_SOURCE), self.before):
            registry.clear()
            registry.update(saved)

    def write(self, relative, name):
        path = self.mod_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(SCENARIO_TEXT.format(name=name), encoding="utf-8")

    def test_scenarios_in_nested_feature_folders_are_found(self):
        self.write("Demo/scenarios/alpha/first.py", "demo-first")
        self.write("Demo/scenarios/beta/deep/second.py", "demo-second")
        scenario.load_mod_scenarios(self.mod_root)
        self.assertIn("demo-first", scenario.SCENARIOS)
        self.assertIn("demo-second", scenario.SCENARIOS)
        self.assertEqual(scenario.get_limit_s("demo-first"), 30)
        self.assertEqual(scenario.SCENARIO_INFO["demo-first"].summary, "A test scenario of a mod.")

    def test_files_that_start_with_an_underscore_are_not_scenarios(self):
        self.write("Demo/scenarios/_helper.py", "demo-helper")
        scenario.load_mod_scenarios(self.mod_root)
        self.assertNotIn("demo-helper", scenario.SCENARIOS)

    def test_other_folders_of_a_mod_are_not_searched(self):
        self.write("Demo/Scripts/other.py", "demo-other")
        scenario.load_mod_scenarios(self.mod_root)
        self.assertNotIn("demo-other", scenario.SCENARIOS)

    def test_loading_twice_does_not_fail(self):
        self.write("Demo/scenarios/a/first.py", "demo-first")
        scenario.load_mod_scenarios(self.mod_root)
        scenario.load_mod_scenarios(self.mod_root)

    def test_a_duplicate_name_between_two_mods_fails_loudly(self):
        self.write("One/scenarios/a/x.py", "demo-same")
        self.write("Two/scenarios/b/y.py", "demo-same")
        with self.assertRaisesRegex(ValueError, "defined twice.*unique"):
            scenario.load_mod_scenarios(self.mod_root)

    def test_a_name_that_a_harness_scenario_has_fails_loudly(self):
        self.write("Demo/scenarios/a/x.py", "smoke")
        with self.assertRaisesRegex(ValueError, "'smoke' is defined twice"):
            scenario.load_mod_scenarios(self.mod_root)


if __name__ == "__main__":
    unittest.main()
