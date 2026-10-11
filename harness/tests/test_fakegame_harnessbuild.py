"""Mock tests for HarnessBuild (spec 10, spike R8): construction site goods, ruins, demolish and a lower site cost, in the fake game kit.

The fake world copies what the real game did (spike-R8.md): a site is not constructed and lists `constructionGoods` ({Type, amt});
a burned or collapsed building becomes Rubble (type 75); demolish removes the ruin from the list.
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
from scenarios import rebuild_cost

WORLD = """
function(fg)
    local world = { buildings = {}, calls = {} }
    local player = fg.object("PawnCPP", { isMainPlayer = true }, "/Game/Fake/Player")
    fg.set_method(player, "GetAddress", function() return 1 end)
    local function add(kind, built, needs)
        local goods = {}
        for _, need in ipairs(needs or {}) do goods[#goods + 1] = { Type = need[1], amt = need[2] } end
        local b = fg.object("SMBuildingMaster", { Data = { bType = kind }, onFire = false, rubble = false, built = built,
                                                  constructionGoods = fg.array(goods, { wrap = false }) })
        fg.set_method(b, "IsRubble", function(self) return self.rubble end)
        fg.set_method(b, "IsConstructed", function(self) return self.built end)
        fg.set_method(b, "StartFire", function(self) self.onFire = true; self.rubble = true; self.Data.bType = 75 end)
        fg.set_method(b, "collapseBuilding", function(self) self.rubble = true; self.Data.bType = 75 end)
        fg.set_method(b, "demolish", function(self)
            for i, other in ipairs(world.buildings) do if other == self then table.remove(world.buildings, i); break end end
        end)
        world.buildings[#world.buildings + 1] = b
        return b
    end
    world.add = add
    -- One game step: fires burn out, every site is built and its goods leave the stock (the number is kept in world.stock).
    world.stock = 100
    function world.step()
        for _, b in ipairs(world.buildings) do
            b.onFire = false
            if not b.built and not b.rubble then
                for i = 1, #b.constructionGoods do world.stock = world.stock - b.constructionGoods[i].amt; b.constructionGoods[i].amt = 0 end
                b.built = true
            end
        end
    end
    add(30, true)
    add(121, true)
    local region = fg.object("Region", { ownerPawn = player, regionName = fg.text("Test Village") })
    fg.set_method(region, "GetBuildings", function() return world.buildings end)
    fg.set_method(region, "getBuildingCount", function(self, kind)
        local n = 0
        for _, b in ipairs(world.buildings) do if b.Data.bType == kind then n = n + 1 end end
        return n
    end)
    fg.object("RTSMultiEngineCPP", { playerRef = player, regions = fg.array({ region }, { wrap = false }) })
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


class BuildingTestCase(unittest.TestCase):
    def setUp(self):
        self.game, self.world = start()
        self.addCleanup(self.game.close)

    def add_site(self, kind=121, needs=((17, 4),)):
        self.world.add(kind, False, self._needs(needs))

    def _needs(self, needs):
        return self.game.lua.eval("function(...) local t = {} for _, v in ipairs({...}) do t[#t + 1] = v end return t end")(
            *[self.game.lua.table_from(list(need)) for need in needs])

    def send(self, command, **fields):
        return run_command(self.game, command, **fields)


class SiteTests(BuildingTestCase):
    def test_a_site_lists_the_goods_it_needs_and_built_ones_list_none(self):
        self.add_site()
        answer = self.send("building_sites", type=121)
        self.assertTrue(answer["ok"])
        self.assertEqual(answer["counts"], {"built": 1, "sites": 1, "rubble": 0})
        site = [row for row in answer["buildings"] if not row["built"]][0]
        self.assertEqual(site["needs"], [{"good": 17, "amount": 4}])
        built = [row for row in answer["buildings"] if row["built"]][0]
        self.assertEqual(built["needs"], [])

    def test_without_a_type_all_buildings_are_listed(self):
        self.assertEqual(self.send("building_sites")["total"], 2)

    def test_a_type_above_the_limit_is_refused(self):
        self.assertFalse(self.send("ruin_building", type=999, method="fire")["ok"])


class RuinTests(BuildingTestCase):
    def test_fire_makes_a_ruin_of_the_built_building(self):
        answer = self.send("ruin_building", type=121, method="fire")
        self.assertTrue(answer["ok"])
        self.assertEqual((answer["before"]["built"], answer["after"]["built"], answer["after"]["rubble"]), (1, 0, 1))
        self.assertTrue(answer["rubble_now"])

    def test_a_missing_type_and_a_bad_method_are_refused(self):
        self.assertIn("no built building of type 50", self.send("ruin_building", type=50, method="fire")["error"])
        self.assertIn("method must be", self.send("ruin_building", type=121, method="melt")["error"])

    def test_a_site_is_not_ruined(self):
        self.send("ruin_building", type=121, method="collapse")
        self.add_site()
        self.assertIn("no built building", self.send("ruin_building", type=121, method="collapse")["error"])

    def test_demolish_removes_the_ruins_only(self):
        self.send("ruin_building", type=121, method="collapse")
        answer = self.send("demolish_ruins")
        self.assertEqual((answer["ok"], answer["before"], answer["demolished"], answer["after"]), (True, 1, 1, 0))
        self.assertEqual(self.send("building_sites")["total"], 1)


class CostTests(BuildingTestCase):
    def test_the_cost_can_be_lowered_and_reads_back(self):
        self.add_site()
        answer = self.send("set_site_cost", type=121, good=17, amount=2)
        self.assertEqual((answer["ok"], answer["before"], answer["needs"]), (True, 4, [{"good": 17, "amount": 2}]))
        sites = self.send("building_sites", type=121)["buildings"]
        self.assertEqual([row["needs"] for row in sites if not row["built"]], [[{"good": 17, "amount": 2}]])

    def test_a_cost_of_zero_is_allowed(self):
        self.add_site()
        self.assertEqual(self.send("set_site_cost", type=121, good=17, amount=0)["needs"], [{"good": 17, "amount": 0}])

    def test_the_cost_cannot_be_raised(self):
        self.add_site()
        answer = self.send("set_site_cost", type=121, good=17, amount=5)
        self.assertFalse(answer["ok"])
        self.assertIn("only be lowered", answer["error"])
        self.assertEqual(self.send("building_sites", type=121)["buildings"][1]["needs"], [{"good": 17, "amount": 4}])

    def test_no_site_and_a_wrong_good_are_refused(self):
        self.assertIn("no construction site", self.send("set_site_cost", type=121, good=17, amount=1)["error"])
        self.add_site()
        self.assertIn("does not need good 16", self.send("set_site_cost", type=121, good=16, amount=1)["error"])
        self.assertFalse(self.send("set_site_cost", type=121, good=17)["ok"])


class FakeBuildBridge:
    def __init__(self, world):
        self.world = world

    def engine_path(self):
        return "engine"

    def player_region_path(self):
        return "region"

    def call_function(self, ref, function, args=None):
        assert function == "getStockOfGood", function
        return self.world.stock


class FakeBuildTime:
    def __init__(self, world):
        self.world = world

    def run_game_seconds(self, seconds, speed=1):
        self.world.step()


class RebuildScenarioContext:
    def __init__(self, game, world, placing_works=True):
        sleep = sleep_in(game)
        self.expect = Expectations(sleep=sleep, monotonic=game.now)
        self.notes, self.metrics = [], {}
        self.log = SimpleNamespace(info=lambda message: None)
        self.bridge = FakeBuildBridge(world)
        self.time = FakeBuildTime(world)
        self.popups = lambda: None
        commands = CommandChannel(game.run_dir / "commands", sleep=sleep, monotonic=game.now)
        self.world = world
        self.placing_works = placing_works
        self.actions = Actions(self.bridge, self.expect, self.notes, commands=commands, mouse_placer=self.place)
        self.given = []
        self.actions.give_item = lambda item, amount: self.given.append((item, amount))

    def place(self, type_id, fx, fy):
        if self.placing_works:
            self.world.add(type_id, False, self.game_needs())

    def game_needs(self):
        return self.world.needs_table

    def metric(self, name, value):
        self.metrics[name] = value

    def result(self):
        result = self.expect.result()
        result["notes"] = list(self.notes)
        return result


class RebuildCostScenarioTests(unittest.TestCase):
    def run_scenario(self, placing_works=True):
        game, world = start()
        self.addCleanup(game.close)
        world.buildings = game.lua.eval("function(w) w.buildings = {} return w.buildings end")(world)
        world.needs_table = game.lua.eval("function() return { { 17, 4 } } end")()
        ctx = RebuildScenarioContext(game, world, placing_works)
        # place_building counts getBuildingCount(type) through the bridge in the real action; the fake bridge has no such call.
        ctx.actions.place_building = lambda type_id, fx=0.65, fy=0.65: ctx.place(type_id, fx, fy)
        return rebuild_cost.run(ctx), ctx

    def test_passes_with_the_rules_of_the_real_game(self):
        result, ctx = self.run_scenario()
        failed = [a["name"] for a in result["asserts"] if not a["ok"]]
        self.assertEqual(failed, [])
        self.assertEqual(ctx.metrics, {"full_cost_planks": 4, "discounted_cost_planks": 2})

    def test_the_scenario_needs_the_mouse_so_it_is_hidden_and_tagged(self):
        self.assertTrue(rebuild_cost.HIDDEN)
        self.assertEqual(rebuild_cost.COVERS, ["R8"])

    def test_a_game_that_places_no_site_stops_with_a_clear_error(self):
        # No site means the cost read finds no site (a failed assert) and the later command is refused by the mod: a loud stop.
        with self.assertRaisesRegex(CommandRefused, "no built building of type 121"):
            self.run_scenario(placing_works=False)


if __name__ == "__main__":
    unittest.main()
