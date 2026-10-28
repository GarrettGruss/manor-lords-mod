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
        self.pawn_address = 1
        self.game.method(self.pawn, "GetAddress", lambda _self: self.pawn_address)
        self.calendar = self.game.obj("TemporalComponent", daysTotal=61, daysUntilNextRaid=730)
        self.region = self.game.obj("Region", ownerPawn=self.pawn)
        self.game.method(self.region, "GetBuildings", lambda _self: self.game.lua.table_from([s["object"] for s in self.stores]))
        self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn, TemporalComponent=self.calendar,
                                    regions=self.game.array([self.region]), debugLog_AI_general=self.game.array([]))
        self.clock = 1000.0
        self.game.method(self.engine, "getGameTimeAdjusted", lambda _self: self.clock)
        self.game.method(self.engine, "spawnRaiders", lambda _self, squads, _centre: self.make_raiders(squads))
        self.bandit = self.game.obj("PawnCPP", isMainPlayer=False, isBandit=True, isAI=True,
                                    commandedSquads=self.game.array([self.game.struct(Value=7)]))  # the squad of the raiders (census)
        self.game.method(self.engine, "spawnArmy", lambda _self, _point, names, _owner, _company, _days: self.make_raiders(len(names)))
        self.add_store("Supplies_5", x=0.0, y=0.0, goods=[(16, 10), (3, 4)])
        self.add_store("Supplies_9", x=5000.0, y=5000.0, goods=[(7, 2)])
        self.game.load_mod(self.mod_name)
        self.game.advance(2)
        self.counter = 0
        self.ask("invasion_set_difficulty", value=1)  # these tests use the numbers of level 1; the mod default is level 2

    # -- the fake village and the fake units ---------------------------------------------

    def add_store(self, name, x, y, goods, btype=6):
        building = self.game.obj("SMBuildingMaster", Data=self.game.struct(bType=btype), Inventory=self.game.array([self.game.struct(Type=t, amt=a) for t, a in goods]))
        store = {"object": building, "goods": list(goods)}
        self.stores.append(store)
        self.game.method(building, "IsRubble", lambda _self: False)
        self.game.method(building, "GetFullName", lambda _self: f"SMBuildingMaster /Game/Map.{name}")
        self.game.method(building, "K2_GetActorLocation", lambda _self: self.game.struct(X=x, Y=y, Z=0.0))

        def add(_self, good):
            store["goods"].append((good["Type"], good["amt"]))
            building.Inventory = self.game.array([self.game.struct(Type=t, amt=a) for t, a in store["goods"]])

        self.game.method(building, "addToInventory", add)

        def consume(_self, good):
            for index, (kind, amount) in enumerate(store["goods"]):
                if kind == good and amount > 0:
                    store["goods"][index] = (kind, amount - 1)
                    break
            building.Inventory = self.game.array([self.game.struct(Type=t, amt=a) for t, a in store["goods"]])

        self.game.method(building, "consumeGoodNoCheck", consume)
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
        self.ask("invasion_plan_now")  # no raid is planned in game year 1
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

    def test_the_scan_of_the_new_units_runs_in_a_later_tick_than_the_spawn(self):
        self.ask("invasion_plan_now")
        self.ask("invasion_set_size", size="small")
        self.game.exec("SCANS = {}; local find = FindAllOf; FindAllOf = function(name) if name == 'SMUnit' then SCANS[#SCANS + 1] = os.clock() end return find(name) end")
        self.assertTrue(self.ask("invasion_force_next")["ok"])
        self.game.advance(3)
        times = self.game.exec("return table.concat(SCANS, ',')").split(",")
        self.assertGreaterEqual(len(times), 2)
        self.assertGreaterEqual(float(times[1]) - float(times[0]), 0.25, "the scan after the spawn waits for a later tick")
        self.assertEqual(self.raid()["initial"], SQUAD_UNITS)

    def test_units_that_existed_before_are_not_raiders(self):
        self.make_unit()
        self.start_raid("small")
        self.assertEqual(self.raid()["initial"], SQUAD_UNITS)


class CensusTests(RaidBehaviorTestCase):
    def test_a_raider_that_left_the_census_is_not_living(self):
        self.start_raid()
        victim = self.units[-1]
        self.assertEqual(self.raid()["living"], SQUAD_UNITS)
        victim.assignedSquadID = self.game.struct(Value=99)  # still in the SMUnit list, not dead, but no squad of the census
        self.game.advance(2)
        raid = self.raid()
        self.assertEqual((raid["living"], raid["deaths"]), (SQUAD_UNITS - 1, 1))
        self.assertFalse(victim.dead)

    def test_a_raider_in_the_census_stays_living(self):
        self.start_raid()
        self.game.advance(4)
        self.assertEqual(self.raid()["living"], SQUAD_UNITS)


