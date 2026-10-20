"""Tests for the feature liege_influence of the pack mod in the fake game.

They run the real Lua files. They do not prove how the real game behaves (see the test scenarios of the feature).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_modstate import find_pack_mod
from test_fakegame_vassals import VassalsTestCase


class LiegeInfluenceTests(VassalsTestCase):
    def setUp(self):
        super().setUp()
        self.pawn.silver = 1000
        self.regional_treasury = 55
        self.engine.regionalTreasury = self.regional_treasury

    def influence(self):
        answer = self.ask("liege_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]["influence"]

    def send(self, amount):
        return self.ask("liege_send_tribute", amount=amount)

    def test_a_new_game_starts_at_influence_0(self):
        self.assertEqual(self.influence(), 0)

    def test_a_paid_tribute_takes_silver_and_raises_influence_by_the_ratio(self):
        answer = self.send(100)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.pawn.silver, 900)
        self.assertAlmostEqual(self.influence(), 10)
        self.assertEqual(self.engine.regionalTreasury, self.regional_treasury)

    def test_the_default_ratio_gives_1_influence_for_10_silver(self):
        self.send(10)
        self.assertAlmostEqual(self.influence(), 1)

    def test_the_ratio_is_read_from_the_config(self):
        self.game.exec('require("config").liege_influence.influence_per_unit = 0.2')
        self.send(100)
        self.assertAlmostEqual(self.influence(), 20)

    def test_a_tribute_the_treasury_cannot_pay_is_refused_and_changes_nothing(self):
        self.send(100)
        answer = self.send(901)
        self.assertFalse(answer["ok"], answer)
        self.assertIn("not enough silver", answer["error"])
        self.assertEqual(self.pawn.silver, 900)
        self.assertAlmostEqual(self.influence(), 10)

    def test_influence_does_not_decay_over_time(self):
        self.send(100)
        self.calendar.daysTotal = self.calendar.daysTotal + 400
        self.game.advance(50)
        self.assertAlmostEqual(self.influence(), 10)

    def test_influence_has_no_cap(self):
        self.pawn.silver = 100000
        for _ in range(60):
            self.send(200)
        self.assertAlmostEqual(self.influence(), 1200)
        before = self.influence()
        self.send(200)
        self.assertAlmostEqual(self.influence(), before + 20)

    def test_open_menu_without_the_pak_gives_a_clear_message(self):
        answer = self.ask("liege_menu_open")
        self.assertTrue(answer["ok"], answer)
        self.assertFalse(answer["result"]["ok"])
        self.assertTrue(answer["result"]["error"])

    def test_menu_state_wants_the_influence_and_tribute_texts(self):
        self.send(100)
        wanted = self.ask("liege_menu_state")["result"]["wanted_texts"]
        self.assertEqual(wanted["InfluenceText"], "Influence: 10")
        self.assertEqual(wanted["TributeInfoText"], "Tribute: 200 silver")
        self.assertFalse(self.ask("liege_menu_state")["result"]["open"])

    def test_close_without_an_open_menu_is_fine(self):
        self.assertTrue(self.ask("liege_menu_close")["result"]["ok"])

    def test_the_menu_tick_is_not_faster_than_100_ms(self):
        self.game.exec('require("config").liege_influence.poll_ms = 10')
        # the scheduler floor is in the feature code
        source = (find_pack_mod() / "Scripts" / "features" / "liege_influence" / "init.lua").read_text(encoding="utf-8")
        self.assertIn("math.max(100, config.poll_ms)", source)


if __name__ == "__main__":
    unittest.main()
