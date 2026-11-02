"""Tests for the feature tribute of the player mod (mod feature M08, change update-vassal-tribute-rich-resources) in the fake game.

They run the real Lua files. The stores of the village are a stub (raid_behavior.world.stores; the building is a stub with addToInventory).
The resource nodes are fake objects with a decal and clumps. They do not prove how the real game behaves
(see the real-game test scenarios of the tribute feature).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_vassals import HandoverBase

STORE_STUB = """
HELD = {}
DEPOSITS = {}
local rw = require("features.raid_behavior.world")
STORE_BUILDING = {
    Inventory = {},
    addToInventory = function(self, item)
        if REFUSE then return end
        self.Inventory[#self.Inventory + 1] = { Type = item.Type, amt = item.amt }
        HELD[item.Type] = (HELD[item.Type] or 0) + item.amt
        DEPOSITS[#DEPOSITS + 1] = item.Type .. ":" .. item.amt
    end,
}
rw.stores = function() return { { by_good = { [30] = 100 }, id = 1, building = STORE_BUILDING } } end
"""

REGION_X = {"Home": 0, "Eichenhau": 100}  # a node at this X lies in that region; any other X lies in no region
IRON, STONE, SALT, CLAY, CARP, EEL, BERRIES, MUSHROOMS, FLAX = 14, 27, 145, 146, 30, 32, 171, 279, 11
MATERIAL = {"iron": "depositMaterial", "stone": "depositMaterial_Stone", "salt": "depositMaterial_Salt", "clay": "depositMaterial_Clay"}
CLUMP_CLASS = {"berries": "Resource_Berries_C", "carp": "Resource_Fish_C", "eel": "Resource_Eel_C", "mushrooms": "Resource_Mushrooms_C"}


class TributeTests(HandoverBase):
    def setUp(self):
        super().setUp()
        self.game.exec(STORE_STUB)
        self.calendar.month = 3
        self.install_region_lookup(self.engine)
        region = self.add_region("Eichenhau", True, 4)
        self.game.method(region, "getTotalNumFamilies", lambda _self: 5)
        self.game.advance(10)
        self.lord_owns("Eichenhau")

    # -- helpers ---------------------------------------------------------------------------

    def install_region_lookup(self, engine):
        def by_pos(_self, pos, _flag):
            for name, x in REGION_X.items():
                if pos["X"] == x:
                    return self.region_by_name[name]
            return None
        self.game.method(engine, "getRegionByPos", by_pos)

    def named(self, class_name, name):
        """A fake object whose GetFName gives `name`."""
        obj = self.game.obj(class_name)
        self.game.method(obj, "GetFName", lambda _self: self.game.text(name))
        return obj

    def clumps(self, class_name, capacities):
        cls = self.named("Class", class_name)
        out = []
        for capacity in capacities:
            clump = self.game.obj("ClumpActor", capacity=capacity)
            self.game.method(clump, "GetClass", lambda _self, cls=cls: cls)
            out.append(clump)
        return out

    def node(self, region="Eichenhau", material=None, size=128, clumps=()):
        """A ResourceNode. `material` is the decal material name or None (a clump node has no material)."""
        decal = self.game.obj("DecalComponent", DecalSize=self.game.struct(X=size, Y=size, Z=100))
        mat = self.named("MaterialInstance", material) if material else self.game.obj("MaterialInstance")
        if material:
            self.game.method(decal, "GetDecalMaterial", lambda _self, mat=mat: mat)
        else:
            self.game.method(decal, "GetDecalMaterial", lambda _self: None)
        x = REGION_X.get(region, 999)
        self.game.method(decal, "K2_GetComponentLocation", lambda _self, x=x: self.game.struct(X=x, Y=5, Z=0))
        return self.game.obj("ResourceNode", ResourceZoneDecal=decal, resourceClumps=self.game.array(list(clumps)))

    def deposit(self, good, region="Eichenhau", size=5000):
        return self.node(region, MATERIAL[good], size)

    def clump_node(self, good, capacities, region="Eichenhau"):
        return self.node(region, None, 128, self.clumps(CLUMP_CLASS[good], capacities))

    def held(self, good):
        return self.game.exec(f"return HELD[{good}] or 0")

    def tribute(self):
        answer = self.ask("tribute_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def change_month(self):
        self.calendar.month = self.calendar.month % 12 + 1
        self.game.advance(5)

    def pay(self):
        """One monthly tick. Returns the first payment of the last tick."""
        self.change_month()
        return self.tribute()["history"][-1]["payments"][0]

    def paid_names(self, payment):
        return [good["name"] for good in payment["goods"]]

    # -- amount and policy -------------------------------------------------------------------

    def test_payout_rules_without_the_game(self):
        amounts = [self.game.exec(f'return require("features.tribute.rules").amount(100, {factor})') for factor in (0.5, 1.0, 1.5, 0.0)]
        self.assertEqual(amounts, [50, 100, 150, 0])

    def test_one_vassal_pays_100_of_each_of_two_rich_goods(self):
        self.deposit("stone")
        self.clump_node("mushrooms", [61, 61])
        payment = self.pay()
        self.assertEqual((self.held(STONE), self.held(MUSHROOMS), self.held(FLAX)), (100, 100, 0))
        self.assertEqual(payment["amount"], 100)
        self.assertEqual(sorted(payment["rich"]), ["mushrooms", "stone"])
        self.assertEqual(self.tribute()["paid_total"], 200)

    def test_the_policy_scales_every_good(self):
        self.deposit("iron")
        self.deposit("salt")
        for policy, expected in (("heavy", 150), ("light", 50), ("fair", 100)):
            self.ask("vassals_set_policy", slot=1, policy=policy)
            payment = self.pay()
            self.assertEqual((payment["policy"], payment["amount"]), (policy, expected))
            self.assertEqual([good["paid"] for good in payment["goods"]], [expected, expected])

    def test_the_tech_factor_keeps_multiplying_the_amount(self):
        self.deposit("iron")
        self.game.exec('require("features.tribute.init").set_share_factor(2)')
        self.assertEqual(self.pay()["amount"], 200)

    # -- detection ---------------------------------------------------------------------------

    def test_goods_of_other_regions_are_not_paid(self):
        self.deposit("stone", region="Home")
        self.deposit("salt", region="Eichenhau")
        payment = self.pay()
        self.assertEqual(self.paid_names(payment), ["salt", "flax"])
        self.assertEqual(self.held(STONE), 0)

    def test_a_node_outside_every_region_is_ignored(self):
        self.deposit("stone", region="Nowhere")
        self.assertEqual(self.paid_names(self.pay()), ["flax", "flax"])

    def test_a_poor_node_is_ignored(self):
        self.deposit("clay", size=4000)
        self.clump_node("berries", [60, 60])      # 120 < 130
        self.clump_node("mushrooms", [60, 61])    # 121 < 122
        self.assertEqual(self.pay()["rich"], [])

    def test_the_limits_are_inclusive_and_clumps_add_up(self):
        self.clump_node("berries", [65, 65])      # 130
        self.clump_node("carp", [100, 100, 185])  # 385
        self.assertEqual(self.pay()["rich"], ["berries", "carp"])

    def test_eel_and_fish_have_their_own_good_ids(self):
        self.clump_node("eel", [385])
        payment = self.pay()
        self.assertEqual((self.held(EEL), self.held(CARP)), (100, 0))
        self.assertEqual(payment["goods"][0]["id"], EEL)

    def test_game_never_counts(self):
        self.node("Eichenhau", "deerDecal_Mat", 5000)
        payment = self.pay()
        self.assertEqual(payment["rich"], [])
        self.assertEqual(self.paid_names(payment), ["flax", "flax"])

    def test_a_node_without_a_decal_or_with_a_broken_read_is_ignored(self):
        self.game.obj("ResourceNode", ResourceZoneDecal=None, resourceClumps=self.game.array([]))
        self.deposit("iron")
        self.assertEqual(self.pay()["rich"], ["iron"])

    # -- choice of the two goods -------------------------------------------------------------

    def test_a_region_with_no_rich_resource_pays_flax_twice(self):
        payment = self.pay()
        self.assertEqual(self.paid_names(payment), ["flax", "flax"])
        self.assertEqual(self.held(FLAX), 200)
        self.assertEqual(self.tribute()["paid_total"], 200)

    def test_a_region_with_one_rich_resource_pays_it_and_flax(self):
        self.clump_node("mushrooms", [122])
        payment = self.pay()
        self.assertEqual(self.paid_names(payment), ["mushrooms", "flax"])
        self.assertEqual((self.held(MUSHROOMS), self.held(FLAX)), (100, 100))

    def test_more_than_two_rich_resources_keep_two_by_tier_and_list_order(self):
        for good in ("clay", "salt", "iron"):
            self.deposit(good)
        self.clump_node("berries", [130])
        payment = self.pay()
        self.assertEqual(self.paid_names(payment), ["iron", "salt"])
        self.assertEqual(payment["dropped"], ["clay", "berries"])
        self.assertEqual((self.held(CLAY), self.held(BERRIES), self.held(FLAX)), (0, 0, 0))

    def test_the_ore_tier_order_is_iron_then_stone_then_salt(self):
        for good in ("salt", "stone", "iron"):
            self.deposit(good)
        self.assertEqual(self.paid_names(self.pay()), ["iron", "stone"])

    def test_clay_and_fish_come_before_berries_and_mushrooms(self):
        self.clump_node("berries", [130])
        self.clump_node("mushrooms", [122])
        self.clump_node("eel", [385])
        self.assertEqual(self.paid_names(self.pay()), ["eel", "berries"])

    def test_flax_is_only_added_when_fewer_than_two_are_detected(self):
        self.deposit("iron")
        self.deposit("stone")
        self.deposit("salt")
        payment = self.pay()
        self.assertNotIn("flax", self.paid_names(payment))
        self.assertEqual(self.held(FLAX), 0)

    # -- cache -------------------------------------------------------------------------------

    def scans(self):
        return self.game.exec('return require("features.tribute.world").scan_count()')

    def test_two_ticks_scan_the_nodes_once(self):
        self.deposit("iron")
        self.pay()
        self.pay()
        self.assertEqual(self.scans(), 1)
        self.assertEqual(self.held(IRON), 200)

    def test_the_nodes_are_read_again_after_a_load(self):
        self.deposit("iron")
        first = self.pay()
        old = self.engine
        engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn, TemporalComponent=self.calendar,
                               regions=old.regions, debugLog_AI_general=self.game.array([]))
        self.install_region_lookup(engine)
        self.game.invalidate(old)
        self.game.advance(5)
        second = self.pay()
        self.assertEqual(self.scans(), 2)
        self.assertEqual(self.paid_names(second), self.paid_names(first))

    def test_a_scan_with_no_node_is_not_cached(self):
        payment = self.pay()
        self.assertEqual(self.scans(), 1)
        self.deposit("iron")
        self.assertEqual(self.pay()["rich"], ["iron"])
        self.assertEqual(self.scans(), 2)
        self.assertEqual(self.paid_names(payment), ["flax", "flax"])

    # -- the clock ---------------------------------------------------------------------------

    def test_one_payment_for_one_month_change(self):
        self.change_month()
        self.game.advance(30)
        self.assertEqual(self.tribute()["ticks"], 1)
        self.change_month()
        self.assertEqual(self.tribute()["ticks"], 2)

    def test_a_season_change_in_the_same_month_pays_nothing(self):
        self.calendar.Season = (self.calendar.Season + 1) % 4
        self.game.advance(5)
        self.assertEqual(self.tribute()["ticks"], 0)

    def test_december_to_january_is_a_month_change(self):
        self.calendar.month = 12
        self.game.advance(5)
        ticks = self.tribute()["ticks"]
        self.calendar.month = 1
        self.game.advance(5)
        self.assertEqual(self.tribute()["ticks"], ticks + 1)

    def test_no_tick_on_the_first_poll(self):
        self.assertEqual(self.tribute()["ticks"], 0)

    def test_the_forced_tick_pays_at_once(self):
        self.deposit("iron")
        answer = self.ask("tribute_tick_now")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["result"]["paid_total"], 200)

    # -- who pays ----------------------------------------------------------------------------

    def test_a_restored_vassal_pays_no_tribute_until_the_village_is_rebuilt(self):
        self.game.exec("local v = require('features.vassals.init'); v.state:set('vassal1_rebuilding', true)")
        self.change_month()
        self.assertEqual(self.tribute()["paid_total"], 0)
        self.assertEqual(self.game.exec("return #DEPOSITS"), 0)
        self.game.exec("local v = require('features.vassals.init'); v.state:set('vassal1_rebuilding', false)")
        self.change_month()
        self.assertEqual(self.tribute()["paid_total"], 200)

    def test_no_vassal_no_tribute(self):
        self.game.exec("local v = require('features.vassals.init'); v.state:set('vassal1_lord', 'none')")
        self.change_month()
        self.assertEqual(self.tribute()["paid_total"], 0)
        self.assertEqual(self.game.exec("return #DEPOSITS"), 0)

    def test_a_refused_deposit_is_counted_and_not_paid(self):
        self.game.exec("REFUSE = true")
        self.change_month()
        state = self.tribute()
        self.assertEqual(state["paid_total"], 0)
        self.assertEqual(state["failed_deposits"], 2)

    def test_the_state_command_has_goods_and_rich_and_no_old_fields(self):
        self.deposit("stone")
        payment = self.pay()
        self.assertEqual(payment["goods"][0], {"name": "stone", "id": STONE, "paid": 100})
        for old in ("families", "production", "share", "finite"):
            self.assertNotIn(old, payment)
        self.assertNotIn("finite_paid", self.tribute())

    # -- vassal targets and siege (M02 iteration 07) ----------------------------------------

    def stub_raid(self, living=18, age=9, target="Eichenhau", kind="subjugation"):
        today = self.calendar.daysTotal
        self.game.exec(f'''require("features.raid_behavior.init").active_raids = function()
            return {{ {{ id = 7, kind = "{kind}", state = "active", target = "{target}", start_day = {today - age}, initial = 18, living = {living} }} }}
        end''')
        self.game.advance(150)

    def test_the_target_regions_are_the_handed_over_vassals(self):
        self.assertEqual(self.game.exec("local r = require('features.vassals.init').target_regions(); return table.concat(r, ',')"), "Eichenhau")

    def test_a_subjugation_raid_that_held_8_days_sacks_and_wipes_the_vassal(self):
        self.stub_raid(living=18, age=9)
        state = self.state()
        self.assertEqual(state["lost"], 1)
        self.assertEqual(state["lost_events"][0]["reason"], "wiped")
        self.assertEqual(state["count"], 0)
        self.assertEqual(len(self.ruins["Eichenhau"]), 4)
        self.assertEqual(self.tribute()["siege"], {"7": "taken"})

    def test_the_vassal_is_lost_only_once(self):
        self.stub_raid(age=9)
        self.stub_raid(age=20)
        self.assertEqual(self.state()["lost"], 1)

    def test_a_raid_younger_than_8_days_takes_nothing(self):
        self.stub_raid(age=5)
        self.assertEqual(self.state()["lost"], 0)

    def test_a_beaten_raid_fails_and_the_vassal_stays(self):
        self.stub_raid(living=8, age=9)
        self.assertEqual(self.state()["lost"], 0)
        self.assertEqual(self.tribute()["siege"], {"7": "failed"})

    def test_a_plunder_raid_or_a_raid_on_home_takes_nothing(self):
        self.stub_raid(age=9, kind="plunder")
        self.stub_raid(age=9, target="Home")
        self.assertEqual(self.state()["lost"], 0)


if __name__ == "__main__":
    unittest.main()
