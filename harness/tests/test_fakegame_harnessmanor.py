"""Mock tests for HarnessManor (spec 12, criterion M1): manor state, the finish shortcut, put and take, worker slots,
and the scenarios manor-storage and manor-storage-workers.

The fake world copies what the real game did (spec 12 notes): a Keep site is not constructed ("Data.constructed" false),
`addToInventory(Good)` adds goods to the building and to the region stock, `consumeGoodNoCheck(good)` removes one unit,
and `RTSMultiEngineCPP:setRegionsManor(building)` sets `Region.manor`.
Worker slots (spike in spec 12, `worker-slots.md`): `getMaxWorkerFamilies` and `getJobType` read the row of `Data.bType` in the DataTable
`buildingStats` (row name = type id, `workerTypes.Y` = slots). `Region:assignFamily(index, building)` sets `family.assignedTo`.
"""

import json
import unittest
from types import SimpleNamespace

import fakegame_path  # noqa: F401
import runlib_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import sleep_in
from runlib.actions import Actions, ActionError
from runlib.commands import CommandChannel, CommandRefused
from runlib.expectations import Expectations
from scenarios import manor_storage, manor_storage_workers

WORLD = """
function(fg)
    local world = { buildings = {}, stock = {} }
    -- buildingStats rows: the Storehouse (72) and the Granary (80) have slots and a role, the Keep (57) has none.
    world.stats = {
        [57] = { isWork = false, job = 0, buildingFunction = 0, storageLimitGeneric = 50, storageLimitPantry = 0, workerTypes = { Y = 0.0 } },
        [72] = { isWork = true, job = 45, buildingFunction = 6, storageLimitGeneric = 250, storageLimitPantry = 0, workerTypes = { Y = 3.0 } },
        [80] = { isWork = true, job = 44, buildingFunction = 5, storageLimitGeneric = 0, storageLimitPantry = 500, workerTypes = { Y = 3.0 } },
    }
    local stats = fg.object("DataTable", {}, "/Game/NotStronghold/Data/buildingStats.buildingStats")
    fg.set_method(stats, "FindRow", function(self, name) return world.stats[tonumber(name)] end)
    world.stats_table = stats
    local player = fg.object("PawnCPP", { isMainPlayer = true }, "/Game/Fake/Player")
    fg.set_method(player, "GetAddress", function() return 1 end)
    local region = fg.object("Region", { ownerPawn = player, regionName = fg.text("Test Village") })
    world.region = region
    local nobody = fg.object("SMBuildingMaster", {}, "/Game/Fake/Nobody")
    fg.invalidate(nobody)
    world.families = {}
    for i = 1, 3 do world.families[i] = fg.object("WorkerFamily", { assignedTo = nobody, familyMembers = {} }) end
    region.workerFamilies = fg.array(world.families, { wrap = false })
    local function ids_list() return setmetatable({}, { __index = { GetArrayNum = function(t) return #t end } }) end
    fg.set_method(region, "assignFamily", function(self, index, building)
        world.families[index + 1].assignedTo = building
        local ids = building.assignedFamilyIDs
        ids[#ids + 1] = index
    end)
    fg.set_method(region, "unassignFamily", function(self, index)
        local building = world.families[index + 1].assignedTo
        local ids = building.assignedFamilyIDs
        for i = #ids, 1, -1 do if ids[i] == index then table.remove(ids, i) end end
        world.families[index + 1].assignedTo = nobody
    end)
    fg.set_method(region, "getNumUnassignedFamilies", function()
        local free = 0
        for _, family in ipairs(world.families) do if not family.assignedTo:IsValid() then free = free + 1 end end
        return free
    end)
    -- Rubble that a worker carries from a Supplies crate into the Keep. mode: "worker" (only with an assigned family), "always", "never".
    function world.haul(units, mode)
        for _, b in ipairs(world.buildings) do
            local carries = b.Data.bType == 57 and (mode == "always" or (mode == "worker" and #b.assignedFamilyIDs > 0 and world.stats[57].workerTypes.Y > 0))
            if carries and units > 0 then
                local found
                for i = 1, #b.Inventory do if b.Inventory[i].Type == 15 then found = b.Inventory[i] end end
                if found then found.amt = found.amt + units else fg.array_add(b.Inventory, { Type = 15, amt = units }) end
            end
        end
    end
    local function add_stock(kind, amount) world.stock[kind] = (world.stock[kind] or 0) + amount end
    world.add_stock = add_stock
    -- The test makes goods leave the Keep, to see that the scenario notices.
    function world.drain(amount)
        for _, b in ipairs(world.buildings) do
            if b.Data.bType == 57 and #b.Inventory > 0 then b.Inventory[1].amt = b.Inventory[1].amt - amount end
        end
    end
    function world.add(kind, built, name)
        local b = fg.object("SMBuildingMaster", { Data = { bType = kind, constructed = built },
                                                  Inventory = fg.array({}, { wrap = false }),
                                                  assignedFamilyIDs = ids_list(), buildingFunction = 0,
                                                  storageLimitGeneric = world.stats[kind] and world.stats[kind].storageLimitGeneric or 0,
                                                  storageLimitPantry = 0,
                                                  constructionGoods = fg.array({ { Type = 16, amt = 10 } }, { wrap = false }) }, name)
        fg.set_method(b, "IsConstructed", function(self) return self.Data.constructed end)
        fg.set_method(b, "getMaxWorkerFamilies", function(self) return math.floor(world.stats[self.Data.bType].workerTypes.Y) end)
        fg.set_method(b, "getJobType", function(self) return world.stats[self.Data.bType].job end)
        fg.set_method(b, "isStorageTypeBuilding", function(self) return self.buildingFunction == 5 or self.buildingFunction == 6 end)
        fg.set_method(b, "getAllWorkers", function(self)
            local people = {}
            for _ = 1, #self.assignedFamilyIDs * 2 do people[#people + 1] = "person" end
            return people
        end)
        fg.set_method(b, "addToInventory", function(self, good)
            local found
            for i = 1, #self.Inventory do if self.Inventory[i].Type == good.Type then found = self.Inventory[i] end end
            if found then found.amt = found.amt + good.amt else fg.array_add(self.Inventory, { Type = good.Type, amt = good.amt }) end
            add_stock(good.Type, good.amt)
        end)
        fg.set_method(b, "consumeGoodNoCheck", function(self, kind)
            for i = 1, #self.Inventory do
                local entry = self.Inventory[i]
                if entry.Type == kind and entry.amt > 0 then entry.amt = entry.amt - 1; add_stock(kind, -1); return end
            end
            error("nothing to consume")
        end)
        world.buildings[#world.buildings + 1] = b
        return b
    end
    fg.set_method(region, "GetBuildings", function() return world.buildings end)
    fg.set_method(region, "getStockOfGood", function(self, kind) return world.stock[kind] or 0 end)
    local engine = fg.object("RTSMultiEngineCPP", { playerRef = player, regions = fg.array({ region }, { wrap = false }) })
    fg.set_method(engine, "setRegionsManor", function(self, manor) region.manor = manor end)
    world.add(30, true, "/Game/Fake/Map.Map:PersistentLevel.SMBuildingMaster_100")
    return world
end
"""


