"""Tests for the Laws menu (change add-laws-menu, #563): the view, the yearly actions, the dialog, the contract entry points and the saved state.

They run the real Lua files in the fake game. The fake game has no pak widget, so the open menu is a stand-in: `menu.is_open` answers true
and the press command runs the same handlers as a click. They do not prove how the widget looks (see the test scenarios laws_menu/*).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_tech_tree import TechTreeTestCase

OPEN_MENU = 'require("core.menu").is_open = function() return true end'
TECH = 'require("features.tech_tree.init")'
SPRING = 0  # these tests use spring = 0 (TechTreeTestCase)
SUMMER = 2


class LawsMenuTestCase(TechTreeTestCase):
    def setUp(self):
        super().setUp()
        self.game.exec(OPEN_MENU)

    def press(self, action, **args):
        return self.ask("laws_menu_press", action=action, **args)

    def menu(self):
        answer = self.ask("laws_menu_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def card(self, law_id):
        return next(card for card in self.menu()["cards"] if card["id"] == law_id)

    def enact_through_menu(self, law_id):
        opened = self.press("enact", id=law_id)
        self.assertTrue(opened["ok"], opened)
        return self.press("confirm")

    def revoke_through_menu(self, law_id):
        opened = self.press("revoke", id=law_id)
        self.assertTrue(opened["ok"], opened)
        return self.press("confirm")

    def prosperity(self, nodes):
        self.choose("prosperity")
        self.grant(len(nodes) - 1)
        for node in nodes:
            self.assertTrue(self.unlock(node)["ok"], node)

    def reload_state(self):
        self.game.exec(f"{TECH}.state:load()")
        self.game.exec("require('features.laws_menu.init').state:load()")

    def new_spring(self):
        for season in (SUMMER, 3, 4, SPRING):
            self.new_season(season)

    def lines(self):
        return self.game.log_lines()


class DefaultTests(LawsMenuTestCase):
    def test_the_shipped_slots_are_one_base_slot_and_at_most_five(self):
        values = self.game.exec('local c = require("config").tech_tree; return c.max_active_laws .. ":" .. c.max_total_laws')
        self.assertEqual(values, "1:5")

    def test_the_header_with_no_law(self):
        state = self.menu()
        header = state["header"]
        self.assertEqual((header["slots_text"], header["max_text"], header["enact_text"], header["revoke_text"], header["unlocked_text"]),
                         ("0 / 1", "(max 5)", "1 / 1", "1 / 1", "0 of 9"))
        self.assertTrue(header["refresh_text"].startswith("Enact and revoke actions refresh in spring"))
        self.assertEqual(len(state["cards"]), 9)
        self.assertTrue(all(card["status"] == "Locked" for card in state["cards"]))

    def test_the_menu_is_registered_with_the_label_laws(self):
        listed = self.game.exec('return table.concat(require("core.menu").state().registered, ",")')
        self.assertIn("laws", listed.split(","))


class CardTests(LawsMenuTestCase):
    def test_a_law_in_force_shows_name_status_source_effects_and_revoke(self):
        self.choose("oppression")
        self.unlock("martial_law")
        self.ask("tech_tree_enact_law", law="conscription")
        card = self.card("conscription")
        self.assertEqual((card["name"], card["status"], card["button"], card["action"], card["enabled"]), ("Conscription", "In force", "Revoke", "revoke", True))
        self.assertEqual(card["source"], "Unlocked by: Tech tree: Oppression, Martial Law")
        self.assertEqual([(e["text"], e["tone"]) for e in card["effects"]], [("Militia attack +10%", "gain"), ("Approval -5", "loss")])

    def test_a_locked_law_says_how_to_unlock_it(self):
        self.choose("oppression")
        card = self.card("conscription")
        self.assertEqual((card["status"], card["button"], card["enabled"], card.get("action")), ("Locked", "Locked", False, None))
        self.assertEqual(card["hint"], "Unlock Martial Law on the Oppression path, or win it from a contract.")
        self.assertEqual(self.card("curfew")["hint"], "Unlock Night Watch in the tech tree, or win it from a contract.")

    def test_a_law_of_the_other_path_stays_locked_with_the_reason(self):
        self.choose("prosperity")
        self.assertEqual(self.card("conscription")["hint"], "Belongs to the Oppression path. A contract can still unlock it.")

    def test_the_effect_signs_follow_the_mockup(self):
        tones = {card["id"]: [e["tone"] for e in card["effects"]] for card in self.menu()["cards"]}
        self.assertEqual(tones["pay_off_warbands"], ["gain"])  # a lower buy-back price is a gain
        self.assertEqual(tones["scorched_earth"], ["gain", "loss"])
        self.assertEqual(tones["curfew"], ["gain", "loss"])
        self.assertEqual(tones["disarm_the_peasantry"], ["neutral", "loss"])
        self.assertEqual(tones["strip_the_dead"], ["gain"])

    def test_the_filter_shows_only_the_cards_of_a_status(self):
        self.prosperity(["fair_courts", "amnesty"])
        self.grant(1)  # a common tech opens the third law
        self.unlock("night_watch")
        self.assertEqual(self.menu()["header"]["unlocked_text"], "3 of 9")
        self.assertEqual(len(self.press("filter", filter="locked")["result"]["cards"]), 6)
        unlocked = self.press("filter", filter="unlocked")["result"]["cards"]
        self.assertEqual(sorted(card["id"] for card in unlocked), ["curfew", "militia_charter", "trade_pacts"])
        self.assertEqual(len(self.press("filter", filter="all")["result"]["cards"]), 9)

    def test_a_law_in_force_counts_as_unlocked(self):
        self.prosperity(["fair_courts"])
        self.ask("tech_tree_enact_law", law="militia_charter")
        self.assertEqual(self.menu()["header"]["unlocked_text"], "1 of 9")

    def test_an_unknown_filter_is_refused(self):
        self.assertFalse(self.press("filter", filter="nope")["ok"])


class SlotTests(LawsMenuTestCase):
    def test_a_full_slot_disables_enact_with_the_text(self):
        self.prosperity(["fair_courts", "amnesty"])
        self.ask("tech_tree_enact_law", law="militia_charter")
        card = self.card("trade_pacts")
        self.assertEqual((card["button"], card["enabled"], card["hint"]), ("Enact", False, "All law slots are used. Revoke a law first."))
        self.assertEqual(self.menu()["header"]["slots_tone"], "warn")

    def test_one_revoke_makes_enact_possible_again(self):
        self.prosperity(["fair_courts", "amnesty"])
        self.ask("tech_tree_enact_law", law="militia_charter")
        self.ask("tech_tree_repeal_law", law="militia_charter")
        self.assertTrue(self.card("trade_pacts")["enabled"])

    def test_an_extra_slot_returns_the_total_and_allows_a_second_law(self):
        self.prosperity(["fair_courts", "amnesty"])
        answer = self.ask("laws_add_slot")
        self.assertEqual((answer["result"]["slots"], answer["result"]["added"]), (2, True))
        self.assertEqual(self.menu()["header"]["slots_text"], "0 / 2")
        self.assertTrue(self.ask("tech_tree_enact_law", law="militia_charter")["ok"])
        self.assertTrue(self.ask("tech_tree_enact_law", law="trade_pacts")["ok"])

    def test_the_slots_stop_at_five_with_a_clear_result(self):
        slots = [self.ask("laws_add_slot")["result"] for _ in range(5)]
        self.assertEqual([row["slots"] for row in slots], [2, 3, 4, 5, 5])
        self.assertEqual([row["added"] for row in slots], [True, True, True, True, False])
        self.assertIn("most law slots (5)", slots[-1]["reason"])
        self.assertEqual(self.menu()["slots"], 5)
        self.assertEqual(self.menu()["extra_slots"], 4)

    def test_the_tech_view_reports_the_slots(self):
        self.ask("laws_add_slot")
        self.assertEqual(self.game.exec(f"return {TECH}.view().max_laws"), 2)


class OldSaveTests(LawsMenuTestCase):
    """A save from before the change can hold two laws in force. The base slot is now 1."""

    def setUp(self):
        super().setUp()
        self.prosperity(["fair_courts", "amnesty"])
        self.game.exec(f'{TECH}.state:set("tech_laws", "militia_charter.trade_pacts")')
        self.game.advance(2)

    def test_both_laws_stay_in_force_and_the_header_says_over_the_cap(self):
        state = self.menu()
        self.assertEqual(sorted(state["laws"]), ["militia_charter", "trade_pacts"])
        self.assertEqual((state["header"]["slots_text"], state["over_cap"]), ("2 / 1", True))
        totals = self.state()["totals"]
        self.assertAlmostEqual(totals["tribute_share_multiplier"], 1.25)

    def test_no_new_law_can_be_enacted_over_the_cap(self):
        self.grant(1)
        self.unlock("night_watch")
        refused = self.ask("tech_tree_enact_law", law="curfew")
        self.assertIn("no free law place (2 in force of 1)", refused["error"])
        card = self.card("curfew")
        self.assertEqual((card["enabled"], card["hint"]), (False, "All law slots are used. Revoke a law first."))
        self.assertIn("All law slots are used", self.press("enact", id="curfew")["error"])

    def test_the_player_can_revoke_one_and_the_other_stays(self):
        self.assertTrue(self.revoke_through_menu("trade_pacts")["ok"])
        state = self.menu()
        self.assertEqual(state["laws"], ["militia_charter"])
        self.assertEqual((state["header"]["slots_text"], state["over_cap"]), ("1 / 1", False))


class ContractTests(LawsMenuTestCase):
    def test_a_contract_unlocks_a_law_with_its_source_text(self):
        answer = self.ask("laws_unlock", id="curfew", source="Contract: Night Watch")
        self.assertEqual((answer["result"]["id"], answer["result"]["changed"], answer["result"]["source"]), ("curfew", True, "Contract: Night Watch"))
        card = self.card("curfew")
        self.assertEqual((card["status"], card["source"], card["button"], card["enabled"]), ("Unlocked", "Unlocked by: Contract: Night Watch", "Enact", True))
        self.assertEqual(self.menu()["header"]["unlocked_text"], "1 of 9")

    def test_an_unknown_id_is_refused_and_a_repeat_changes_nothing(self):
        refused = self.ask("laws_unlock", id="magic", source="x")
        self.assertFalse(refused["ok"])
        self.assertIn("unknown law", refused["error"])
        self.ask("laws_unlock", id="curfew", source="Contract: A")
        again = self.ask("laws_unlock", id="curfew", source="Contract: B")
        self.assertFalse(again["result"]["changed"])
        self.assertEqual(self.card("curfew")["source"], "Unlocked by: Contract: A")
        self.assertEqual(self.game.exec(f"return {TECH}.state:get('laws_unlocked')"), "curfew")

    def test_a_missing_source_text_shows_contract(self):
        self.ask("laws_unlock", id="curfew")
        self.assertEqual(self.card("curfew")["source"], "Unlocked by: Contract")

    def test_a_contract_law_works_whatever_the_path_and_the_tech(self):
        self.choose("oppression")
        self.assertIn("other path", self.ask("tech_tree_enact_law", law="trade_pacts")["error"])
        self.ask("laws_unlock", id="trade_pacts", source="Contract: Trade")
        answer = self.enact_through_menu("trade_pacts")
        self.assertTrue(answer["ok"], answer)
        self.assertAlmostEqual(self.state()["totals"]["tribute_share_multiplier"], 1.25)

    def test_a_contract_law_works_before_a_path_is_chosen(self):
        self.ask("laws_unlock", id="conscription", source="Contract: Levy")
        self.assertTrue(self.enact_through_menu("conscription")["ok"])

    def test_the_path_rule_still_holds_for_the_tech_tree(self):
        self.choose("oppression")
        self.assertIn("other path", self.unlock("fair_courts")["error"])
        self.assertEqual(self.card("trade_pacts")["status"], "Locked")

    def test_the_source_text_and_the_slots_survive_a_load(self):
        self.ask("laws_unlock", id="curfew", source="Contract: Night Watch; 100% (Large)")
        self.ask("laws_add_slot")
        self.reload_state()
        self.game.advance(2)
        self.assertEqual(self.card("curfew")["source"], "Unlocked by: Contract: Night Watch; 100% (Large)")
        self.assertEqual(self.menu()["header"]["slots_text"], "0 / 2")

    def test_a_save_without_the_new_keys_loads_with_no_slot_and_no_unlock(self):
        self.game.exec(f"""
            local state = {TECH}.state
            state:set("law_extra_slots", 0); state:set("laws_unlocked", ""); state:set("laws_sources", "")
        """)
        self.reload_state()
        state = self.menu()
        self.assertEqual((state["slots"], state["granted"], state["extra_slots"]), (1, [], 0))

    def test_a_long_source_text_is_cut(self):
        self.ask("laws_unlock", id="curfew", source="x" * 200)
        self.assertEqual(len(self.card("curfew")["source"]), len("Unlocked by: ") + 120)


class ActionTests(LawsMenuTestCase):
    def setUp(self):
        super().setUp()
        self.game.exec(f"require('features.laws_menu.init')")
        self.ask("laws_add_slot")
        self.ask("laws_add_slot")
        self.prosperity(["fair_courts", "amnesty", "militia_rights"])
        self.game.advance(3)

    def test_one_enact_a_year_then_the_button_is_disabled(self):
        self.assertTrue(self.enact_through_menu("militia_charter")["ok"])
        header = self.menu()["header"]
        self.assertEqual((header["enact_text"], header["enact_tone"]), ("0 / 1", "bad"))
        card = self.card("trade_pacts")
        self.assertEqual((card["enabled"], card["hint"], card["hint_tone"]), (False, "No enact action left this year.", "bad"))
        refused = self.press("enact", id="trade_pacts")
        self.assertFalse(refused["ok"])
        self.assertIn("No enact action left this year.", refused["error"])
        self.assertEqual(self.menu()["laws"], ["militia_charter"])

    def test_one_revoke_a_year_independent_of_the_enact(self):
        self.ask("tech_tree_enact_law", law="militia_charter")
        self.ask("tech_tree_enact_law", law="trade_pacts")
        self.assertTrue(self.revoke_through_menu("militia_charter")["ok"])
        header = self.menu()["header"]
        self.assertEqual((header["revoke_text"], header["revoke_tone"], header["enact_text"]), ("0 / 1", "bad", "1 / 1"))
        card = self.card("trade_pacts")
        self.assertEqual((card["button"], card["enabled"], card["hint"]), ("Revoke", False, "No revoke action left this year."))
        self.assertIn("No revoke action left this year.", self.press("revoke", id="trade_pacts")["error"])
        self.assertEqual(self.menu()["laws"], ["trade_pacts"])
        self.assertTrue(self.enact_through_menu("militia_charter")["ok"], "the enact action is still free")

    def test_the_actions_come_back_at_the_start_of_spring(self):
        self.enact_through_menu("militia_charter")
        self.revoke_through_menu("militia_charter")
        self.assertEqual((self.menu()["enact_left"], self.menu()["revoke_left"]), (0, 0))
        self.new_season(SUMMER)
        self.assertEqual(self.menu()["enact_left"], 0, "summer gives nothing")
        for season in (3, 4):
            self.new_season(season)
        self.assertEqual(self.menu()["enact_left"], 0)
        self.new_season(SPRING)
        self.game.advance(40)
        state = self.menu()
        self.assertEqual((state["enact_left"], state["revoke_left"]), (1, 1))
        self.assertEqual((state["header"]["enact_text"], state["header"]["revoke_text"]), ("1 / 1", "1 / 1"))
        self.assertTrue(any("LAWS actions refreshed" in line for line in self.lines()))

    def test_the_same_spring_refreshes_only_once(self):
        self.new_spring()
        self.game.advance(40)
        self.enact_through_menu("militia_charter")
        self.game.advance(40)
        self.assertEqual(self.menu()["enact_left"], 0)

    def test_the_used_actions_survive_a_load_and_a_load_in_spring_gives_nothing_back(self):
        self.enact_through_menu("militia_charter")
        self.reload_state()
        self.game.advance(40)
        self.assertEqual(self.menu()["enact_left"], 0)
        self.assertEqual(self.game.exec("return require('features.laws_menu.init').state:get('laws_enact_used')"), 1)

    def test_the_header_counts_the_days_to_spring(self):
        self.calendar.day = 125
        self.assertEqual(self.menu()["header"]["refresh_text"], "Enact and revoke actions refresh in spring, in 300 days.")
        self.calendar.day = 60
        self.assertEqual(self.menu()["header"]["refresh_text"], "Enact and revoke actions refresh in spring, in 0 days.")

    def test_the_low_level_tech_commands_use_no_action(self):
        self.ask("tech_tree_enact_law", law="militia_charter")
        self.ask("tech_tree_enact_law", law="trade_pacts")
        self.assertEqual(self.menu()["enact_left"], 1)

    def test_the_slot_check_comes_after_the_action_check(self):
        self.game.exec(f'{TECH}.state:set("law_extra_slots", 0)')
        self.ask("tech_tree_enact_law", law="militia_charter")
        self.assertEqual(self.card("trade_pacts")["hint"], "All law slots are used. Revoke a law first.")
        refused = self.press("enact", id="trade_pacts")
        self.assertIn("All law slots are used. Revoke a law first.", refused["error"])


class DialogTests(LawsMenuTestCase):
    def setUp(self):
        super().setUp()
        self.prosperity(["fair_courts", "amnesty"])

    def test_enact_opens_a_dialog_and_changes_nothing(self):
        answer = self.press("enact", id="trade_pacts")
        self.assertTrue(answer["ok"], answer)
        dialog = answer["result"].get("dialog")
        self.assertEqual((dialog["title"], dialog["question"], dialog["confirm"], dialog["cancel"]), ("Enact law", "Enact Trade Pacts?", "Enact", "Cancel"))
        self.assertEqual(dialog["cost"], "This uses your 1 enact action of this year. The law takes effect at once.")
        self.assertEqual([(e["text"], e["tone"]) for e in dialog["effects"]], [("Tribute share +25%", "gain")])
        state = self.menu()
        self.assertEqual((state["laws"], state["enact_left"]), ([], 1))
        self.assertEqual(self.state()["laws"], [])

    def test_cancel_closes_the_dialog_and_nothing_changes(self):
        self.press("enact", id="trade_pacts")
        answer = self.press("cancel")
        self.assertIsNone(answer["result"].get("dialog"))
        self.assertEqual((self.menu()["laws"], self.menu()["enact_left"]), ([], 1))
        self.assertFalse(self.press("confirm")["ok"], "nothing is open to confirm")

    def test_confirm_enacts_and_uses_the_action(self):
        self.press("enact", id="trade_pacts")
        answer = self.press("confirm")
        self.assertTrue(answer["ok"], answer)
        state = answer["result"]
        self.assertEqual((state["laws"], state["enact_left"], state.get("dialog")), (["trade_pacts"], 0, None))
        self.assertAlmostEqual(self.state()["totals"]["tribute_share_multiplier"], 1.25)

    def test_the_revoke_dialog_and_confirm(self):
        self.enact_through_menu("trade_pacts")
        self.new_spring()
        self.game.advance(40)
        answer = self.press("revoke", id="trade_pacts")
        dialog = answer["result"].get("dialog")
        self.assertEqual((dialog["title"], dialog["question"], dialog["confirm"]), ("Revoke law", "Revoke Trade Pacts?", "Revoke"))
        self.assertEqual(dialog["cost"], "This uses your 1 revoke action of this year. The effects end at once.")
        state = self.press("confirm")["result"]
        self.assertEqual((state["laws"], state["revoke_left"]), ([], 0))
        self.assertEqual(self.state()["totals"]["tribute_share_multiplier"], 1)

    def test_a_disabled_button_opens_no_dialog(self):
        self.enact_through_menu("militia_charter")
        answer = self.press("enact", id="trade_pacts")
        self.assertFalse(answer["ok"])
        self.assertIsNone(self.menu().get("dialog"))

    def test_a_locked_law_and_a_wrong_action_open_no_dialog(self):
        self.assertFalse(self.press("enact", id="conscription")["ok"])
        self.assertFalse(self.press("revoke", id="trade_pacts")["ok"], "the law is not in force")
        self.assertFalse(self.press("enact", id="nope")["ok"])
        self.assertIsNone(self.menu().get("dialog"))

    def test_the_menu_state_works_when_closed_but_the_press_needs_the_open_menu(self):
        self.game.exec('require("core.menu").is_open = function() return false end')
        self.assertFalse(self.menu()["open"])
        answer = self.press("enact", id="trade_pacts")
        self.assertFalse(answer["ok"])
        self.assertIn("not open", answer["error"])

    def test_closing_the_menu_drops_the_dialog(self):
        self.press("enact", id="trade_pacts")
        self.game.exec("local fl = require('features.laws_menu.init'); fl.cancel()")
        self.assertIsNone(self.menu().get("dialog"))


class OpenWithoutPakTests(LawsMenuTestCase):
    def test_open_menu_without_the_pak_gives_a_clear_message(self):
        self.game.exec('require("core.menu").is_open = function() return false end')
        answer = self.ask("laws_menu_open")
        self.assertTrue(answer["ok"], answer)
        self.assertFalse(answer["result"]["ok"])
        self.assertTrue(answer["result"]["error"])

    def test_close_without_an_open_menu_is_fine(self):
        self.game.exec('require("core.menu").is_open = function() return false end')
        self.assertTrue(self.ask("laws_menu_close")["result"]["ok"])

    def test_the_window_tick_is_not_faster_than_100_ms(self):
        from test_fakegame_modstate import find_pack_mod
        source = (find_pack_mod() / "Scripts" / "features" / "laws_menu" / "init.lua").read_text(encoding="utf-8")
        self.assertIn("math.max(100, config.poll_ms)", source)


if __name__ == "__main__":
    unittest.main()
