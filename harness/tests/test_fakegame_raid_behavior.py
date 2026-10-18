"""Tests for the feature raid_behavior of the pack mod (mod feature M03, iteration 01) in the fake game.

They run the real Lua files. The fake world has a calendar, a raid spawn that makes units, a village with two stores
and a unit list. They do not prove how the real game behaves.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from test_fakegame_modstate import FNAME, HELPERS, find_pack_mod

SQUAD_UNITS = 18
EXIT_Y = -85000


class RaidBehaviorTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        pack = find_pack_mod()
        self.mod_name = pack.name
        self.game.exec(f'package.path = "{(pack / "Scripts").as_posix()}/?.lua;" .. package.path')
        self.game.exec(FNAME + HELPERS)
        self.units, self.addresses, self.stores = [], {}, []
        self.pawn = self.game.obj("PawnCPP", Tags=self.game.array([]))
        self.game.method(self.pawn, "playEventMessage", lambda _self, _kind, _text, _sub: None)
        self.game.method(self.pawn, "K2_GetActorLocation", lambda _self: self.game.struct(X=0.0, Y=0.0, Z=0.0))
        self.game.method(self.pawn, "GetAddress", lambda _self: 1)
        self.calendar = self.game.obj("TemporalComponent", daysTotal=61, daysUntilNextRaid=730)
        self.region = self.game.obj("Region", ownerPawn=self.pawn)
        self.game.method(self.region, "GetBuildings", lambda _self: self.game.lua.table_from([s["object"] for s in self.stores]))
        self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn, TemporalComponent=self.calendar,
                                    regions=self.game.array([self.region]), debugLog_AI_general=self.game.array([]))
        self.game.method(self.engine, "spawnRaiders", lambda _self, squads, _centre: self.make_raiders(squads))
        self.bandit = self.game.obj("PawnCPP", isBandit=True)
        self.game.method(self.engine, "spawnArmy", lambda _self, _point, names, _owner, _company, _days: self.make_raiders(len(names)))
        self.add_store("Supplies_5", x=0.0, y=0.0, goods=[(16, 10), (3, 4)])
        self.add_store("Supplies_9", x=5000.0, y=5000.0, goods=[(7, 2)])
        self.game.load_mod(self.mod_name)
        self.game.advance(2)
        self.counter = 0

    # -- the fake village and the fake units ---------------------------------------------

    def add_store(self, name, x, y, goods):
        building = self.game.obj("SMBuildingMaster", Inventory=self.game.array([self.game.struct(Type=t, amt=a) for t, a in goods]))
        store = {"object": building, "goods": list(goods)}
        self.stores.append(store)
        self.game.method(building, "IsRubble", lambda _self: False)
        self.game.method(building, "GetFullName", lambda _self: f"SMBuildingMaster /Game/Map.{name}")
        self.game.method(building, "K2_GetActorLocation", lambda _self: self.game.struct(X=x, Y=y, Z=0.0))

        def add(_self, good):
            store["goods"].append((good["Type"], good["amt"]))
            building.Inventory = self.game.array([self.game.struct(Type=t, amt=a) for t, a in store["goods"]])

        self.game.method(building, "addToInventory", add)
        return store

    def make_unit(self, x=100.0, y=100.0, loot=0):
        unit = self.game.obj("SMUnit", dead=False, ItemsLooted=loot, realPos=self.game.struct(X=x, Y=y, Z=0.0),
                             assignedSquadID=self.game.struct(Value=7))
        number = 1000 + len(self.units)
        self.game.method(unit, "GetAddress", lambda _self, number=number: number)
        self.game.method(unit, "just_die", lambda _self, unit=unit: setattr(unit, "dead", True))
        self.units.append(unit)
        return unit

    def make_raiders(self, squads):
        for _ in range(squads * SQUAD_UNITS):
            self.make_unit()

    def stock(self, store):
        return sum(amount for _, amount in store["goods"])

    # -- the commands --------------------------------------------------------------------

    def ask(self, name, **args):
        self.counter += 1
        folder = self.game.run_dir / "modcmd" / self.mod_name
        folder.mkdir(parents=True, exist_ok=True)
        body = {"id": f"{self.counter:04d}", "command": f"{self.mod_name}.{name}", "args": args}
        (folder / f"{self.counter:04d}.json").write_text(json.dumps(body), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{self.counter:04d}.result.json").read_text(encoding="utf-8"))

    def raid(self):
        answer = self.ask("raid_behavior_state")
        self.assertTrue(answer["ok"], answer)
        raids = answer["result"]["raids"]
        return raids[0] if raids else None

    def start_raid(self, size="small"):
        self.ask("invasion_state")
        self.ask("invasion_set_size", size=size)
        self.assertTrue(self.ask("invasion_force_next")["ok"])
        self.game.advance(3)


class RaidStartTests(RaidBehaviorTestCase):
    def test_no_raid_before_the_spawn(self):
        self.assertEqual(self.ask("raid_behavior_state")["result"]["raids"], [])

    def test_a_spawn_starts_a_raid_with_all_new_units(self):
        self.start_raid("small")
        raid = self.raid()
        self.assertEqual((raid["state"], raid["initial"], raid["living"], raid["squads"]), ("active", SQUAD_UNITS, SQUAD_UNITS, 1))

    def test_units_that_existed_before_are_not_raiders(self):
        self.make_unit()
        self.start_raid("small")
        self.assertEqual(self.raid()["initial"], SQUAD_UNITS)


class LootTests(RaidBehaviorTestCase):
    def raiders(self):
        return self.units[-SQUAD_UNITS:]

    def test_loot_of_a_dead_raider_goes_to_the_nearest_store(self):
        self.start_raid()
        victim = self.raiders()[0]
        victim.ItemsLooted = 4
        victim.realPos = self.game.struct(X=10.0, Y=10.0, Z=0.0)
        self.game.advance(2)
        victim.dead = True
        victim.ItemsLooted = 0
        self.game.advance(2)
        raid = self.raid()
        self.assertEqual((raid["living"], raid["deaths"], raid["returned"], raid["lost"]), (SQUAD_UNITS - 1, 1, 4, 0))
        self.assertEqual(self.stock(self.stores[0]), 14 + 4)
        self.assertEqual(self.stock(self.stores[1]), 2)
        self.assertIn((16, 4), self.stores[0]["goods"])  # the good that the store holds most of

    def test_a_far_death_uses_the_far_store(self):
        self.start_raid()
        victim = self.raiders()[0]
        victim.ItemsLooted = 3
        victim.realPos = self.game.struct(X=4900.0, Y=5100.0, Z=0.0)
        self.game.advance(2)
        victim.dead = True
        self.game.advance(2)
        self.assertEqual(self.stock(self.stores[1]), 2 + 3)

    def test_a_unit_that_vanishes_inland_counts_as_dead(self):
        self.start_raid()
        victim = self.raiders()[0]
        victim.ItemsLooted = 2
        self.game.advance(2)
        self.game.invalidate(victim)
        self.game.advance(2)
        self.assertEqual((self.raid()["deaths"], self.raid()["returned"]), (1, 2))

    def test_a_unit_that_walks_off_the_map_keeps_its_loot(self):
        self.start_raid()
        leaver = self.raiders()[0]
        leaver.ItemsLooted = 5
        leaver.realPos = self.game.struct(X=0.0, Y=float(EXIT_Y - 100), Z=0.0)
        self.game.advance(2)
        self.game.invalidate(leaver)
        self.game.advance(2)
        raid = self.raid()
        self.assertEqual((raid["departures"], raid["deaths"], raid["returned"]), (1, 0, 0))
        self.assertEqual(self.stock(self.stores[0]), 14)
        self.assertGreaterEqual(raid["looted_total"], 5)

    def test_a_unit_that_dies_in_view_at_the_edge_is_dead_not_left(self):
        self.start_raid()
        victim = self.raiders()[0]
        victim.ItemsLooted = 2
        victim.realPos = self.game.struct(X=0.0, Y=float(EXIT_Y - 100), Z=0.0)
        self.game.advance(2)
        victim.dead = True
        self.game.advance(2)
        raid = self.raid()
        self.assertEqual((raid["deaths"], raid["departures"], raid["returned"]), (1, 0, 2))

    def test_loot_above_the_carry_cap_is_cut(self):
        self.start_raid()
        unit = self.raiders()[0]
        unit.ItemsLooted = 15
        self.game.advance(2)
        self.assertEqual(unit.ItemsLooted, 10)
        self.assertEqual(self.raid()["capped"], 1)

    def test_no_store_means_the_loot_is_lost(self):
        self.stores.clear()
        self.start_raid()
        victim = self.raiders()[0]
        victim.ItemsLooted = 3
        self.game.advance(2)
        victim.dead = True
        self.game.advance(2)
        raid = self.raid()
        self.assertEqual((raid["returned"], raid["lost"]), (0, 3))


class EndTests(RaidBehaviorTestCase):
    def test_the_raid_ends_destroyed_when_all_raiders_die(self):
        self.start_raid()
        for unit in self.units:
            unit.dead = True
        self.game.advance(2)
        raid = self.raid()
        self.assertEqual((raid["state"], raid["living"]), ("destroyed", 0))

    def test_the_raid_ends_left_when_raiders_walk_off(self):
        self.start_raid()
        for unit in self.units:
            unit.ItemsLooted = 1
            unit.realPos = self.game.struct(X=0.0, Y=float(EXIT_Y - 1), Z=0.0)
        self.game.advance(2)
        for unit in self.units:
            self.game.invalidate(unit)
        self.game.advance(2)
        self.assertEqual(self.raid()["state"], "left")

    def test_the_native_leave_line_is_noticed(self):
        self.start_raid()
        self.engine.debugLog_AI_general = self.game.array([self.game.text("Outlaws (36) Army - enough looted. Leaving map.")])
        self.game.advance(2)
        self.assertTrue(self.raid()["leaving"])
        self.assertEqual(self.raid()["state"], "left")

    def test_the_numbers_are_kept_in_the_pawn_tags(self):
        self.start_raid()
        tags = list(self.game.lua.eval("tag_names")(self.pawn).values())
        self.assertIn("invasion:raid_count=1", tags)
        self.assertIn("invasion:raid_state=1", tags)


class RoleRaidLeaveTests(RaidBehaviorTestCase):
    def raiders(self):
        return self.units[-SQUAD_UNITS:]

    def go_far(self):
        for unit in self.raiders():
            unit.realPos = self.game.struct(X=60000.0, Y=0.0, Z=0.0)

    def stores_total(self):
        return sum(self.stock(store) for store in self.stores)

    def test_a_role_raid_leaves_after_enough_loot_and_the_loot_leaves_with_it(self):
        self.start_raid()
        stock = self.stores_total()
        for unit in self.raiders():
            unit.ItemsLooted = 4
        self.game.advance(3)
        self.assertEqual((self.raid()["leave_reason"], self.raid()["living"]), ("loot", SQUAD_UNITS))  # near the village: kept
        self.assertFalse(any(unit.dead for unit in self.raiders()))
        self.go_far()
        self.game.advance(3)
        raid = self.raid()
        self.assertEqual((raid["state"], raid["leave_reason"], raid["living"]), ("left", "loot", 0))
        self.assertEqual((raid["departures"], raid["deaths"], raid["carried_out"], raid["returned"]), (SQUAD_UNITS, 0, 4 * SQUAD_UNITS, 0))
        self.assertEqual(self.stores_total(), stock)
        self.assertTrue(all(unit.dead for unit in self.raiders()))

    def test_a_role_raid_leaves_after_enough_losses(self):
        self.start_raid()
        for unit in self.raiders()[: SQUAD_UNITS // 2]:
            unit.dead = True
        self.game.advance(3)
        self.go_far()
        self.game.advance(3)
        raid = self.raid()
        self.assertEqual((raid["state"], raid["leave_reason"]), ("left", "losses"))
        self.assertEqual((raid["deaths"], raid["departures"]), (SQUAD_UNITS // 2, SQUAD_UNITS // 2))

    def test_a_role_raid_leaves_at_the_time_limit(self):
        self.start_raid()
        self.calendar.daysTotal = self.calendar.daysTotal + 30
        self.game.advance(3)
        self.go_far()
        self.game.advance(3)
        raid = self.raid()
        self.assertEqual((raid["state"], raid["leave_reason"]), ("left", "time"))

    def test_a_leaving_raid_is_removed_only_in_a_quiet_spot(self):
        self.start_raid()
        self.calendar.daysTotal = self.calendar.daysTotal + 30
        self.game.advance(3)
        near, far = self.raiders()[:3], self.raiders()[3:]
        for unit in far:
            unit.realPos = self.game.struct(X=60000.0, Y=0.0, Z=0.0)
        self.game.advance(3)
        self.assertTrue(all(unit.dead for unit in far))
        self.assertFalse(any(unit.dead for unit in near))
        self.assertEqual(self.raid()["state"], "active")
        self.assertEqual(self.raid()["living"], 3)

    def test_a_role_raid_below_every_limit_stays(self):
        self.start_raid()
        self.raiders()[0].ItemsLooted = 4
        self.game.advance(3)
        raid = self.raid()
        self.assertEqual((raid["state"], raid["living"], raid.get("leave_reason")), ("active", SQUAD_UNITS, None))

    def test_a_native_raid_is_never_removed(self):
        self.ask("invasion_set_roles", enabled=False)
        self.start_raid()
        for unit in self.raiders():
            unit.ItemsLooted = 4
        self.calendar.daysTotal = self.calendar.daysTotal + 30
        self.game.advance(3)
        raid = self.raid()
        self.assertEqual((raid["state"], raid["roles"], raid["living"]), ("active", False, SQUAD_UNITS))
        self.assertFalse(any(unit.dead for unit in self.raiders()))


class LordRaidRulesTests(RaidBehaviorTestCase):
    def run_lua(self, code):
        return self.game.lua.eval(f"(function() local rules = require('features.raid_behavior.rules'); {code} end)")()

    def test_the_plunder_counts_only_raiders_inside_the_battle_radius_once_a_day(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1, 2, 3, 4 }, true, { anchor = { x = 0, y = 0 } })
            local seen = { [1] = { x = 100, y = 0 }, [2] = { x = 3000, y = 0 }, [3] = { x = 9000, y = 0 }, [4] = { dead = true, x = 0, y = 0 } }
            local plunder, leave = { battle_radius = 4000, per_unit_day = 2 }, { loot_per_raider = 4 }
            local first = rules.plunder_amount(raid, seen, plunder, leave, 11)
            local again = rules.plunder_amount(raid, seen, plunder, leave, 11)
            rules.record_plunder(raid, first)
            return first .. ',' .. again .. ',' .. rules.looted_total(raid)""")
        self.assertEqual(result, "4,0,4")

    def test_the_plunder_stops_at_the_goal_and_the_leave_rule_fires(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1, 2 }, true, { anchor = { x = 0, y = 0 } })
            local seen = { [1] = { x = 0, y = 0 }, [2] = { x = 0, y = 0 } }
            local plunder, leave = { battle_radius = 4000, per_unit_day = 100 }, { loot_per_raider = 4, loss_share = 0.5, max_days = 25 }
            local amount = rules.plunder_amount(raid, seen, plunder, leave, 11)
            rules.record_plunder(raid, amount)
            local reason = rules.leave_reason(raid, 11, leave)
            rules.begin_leave(raid, reason, 11)
            return amount .. ',' .. tostring(reason) .. ',' .. tostring(raid.units[1].exiting)""")
        self.assertEqual(result, "8,loot,true")

    def test_a_native_raid_has_no_plunder(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1 }, true, nil)
            return rules.plunder_amount(raid, { [1] = { x = 0, y = 0 } }, { battle_radius = 4000, per_unit_day = 5 }, { loot_per_raider = 4 }, 11)""")
        self.assertEqual(result, 0)

    def test_a_subjugation_raid_has_no_plunder_and_never_leaves(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1, 2 }, true, { anchor = { x = 0, y = 0 }, kind = 'subjugation' })
            local seen = { [1] = { x = 0, y = 0 }, [2] = { x = 0, y = 0 } }
            local plunder, leave = { battle_radius = 4000, per_unit_day = 100 }, { loot_per_raider = 4, loss_share = 0.5, max_days = 25 }
            local amount = rules.plunder_amount(raid, seen, plunder, leave, 11)
            raid.deaths = 2
            return amount .. ',' .. tostring(rules.leave_reason(raid, 500, leave))""")
        self.assertEqual(result, "0,nil")


if __name__ == "__main__":
    unittest.main()