def start():
    game = FakeGame()
    game.start()
    world = game.lua.eval(WORLD)(game.fg)
    game.load_mod("HarnessActions")
    game.advance(1)
    return game, world


def run_command(game, command, **fields):
    folder = game.run_dir / "commands"
    folder.mkdir(exist_ok=True)
    number = len(list(folder.glob("*.json"))) // 2 + 1
    (folder / f"{number:04d}.json").write_text(json.dumps({"id": f"{number:04d}", "command": command, **fields}), encoding="utf-8")
    game.advance(1)
    return json.loads((folder / f"{number:04d}.result.json").read_text(encoding="utf-8"))


class ManorTestCase(unittest.TestCase):
    def setUp(self):
        self.game, self.world = start()
        self.addCleanup(self.game.close)

    def add_keep(self, built=False):
        return self.world.add(57, built, "/Game/Fake/Map.Map:PersistentLevel.SMBuildingMaster_200")

    def send(self, command, **fields):
        return run_command(self.game, command, **fields)

    def finished_keep(self):
        self.add_keep()
        self.assertTrue(self.send("finish_manor_site", type=57)["ok"])


class StateTests(ManorTestCase):
    def test_a_village_without_a_manor_lists_no_module(self):
        answer = self.send("manor_state")
        self.assertEqual((answer["ok"], answer["count"], answer["region_has_manor"]), (True, 0, False))

    def test_a_keep_site_is_listed_as_not_built(self):
        self.add_keep()
        module = self.send("manor_state")["modules"][0]
        self.assertEqual((module["type"], module["built"], module["is_region_manor"], module["goods"]), (57, False, False, []))

    def test_other_buildings_are_not_manor_modules(self):
        self.assertEqual(self.send("manor_state")["count"], 0)