class LootTests(RaidBehaviorTestCase):
    def raiders(self):
        return self.units[-SQUAD_UNITS:]

    def test_a_unit_that_vanishes_inland_counts_as_dead(self):
        self.start_raid()
        victim = self.raiders()[0]
        victim.ItemsLooted = 2
        self.game.advance(2)
        self.game.invalidate(victim)
        self.game.advance(2)
        self.assertEqual(self.raid()["deaths"], 1)

    def test_a_unit_that_walks_off_the_map_keeps_its_loot(self):
        self.start_raid()
        leaver = self.raiders()[0]
        leaver.ItemsLooted = 5
        leaver.realPos = self.game.struct(X=0.0, Y=float(EXIT_Y - 100), Z=0.0)
        self.game.advance(2)
        self.game.invalidate(leaver)
        self.game.advance(2)
        raid = self.raid()
        self.assertEqual((raid["departures"], raid["deaths"]), (1, 0))
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
        self.assertEqual((raid["deaths"], raid["departures"]), (1, 0))

    def test_a_native_raid_loot_is_not_written_by_the_mod(self):
        self.ask("invasion_set_roles", enabled=False)
        self.start_raid()
        unit = self.raiders()[0]
        unit.ItemsLooted = 25
        self.game.advance(2)
        self.assertEqual(unit.ItemsLooted, 25)
        raid = self.raid()
        self.assertEqual((raid["capped"], raid.get("raid_type")), (0, None))

    def test_a_bandit_raid_loot_is_not_written_by_the_mod(self):
        self.start_raid()
        unit = self.raiders()[0]
        unit.ItemsLooted = 8
        self.game.advance(2)
        self.assertEqual(unit.ItemsLooted, 8)
        raid = self.raid()
        self.assertEqual((raid["capped"], raid["raid_type"]), (0, "bandit"))

    def test_the_state_shows_the_carry_cap(self):
        answer = self.ask("raid_behavior_state")
        self.assertEqual(answer["result"]["carry_cap"], 10)


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

    def test_an_end_watcher_gets_the_summary_with_the_target_once(self):
        self.game.exec('ENDED = {}; require("features.raid_behavior.init").watch_end(function(s) ENDED[#ENDED + 1] = s.state .. ":" .. tostring(s.target) end)')
        self.start_raid()
        self.assertEqual(self.game.exec("return #ENDED"), 0)
        for unit in self.units:
            unit.dead = True
        self.game.advance(4)
        self.assertEqual(self.game.exec("return #ENDED"), 1)
        self.assertTrue(self.game.exec("return ENDED[1]").startswith("destroyed:"))
        self.assertNotEqual(self.game.exec("return ENDED[1]"), "destroyed:nil")

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


class BanditRaidTests(RaidBehaviorTestCase):
    """The mod does not send a bandit squad raid home (owner decision 2026-10-21)."""
    def raiders(self):
        return self.units[-SQUAD_UNITS:]

    def test_a_leaving_bandit_raid_is_not_removed_or_sent_home(self):
        self.start_raid()
        for unit in self.raiders():
            unit.ItemsLooted = 4
            unit.realPos = self.game.struct(X=60000.0, Y=-90000.0, Z=0.0)  # far from the village and at the map edge
        self.calendar.daysTotal = self.calendar.daysTotal + 30
        self.game.advance(4)
        raid = self.raid()
        self.assertEqual((raid["state"], raid["living"]), ("active", SQUAD_UNITS))
        self.assertFalse(any(unit.dead for unit in self.raiders()))

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


