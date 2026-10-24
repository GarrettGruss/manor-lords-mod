"""Tests for the vassals guard of the feature scenario_settings (change add-game-settings-guard, #438) in the fake game.

They run the real Lua files. The guard value `vassals` is read once at a new game, kept over a load, and a save without it
uses the live check (no AI lord pawn). The warning shows only when vassals are not enabled, and nothing is locked.
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_scenario_settings import DEFAULTS, GAME_SETUP, HUSSITE_SETUP, RulesTests, SettingsTestCase

AI_LORDS_2 = {**GAME_SETUP, "numGenericAILords": 2}
WARNING = "vassals are not enabled"


class GuardTestCase(SettingsTestCase):
    def vassals(self):
        return self.settings()["vassals"]

    def reload_mod_state(self):
        """Plays a load: the pawn keeps its Tags, the mod state is read again."""
        self.game.exec('require("ModState").open("invasion", "pawn"):load()', state=self.mod_name)


class NewGameTests(GuardTestCase):
    def test_ai_opponents_2_gives_vassals_true_and_no_warning(self):
        self.stand_in_menu()
        self.start_game("", 1, AI_LORDS_2)
        state = self.settings()
        self.assertEqual(state["vassals"], 1)
        self.assertIsNone(state.get("warning"))

    def test_ai_opponents_0_gives_vassals_false_and_the_warning(self):
        self.stand_in_menu()
        self.start_game("", 1, HUSSITE_SETUP)
        state = self.settings()
        self.assertEqual(state["vassals"], 0)
        self.assertIn(WARNING, state["warning"])

    def test_an_unreadable_setup_leaves_the_value_unknown(self):
        self.stand_in_menu()
        self.start_game("", 1)
        self.assertEqual(self.vassals(), -1)

    def test_nothing_is_locked_when_vassals_are_off(self):
        self.stand_in_menu()
        self.start_game("", 1, HUSSITE_SETUP)
        answer = self.ask("scenario_settings_set", yearly=3, great=3, vassal=3)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual({k: self.settings()[k] for k in ("yearly", "great", "vassal")}, {"yearly": 3, "great": 3, "vassal": 3})

    def test_the_off_map_adversary_absent_locks_nothing(self):
        self.stand_in_menu()
        self.start_game("", 1, {**AI_LORDS_2, "adversary_baron": False})
        self.assertEqual(self.vassals(), 1)
        answer = self.ask("scenario_settings_set", yearly=3)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.settings()["yearly"], 3)


class LoadTests(GuardTestCase):
    def test_the_value_stays_over_a_load_and_the_setup_is_not_read_again(self):
        self.stand_in_menu()
        self.start_game("", 1, HUSSITE_SETUP)
        self.ask("scenario_settings_click", action="begin")
        self.assertEqual(self.vassals(), 0)
        # Load: the same pawn Tags, a new game instance. The setup now says AI opponents 2 (it is not the setup of the saved game).
        self.instance.savefileToLoad = self.game.text("saveGame_2")
        self.instance.gameSetup = self.game.struct(currentGameSetup=self.game.struct(**AI_LORDS_2))
        self.calendar.daysTotal = 40
        self.reload_mod_state()
        self.game.advance(2)
        self.assertEqual(self.vassals(), 0)

    def test_an_old_save_without_ai_lord_pawns_stores_false(self):
        self.start_game("saveGame_4", 61)
        self.assertEqual(self.vassals(), 0)
        self.reload_mod_state()
        self.assertEqual(self.vassals(), 0, "the result is stored in the mod state")

    def test_an_old_save_with_an_ai_lord_pawn_stores_true(self):
        self.game.obj("PawnCPP_AI")
        self.start_game("saveGame_4", 61)
        self.assertEqual(self.vassals(), 1)
        self.assertIsNone(self.settings().get("warning"))

    def test_a_stored_value_is_not_replaced_by_the_live_check(self):
        self.game.obj("PawnCPP_AI")
        self.start_game("saveGame_4", 61)
        self.assertEqual(self.vassals(), 1)


class RulesOfTheGuardTests(unittest.TestCase):
    run_lua = RulesTests.run_lua

    def test_vassals_from_setup(self):
        self.assertEqual(self.run_lua("return tostring(rules.vassals_from_setup({ ai_lords = 0 })) .. tostring(rules.vassals_from_setup({ ai_lords = 3 })) .. tostring(rules.vassals_from_setup({}))"), "01nil")

    def test_the_warning_is_added_only_when_vassals_are_off(self):
        text = self.run_lua("config.vassals_warning = 'W'; return rules.background_with_warning(config, 0) .. '|' .. rules.background_with_warning(config, 1) .. '|' .. rules.background_with_warning(config, -1)")
        warned, plain, unknown = text.split("|")
        self.assertTrue(warned.endswith("\n\nW"))
        self.assertEqual(plain, unknown)
        self.assertNotIn("W", plain[-3:])


if __name__ == "__main__":
    unittest.main()