class FinishTests(ManorTestCase):
    def test_finish_builds_the_keep_and_registers_it_as_the_region_manor(self):
        self.add_keep()
        answer = self.send("finish_manor_site", type=57)
        self.assertEqual((answer["ok"], answer["module"]["built"], answer["module"]["is_region_manor"]), (True, True, True))
        self.assertTrue(self.send("manor_state")["region_has_manor"])

    def test_finish_without_a_site_and_with_a_wrong_type_is_refused(self):
        self.assertIn("no unfinished manor module", self.send("finish_manor_site", type=57)["error"])
        self.assertIn("must be a manor type", self.send("finish_manor_site", type=121)["error"])

    def test_a_built_keep_is_not_finished_twice(self):
        self.add_keep(built=True)
        self.assertIn("no unfinished", self.send("finish_manor_site", type=57)["error"])


class StoreTests(ManorTestCase):
    def test_put_and_take_change_the_module_and_the_region_stock(self):
        self.finished_keep()
        put = self.send("manor_put", good=27, amount=20)
        self.assertEqual((put["ok"], put["before"], put["after"], put["stock_before"], put["stock_after"]), (True, 0, 20, 0, 20))
        take = self.send("manor_take", good=27, amount=5)
        self.assertEqual((take["ok"], take["before"], take["after"], take["stock_after"]), (True, 20, 15, 15))
        self.assertEqual(self.send("manor_state")["modules"][0]["goods"], [{"good": 27, "amount": 15}])

    def test_put_into_a_site_that_is_not_built_is_refused(self):
        self.add_keep()
        self.assertIn("no built manor module", self.send("manor_put", good=27, amount=1)["error"])

    def test_a_put_over_the_capacity_is_refused_and_changes_nothing(self):
        self.finished_keep()
        self.send("manor_put", good=27, amount=150)
        answer = self.send("manor_put", good=16, amount=51)
        self.assertFalse(answer["ok"])
        self.assertIn("do not fit", answer["error"])
        self.assertEqual(self.send("manor_state")["modules"][0]["total"], 150)
        self.assertTrue(self.send("manor_put", good=16, amount=50)["ok"])

    def test_a_take_of_more_than_the_module_holds_is_refused(self):
        self.finished_keep()
        self.send("manor_put", good=27, amount=3)
        answer = self.send("manor_take", good=27, amount=4)
        self.assertFalse(answer["ok"])
        self.assertIn("holds only 3", answer["error"])
        self.assertEqual(self.send("manor_state")["modules"][0]["goods"], [{"good": 27, "amount": 3}])

    def test_bad_inputs_are_refused(self):
        self.finished_keep()
        self.assertIn("item number", self.send("manor_put", good=999, amount=1)["error"])
        self.assertIn("amount must be", self.send("manor_put", good=27, amount=0)["error"])
        self.assertIn("amount must be", self.send("manor_put", good=27, amount=1001)["error"])
        self.assertIn("amount must be", self.send("manor_take", good=27)["error"])
        self.assertIn("no manor module with id 5", self.send("manor_take", good=27, amount=1, manor=5)["error"])


class FakeManorBridge:
    def __init__(self, world):
        self.world = world

    def engine_path(self):
        return "engine"

    def player_region_path(self):
        return "region"

    def call_function(self, ref, function, args=None):
        assert function == "getStockOfGood", function
        return self.world.stock[args[0]] if args[0] in self.world.stock else 0


class FakeManorTime:
    def __init__(self, world, drift=0, haul="worker"):
        self.world = world
        self.drift = drift
        self.haul = haul

    def run_game_seconds(self, seconds, speed=1):
        # A test can make the game "move" stone out of the manor, to see that the scenario notices.
        if self.drift:
            self.world.drain(self.drift)
        # Two units of rubble a game day, as a real storehouse worker does (about 5 in 2 days in the spike).
        self.world.haul(round(seconds / 40 * 2), self.haul)


class ManorScenarioContext:
    def __init__(self, game, world, placing_works=True, drift=0, haul="worker"):
        sleep = sleep_in(game)
        self.expect = Expectations(sleep=sleep, monotonic=game.now)
        self.notes, self.metrics = [], {}
        self.log = SimpleNamespace(info=lambda message: None)
        self.bridge = FakeManorBridge(world)
        self.time = FakeManorTime(world, drift, haul)
        commands = CommandChannel(game.run_dir / "commands", sleep=sleep, monotonic=game.now)
        self.world = world
        self.actions = Actions(self.bridge, self.expect, self.notes, commands=commands, mouse_placer=lambda *a: None)
        self.actions.give_item = lambda item, amount: world.add_stock(item, amount)
        self.actions.place_building = (lambda type_id, fx=0.65, fy=0.65:
                                       world.add(type_id, False, "/Game/Fake/Map.Map:PersistentLevel.SMBuildingMaster_200") if placing_works else None)

    def metric(self, name, value):
        self.metrics[name] = value

    def result(self):
        result = self.expect.result()
        result["notes"] = list(self.notes)
        return result


