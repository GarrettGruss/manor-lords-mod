"""Tests for the feature liege_influence of the pack mod in the fake game (the arms shipment tests left with change update-liege-contracts-tiers, #533).

They run the real Lua files. They do not prove how the real game behaves (see the test scenarios of the feature).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_modstate import find_pack_mod
from test_fakegame_vassals import VassalsTestCase


class LiegeInfluenceTests(VassalsTestCase):
    """Change update-liege-tribute-to-contracts (#505): only contracts change the influence; the tribute is gone."""

    def setUp(self):
        super().setUp()
        self.pawn.silver = 1000

    def influence(self):
        answer = self.ask("liege_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]["influence"]

    def set_influence(self, value):
        self.game.exec(f'require("features.liege_influence.init").state:set("liege_influence", {value})')

    def test_a_new_game_starts_at_influence_0(self):
        self.assertEqual(self.influence(), 0)

    def test_the_tribute_command_is_gone(self):
        answer = self.ask("liege_send_tribute", amount=100)
        self.assertFalse(answer["ok"])
        self.assertIn("unknown", answer["error"].lower())
        self.assertEqual(self.pawn.silver, 1000)
        self.assertEqual(self.influence(), 0)

    def test_the_tribute_config_values_are_gone(self):
        config = self.game.exec('local c = require("config").liege_influence; return tostring(c.influence_per_unit) .. ":" .. tostring(c.tribute_button_amount)')
        self.assertEqual(config, "nil:nil")

    def test_influence_does_not_decay_over_time(self):
        self.set_influence(10)
        self.calendar.daysTotal = self.calendar.daysTotal + 400
        self.game.advance(50)
        self.assertAlmostEqual(self.influence(), 10)

    def test_influence_has_no_cap(self):
        self.set_influence(1200)
        self.game.exec('require("features.liege_influence.init").change_influence(20)')
        self.assertAlmostEqual(self.influence(), 1220)

    def test_a_penalty_stops_at_0(self):
        self.set_influence(30)
        self.assertEqual(self.game.exec('return require("features.liege_influence.init").change_influence(-500)'), 0)
        self.assertEqual(self.influence(), 0)

    def test_the_state_command_has_the_influence_and_silver_and_no_arms_fields(self):
        self.set_influence(10)
        state = self.ask("liege_state")["result"]
        self.assertEqual((state["influence"], state["silver"]), (10, 1000))
        for key in ("arms_last_day", "arms_enabled", "arms_reason", "arms_days_left"):
            self.assertNotIn(key, state)
        self.assertFalse(self.ask("liege_menu_state")["result"]["open"])

    def test_the_arms_commands_are_gone(self):
        for name, args in (("liege_request_arms", {}), ("liege_test_set_arms_day", {"day": 1})):
            answer = self.ask(name, **args)
            self.assertFalse(answer["ok"], name)
            self.assertIn("unknown", answer["error"].lower())


if __name__ == "__main__":
    unittest.main()
