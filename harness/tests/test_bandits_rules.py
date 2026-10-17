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

    def test_tick_due(self):
        self.assertFalse(self.rules.tick_due(100, 0, 30))
        self.assertFalse(self.rules.tick_due(129, 100, 30))
        self.assertTrue(self.rules.tick_due(130, 100, 30))


if __name__ == "__main__":
    unittest.main()
