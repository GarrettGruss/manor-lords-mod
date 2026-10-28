"""Tests for laws and vassal policies of the tech tree (mod feature M12.04) in the fake game, and for their loader checks."""

import json
import unittest

import fakegame_path  # noqa: F401
from test_fakegame_tech_tree import TechTreeTestCase, LoaderTests, tree_document


class LawLoaderTests(LoaderTests):
    def test_the_shipped_file_has_nine_laws_and_two_policy_gates(self):
        tree = self.build(tree_document())
        self.assertEqual(len(tree.laws), 9)
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
        self.grant(len(nodes) - 1)
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
        self.assertNotIn("vassal_loyalty_bonus", answer["result"]["totals"])
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


class CommonLawTests(LawTestCase):
    """Change update-tech-tree-yearly-picks: three common laws, free, repealable, counted in the limit."""

    def test_a_common_law_needs_its_common_tech_but_no_path(self):
        self.assertIn("needs the node 'night_watch'", self.enact("curfew")["error"])
        self.assertTrue(self.unlock("night_watch")["ok"])
        answer = self.enact("curfew")
        self.assertTrue(answer["ok"], answer)
        self.assertAlmostEqual(answer["result"]["totals"]["banditry_gain_multiplier"], 0.5)

    def test_a_common_law_counts_toward_the_limit(self):
        self.grant(3)
        self.choose("oppression")
        for node in ("martial_law", "night_watch", "corpse_robbing"):
            self.assertTrue(self.unlock(node)["ok"], node)
        self.assertTrue(self.enact("conscription")["ok"])
        self.assertTrue(self.enact("curfew")["ok"])
        self.assertIn("no free law place", self.enact("strip_the_dead")["error"])

    def test_a_common_law_works_on_both_paths(self):
        self.grant(1)
        self.choose("prosperity")
        self.unlock("night_watch")
        self.assertTrue(self.enact("curfew")["ok"])

    def test_the_common_laws_set_their_totals_and_repeal_clears_them(self):
        self.grant(2)
        for node in ("night_watch", "corpse_robbing", "armory_census"):
            self.assertTrue(self.unlock(node)["ok"], node)
        self.assertTrue(self.enact("strip_the_dead")["ok"])
        totals = self.enact("disarm_the_peasantry")["result"]["totals"]
        self.assertEqual((totals["corpse_loot"], totals["disarm_homes"], totals["banditry_gain_multiplier"]), (True, True, 1))
        repealed = self.ask("tech_tree_repeal_law", law="strip_the_dead")["result"]["totals"]
        self.assertEqual((repealed["corpse_loot"], repealed["disarm_homes"]), (False, True))

    def test_the_common_techs_alone_change_no_total(self):
        self.grant(2)
        for node in ("night_watch", "corpse_robbing", "armory_census"):
            self.unlock(node)
        totals = self.state()["totals"]
        self.assertEqual((totals["corpse_loot"], totals["disarm_homes"], totals["banditry_gain_multiplier"]), (False, False, 1))

    def test_the_approval_of_disarm_and_curfew_is_in_the_totals(self):
        self.grant(1)
        self.unlock("armory_census")
        self.unlock("night_watch")
        self.enact("disarm_the_peasantry")
        totals = self.enact("curfew")["result"]["totals"]
        self.assertEqual(totals["approval_bonus"], -7)
        self.ask("tech_tree_repeal_law", law="curfew")
        self.assertEqual(self.state()["totals"]["approval_bonus"], -3)

    def test_the_window_view_keeps_the_common_laws_apart(self):
        view = self.game.exec("local view = require('features.tech_tree.init').view(); return #view.laws .. ',' .. #view.common_laws")
        self.assertEqual(view, "0,3")


class CurfewOrderTests(LawTestCase):
    def tick(self):
        self.ask("bandits_set_order", value=50)
        return self.ask("bandits_tick_now")["result"]["last_tick"]

    def setUp(self):
        super().setUp()
        self.game.method(self.region, "getNumHomelessFamilies", lambda _self: 4)
        self.unlock("night_watch")

    def test_curfew_halves_the_order_loss_and_repeal_restores_it(self):
        self.assertEqual(self.tick()["homeless_term"], 20)
        self.enact("curfew")
        self.game.advance(4)
        tick = self.tick()
        self.assertEqual((tick["homeless_term"], tick["manor_term"], tick["order_after"]), (10, 10, 50))
        self.ask("tech_tree_repeal_law", law="curfew")
        self.game.advance(4)
        self.assertEqual(self.tick()["homeless_term"], 20)


