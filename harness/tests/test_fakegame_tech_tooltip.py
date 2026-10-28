"""Tests for the tooltip text builder of the tech tree menu (change add-tech-tooltip). Pure Lua, run through lupa."""

import json
import unittest

import fakegame_path  # noqa: F401
from lupa import LuaRuntime
from test_fakegame_modstate import find_pack_mod

PACK = find_pack_mod()
TREE_FILE = PACK / "data" / "tech_tree" / "tree.json"


class TooltipTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime()
        self.lua.execute(f'package.path = "{(PACK / "Scripts").as_posix()}/?.lua;{(PACK.parent / "shared").as_posix()}/?/?.lua;" .. package.path')
        self.lines = self.lua.execute('return (require("features.tech_tree_widget.lines"))')
        loader = self.lua.execute('return (require("features.tech_tree.tree"))')
        decoded = self.lua.execute('return (require("HarnessJson"))').decode(TREE_FILE.read_text(encoding="utf-8"))
        self.tree = loader.build(decoded)
        self.doc = json.loads(TREE_FILE.read_text(encoding="utf-8"))

    def text_of(self, source) -> list:
        return str(self.lines.effect_lines(source, self.tree)).split("\n")

    def test_percent_effect(self):
        self.assertIn("Militia attack +10%", self.text_of(self.tree.by_id["militia_rights"]))
        self.assertIn("Buy-back price -50%", self.text_of(self.tree.by_id["amnesty"]))
        self.assertIn("Tribute share -25%", self.text_of(self.tree.laws_by_id["scorched_earth"]))

    def test_flat_effect(self):
        self.assertIn("Public Order +10", self.text_of(self.tree.by_id["martial_law"]))
        self.assertIn("Approval -5", self.text_of(self.tree.laws_by_id["conscription"]))

    def test_several_effects_and_condition(self):
        self.assertEqual(self.text_of(self.tree.by_id["iron_hand"])[:3],
                         ["Public Order +15", "Buy-back price +25%", "Manor storage capacity +200"])
        self.assertIn("Public Order +25 (needs at least 4 garrison squads)", self.text_of(self.tree.by_id["fear_of_the_lord"]))

    def test_decimal_percent(self):
        self.assertEqual(self.lines.effect_line(self.lua.table_from({"kind": "tribute_share", "value": 0.025}), self.lua.table_from({"tribute_share": "percent"})),
                         "Tribute share +2.5%")

    def test_common_law_effects_have_a_text_without_a_number_error(self):
        # The laws strip and the common law tooltips show these (flag and factor kinds). A factor shows its value.
        self.assertEqual(self.text_of(self.tree.laws_by_id["strip_the_dead"]), ["Corpse loot at the pit"])
        self.assertEqual(self.text_of(self.tree.laws_by_id["disarm_the_peasantry"]), ["Home weapons go to the storehouse", "Approval -3"])
        self.assertEqual(self.text_of(self.tree.laws_by_id["curfew"]), ["Banditry order loss x0.5", "Approval -4"])

    def test_policy_line(self):
        self.assertIn("Opens vassal policy heavy", self.text_of(self.tree.by_id["martial_law"]))
        self.assertNotIn("Opens vassal policy heavy", self.text_of(self.tree.by_id["iron_hand"]))

    def test_every_node_and_law_has_one_line_per_effect(self):
        # The common techs and laws have flag and factor effects (see the test above), not a signed number.
        for group, by_id in (("nodes", self.tree.by_id), ("laws", self.tree.laws_by_id)):
            for raw in self.doc[group]:
                if raw.get("path") == "common":
                    continue
                text = self.text_of(by_id[raw["id"]])
                numeric = [line for line in text if not line.startswith("Opens")]
                self.assertEqual(len(numeric), len(raw["effect"]), raw["id"])
                for line in numeric:
                    self.assertRegex(line, r"[+-]\d")


if __name__ == "__main__":
    unittest.main()
