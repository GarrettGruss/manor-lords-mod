"""The scenario list of the MCP tools uses the real registry: descriptions shown, test-only scenarios hidden."""

import unittest
from pathlib import Path

import harness_tools_path  # noqa: F401  (puts mcp/ and harness/ on sys.path)
from harness_tools import tools


class ScenarioListTest(unittest.TestCase):
    def test_real_scenarios_have_descriptions(self):
        scenarios = tools.load_scenarios()
        self.assertIn("smoke", scenarios)
        for name, description in scenarios.items():
            self.assertTrue(description, f"scenario {name} has no description")
            self.assertNotEqual(description, "(no description)", f"scenario {name} has no description")

    def test_test_only_scenarios_are_hidden(self):
        names = set(tools.load_scenarios())
        self.assertFalse({n for n in names if n.startswith("selftest-")}, "self tests must not be listed")
        self.assertNotIn("probe-actions", names)

    def test_a_hidden_scenario_cannot_be_started_through_the_tool(self):
        result = tools.run_scenario(Path("does-not-exist"), Path("."), "selftest-crash")
        self.assertFalse(result["ok"])
        self.assertIn("Unknown scenario", result["error"])


if __name__ == "__main__":
    unittest.main()
