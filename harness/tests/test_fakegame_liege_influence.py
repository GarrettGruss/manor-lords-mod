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
        self.assertEqual(wanted["TributeInfoText"], "Tribute: 200 silver (you have 900)")
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

    def test_a_failed_delivery_costs_nothing_and_keeps_the_cooldown_free(self):
        self.world.buildings[1].Data.constructed = False  # no built manor
        answer = self.request()
        self.assertFalse(answer["ok"])
        self.assertIn("manor", answer["error"])
        state = self.liege()
        self.assertEqual((self.pawn.silver, state["arms_last_day"], state["arms_enabled"]), (500, -1, True))

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
