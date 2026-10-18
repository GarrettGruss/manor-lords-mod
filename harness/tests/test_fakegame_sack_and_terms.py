"""Tests for the feature sack_and_terms of the pack mod (mod feature M06, iteration 01) in the fake game.

They run the real Lua files of the feature. HarnessSack is a small stand-in with a counted village: its own rules
are tested in test_fakegame_harnesssack.py. These tests do not prove how the real game behaves.
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_raid_behavior import SQUAD_UNITS, RaidBehaviorTestCase

SACK_STAND_IN = """
village = { standing = 10, goods = { [16] = 14, [3] = 4 }, families = 5 }
local function census()
    local by_good, total = {}, 0
    for kind, amount in pairs(village.goods) do by_good[kind] = amount; total = total + amount end
    return { buildings = { standing = village.standing, total = village.standing }, stock = { total = total, by_good = by_good },
             people = { families = village.families, population = village.families * 2 } }
end
package.preload["HarnessSack"] = function()
    return {
        sack_census = function() return { ok = true, census = census() } end,
        sack_goods = function(r) village.goods[r.good] = village.goods[r.good] - r.amount; return { ok = true, removed = r.amount } end,
        sack_people = function(r) village.families = village.families - r.count; return { ok = true, families = r.count, people = r.count * 2 } end,
        sack_buildings = function(r) village.standing = village.standing - r.count; return { ok = true, hit = r.count } end,
    }
end
"""


class SackTestCase(RaidBehaviorTestCase):
    def setUp(self):
        super().setUp()
        self.game.exec(SACK_STAND_IN)
        for store in self.stores:
            self.make_consumable(store)

    def make_consumable(self, store):
        def consume(_self, good, store=store):
            for index, (kind, amount) in enumerate(store["goods"]):
                if kind == good and amount > 0:
                    store["goods"][index] = (kind, amount - 1)
                    break
            store["object"].Inventory = self.game.array([self.game.struct(Type=k, amt=a) for k, a in store["goods"]])

        self.game.method(store["object"], "consumeGoodNoCheck", consume)

    def held_by_good(self):
        held = {}
        for store in self.stores:
            for kind, amount in store["goods"]:
                held[kind] = held.get(kind, 0) + amount
        return held

    def sync_stand_in_stock(self):
        entries = ", ".join(f"[{kind}] = {amount}" for kind, amount in self.held_by_good().items())
        self.game.exec("village.goods = { " + entries + " }")

    def sack_now(self, difficulty=None):
        args = {} if difficulty is None else {"difficulty": difficulty}
        answer = self.ask("sack_now", **args)
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def sack_state(self):
        return self.ask("sack_state")["result"]

    def set_village(self, standing=10, families=5):
        self.game.exec(f"village.standing = {standing}; village.families = {families}")

    def make_raid_leave_by_loot(self):
        self.start_raid()
        for unit in self.units[-SQUAD_UNITS:]:
            unit.ItemsLooted = 4
        self.game.advance(3)


class SackSizeTests(SackTestCase):
    def test_the_sack_share_is_linear_and_every_count_rounds_up(self):
        expected = {1: (20, 2, 1), 2: (35, 4, 2), 3: (50, 5, 3)}  # percent, buildings, families
        for difficulty, (percent, buildings, families) in expected.items():
            self.set_village()
            self.sync_stand_in_stock()
            held = self.held_by_good()
            want = sum(-(-amount * percent // 100) for amount in held.values())
            result = self.sack_now(difficulty)
            self.assertEqual(result["percent"], percent)
            self.assertEqual((result["taken"]["buildings_hit"], result["taken"]["families_removed"]), (buildings, families), difficulty)
            # The fake method wrapper may run one call twice, so the count of the mod is compared, not the fake stores.
            self.assertEqual(result["taken"]["goods_removed"], want, (difficulty, held))
            self.calendar.daysTotal = self.calendar.daysTotal + 400  # a new window for the next difficulty

    def test_a_normal_sack_keeps_one_family(self):
        self.set_village(families=1)
        result = self.sack_now(3)
        self.assertEqual((result["taken"]["families_removed"], result["after"]["families"]), (0, 1))
        self.set_village(families=2)
        self.calendar.daysTotal = self.calendar.daysTotal + 400
        self.assertEqual(self.sack_now(3)["after"]["families"], 1)

    def test_the_difficulty_comes_from_the_invasion_state_by_default(self):
        self.ask("invasion_set_difficulty", value=3)
        self.assertEqual(self.sack_now()["difficulty"], 3)


class RepeatedSackTests(SackTestCase):
    def test_the_second_sack_in_the_window_is_fatal_and_takes_every_family(self):
        first = self.sack_now(1)
        self.assertFalse(first["fatal"])
        second = self.sack_now(1)
        self.assertTrue(second["fatal"])
        self.assertEqual(second["after"]["families"], 0)

    def test_with_the_fatal_switch_off_the_limit_is_flagged_and_people_stay(self):
        self.ask("sack_set_fatal", enabled=False)
        self.sack_now(1)
        second = self.sack_now(1)
        self.assertTrue(second["limit_reached"])
        self.assertFalse(second["fatal"])
        self.assertGreater(second["after"]["families"], 0)

    def test_a_sack_after_the_window_starts_a_new_window(self):
        self.sack_now(1)
        self.calendar.daysTotal = self.calendar.daysTotal + 361
        third = self.sack_now(1)
        self.assertEqual((third["window_count"], third["fatal"]), (1, False))
        self.assertEqual(self.sack_state()["sack_count"], 2)

    def test_the_counter_is_kept_in_the_pawn_tags(self):
        self.sack_now(1)
        tags = list(self.game.lua.eval("tag_names")(self.pawn).values())
        self.assertIn("invasion:sack_count=1", tags)
        self.assertIn("invasion:sack_window_count=1", tags)


class LostBattleTests(SackTestCase):
    def test_a_raid_that_leaves_with_its_loot_sacks_the_town_once(self):
        self.make_raid_leave_by_loot()
        state = self.sack_state()
        self.assertEqual(state["sack_count"], 1)
        self.assertEqual(state["history"][0]["reason"], "loot")
        self.game.advance(5)
        self.assertEqual(self.sack_state()["sack_count"], 1)

    def test_a_raid_that_leaves_at_the_time_limit_sacks_the_town(self):
        self.start_raid()
        self.calendar.daysTotal = self.calendar.daysTotal + 30
        self.game.advance(3)
        self.assertEqual(self.sack_state()["history"][0]["reason"], "time")

    def test_a_raid_that_lost_many_raiders_does_not_sack_the_town(self):
        self.start_raid()
        for unit in self.units[-SQUAD_UNITS:][: SQUAD_UNITS // 2]:
            unit.dead = True
        self.game.advance(3)
        self.assertEqual(self.raid()["leave_reason"], "losses")
        self.assertEqual(self.sack_state()["sack_count"], 0)

    def test_a_native_raid_does_not_sack_the_town(self):
        self.ask("invasion_set_roles", enabled=False)
        self.start_raid()
        for unit in self.units[-SQUAD_UNITS:]:
            unit.ItemsLooted = 4
        self.calendar.daysTotal = self.calendar.daysTotal + 30
        self.game.advance(3)
        self.assertEqual(self.sack_state()["sack_count"], 0)


if __name__ == "__main__":
    unittest.main()
