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
            "manor_term": 10, "homeless_term": 5, "threshold": 25, "timer_days": 60, "warn_days": 30,
            "rebellion_families": 6, "order_gain": 25, "min_families_left": 1,
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
        self.assertEqual(self.timer(20, 200, 230), ("wait", 30, True))
        self.assertEqual(self.timer(20, 200, 250), ("wait", 10, True))
        self.assertEqual(self.timer(20, 200, 260)[0], "leave")
        self.assertEqual(self.timer(20, 200, 220), ("wait", 40, False))

    def test_timer_resets_when_order_reaches_the_threshold(self):
        self.assertEqual(self.timer(25, 200, 230)[0], "reset")
        self.assertEqual(self.timer(25, 200, 400)[0], "reset")  # also after the time ran out

    def test_leavers_keep_one_family(self):
        cfg = self.order_cfg()
        self.assertEqual([self.rules.leavers_for(n, cfg) for n in (40, 19, 10, 1, 0)], [6, 6, 6, 0, 0])
        self.assertEqual([self.rules.leavers_for(n, cfg) for n in (7, 6, 3)], [6, 5, 2])

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

    # -- rebellion (change update-banditry-rebellion-raid) --------------------------------------

    def test_the_default_config_values(self):
        self.lua.execute("Key = setmetatable({}, { __index = function(_, name) return name end })")
        config = self.lua.execute((find_pack_mod() / "Scripts" / "config.lua").read_text(encoding="utf-8"))
        bandits = config.bandits
        self.assertEqual((bandits.threshold, bandits.timer_days, bandits.order_gain, bandits.tick_days), (25, 60, 25, 30))
        self.assertEqual((bandits.rebellion_families, bandits.rebellion_squads, bandits.loot_override_slots), (6, 1, 200))
        self.assertEqual(sorted(bandits.rebellion_weapon_ids.values()), [133, 163, 164, 177, 178, 205, 206, 270, 271, 273, 288, 289])
        self.assertIsNone(bandits.leavers)

    def inventory(self, *rows):
        return self.lua.table_from([self.lua.table_from({"id": i, "amount": a}) for i, a in rows])

    def test_a_home_is_valid_with_one_weapon_or_armor_item(self):
        ids = self.rules.id_set(self.lua.table_from([133, 271]))
        self.assertEqual(list(self.rules.armed_goods(self.inventory((133, 2), (15, 9), (271, 1)), ids).values()), [133, 133, 271])
        self.assertEqual(list(self.rules.armed_goods(self.inventory((15, 9), (3, 2)), ids).values()), [])
        self.assertEqual(list(self.rules.armed_goods(self.inventory(), ids).values()), [])

    def test_the_pick_takes_the_wanted_number_without_repeats(self):
        valid = self.lua.table_from(list(range(1, 10)))
        picked = list(self.rules.pick_families(valid, 6, lambda n: 1).values())  # always the first of the rest
        self.assertEqual(picked, [1, 2, 3, 4, 5, 6])
        picked = list(self.rules.pick_families(valid, 6, lambda n: n).values())  # always the last of the rest
        self.assertEqual(picked, [9, 8, 7, 6, 5, 4])
        self.assertEqual(len(list(valid.values())), 9)  # the input stays
        self.assertEqual(len(list(self.rules.pick_families(valid, 20, lambda n: 1).values())), 9)

    def test_the_rebellion_is_blocked_with_too_few_valid_families(self):
        self.assertIsNone(self.rules.rebellion_block(6, 6))
        self.assertIsNone(self.rules.rebellion_block(9, 6))
        self.assertEqual(self.rules.rebellion_block(5, 6), "5 valid families found, 6 needed")
        self.assertIn("0 valid", self.rules.rebellion_block(0, 6))

    def test_goods_spread_round_robin_over_the_units(self):
        spread = self.rules.spread_goods(self.lua.table_from(list(range(100, 130))), 18)
        lists = [list(spread[i].values()) for i in range(1, 19)]
        self.assertEqual(sorted(g for row in lists for g in row), list(range(100, 130)))  # 30 goods, none twice
        self.assertEqual(sorted(len(row) for row in lists), [1] * 6 + [2] * 12)
        few = self.rules.spread_goods(self.lua.table_from([1, 2, 3]), 18)
        self.assertEqual([len(list(few[i].values())) for i in range(1, 19)], [1, 1, 1] + [0] * 15)

    def test_a_blocked_rebellion_retries_only_after_a_new_tick(self):
        self.assertTrue(self.rules.retry_due(None, 100))
        self.assertFalse(self.rules.retry_due(100, 100))
        self.assertTrue(self.rules.retry_due(100, 130))


if __name__ == "__main__":
    unittest.main()
