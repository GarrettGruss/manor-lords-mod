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
        self.bandit = self.game.obj("PawnCPP", isMainPlayer=False, isBandit=True, isAI=True,
                                    commandedSquads=self.game.array([self.game.struct(Value=7)]))  # the squad of the raiders (census)
        self.game.method(self.engine, "spawnArmy", lambda _self, _point, names, _owner, _company, _days: self.make_raiders(len(names)))
        self.add_store("Supplies_5", x=0.0, y=0.0, goods=[(16, 10), (3, 4)])
        self.add_store("Supplies_9", x=5000.0, y=5000.0, goods=[(7, 2)])
        self.game.load_mod(self.mod_name)
        self.game.advance(2)
        self.counter = 0

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

    def test_the_plunder_returns_the_goods_by_type(self):
        result = self.game.lua.eval("(function() local taken, by_good = require('features.raid_behavior.world').plunder(20, require('config').raid_behavior.store_tiers); return taken .. ',' .. by_good[16] end)")()
        self.assertEqual(result, "16,10")

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

if __name__ == "__main__":
    unittest.main()
