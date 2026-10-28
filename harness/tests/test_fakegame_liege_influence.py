"""Tests for the feature liege_influence of the pack mod in the fake game.

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

    def test_the_menu_state_wants_the_influence_and_silver_texts(self):
        self.set_influence(10)
        wanted = self.ask("liege_menu_state")["result"]["wanted_texts"]
        self.assertEqual(wanted["InfluenceText"], "Influence: 10")
        self.assertEqual(wanted["SilverText"], "Silver: 1000")
        self.assertNotIn("TributeInfoText", wanted)
        self.assertFalse(self.ask("liege_menu_state")["result"]["open"])


if __name__ == "__main__":
    unittest.main()


from test_fakegame_manor_stronghold import ManorStorageTestCase  # noqa: E402

SHIELD, SPEAR = 271, 133


class ArmsShipmentTests(ManorStorageTestCase):
    """Change add-scenario-start-kit (#425): the button "Request arms shipment" (the command runs the same code)."""

    def setUp(self):
        super().setUp()
        self.pawn.silver = 500

    def request(self):
        return self.ask("liege_request_arms")

    def liege(self):
        return self.ask("liege_state")["result"]

    def stock(self, good):
        return self.world.stock[good] or 0

    def test_a_shipment_delivers_30_shields_and_30_spears_and_takes_200_silver(self):
        answer = self.request()
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((self.stock(SHIELD), self.stock(SPEAR)), (30, 30))
        self.assertEqual(self.pawn.silver, 300)

    def test_after_a_shipment_the_button_is_disabled_with_the_days_left(self):
        self.request()
        state = self.liege()
        self.assertFalse(state["arms_enabled"])
        self.assertEqual(state["arms_reason"], "180 days left")
        self.calendar.daysTotal = self.calendar.daysTotal + 100
        self.assertEqual(self.liege()["arms_reason"], "80 days left")

    def test_a_click_in_the_cooldown_delivers_nothing(self):
        self.request()
        answer = self.request()
        self.assertFalse(answer["ok"])
        self.assertIn("days left", answer["error"])
        self.assertEqual((self.stock(SHIELD), self.pawn.silver), (30, 300))

    def test_after_180_days_it_is_enabled_again(self):
        self.request()
        self.calendar.daysTotal = self.calendar.daysTotal + 180
        self.assertTrue(self.liege()["arms_enabled"])
        self.assertTrue(self.request()["ok"])
        self.assertEqual(self.stock(SHIELD), 60)

    def test_not_enough_silver_is_refused_with_the_missing_amount(self):
        self.pawn.silver = 150
        state = self.liege()
        self.assertFalse(state["arms_enabled"])
        self.assertEqual(state["arms_reason"], "need 200 silver, 50 missing")
        answer = self.request()
        self.assertFalse(answer["ok"])
        self.assertEqual((self.stock(SHIELD), self.pawn.silver), (0, 150))

    def wanted_arms_text(self):
        return self.ask("liege_menu_state")["result"]["wanted_texts"]["ArmsInfoText"]

    def test_no_manor_disables_the_button_with_the_reason_and_a_click_does_nothing(self):
        self.world.buildings[1].Data.constructed = False  # no built manor
        state = self.liege()
        self.assertFalse(state["arms_enabled"])
        self.assertEqual(state["arms_reason"], "Build a manor first")
        self.assertTrue(self.wanted_arms_text().endswith("\nBuild a manor first"))
        answer = self.request()
        self.assertFalse(answer["ok"])
        self.assertIn("manor", answer["error"])
        state = self.liege()
        self.assertEqual((self.pawn.silver, state["arms_last_day"]), (500, -1))

    def test_a_built_manor_enables_the_button_and_shows_no_reason(self):
        state = self.liege()
        self.assertTrue(state["arms_enabled"])
        self.assertNotIn("\n", self.wanted_arms_text())

    def test_the_reason_of_a_disabled_button_shows_under_it_for_silver_and_cooldown(self):
        self.pawn.silver = 150
        self.assertTrue(self.wanted_arms_text().endswith("\nneed 200 silver, 50 missing"))
        self.pawn.silver = 500
        self.request()
        self.assertTrue(self.wanted_arms_text().endswith("\n180 days left"))

    def test_a_full_manor_store_fails_the_delivery(self):
        self.assertTrue(self.ask("manor_put", good=27, amount=180)["ok"])
        answer = self.request()
        self.assertFalse(answer["ok"])
        self.assertIn("full", answer["error"])
        self.assertEqual((self.stock(SHIELD), self.pawn.silver), (0, 500))

    def test_a_delivery_that_fails_after_the_first_good_is_rolled_back(self):
        self.game.exec('require("config").liege_influence.arms_shipment.goods[2].id = 999')
        self.game.exec("""
            local manor = require("HarnessManor")
            local put = manor.manor_put
            manor.manor_put = function(request)
                if request.good == 999 then return { ok = false, error = "refused" } end
                return put(request)
            end""")
        answer = self.request()
        self.assertFalse(answer["ok"])
        self.assertEqual((self.stock(SHIELD), self.pawn.silver), (0, 500))

    def test_the_cooldown_day_is_a_saved_mod_state_entry(self):
        self.request()
        tags = [tag for tag in self.game.lua.eval("tag_names")(self.pawn).values()]
        self.assertTrue(any(tag.startswith("invasion:arms_last_day=") for tag in tags), tags)

    def test_the_cost_and_goods_come_from_the_config(self):
        self.game.exec('local c = require("config").liege_influence.arms_shipment; c.cost = 50; c.goods = { { id = 133, amount = 5, name = "spear" } }')
        self.assertTrue(self.request()["ok"])
        self.assertEqual((self.stock(SPEAR), self.stock(SHIELD), self.pawn.silver), (5, 0, 450))
