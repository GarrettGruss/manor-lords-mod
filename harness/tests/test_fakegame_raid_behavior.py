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

    def test_the_numbers_are_kept_in_the_pawn_tags(self):
        self.start_raid()
        tags = list(self.game.lua.eval("tag_names")(self.pawn).values())
        self.assertIn("invasion:raid_count=1", tags)
        self.assertIn("invasion:raid_state=1", tags)


if __name__ == "__main__":
    unittest.main()
