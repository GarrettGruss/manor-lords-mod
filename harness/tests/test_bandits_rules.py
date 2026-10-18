"""Tests for the pure rules of the bandits feature (Scripts/features/bandits/rules.lua)."""

import unittest
from pathlib import Path

from lupa import LuaRuntime

from test_fakegame_modstate import find_pack_mod

RULES = find_pack_mod() / "Scripts" / "features" / "bandits" / "rules.lua"
BANDS = [(75, 0.10), (50, 0.25), (25, 0.50)]


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime()
        self.rules = self.lua.execute(RULES.read_text(encoding="utf-8"))
        self.bands = self.lua.table_from([self.lua.table_from({"below": b, "chance": c}) for b, c in BANDS])

    def test_debuff_rounds_up(self):
        self.assertEqual(self.rules.debuff(65, 1), 35)
        self.assertEqual(self.rules.debuff(65, 2), 70)
        self.assertEqual(self.rules.debuff(65, 1.5), 53)

    def test_order_is_clamped(self):
        self.assertEqual(self.rules.debuffed_order(100, 0, 3), 0)

    def test_chance_bands(self):
        chances = {order: self.rules.chance_for(order, self.bands) for order in (80, 75, 74, 49, 24, 0)}
        self.assertEqual(chances, {80: 0, 75: 0, 74: 0.10, 49: 0.25, 24: 0.50, 0: 0.50})

    def test_roll_under_the_chance_converts(self):
        self.assertTrue(self.rules.should_convert(60, self.bands, 0.09))
        self.assertFalse(self.rules.should_convert(60, self.bands, 0.10))
        self.assertFalse(self.rules.should_convert(90, self.bands, 0.0))

    def test_natural_order_follows_the_game(self):
        self.assertEqual(self.rules.natural_order(80, None, None), 80)
        self.assertEqual(self.rules.natural_order(35, 35, 100), 100)  # the mod's own write
        self.assertEqual(self.rules.natural_order(90, 35, 100), 90)   # the game rewrote it

    def test_season_changed(self):
        self.assertFalse(self.rules.season_changed(1, -1))  # nothing saved: store only
        self.assertFalse(self.rules.season_changed(1, 1))
        self.assertTrue(self.rules.season_changed(2, 1))
        self.assertTrue(self.rules.season_changed(0, 3))  # autumn to winter


    def cfg(self, multiplier=1.0):
        return self.lua.table_from({"silver_per_family": 10, "price_multiplier": multiplier})

    def facts(self, **changes):
        base = {"outstanding": 2, "bandit_units": 18, "free_slots": 4, "silver": 100}
        base.update(changes)
        return self.lua.table_from(base)

    def test_buy_back_price_and_tech_multipliers(self):
        # C8: Iron Hand 1.25 and Amnesty 0.5, rounded up
        self.assertEqual([self.rules.buy_back_price(n, self.cfg(1.0)) for n in (1, 2)], [10, 20])
        self.assertEqual([self.rules.buy_back_price(n, self.cfg(1.25)) for n in (1, 2)], [13, 25])
        self.assertEqual([self.rules.buy_back_price(n, self.cfg(0.5)) for n in (1, 2)], [5, 10])

    def test_families_to_return_is_limited_by_free_slots(self):
        self.assertEqual(self.rules.families_to_return(2, 4), 2)
        self.assertEqual(self.rules.families_to_return(5, 3), 3)
        self.assertEqual(self.rules.families_to_return(0, 3), 0)

    def test_buy_back_refusals(self):
        refusal = lambda **changes: self.rules.buy_back_refusal(self.facts(**changes), self.cfg())  # noqa: E731
        self.assertIsNone(refusal())
        self.assertIsNone(refusal(silver=20))  # exactly the price
        self.assertIn("silver", refusal(silver=19))
        self.assertIn("free home", refusal(free_slots=0))
        self.assertIn("no families", refusal(outstanding=0))
        self.assertIn("no bandit units", refusal(bandit_units=0))

    def test_the_price_follows_the_slots_not_the_outstanding_families(self):
        self.assertIn("silver", self.rules.buy_back_refusal(self.facts(outstanding=6, free_slots=3, silver=29), self.cfg()))
        self.assertIsNone(self.rules.buy_back_refusal(self.facts(outstanding=6, free_slots=3, silver=30), self.cfg()))


if __name__ == "__main__":
    unittest.main()
