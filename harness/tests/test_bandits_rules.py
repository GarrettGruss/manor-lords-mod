"""Tests for the pure rules of the bandits feature (Scripts/features/bandits/rules.lua)."""

import unittest
from pathlib import Path

from lupa import LuaRuntime

from test_fakegame_modstate import find_pack_mod

RULES = find_pack_mod() / "Scripts" / "features" / "bandits" / "rules.lua"


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime()
        self.rules = self.lua.execute(RULES.read_text(encoding="utf-8"))

    def order_cfg(self):
        return self.lua.table_from({
            "manor_term": 10, "homeless_term": 5, "threshold": 25, "timer_days": 90, "warn_days": 30,
            "leavers": 18, "order_gain": 25, "min_families_left": 1,
        })

    def timer(self, order, start, today):
        step = self.rules.timer_step(order, start, today, self.order_cfg())
        return step.action, step.days_left, step.warn

    def test_order_is_clamped(self):
        self.assertEqual([self.rules.clamp_order(v) for v in (-5, 0, 50, 100, 130)], [0, 0, 50, 100, 100])

    def test_tick_with_homeless_villagers(self):
        record = self.rules.tick_order(50, 4, 0, self.order_cfg())
        self.assertEqual(
            (record.order_before, record.manor_term, record.homeless_count, record.homeless_term, record.order_after),
            (50, 10, 4, 20, 40),
        )

    def test_tick_is_clamped(self):
        self.assertEqual(self.rules.tick_order(95, 0, 0, self.order_cfg()).order_after, 100)
        self.assertEqual(self.rules.tick_order(10, 5, 0, self.order_cfg()).order_after, 0)

    def test_order_bonus_is_added_to_the_manor_term(self):
        record = self.rules.tick_order(50, 0, 5, self.order_cfg())
        self.assertEqual((record.manor_term, record.order_after), (15, 65))

    def test_tick_is_due_after_tick_days(self):
        self.assertFalse(self.rules.tick_due(100, -1, 30))  # nothing saved: store only
        self.assertFalse(self.rules.tick_due(129, 100, 30))
        self.assertTrue(self.rules.tick_due(130, 100, 30))

    def test_timer_starts_below_the_threshold(self):
        self.assertEqual(self.timer(20, -1, 200)[0], "start")
        self.assertEqual(self.timer(25, -1, 200)[0], "none")

    def test_timer_waits_warns_and_expires(self):
        self.assertEqual(self.timer(20, 200, 230), ("wait", 60, False))
        self.assertEqual(self.timer(20, 200, 260), ("wait", 30, True))
        self.assertEqual(self.timer(20, 200, 290)[0], "leave")

    def test_timer_resets_when_order_reaches_the_threshold(self):
        self.assertEqual(self.timer(25, 200, 230)[0], "reset")
        self.assertEqual(self.timer(25, 200, 400)[0], "reset")  # also after the time ran out

    def test_leavers_keep_one_family(self):
        cfg = self.order_cfg()
        self.assertEqual([self.rules.leavers_for(n, cfg) for n in (40, 19, 10, 1, 0)], [18, 18, 9, 0, 0])

    def test_order_after_the_leave(self):
        cfg = self.order_cfg()
        self.assertEqual([self.rules.order_after_leave(n, cfg) for n in (20, 90)], [45, 100])

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

    def test_refund_is_what_the_game_took_up_to_the_price(self):
        self.assertEqual(self.rules.refund_amount(100, 80, 20), 20)
        self.assertEqual(self.rules.refund_amount(100, 70, 20), 20)  # income or other costs do not raise the refund
        self.assertEqual(self.rules.refund_amount(100, 100, 20), 0)
        self.assertEqual(self.rules.refund_amount(100, 130, 20), 0)

    def test_the_price_follows_the_slots_not_the_outstanding_families(self):
        self.assertIn("silver", self.rules.buy_back_refusal(self.facts(outstanding=6, free_slots=3, silver=29), self.cfg()))
        self.assertIsNone(self.rules.buy_back_refusal(self.facts(outstanding=6, free_slots=3, silver=30), self.cfg()))


if __name__ == "__main__":
    unittest.main()