class GreatRaidWinTests(RaidBehaviorTestCase):
    """The great raid is won when the final army is dead. The relief army (player side) makes no units here."""

    def setUp(self):
        super().setUp()
        self.game.method(self.engine, "spawnArmy", lambda _self, _point, names, owner, _company, _days: (
            None if owner.isBandit is not True else self.make_raiders(len(names))))

    def great(self):
        answer = self.ask("invasion_great_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def next_day(self):
        self.calendar.daysTotal = self.calendar.daysTotal + 1
        self.game.advance(2)

    def test_the_phase_is_won_after_the_final_army_is_dead(self):
        self.ask("invasion_set_difficulty", value=1)
        self.assertTrue(self.ask("invasion_great_force_start")["ok"])
        self.next_day()
        for _ in range(4):
            self.ask("invasion_great_skip_wait")
            self.next_day()
        self.assertEqual(self.great()["phase"], 2)
        self.next_day()
        self.assertEqual(self.great()["phase"], 2)  # the final army lives
        for unit in self.units:
            unit.dead = True
        self.game.advance(2)
        self.next_day()
        self.assertEqual(self.great()["phase"], 3)


class StoreTierTests(RaidBehaviorTestCase):
    def run_lua(self, code):
        return self.game.lua.eval(f"(function() local rules = require('features.raid_behavior.rules'); {code} end)")()

    STEAL = "{ threshold = 20000, rate = 10, goals = { plunder = 100, great = 300 } }"

    def test_the_config_has_the_tiers_the_threshold_the_rate_and_the_goals(self):
        answer = self.ask("raid_behavior_state")["result"]
        self.assertEqual(answer["store_tiers"]["6"], 1)
        self.assertEqual(answer["store_tiers"]["72"], 1)
        self.assertEqual(answer["store_tiers"]["98"], 2)
        self.assertEqual((answer["steal"]["threshold"], answer["steal"]["rate"]), (20000, 10))
        self.assertEqual((answer["steal"]["goals"]["plunder"], answer["steal"]["goals"]["great"]), (100, 300))

    def test_only_a_unit_beyond_the_threshold_steals(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1, 2, 3 }, true, { anchor = { x = 0, y = 0 }, kind = 'plunder' })
            local seen = { [1] = { x = 19999, y = 0 }, [2] = { x = 0, y = 20001 }, [3] = { x = 30000, y = 0 } }
            return rules.steal_amount(raid, seen, %s, 11)""" % self.STEAL)
        self.assertEqual(result, 20)

    def test_a_dead_unit_and_a_unit_without_a_place_do_not_steal(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1, 2 }, true, { anchor = { x = 0, y = 0 }, kind = 'plunder' })
            return rules.steal_amount(raid, { [1] = { dead = true, x = 90000, y = 0 }, [2] = {} }, %s, 11)""" % self.STEAL)
        self.assertEqual(result, 0)

    def test_the_steal_runs_once_a_day(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1 }, true, { anchor = { x = 0, y = 0 }, kind = 'plunder' })
            local seen = { [1] = { x = 90000, y = 0 } }
            local steal = %s
            return rules.steal_amount(raid, seen, steal, 11) .. ',' .. rules.steal_amount(raid, seen, steal, 11) .. ',' .. rules.steal_amount(raid, seen, steal, 12)""" % self.STEAL)
        self.assertEqual(result, "10,0,10")

    def test_the_steal_stops_at_the_goal(self):
        result = self.run_lua("""
            local units = {}
            for i = 1, 4 do units[i] = i end
            local raid = rules.new_raid(1, 10, 1, units, true, { anchor = { x = 0, y = 0 }, kind = 'plunder' })
            local seen = {}
            for i = 1, 4 do seen[i] = { x = 90000, y = 0 } end
            local steal = %s
            local parts = {}
            for day = 11, 16 do
                local amount = rules.steal_amount(raid, seen, steal, day)
                rules.record_steal(raid, amount)
                parts[#parts + 1] = amount
            end
            return table.concat(parts, ',') .. ';' .. raid.stolen""" % self.STEAL)
        self.assertEqual(result, "40,40,20,0,0,0;100")

    def test_a_great_raid_has_the_large_goal_and_other_raids_do_not_steal(self):
        result = self.run_lua("""
            local steal = %s
            local great = rules.new_raid(1, 10, 1, { 1 }, true, { anchor = { x = 0, y = 0 }, kind = 'great' })
            local native = rules.new_raid(2, 10, 1, { 1 }, false, nil)
            local sub = rules.new_raid(3, 10, 1, { 1 }, true, { anchor = { x = 0, y = 0 }, kind = 'subjugation' })
            return tostring(rules.steal_goal(great, steal)) .. ',' .. tostring(rules.steal_goal(native, steal)) .. ',' .. tostring(rules.steal_goal(sub, steal))""" % self.STEAL)
        self.assertEqual(result, "300,nil,nil")

    def test_the_tier_of_a_store_type(self):
        result = self.run_lua("""
            local tiers = { [6] = 1, [98] = 2 }
            return tostring(rules.tier_of(tiers, 6)) .. ',' .. tostring(rules.tier_of(tiers, 98)) .. ',' .. tostring(rules.tier_of(tiers, 12)) .. ',' .. tostring(rules.tier_of(tiers, nil))""")
        self.assertEqual(result, "1,2,nil,nil")

    def test_a_native_raid_has_no_steal(self):
        self.start_raid("small")
        self.game.advance(5)
        raid = self.raid()
        self.assertEqual(raid["stolen"], 0)


class StoreTierWorldTests(RaidBehaviorTestCase):
    def test_the_plunder_takes_goods_from_tier_1_stores_only(self):
        manor = self.add_store("Keep_3", x=0.0, y=0.0, goods=[(27, 100)], btype=98)
        granary = self.add_store("Granary_4", x=0.0, y=0.0, goods=[(3, 50)], btype=72)
        other = self.add_store("Market_6", x=0.0, y=0.0, goods=[(5, 40)], btype=12)
        taken = self.game.lua.eval("(function() return require('features.raid_behavior.world').plunder(500, require('config').raid_behavior.store_tiers) end)")()
        self.assertEqual(self.stock(manor), 100)
        self.assertEqual(self.stock(other), 40)
        self.assertEqual(self.stock(granary), 0)
        self.assertEqual(self.stock(self.stores[0]) + self.stock(self.stores[1]), 0)
        self.assertEqual(taken[0], 14 + 2 + 50)


class CorpsePitLootTests(RaidBehaviorTestCase):
    "Change add-corpse-pit-loot: the plunder record and the share for each body that reaches the pit."

    def run_lua(self, code):
        return self.game.lua.eval(f"(function() local rules = require('features.raid_behavior.rules'); {code} end)")()

    HUSSITE = "{ anchor = { x = 0, y = 0 }, kind = 'plunder' }"

    def hussite(self, raiders=10):
        return f"local keys = {{}}; for i = 1, {raiders} do keys[i] = i end; local raid = rules.new_raid(1, 10, 1, keys, true, {self.HUSSITE})"

    def test_the_tick_records_the_goods_it_takes(self):
        result = self.run_lua(self.hussite() + "; rules.record_plunder(raid, 10, { [3] = 6, [16] = 4 }); rules.record_plunder(raid, 2, { [3] = 2 }); return raid.plunder_goods[3] .. ',' .. raid.plunder_goods[16] .. ',' .. raid.plundered")
        self.assertEqual(result, "8,4,12")

    def test_a_native_raid_has_no_record(self):
        result = self.run_lua("local raid = rules.new_raid(1, 10, 1, { 1, 2 }, false, nil); rules.record_plunder(raid, 5, { [3] = 5 }); rules.note_deaths(raid, { { key = 1 } }); return next(raid.plunder_goods) == nil and raid.unpaid == 0")
        self.assertTrue(result)

    def test_one_body_gives_its_share(self):
        result = self.run_lua(self.hussite(10) + "; rules.record_plunder(raid, 40, { [3] = 40 }); rules.note_deaths(raid, { { key = 1 } }); local goods, paid = rules.pay_bodies({ raid }, 1); return goods[3] .. ',' .. paid .. ',' .. raid.unpaid")
        self.assertEqual(result, "4,1,0")

    def test_the_share_rounds_down(self):
        result = self.run_lua(self.hussite(10) + "; rules.record_plunder(raid, 5, { [4] = 5 }); rules.note_deaths(raid, { { key = 1 } }); local goods, paid = rules.pay_bodies({ raid }, 1); return tostring(goods[4]) .. ',' .. paid")
        self.assertEqual(result, "nil,1")

    def test_two_bodies_in_one_poll_give_two_shares(self):
        result = self.run_lua(self.hussite(10) + "; rules.record_plunder(raid, 40, { [3] = 40 }); rules.note_deaths(raid, { { key = 1 }, { key = 2 }, { key = 3 } }); local goods, paid = rules.pay_bodies({ raid }, 2); return goods[3] .. ',' .. paid .. ',' .. raid.unpaid")
        self.assertEqual(result, "8,2,1")

    def test_a_body_the_mod_does_not_know_is_ignored(self):
        result = self.run_lua(self.hussite(10) + "; rules.record_plunder(raid, 40, { [3] = 40 }); rules.note_deaths(raid, { { key = 1 } }); local goods, paid = rules.pay_bodies({ raid }, 5); local again, more = rules.pay_bodies({ raid }, 5); return goods[3] .. ',' .. paid .. ',' .. more")
        self.assertEqual(result, "4,1,0")

    def test_a_departure_is_not_a_body(self):
        result = self.run_lua(self.hussite(2) + "; local deaths = rules.update(raid, { [1] = { dead = false, x = 0, y = -90000 }, [2] = { dead = false, x = 0, y = -90000 } }, { carry_cap = 10, exit_y = -85000 }, 11); rules.note_deaths(raid, deaths); return raid.unpaid")
        self.assertEqual(result, 0)

    def test_the_world_reads_a_pit_and_adds_goods(self):
        pit = self.add_store("Pit_7", x=0.0, y=0.0, goods=[(233, 3)], btype=113)
        result = self.game.lua.eval("(function() local world = require('features.raid_behavior.world'); local pits = world.pits(); local ok = world.pit_add(pits[1], { [3] = 4 }); return #pits .. ',' .. pits[1].corpses .. ',' .. tostring(ok) end)")()
        self.assertEqual(result, "1,3,true")
        self.assertIn((3, 4), pit["goods"])

    def test_a_pit_add_raises_the_storage_limits_to_the_stored_total(self):
        pit = self.add_store("Pit_7", x=0.0, y=0.0, goods=[(233, 3), (3, 10)], btype=113)
        pit["object"].storageLimitGeneric = 0
        pit["object"].storageLimitLarge = 0
        pit["object"].storageLimitPantry = 5
        result = self.game.lua.eval("(function() local world = require('features.raid_behavior.world'); local pits = world.pits(); world.pit_add(pits[1], { [3] = 400, [15] = 7 }); return world.pit_limit(pits[1]) end)")()
        self.assertEqual(result, 420)
        self.assertEqual(sum(a for t, a in pit["goods"] if t == 3), 410)

    def test_no_pit_is_an_empty_list(self):
        self.assertEqual(self.game.lua.eval("(function() return #require('features.raid_behavior.world').pits() end)")(), 0)

    def test_a_native_raid_body_at_the_pit_gives_nothing_and_no_pit_is_no_error(self):
        self.start_raid("small")
        self.game.advance(3)
        pit = self.add_store("Pit_7", x=0.0, y=0.0, goods=[(233, 0)], btype=113)
        self.game.advance(3)
        before = list(pit["goods"])
        pit["goods"][0] = (233, 2)
        pit["object"].Inventory = self.game.array([self.game.struct(Type=t, amt=a) for t, a in pit["goods"]])
        self.game.advance(3)
        self.assertEqual(pit["goods"], [(233, 2)], before)

    def test_the_pit_state_command_lists_the_pit(self):
        self.add_store("Pit_7", x=0.0, y=0.0, goods=[(233, 2), (3, 5)], btype=113)
        answer = self.ask("raid_behavior_pit_state")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["result"]["pits"], [{"corpses": 2, "goods": [{"good": 3, "amount": 5}, {"good": 233, "amount": 2}], "limit": 0}])

    def test_the_plunder_returns_the_goods_by_type(self):
        result = self.game.lua.eval("(function() local taken, by_good = require('features.raid_behavior.world').plunder(20, require('config').raid_behavior.store_tiers); return taken .. ',' .. by_good[16] end)")()
        self.assertEqual(result, "16,10")

class StripTheDeadRulesTests(RaidBehaviorTestCase):
    "Change update-tech-tree-yearly-picks: loot variants for bodies that are not Hussite raiders."

    def run_lua(self, code):
        return self.game.lua.eval(f"(function() local rules = require('features.raid_behavior.rules'); {code} end)")()

    LOOT = "{ bandit = { { goods = { [177] = 1, [270] = 1 } }, { weight = 1, goods = { [177] = 1, [270] = 1, [273] = 1 } } }, soldier = {} }"

    def test_the_variant_follows_the_roll_and_the_weights(self):
        result = self.run_lua("""
            local list = { { goods = { [1] = 1 } }, { weight = 3, goods = { [2] = 1 } } }
            local function which(roll) for good in pairs(rules.pick_variant(list, roll)) do return good end end
            return which(0) .. ',' .. which(0.24) .. ',' .. which(0.25) .. ',' .. which(0.99)""")
        self.assertEqual(result, "1,1,2,2")

    def test_an_empty_list_or_a_missing_kind_pays_nothing(self):
        result = self.run_lua("return tostring(next(rules.pick_variant({}, 0.5))) .. ',' .. tostring(next(rules.pick_variant(nil, 0.5)))")
        self.assertEqual(result, "nil,nil")

    def test_a_native_death_is_counted_apart_from_a_hussite_one(self):
        result = self.run_lua("""
            local native = rules.new_raid(1, 10, 1, { 1, 2 }, false, nil)
            local hussite = rules.new_raid(2, 10, 1, { 1, 2 }, true, { anchor = { x = 0, y = 0 }, kind = 'plunder' })
            rules.note_deaths(native, { { key = 1 }, { key = 2 } }); rules.note_deaths(hussite, { { key = 1 } })
            return native.unpaid_other .. ',' .. native.unpaid .. ',' .. hussite.unpaid_other .. ',' .. hussite.unpaid""")
        self.assertEqual(result, "2,0,0,1")

    def test_each_body_draws_its_own_variant_and_is_paid_once(self):
        result = self.run_lua("""
            local native = rules.new_raid(1, 10, 1, { 1, 2, 3 }, false, nil)
            rules.note_deaths(native, { { key = 1 }, { key = 2 }, { key = 3 } })
            local rolls, index = { 0.1, 0.9, 0.1 }, 0
            local goods, paid = rules.pay_other_bodies({ native }, 2, %s, 'bandit', function() index = index + 1; return rolls[index] end)
            local again, more = rules.pay_other_bodies({ native }, 5, %s, 'bandit', function() return 0 end)
            return goods[177] .. ',' .. goods[270] .. ',' .. goods[273] .. ',' .. paid .. ',' .. more .. ',' .. native.unpaid_other""" % (self.LOOT, self.LOOT))
        self.assertEqual(result, "2,2,1,2,1,0")

    def test_a_soldier_or_unknown_kind_pays_no_goods_but_the_body_is_consumed(self):
        result = self.run_lua("""
            local native = rules.new_raid(1, 10, 1, { 1 }, false, nil)
            rules.note_deaths(native, { { key = 1 } })
            local goods, paid = rules.pay_other_bodies({ native }, 1, %s, 'soldier', function() return 0 end)
            return tostring(next(goods)) .. ',' .. paid""" % self.LOOT)
        self.assertEqual(result, "nil,1")

    def test_the_shipped_config_has_the_two_owner_variants(self):
        result = self.run_lua("""
            local loot = require('config').raid_behavior.body_loot
            local function size(goods) local n = 0 for _ in pairs(goods) do n = n + 1 end return n end
            return #loot.bandit .. ',' .. size(loot.bandit[1].goods) .. ',' .. size(loot.bandit[2].goods) .. ',' .. loot.bandit[2].goods[273] .. ',' .. #loot.soldier""")
        self.assertEqual(result, "2,2,3,1,0")


class StripTheDeadPitTests(RaidBehaviorTestCase):
    "Change update-tech-tree-yearly-picks: the pit pays only while the law is in force."

    def setUp(self):
        super().setUp()
        self.calendar.Season = 1  # the tech tree needs a season for its start pick
        self.game.advance(4)
        self.pit = self.add_store("Pit_7", x=0.0, y=0.0, goods=[(233, 0)], btype=113)
        self.start_raid("small")
        self.game.advance(3)

    def enact_law(self):
        self.assertTrue(self.ask("tech_tree_unlock", node="corpse_robbing")["ok"])
        self.assertTrue(self.ask("tech_tree_enact_law", law="strip_the_dead")["ok"])
        self.game.advance(3)

    def kill_and_deliver(self, bodies):
        for unit in self.units[:bodies]:
            unit.dead = True
        self.game.advance(3)  # the tracker sees the deaths
        self.pit["goods"][0] = (233, self.pit["goods"][0][1] + bodies)
        self.pit["object"].Inventory = self.game.array([self.game.struct(Type=t, amt=a) for t, a in self.pit["goods"]])
        self.game.advance(3)

    def goods(self, good):
        return sum(amount for kind, amount in self.pit["goods"] if kind == good)

    def order(self):
        return self.ask("bandits_state")["result"]["mod_order"]

    def test_without_the_law_nothing_is_paid_and_the_order_stays(self):
        before = self.order()
        self.kill_and_deliver(2)
        self.assertEqual((self.goods(177), self.goods(270), self.goods(273)), (0, 0, 0))
        self.assertEqual(self.order(), before)

    def test_with_the_law_each_native_body_pays_a_variant_and_costs_one_order(self):
        self.enact_law()
        before = self.order()
        self.kill_and_deliver(2)
        self.assertEqual((self.goods(177), self.goods(270)), (2, 2))
        self.assertIn(self.goods(273), (0, 1, 2))
        self.assertEqual(self.order(), before - 2)

    def test_bodies_that_arrive_before_the_law_are_not_paid_later(self):
        self.kill_and_deliver(2)
        self.enact_law()
        self.game.advance(5)
        self.assertEqual(self.goods(177), 0)

    def test_the_law_repealed_stops_the_pay_out(self):
        self.enact_law()
        self.ask("tech_tree_repeal_law", law="strip_the_dead")
        self.game.advance(3)
        self.kill_and_deliver(1)
        self.assertEqual(self.goods(177), 0)


class LordRaidRulesTests(RaidBehaviorTestCase):
    def run_lua(self, code):
        return self.game.lua.eval(f"(function() local rules = require('features.raid_behavior.rules'); {code} end)")()

    def test_the_plunder_counts_only_raiders_inside_the_battle_radius_once_a_day(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1, 2, 3, 4 }, true, { anchor = { x = 0, y = 0 } })
            local seen = { [1] = { x = 100, y = 0 }, [2] = { x = 3000, y = 0 }, [3] = { x = 9000, y = 0 }, [4] = { dead = true, x = 0, y = 0 } }
            local plunder, leave = { battle_radius = 4000, per_unit_day = 2 }, { loot_per_raider = 4 }
            local first = rules.plunder_amount(raid, seen, plunder, leave, 11, 4)
            local again = rules.plunder_amount(raid, seen, plunder, leave, 11, 4)
            rules.record_plunder(raid, first)
            return first .. ',' .. again .. ',' .. rules.looted_total(raid)""")
        self.assertEqual(result, "4,0,4")

    def test_the_plunder_stops_at_the_goal_and_the_leave_rule_fires(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1, 2 }, true, { anchor = { x = 0, y = 0 } })
            local seen = { [1] = { x = 0, y = 0 }, [2] = { x = 0, y = 0 } }
            local plunder, leave = { battle_radius = 4000, per_unit_day = 100 }, { loot_per_raider = 4, loss_share = 0.5, max_days = 25 }
            local amount = rules.plunder_amount(raid, seen, plunder, leave, 11, 4)
            rules.record_plunder(raid, amount)
            local reason = rules.leave_reason(raid, 11, leave, 4)
            rules.begin_leave(raid, reason, 11)
            return amount .. ',' .. tostring(reason) .. ',' .. tostring(raid.units[1].exiting)""")
        self.assertEqual(result, "8,loot,true")

    def test_a_native_raid_has_no_plunder(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1 }, true, nil)
            return rules.plunder_amount(raid, { [1] = { x = 0, y = 0 } }, { battle_radius = 4000, per_unit_day = 5 }, { loot_per_raider = 4 }, 11, 4)""")
        self.assertEqual(result, 0)

    def test_a_subjugation_raid_has_no_plunder_and_never_leaves(self):
        result = self.run_lua("""
            local raid = rules.new_raid(1, 10, 1, { 1, 2 }, true, { anchor = { x = 0, y = 0 }, kind = 'subjugation' })
            local seen = { [1] = { x = 0, y = 0 }, [2] = { x = 0, y = 0 } }
            local plunder, leave = { battle_radius = 4000, per_unit_day = 100 }, { loot_per_raider = 4, loss_share = 0.5, max_days = 25 }
            local amount = rules.plunder_amount(raid, seen, plunder, leave, 11, 4)
            raid.deaths = 2
            return amount .. ',' .. tostring(rules.leave_reason(raid, 500, leave, 4))""")
        self.assertEqual(result, "0,nil")


    def test_a_hussite_raid_reaches_its_carry_cap(self):
        result = self.run_lua("""
            local units = {}
            for i = 1, 12 do units[i] = i end
            local raid = rules.new_raid(1, 10, 1, units, true, { anchor = { x = 0, y = 0 } })
            local seen = {}
            for i = 1, 12 do seen[i] = { x = 0, y = 0 } end
            local plunder, leave = { battle_radius = 4000, per_unit_day = 7 }, { loot_per_raider = 4, loss_share = 0.5, max_days = 25 }
            for day = 11, 40 do rules.record_plunder(raid, rules.plunder_amount(raid, seen, plunder, leave, day, 10)) end
            return raid.plundered""")
        self.assertEqual(result, 120)

    def test_a_hussite_raid_leaves_by_loot_when_it_is_full(self):
        result = self.run_lua("""
            local units = {}
            for i = 1, 12 do units[i] = i end
            local raid = rules.new_raid(1, 10, 1, units, true, { anchor = { x = 0, y = 0 } })
            local leave = { loot_per_raider = 4, loss_share = 0.5, max_days = 25 }
            raid.plundered = 48
            local at_48 = rules.leave_reason(raid, 11, leave, 10)
            raid.plundered = 120
            return tostring(at_48) .. ',' .. tostring(rules.leave_reason(raid, 11, leave, 10))""")
        self.assertEqual(result, "nil,loot")

    def test_the_mod_cuts_the_loot_of_a_hussite_raider_only(self):
        result = self.run_lua("""
            local hussite = rules.new_raid(1, 10, 1, { 1 }, true, { anchor = { x = 0, y = 0 } })
            local native = rules.new_raid(2, 10, 1, { 1 }, false, nil)
            local config = { carry_cap = 10, exit_y = -85000 }
            local seen_h, seen_n = { [1] = { loot = 25, x = 0, y = 0 } }, { [1] = { loot = 25, x = 0, y = 0 } }
            rules.update(hussite, seen_h, config, 11)
            rules.update(native, seen_n, config, 11)
            return tostring(seen_h[1].new_loot) .. ',' .. tostring(seen_n[1].new_loot) .. ',' .. hussite.capped .. ',' .. native.capped""")
        self.assertEqual(result, "10,nil,1,0")

class LootOverrideModuleTests(unittest.TestCase):
    """The loot override module (features/raid_behavior/loot_override.lua) alone, with a plain Lua slot store."""

    def setUp(self):
        from lupa import LuaRuntime
        self.lua = LuaRuntime()
        path = find_pack_mod() / "Scripts" / "features" / "raid_behavior" / "loot_override.lua"
        self.lua.execute("LOG = {}")
        self.module = self.lua.execute(path.read_text(encoding="utf-8"))
        self.lua.globals().MODULE = self.module
        self.lua.execute("""
            SLOTS = {}
            STORE = { slots = 3, get = function(i) return SLOTS[i] or '' end, set = function(i, text) SLOTS[i] = text end }
            local function add(level) return function(_, message) LOG[#LOG + 1] = level .. ': ' .. message end end
            LO = MODULE.new(STORE, { info = add('info'), warn = add('warn'), error = add('error') })
        """)

    def run_lua(self, code):
        return self.lua.eval(f"(function() {code} end)")()

    def test_a_slot_text_round_trips(self):
        text = self.module.encode(31, 4, self.lua.table_from([271, 133, 133]))
        self.assertEqual(text, "31_4_133x2-271x1")
        self.assertEqual(self.run_lua("local s, i, g = MODULE.decode('31_4_133x2-271x1'); return s .. ',' .. i .. ',' .. #g .. ',' .. g[1] .. g[3]"), "31,4,3,133271")
        self.assertIsNone(self.module.decode("garbage")[0])

    def test_a_slot_text_uses_only_characters_that_modstate_allows(self):
        self.assertRegex(self.module.encode(31, 4, self.lua.table_from([271, 133, 133])), r"^[A-Za-z0-9_.\-]*$")

    def test_set_get_and_take(self):
        self.assertEqual(self.run_lua("return LO.set({ address = 5, squad = 31, index = 1 }, { 133 })"), True)
        self.assertEqual(self.run_lua("return LO.get(5)[1]"), 133)
        self.assertEqual(self.run_lua("return SLOTS[1]"), "31_1_133x1")
        self.assertEqual(self.run_lua("return LO.take(5)[1]"), 133)
        self.assertEqual(self.run_lua("return tostring(LO.get(5)) .. ',' .. SLOTS[1] .. ',' .. LO.count()"), "nil,,0")

    def test_a_unit_without_goods_gets_no_entry(self):
        self.run_lua("LO.set({ address = 5, squad = 31, index = 1 }, {})")
        self.assertEqual(self.run_lua("return LO.count()"), 0)

    def test_all_slots_full_logs_an_error_and_drops_the_new_entry(self):
        for number in range(1, 4):
            self.run_lua(f"LO.set({{ address = {number}, squad = 31, index = {number} }}, {{ 133 }})")
        answer = self.run_lua("local ok, why = LO.set({ address = 9, squad = 31, index = 9 }, { 133 }); return tostring(ok) .. ':' .. why")
        self.assertEqual(answer, "nil:slots full")
        self.assertEqual(self.run_lua("return LO.count() .. ',' .. tostring(LO.get(9))"), "3,nil")
        self.assertIn("error: ", self.run_lua("return LOG[#LOG]"))

    def test_a_freed_slot_is_used_again(self):
        for number in range(1, 4):
            self.run_lua(f"LO.set({{ address = {number}, squad = 31, index = {number} }}, {{ 133 }})")
        self.run_lua("LO.take(2)")
        self.run_lua("LO.set({ address = 9, squad = 32, index = 1 }, { 271 })")
        self.assertEqual(self.run_lua("return SLOTS[2]"), "32_1_271x1")

    def test_a_living_unit_that_is_not_listed_left_the_map(self):
        self.run_lua("LO.set({ address = 5, squad = 31, index = 1 }, { 133 })")
        self.assertEqual(self.run_lua("return LO.poll({}, 100)"), 1)
        self.assertEqual(self.run_lua("return LO.count() .. ',' .. SLOTS[1]"), "0,")

    def test_a_dead_unit_keeps_its_entry_until_the_body_expires(self):
        self.run_lua("LO.set({ address = 5, squad = 31, index = 1 }, { 133 })")
        self.run_lua("LO.poll({ [5] = { dead = true } }, 100)")
        self.assertEqual(self.run_lua("return LO.poll({}, 129)"), 0)  # the body is gone from the list, the entry stays
        self.assertEqual(self.run_lua("return LO.count()"), 1)
        self.assertEqual(self.run_lua("return LO.poll({}, 131)"), 1)  # more than 30 game days after the death
        self.assertEqual(self.run_lua("return LO.count()"), 0)

    def test_pay_takes_dead_units_oldest_first_and_only_as_many_as_bodies(self):
        self.run_lua("LO.set({ address = 1, squad = 31, index = 1 }, { 133 }); LO.set({ address = 2, squad = 31, index = 2 }, { 271, 271 }); LO.set({ address = 3, squad = 31, index = 3 }, { 163 })")
        self.run_lua("LO.poll({ [2] = { dead = true }, [1] = { dead = false }, [3] = { dead = false } }, 100); LO.poll({ [1] = { dead = false }, [3] = { dead = true } }, 101)")
        self.assertEqual(self.run_lua("local goods, paid = LO.pay(1); return paid .. ',' .. tostring(goods[271]) .. ',' .. tostring(goods[163])"), "1,2,nil")
        self.assertEqual(self.run_lua("local goods, paid = LO.pay(5); return paid .. ',' .. tostring(goods[163]) .. ',' .. LO.count()"), "1,1,1")  # the living unit stays
        self.assertEqual(self.run_lua("local goods, paid = LO.pay(5); return paid"), 0)

    def test_load_saved_reads_the_slots_and_clears_an_unreadable_one(self):
        self.run_lua("SLOTS[1] = '31_1_133x1'; SLOTS[2] = 'broken'; SLOTS[3] = '31_2_271x2'")
        self.assertEqual(self.run_lua("return LO.load_saved()"), 2)
        self.assertEqual(self.run_lua("return SLOTS[2]"), "")

    def test_relink_gives_the_entries_of_a_squad_to_its_units_in_order(self):
        self.run_lua("SLOTS[1] = '31_2_271x1'; SLOTS[2] = '31_1_133x1'; SLOTS[3] = '40_1_163x1'; LO.load_saved()")
        answer = self.run_lua("""
            local linked, unlinked = LO.relink({ [31] = { { address = 70 }, { address = 71 } } })
            return linked .. ',' .. unlinked .. ',' .. LO.get(70)[1] .. ',' .. LO.get(71)[1] .. ',' .. tostring(LO.get(72))""")
        self.assertEqual(answer, "2,1,133,271,nil")  # index 1 -> first unit, index 2 -> second unit; squad 40 has no unit yet

    def test_a_lost_entry_is_dropped_logged_and_its_slot_is_empty(self):
        self.run_lua("SLOTS[1] = '40_1_163x1'; LO.load_saved(); LO.relink({})")
        self.assertEqual(self.run_lua("return LO.drop_unlinked()"), 1)
        self.assertEqual(self.run_lua("return SLOTS[1] .. '|' .. LO.count()"), "|0")
        self.assertIn("lost slot=1 squad=40", self.run_lua("return LOG[#LOG]"))

    def test_clear_all_empties_every_slot(self):
        self.run_lua("LO.set({ address = 1, squad = 31, index = 1 }, { 133 }); LO.set({ address = 2, squad = 31, index = 2 }, { 133 }); LO.clear_all()")
        self.assertEqual(self.run_lua("return LO.count() .. ',' .. (SLOTS[1] or 'x') .. ',' .. (SLOTS[2] or 'x')"), "0,,")


class LootOverridePitTests(RaidBehaviorTestCase):
    """The override at the corpse pit and after a load, with the whole mod in the fake game."""

    def overrides(self, code):
        return self.game.lua.eval(f"(function() local lo = require('features.raid_behavior.init').loot_override; {code} end)")()

    def with_entry(self, goods="{ 133 }"):
        unit = self.make_unit()
        address = 1000 + len(self.units) - 1
        self.overrides(f"lo.set({{ address = {address}, squad = 7, index = 1 }}, {goods})")
        return unit, address

    def deliver(self, pit, bodies=1):
        for index, (kind, amount) in enumerate(pit["goods"]):
            if kind == 233:
                pit["goods"][index] = (kind, amount + bodies)
        pit["object"].Inventory = self.game.array([self.game.struct(Type=t, amt=a) for t, a in pit["goods"]])
        self.game.advance(3)

    def test_a_body_with_an_override_gives_its_goods_at_the_pit_and_the_entry_ends(self):
        unit, _ = self.with_entry("{ 133, 133, 271 }")
        pit = self.add_store("Pit_7", x=0.0, y=0.0, goods=[(233, 0)], btype=113)
        self.game.advance(3)
        unit.dead = True
        self.game.advance(3)
        self.deliver(pit)
        goods = dict(pit["goods"])
        self.assertEqual((goods.get(133), goods.get(271)), (2, 1))
        self.assertEqual(self.overrides("return lo.count()"), 0)
        self.assertTrue(any("override_paid=1" in line for line in self.game.log_lines()))

    def test_a_body_without_an_override_gives_the_same_as_before(self):
        unit = self.make_unit()
        pit = self.add_store("Pit_7", x=0.0, y=0.0, goods=[(233, 0)], btype=113)
        self.game.advance(3)
        unit.dead = True
        self.game.advance(3)
        self.deliver(pit)
        self.assertEqual(pit["goods"], [(233, 1)])

    def test_a_living_unit_with_an_entry_is_not_paid_when_some_other_body_arrives(self):
        self.with_entry()
        pit = self.add_store("Pit_7", x=0.0, y=0.0, goods=[(233, 0)], btype=113)
        self.game.advance(3)
        self.deliver(pit)
        self.assertEqual(pit["goods"], [(233, 1)])
        self.assertEqual(self.overrides("return lo.count()"), 1)

    def test_units_that_leave_the_map_lose_their_entries_and_pay_nothing(self):
        units = [self.with_entry()[0] for _ in range(3)]
        pit = self.add_store("Pit_7", x=0.0, y=0.0, goods=[(233, 0)], btype=113)
        self.game.advance(3)
        for unit in units:
            self.game.invalidate(unit)
        self.game.advance(3)
        self.assertEqual(self.overrides("return lo.count()"), 0)
        self.deliver(pit)
        self.assertEqual(pit["goods"], [(233, 1)])

    def test_the_override_does_not_change_the_loot_the_unit_carries(self):
        unit = self.make_unit(loot=7)
        self.overrides(f"lo.set({{ address = {1000 + len(self.units) - 1}, squad = 7, index = 1 }}, {{ 133 }})")
        self.game.advance(5)
        self.assertEqual(unit.ItemsLooted, 7)

    def test_the_state_command_lists_the_entries(self):
        self.with_entry("{ 133, 271 }")
        entries = self.ask("raid_behavior_override_state")["result"]["entries"]
        self.assertEqual([(e["squad"], e["index"], e["goods"], e["linked"]) for e in entries], [(7, 1, [133, 271], True)])

    def test_after_a_load_the_saved_entries_are_linked_to_the_new_units(self):
        self.with_entry("{ 133 }")
        self.game.advance(3)
        for unit in self.units:
            self.game.invalidate(unit)
        self.units.clear()
        self.pawn_address = 2  # the load: a new player pawn address and new unit objects
        new = self.make_unit()
        self.game.advance(4)
        entries = self.ask("raid_behavior_override_state")["result"]["entries"]
        self.assertEqual([(e["squad"], e["index"], e["goods"], e["linked"]) for e in entries], [(7, 1, [133], True)])
        self.assertTrue(any("LOOT_OVERRIDE relink done entries=1 lost=0" in line for line in self.game.log_lines()))
        new.dead = True
        self.game.advance(3)
        pit = self.add_store("Pit_7", x=0.0, y=0.0, goods=[(233, 0)], btype=113)
        self.game.advance(3)
        self.deliver(pit)
        self.assertEqual(dict(pit["goods"]).get(133), 1)

    def test_an_entry_whose_unit_is_not_found_is_dropped_after_the_window(self):
        self.with_entry("{ 133 }")
        for unit in self.units:
            self.game.invalidate(unit)
        self.units.clear()
        self.pawn_address = 2
        self.game.advance(3)
        self.assertEqual(self.ask("raid_behavior_override_state")["result"]["relinking"], True)
        self.clock += 11  # the window of 10 game seconds ends
        self.game.advance(4)
        answer = self.ask("raid_behavior_override_state")["result"]
        self.assertEqual((answer["count"], answer["relinking"]), (0, False))
        self.assertTrue(any("LOOT_OVERRIDE lost slot=" in line for line in self.game.log_lines()))
        self.assertTrue(any("relink done entries=0 lost=1" in line for line in self.game.log_lines()))


if __name__ == "__main__":
    unittest.main()
