"""Tests for laws and vassal policies of the tech tree (mod feature M12.04) in the fake game, and for their loader checks."""

import json
import unittest

import fakegame_path  # noqa: F401
from test_fakegame_tech_tree import TechTreeTestCase, LoaderTests, tree_document


class LawLoaderTests(LoaderTests):
    def test_the_shipped_file_has_six_laws_and_two_policy_gates(self):
        tree = self.build(tree_document())
        self.assertEqual(len(tree.laws), 6)
        self.assertIsNotNone(tree.policy_gates["heavy"])

    def test_a_law_id_equal_to_a_node_id_is_refused(self):
        document = tree_document()
        document["laws"][0]["id"] = "martial_law"
        self.assert_refused(document, "not unique")

    def test_a_law_with_an_unknown_node_or_other_path_is_refused(self):
        document = tree_document()
        document["laws"][0]["requires"] = ["nope"]
        self.assert_refused(document, "unknown node")
        document = tree_document()
        document["laws"][0]["requires"] = ["fair_courts"]
        self.assert_refused(document, "another path")

    def test_a_law_with_an_unknown_effect_kind_is_refused(self):
        document = tree_document()
        document["laws"][0]["effect"][0]["kind"] = "magic"
        self.assert_refused(document, "unknown kind")

    def test_a_policy_gate_with_an_unknown_node_is_refused(self):
        document = tree_document()
        document["vassal_policies"][0]["requires"] = ["nope"]
        self.assert_refused(document, "unknown node")

    def test_a_file_without_laws_still_loads(self):
        document = tree_document()
        del document["laws"], document["vassal_policies"]
        self.assertEqual(len(self.build(document).laws), 0)


del LoaderTests  # run the inherited loader tests only once, in test_fakegame_tech_tree


class LawTestCase(TechTreeTestCase):
    def prosperity(self, nodes):
        self.choose("prosperity")
        self.region.settlementLevel = 4
        for node in nodes:
            self.assertTrue(self.unlock(node)["ok"], node)

    def enact(self, law):
        return self.ask("tech_tree_enact_law", law=law)

    def lines(self):
        return self.game.log_lines()


class EnactTests(LawTestCase):
    def test_a_law_needs_a_path_and_its_node(self):
        self.assertIn("no path", self.enact("trade_pacts")["error"])
        self.prosperity(["fair_courts"])
        self.assertIn("needs the node 'amnesty'", self.enact("trade_pacts")["error"])

    def test_a_law_of_the_other_path_is_refused(self):
        self.prosperity(["fair_courts"])
        self.assertIn("other path", self.enact("conscription")["error"])

    def test_an_enacted_law_changes_the_totals_and_can_be_repealed(self):
        self.prosperity(["fair_courts", "amnesty"])
        answer = self.enact("trade_pacts")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["result"]["laws"], ["trade_pacts"])
        self.assertAlmostEqual(answer["result"]["totals"]["tribute_share_multiplier"], 1.25)
        self.assertEqual(answer["result"]["totals"]["vassal_loyalty_bonus"], 2)
        self.assertTrue(any("tribute_share" in line or "effects applied" in line for line in self.lines()))
        repealed = self.ask("tech_tree_repeal_law", law="trade_pacts")
        self.assertEqual(repealed["result"]["laws"], [])
        self.assertEqual(repealed["result"]["totals"]["tribute_share_multiplier"], 1)

    def test_a_second_enactment_and_a_repeal_of_an_unknown_law_are_refused(self):
        self.prosperity(["fair_courts"])
        self.assertTrue(self.enact("militia_charter")["ok"])
        self.assertIn("already in force", self.enact("militia_charter")["error"])
        self.assertIn("not in force", self.ask("tech_tree_repeal_law", law="trade_pacts")["error"])

    def test_only_two_laws_fit_at_the_same_time(self):
        self.prosperity(["fair_courts", "amnesty", "militia_rights"])
        self.assertTrue(self.enact("militia_charter")["ok"])
        self.assertTrue(self.enact("trade_pacts")["ok"])
        self.assertIn("no free law place", self.enact("pay_off_warbands")["error"])

    def test_the_laws_are_kept_in_the_pawn_tags(self):
        self.prosperity(["fair_courts"])
        self.enact("militia_charter")
        tags = list(self.game.lua.eval("tag_names")(self.pawn).values())
        self.assertIn("invasion:tech_laws=militia_charter", tags)


class VassalPolicyTests(LawTestCase):
    def setUp(self):
        super().setUp()
        self.game.exec("return require('features.vassals.init').register_vassal('Test_Region')")

    def set_policy(self, policy):
        return self.ask("tech_tree_set_vassal_policy", slot=1, policy=policy)

    def test_fair_is_always_open(self):
        self.assertTrue(self.set_policy("fair")["ok"])

    def test_light_needs_prosperity_and_fair_courts(self):
        self.assertIn("belongs to the path prosperity", self.set_policy("light")["error"])
        self.choose("prosperity")
        self.assertIn("needs the node 'fair_courts'", self.set_policy("light")["error"])
        self.unlock("fair_courts")
        self.assertTrue(self.set_policy("light")["ok"])

    def test_heavy_is_closed_to_the_prosperity_path(self):
        self.prosperity(["fair_courts"])
        self.assertIn("belongs to the path oppression", self.set_policy("heavy")["error"])

    def test_heavy_opens_with_martial_law(self):
        self.choose("oppression")
        self.unlock("martial_law")
        self.assertTrue(self.set_policy("heavy")["ok"])


if __name__ == "__main__":
    unittest.main()


class WidgetLawTests(LawTestCase):
    def wanted_line(self):
        return self.ask("tech_tree_widget_state")["result"]["wanted_laws_line"]

    def test_the_laws_line_follows_the_laws_in_force(self):
        self.assertEqual(self.wanted_line(), "Laws: choose a path first")
        self.prosperity(["fair_courts", "amnesty"])
        self.assertEqual(self.wanted_line(), "Laws: 0 of 2 in force")
        self.enact("trade_pacts")
        self.assertEqual(self.wanted_line(), "Laws: 1 of 2 in force")

    def test_the_law_labels_say_what_a_click_does(self):
        self.prosperity(["fair_courts", "amnesty"])
        self.enact("trade_pacts")
        labels = self.game.exec(
            "local lines = require('features.tech_tree_widget.lines'); local out = {};"
            " for _, law in ipairs(require('features.tech_tree.init').view().laws) do out[#out + 1] = lines.law_label(law) end;"
            " return table.concat(out, '|')")
        self.assertEqual(labels, "Enact Militia Charter|[in force] Trade Pacts (repeal)|Pay Off Warbands (closed)")

    def test_press_needs_an_open_widget(self):
        answer = self.ask("tech_tree_widget_press", kind="law", index=1)
        self.assertFalse(answer["ok"])
        self.assertIn("not open", answer["error"])