class DisarmTests(LawTestCase):
    def setUp(self):
        super().setUp()
        self.region_buildings = []
        self.game.method(self.region, "GetBuildings", lambda _self: self.game.lua.table_from([b["object"] for b in self.region_buildings]))
        self.storehouse = self.building(6, [])
        self.home_a = self.building(3, [(133, 3), (4, 5)])
        self.home_b = self.building(3, [(271, 2), (133, 1)])
        self.unlock("armory_census")

    def building(self, kind, goods):
        building = self.game.obj("SMBuildingMaster", Data=self.game.struct(bType=kind), Inventory=self.game.array([self.game.struct(Type=t, amt=a) for t, a in goods]))
        row = {"object": building, "goods": list(goods)}
        self.region_buildings.append(row)
        self.game.method(building, "IsRubble", lambda _self: False)

        def refresh():
            building.Inventory = self.game.array([self.game.struct(Type=t, amt=a) for t, a in row["goods"]])

        def consume(_self, good):
            for index, (kind_, amount) in enumerate(row["goods"]):
                if kind_ == good and amount > 0:
                    row["goods"][index] = (kind_, amount - 1)
                    break
            refresh()

        def add(_self, good):
            row["goods"].append((good["Type"], good["amt"]))
            refresh()

        self.game.method(building, "consumeGoodNoCheck", consume)
        self.game.method(building, "addToInventory", add)
        row["refresh"] = refresh
        return row

    def held(self, row, good):
        return sum(amount for kind, amount in row["goods"] if kind == good)

    def put(self, row, good, amount):
        row["goods"].append((good, amount))
        row["refresh"]()

    def next_day(self):
        self.calendar.daysTotal = self.calendar.daysTotal + 1
        self.game.advance(4)

    def test_the_law_moves_home_weapons_to_the_storehouse(self):
        self.assertTrue(self.enact("disarm_the_peasantry")["ok"])
        self.game.advance(4)
        self.assertEqual((self.held(self.home_a, 133), self.held(self.home_b, 133), self.held(self.home_b, 271)), (0, 0, 0))
        self.assertEqual(self.held(self.home_a, 4), 5)  # goods that are not weapons stay
        self.assertEqual((self.held(self.storehouse, 133), self.held(self.storehouse, 271)), (4, 2))
        self.assertTrue(any("TECH_TREE disarm" in line and "moved=6" in line for line in self.lines()))

    def test_a_new_weapon_is_moved_at_the_next_tick_day_only(self):
        self.enact("disarm_the_peasantry")
        self.game.advance(4)
        self.put(self.home_a, 133, 2)
        self.game.advance(4)
        self.assertEqual(self.held(self.home_a, 133), 2)  # the same game day: no tick
        self.next_day()
        self.assertEqual(self.held(self.home_a, 133), 0)

    def test_without_the_law_or_after_the_repeal_the_homes_keep_their_weapons(self):
        self.next_day()
        self.assertEqual(self.held(self.home_a, 133), 3)
        self.enact("disarm_the_peasantry")
        self.game.advance(4)
        self.ask("tech_tree_repeal_law", law="disarm_the_peasantry")
        self.put(self.home_a, 133, 2)
        self.next_day()
        self.next_day()
        self.assertEqual(self.held(self.home_a, 133), 2)

    def test_a_missing_storehouse_is_logged_and_nothing_is_taken(self):
        self.region_buildings.remove(self.storehouse)
        self.enact("disarm_the_peasantry")
        self.game.advance(4)
        self.assertEqual(self.held(self.home_a, 133), 3)
        self.assertTrue(any("disarm skipped" in line for line in self.lines()))


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
    def lua_text(self, expression):
        return self.game.exec("local lines = require('features.tech_tree_widget.lines'); local view = require('features.tech_tree.init').view(); return " + expression)

    def test_the_strip_count_follows_the_laws_in_force(self):
        self.assertEqual(self.lua_text("lines.strip_count_text(view)"), "0 of 2 max")
        self.prosperity(["fair_courts", "amnesty"])
        self.enact("trade_pacts")
        self.assertEqual(self.lua_text("lines.strip_count_text(view)"), "1 of 2 max")

    def test_the_strip_counts_a_common_law(self):
        self.grant(3)
        self.unlock("night_watch")
        self.enact("curfew")
        self.assertEqual(self.lua_text("lines.strip_count_text(view)"), "1 of 2 max")

    def test_the_law_button_says_what_a_click_does(self):
        self.prosperity(["fair_courts", "amnesty"])
        self.enact("trade_pacts")
        labels = self.lua_text(
            "(function() local by_id = lines.law_rows_by_id(view); local out = {};"
            " for _, id in ipairs({ 'militia_charter', 'trade_pacts', 'pay_off_warbands', 'conscription' }) do out[#out + 1] = tostring(lines.law_button_label(by_id[id])) end;"
            " return table.concat(out, '|') end)()")
        self.assertEqual(labels, "Enact|Repeal|nil|nil")

    def test_a_law_with_no_free_place_keeps_its_enact_button(self):
        self.grant(3)
        self.prosperity(["fair_courts", "amnesty"])
        self.unlock("night_watch")
        self.enact("trade_pacts")
        self.enact("militia_charter")
        labels = self.lua_text(
            "(function() local by_id = lines.law_rows_by_id(view); local out = {};"
            " for _, id in ipairs({ 'curfew', 'pay_off_warbands' }) do out[#out + 1] = tostring(lines.law_button_label(by_id[id])) end;"
            " return table.concat(out, '|') end)()")
        self.assertEqual(labels, "Enact|nil")  # Curfew: tech unlocked, no free place. Pay Off Warbands: tech not unlocked.

    def test_a_card_names_the_law_of_its_tech(self):
        text = self.lua_text("lines.card_law_text(lines.law_of_node('amnesty', require('features.tech_tree.init').tree)) .. '|' .. lines.card_law_text(lines.law_of_node('golden_age', require('features.tech_tree.init').tree))")
        self.assertEqual(text, "Trade Pacts|No law")

    def test_the_strip_place_shows_name_and_effects(self):
        self.prosperity(["fair_courts", "amnesty"])
        self.enact("trade_pacts")
        text = self.lua_text("lines.strip_place_text(lines.enacted_laws(view)[1], require('features.tech_tree.init').tree) .. '|' .. lines.strip_place_text(nil, nil)")
        self.assertEqual(text, "Trade Pacts\nTribute share +25%|Empty place")

    def test_press_needs_an_open_widget(self):
        answer = self.ask("tech_tree_widget_press", kind="law", index=1)
        self.assertFalse(answer["ok"])
        self.assertIn("not open", answer["error"])
