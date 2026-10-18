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
package.loaded["HarnessSack"] = nil -- HarnessManor may have loaded the real module first
SACK_REGIONS = {}   -- the region name that each call got
package.preload["HarnessSack"] = function()
    return {
        playerRegion = function(name) SACK_REGIONS[#SACK_REGIONS + 1] = "stores:" .. tostring(name); return require("ManorCore").player_region() end,
        sack_census = function(r) SACK_REGIONS[#SACK_REGIONS + 1] = "census:" .. tostring(r and r.region); return { ok = true, census = census() } end,
        sack_goods = function(r) village.goods[r.good] = village.goods[r.good] - r.amount; return { ok = true, removed = r.amount } end,
        sack_people = function(r) SACK_REGIONS[#SACK_REGIONS + 1] = "people:" .. tostring(r.region); village.families = village.families - r.count; return { ok = true, families = r.count, people = r.count * 2 } end,
        sack_buildings = function(r) SACK_REGIONS[#SACK_REGIONS + 1] = "buildings:" .. tostring(r.region); village.standing = village.standing - r.count; return { ok = true, hit = r.count } end,
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


class SackRegionTests(SackTestCase):
    """M06.04: the sack hits the region under attack, or the home region, and not the first region of the player."""

    def own_regions(self, *names):
        listing = ", ".join(f'"{name}"' for name in names)
        self.game.exec(f'require("features.sack_and_terms.world").player_region_names = function() return {{ {listing} }} end')

    def set_home(self, name):
        self.game.exec(f'require("features.vassals.init").state:set("vassals_home_region", "{name}")')

    def asked(self):
        return list(self.game.exec("return table.concat(SACK_REGIONS, ',')").split(","))

    def test_a_manual_sack_hits_the_home_region(self):
        self.own_regions("Capital", "Home")
        self.set_home("Home")
        self.sack_now(1)
        self.assertEqual(self.sack_state()["history"][0]["region"], "Home")
        self.assertTrue(all(call.endswith(":Home") for call in self.asked()), self.asked())

    def test_the_rule_prefers_the_target_then_the_home_then_nothing(self):
        self.game.exec("""local rules = require("features.sack_and_terms.rules")
            RESULT = rules.sack_region("Capital", "Home", { "Capital", "Home" }) .. "," .. rules.sack_region("Gone", "Home", { "Capital", "Home" }) .. "," .. tostring(rules.sack_region("Gone", "none", { "Capital" })) .. "," .. rules.sack_region(nil, "Home", { "Home" })""")
        self.assertEqual(self.game.exec("return RESULT"), "Capital,Home,nil,Home")

    def test_no_known_region_keeps_the_first_region_of_the_player(self):
        self.own_regions()
        self.sack_now(1)
        self.assertTrue(all(call.endswith(":nil") for call in self.asked()), self.asked())

    def test_a_raid_that_leaves_by_loot_sacks_its_own_target(self):
        self.own_regions("Capital", "Home")
        self.set_home("Home")
        self.game.exec('require("ManorCore").region_row = function() return { region = "Capital" } end') # the raid targets the capital
        self.make_raid_leave_by_loot()
        self.assertEqual(self.sack_state()["history"][0]["region"], "Capital")
        self.assertTrue(all(call.endswith(":Capital") for call in self.asked()), self.asked())

    def test_a_raid_on_a_region_the_player_does_not_own_sacks_the_home_region(self):
        self.own_regions("Home")
        self.set_home("Home")
        self.game.exec('require("ManorCore").region_row = function() return { region = "VassalLand" } end')
        self.make_raid_leave_by_loot()
        self.assertEqual(self.sack_state()["history"][0]["region"], "Home")


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


class TermsTests(SackTestCase):
    def setUp(self):
        super().setUp()
        self.pawn.silver = 500
        self.start_raid()

    def terms(self):
        return self.ask("terms_state")["result"]

    def test_the_offer_amounts_grow_with_the_difficulty(self):
        for difficulty, (payment, tribute) in {1: (100, 30), 2: (200, 60), 3: (300, 90)}.items():
            self.ask("invasion_set_difficulty", value=difficulty)
            offer = self.ask("terms_offer")["result"]["offer"]
            self.assertEqual((offer["payment"], offer["tribute"]), (payment, tribute))

    def test_a_payment_takes_the_silver_and_ends_the_raid_without_a_sack(self):
        self.ask("terms_offer")
        answer = self.ask("terms_accept", kind="payment")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.pawn.silver, 400)
        self.game.advance(3)
        self.assertEqual(self.raid()["leave_reason"], "terms")
        self.assertEqual(self.sack_state()["sack_count"], 0)
        self.assertEqual(self.terms()["state"], 2)

    def test_a_payment_without_enough_silver_is_refused(self):
        self.pawn.silver = 99
        self.ask("terms_offer")
        self.assertFalse(self.ask("terms_accept", kind="payment")["ok"])
        self.assertEqual((self.pawn.silver, self.raid().get("leave_reason")), (99, None))

    def test_accepting_without_an_offer_is_refused(self):
        self.assertFalse(self.ask("terms_accept", kind="payment")["ok"])

    def test_vassalage_costs_nothing_now_and_sets_the_tribute_day(self):
        self.ask("terms_offer")
        day = self.calendar.daysTotal
        self.assertTrue(self.ask("terms_accept", kind="vassalage")["ok"])
        state = self.terms()
        self.assertEqual((self.pawn.silver, state["state"], state["next_tribute_day"]), (500, 3, int(day) + 360))
        self.assertEqual(self.raid()["leave_reason"], "terms")

    def test_the_tribute_is_paid_on_its_day_and_never_more_than_the_silver(self):
        self.ask("terms_offer")
        self.ask("terms_accept", kind="vassalage")
        self.calendar.daysTotal = self.calendar.daysTotal + 361
        self.game.advance(4)
        self.assertEqual(self.pawn.silver, 470)
        self.assertGreater(self.terms()["next_tribute_day"], self.calendar.daysTotal)
        self.pawn.silver = 10
        self.calendar.daysTotal = self.calendar.daysTotal + 361
        self.game.advance(4)
        self.assertEqual(self.pawn.silver, 0)

    def test_a_declined_offer_leaves_the_raid_alone(self):
        self.ask("terms_offer")
        self.assertTrue(self.ask("terms_decline")["ok"])
        self.assertFalse(self.ask("terms_accept", kind="payment")["ok"])
        self.assertIsNone(self.raid().get("leave_reason"))


if __name__ == "__main__":
    unittest.main()