class ManorStorageScenarioTests(unittest.TestCase):
    def run_scenario(self, **options):
        game, world = start()
        self.addCleanup(game.close)
        ctx = ManorScenarioContext(game, world, **options)
        return manor_storage.run(ctx), ctx

    def test_passes_with_the_rules_of_the_real_game(self):
        result, ctx = self.run_scenario()
        failed = [a["name"] for a in result["asserts"] if not a["ok"]]
        self.assertEqual(failed, [])
        self.assertEqual(ctx.metrics, {"manor_stone_kept": 15})

    def test_goods_that_leave_the_manor_during_the_days_fail_the_scenario(self):
        result, _ = self.run_scenario(drift=3)
        failed = [a["name"] for a in result["asserts"] if not a["ok"]]
        self.assertIn("after 2 game days the manor still holds the stone", failed)

    def test_a_game_that_places_no_keep_fails_the_site_assert_and_stops_loudly(self):
        with self.assertRaisesRegex(CommandRefused, "no unfinished manor module of type 57"):
            self.run_scenario(placing_works=False)

    def test_the_scenario_needs_the_mouse_so_it_is_hidden_and_tagged(self):
        self.assertTrue(manor_storage.HIDDEN)
        self.assertEqual(manor_storage.COVERS, ["M1"])

    def test_the_action_checks_its_inputs_before_it_sends(self):
        game, world = start()
        self.addCleanup(game.close)
        ctx = ManorScenarioContext(game, world)
        with self.assertRaises(ActionError):
            ctx.actions.manor_put(27, 0)
        with self.assertRaises(ActionError):
            ctx.actions.manor_take(300, 1)


class WorkerSlotTests(ManorTestCase):
    def test_the_keep_has_no_slot_and_no_role_before_the_write(self):
        self.finished_keep()
        module = self.send("manor_worker_state")["modules"][0]
        self.assertEqual((module["max_slots"], module["job"], module["assigned"], module["is_storage"]), (0, 0, 0, False))

    def test_worker_slot_gives_the_storehouse_role_and_reads_it_back(self):
        self.finished_keep()
        answer = self.send("manor_worker_slot", job=45, slots=3)
        self.assertEqual((answer["ok"], answer["job_name"], answer["after"]["max_slots"], answer["after"]["job"], answer["after"]["is_storage"]),
                         (True, "WarehouseWorker", 3, 45, True))
        self.assertEqual(answer["before"]["max_slots"], 0)
        row = self.world.stats[57]
        self.assertEqual((row["isWork"], row["job"], row["buildingFunction"], row["storageLimitGeneric"]), (True, 45, 6, 250))

    def test_worker_slot_with_the_granary_role_sets_the_pantry_limit(self):
        self.finished_keep()
        answer = self.send("manor_worker_slot", job=44, slots=2)
        self.assertEqual((answer["ok"], answer["after"]["job"], answer["after"]["max_slots"]), (True, 44, 2))
        self.assertEqual(self.world.stats[57]["storageLimitPantry"], 500)

    def test_worker_slot_refuses_bad_inputs(self):
        self.finished_keep()
        self.assertIn("job must be 45", self.send("manor_worker_slot", job=1, slots=3)["error"])
        self.assertIn("job must be 45", self.send("manor_worker_slot", slots=3)["error"])
        self.assertIn("slots must be from 1 to 6", self.send("manor_worker_slot", job=45, slots=0)["error"])
        self.assertIn("slots must be from 1 to 6", self.send("manor_worker_slot", job=45, slots=7)["error"])
        self.assertIn("slots must be from 1 to 6", self.send("manor_worker_slot", job=45)["error"])

    def test_worker_slot_on_a_site_that_is_not_built_is_refused(self):
        self.add_keep()
        self.assertIn("no built manor module", self.send("manor_worker_slot", job=45, slots=3)["error"])

    def test_worker_slot_fails_loudly_when_the_building_does_not_read_the_write(self):
        self.finished_keep()
        # A game that ignores the table: the building reads a fixed number.

        building = [b for b in self.world.buildings.values() if b.Data.bType == 57][0]
        self.game.method(building, "getMaxWorkerFamilies", lambda this: 0)
        answer = self.send("manor_worker_slot", job=45, slots=3)
        self.assertFalse(answer["ok"])
        self.assertIn("reads 0 slots", answer["error"])

    def test_assign_worker_takes_the_first_free_family_and_reads_it_back(self):
        self.finished_keep()
        self.send("manor_worker_slot", job=45, slots=2)
        first = self.send("manor_assign_worker")
        self.assertEqual((first["ok"], first["family"], first["before"]["assigned"], first["after"]["assigned"], first["after"]["workers"]), (True, 0, 0, 1, 2))
        second = self.send("manor_assign_worker")
        self.assertEqual((second["ok"], second["family"]), (True, 1))
        self.assertEqual(self.send("manor_worker_state")["unassigned_families"], 1)

    def test_assign_worker_refuses_without_a_slot_with_all_slots_taken_and_for_bad_families(self):
        self.finished_keep()
        self.assertIn("no worker slot", self.send("manor_assign_worker")["error"])
        self.send("manor_worker_slot", job=45, slots=1)
        self.assertTrue(self.send("manor_assign_worker", family=2)["ok"])
        self.assertIn("all 1 worker slots are taken", self.send("manor_assign_worker")["error"])
        self.send("manor_worker_slot", job=45, slots=3)
        self.assertIn("family must be from 0 to 2", self.send("manor_assign_worker", family=3)["error"])
        self.assertIn("already has a workplace", self.send("manor_assign_worker", family=2)["error"])

    def test_assign_worker_needs_a_free_family(self):
        self.finished_keep()
        self.send("manor_worker_slot", job=45, slots=6)
        for _ in range(3):
            self.assertTrue(self.send("manor_assign_worker")["ok"])
        self.assertIn("no family without a workplace", self.send("manor_assign_worker")["error"])

    def test_unassign_takes_every_family_off(self):
        self.finished_keep()
        self.send("manor_worker_slot", job=45, slots=3)
        self.send("manor_assign_worker")
        self.send("manor_assign_worker")
        answer = self.send("manor_unassign_workers")
        self.assertEqual((answer["ok"], answer["before"]["assigned"], answer["after"]["assigned"]), (True, 2, 0))
        self.assertEqual(self.send("manor_worker_state")["unassigned_families"], 3)

    def test_the_actions_check_their_inputs_before_they_send(self):
        game, world = start()
        self.addCleanup(game.close)
        ctx = ManorScenarioContext(game, world)
        with self.assertRaises(ActionError):
            ctx.actions.manor_worker_slot(1, 3)
        with self.assertRaises(ActionError):
            ctx.actions.manor_worker_slot(45, 0)
        with self.assertRaises(ActionError):
            ctx.actions.manor_assign_worker(family=-1)


class ManorStorageWorkersScenarioTests(unittest.TestCase):
    def run_scenario(self, **options):
        game, world = start()
        self.addCleanup(game.close)
        ctx = ManorScenarioContext(game, world, **options)
        return manor_storage_workers.run(ctx), ctx

    def failed(self, result):
        return [a["name"] for a in result["asserts"] if not a["ok"]]

    def test_passes_with_the_rules_of_the_real_game(self):
        result, ctx = self.run_scenario()
        self.assertEqual(self.failed(result), [])
        self.assertEqual(ctx.metrics, {"manor_goods_hauled": 6})

    def test_goods_that_arrive_without_a_worker_fail_the_control(self):
        result, _ = self.run_scenario(haul="always")
        self.assertIn("control: with a slot and no worker nothing arrives in 2 game days", self.failed(result))

    def test_a_worker_that_carries_nothing_fails_the_scenario(self):
        result, _ = self.run_scenario(haul="never")
        self.assertIn("the worker carried goods into the Keep in 3 game days (units)", self.failed(result))

    def test_a_game_that_places_no_keep_stops_loudly(self):
        with self.assertRaisesRegex(CommandRefused, "no unfinished manor module of type 57"):
            self.run_scenario(placing_works=False)

    def test_the_scenario_is_hidden_and_tagged(self):
        self.assertTrue(manor_storage_workers.HIDDEN)
        self.assertEqual(manor_storage_workers.COVERS, ["M1"])
        self.assertEqual(manor_storage_workers.STOREHOUSE_JOB, 45)


if __name__ == "__main__":
    unittest.main()
