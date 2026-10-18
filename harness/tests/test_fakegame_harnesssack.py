"""Mock tests for HarnessSack and HarnessLoot (spec 10, spikes S6 and R3): a fake village with buildings, goods and families."""

import json
import re
import unittest
from pathlib import Path

import fakegame_path  # noqa: F401
from fakegame import FakeGame

REPO = Path(__file__).resolve().parents[2]

# A village of 4 buildings. 2 hold goods. 5 families of 2 members. Rules copied from what the real game did (spike S6):
# collapse -> rubble at once; fire -> rubble flag at once, goods lost when the fire is out (the test calls burn_out);
# consumeGoodNoCheck removes one unit; just_die marks the unit dead.
BUILD_VILLAGE = """
function(fg, options)
    local village = { buildings = {}, units = {}, families = {}, fires = {}, calls = {} }
    local player = fg.object("PawnCPP", { isMainPlayer = true }, "/Game/Fake/Player")
    fg.set_method(player, "GetAddress", function() return 1 end)
    local other = fg.object("PawnCPP", { isMainPlayer = false }, "/Game/Fake/Other")
    fg.set_method(other, "GetAddress", function() return 2 end)

    local function good(kind, amt) return { Type = kind, amt = amt } end
    local function addBuilding(kind, goods)
        local items = {}
        for _, g in ipairs(goods) do items[#items + 1] = good(g[1], g[2]) end
        local b = fg.object("SMBuildingMaster", { Data = { bType = kind }, onFire = false, rubble = false,
                                                  Inventory = fg.array(items, { wrap = false }), items = items })
        fg.set_method(b, "IsRubble", function(self) return self.rubble end)
        fg.set_method(b, "StartFire", function(self) self.onFire = true; self.rubble = true; village.calls[#village.calls + 1] = "fire" end)
        fg.set_method(b, "collapseBuilding", function(self) self.rubble = true; self.Data.bType = 75; village.calls[#village.calls + 1] = "collapse" end)
        fg.set_method(b, "consumeGoodNoCheck", function(self, kind2)
            if options.refuse_consume then return end
            for _, g in ipairs(self.items) do
                if g.Type == kind2 and g.amt > 0 then g.amt = g.amt - 1; return end
            end
        end)
        village.buildings[#village.buildings + 1] = b
        return b
    end
    addBuilding(30, {})
    addBuilding(88, { { 16, 8 } })
    addBuilding(88, { { 172, 20 }, { 216, 20 }, { 15, 20 }, { 6, 10 } })
    addBuilding(87, {})

    local function addFamily(members)
        local list = {}
        for i = 1, members do
            local unit = fg.object("SMUnit", { dead = false })
            fg.set_method(unit, "just_die", function(self) self.dead = true end)
            list[#list + 1] = unit
            village.units[#village.units + 1] = unit
        end
        village.families[#village.families + 1] = { familyMembers = fg.array(list, { wrap = false }), list = list }
    end
    for _ = 1, 5 do addFamily(2) end

    local famStructs = {}
    for _, f in ipairs(village.families) do famStructs[#famStructs + 1] = f end
    local region = fg.object("Region", { ownerPawn = player, regionName = fg.text("Test Village"),
                                         workerFamilies = fg.array(famStructs, { wrap = false }) })
    local function livingMembers(family)
        local n = 0
        for _, u in ipairs(family.list) do if not u.dead then n = n + 1 end end
        return n
    end
    fg.set_method(region, "GetBuildings", function() return village.buildings end)
    fg.set_method(region, "getStock", function()
        local sums, order = {}, {}
        for _, b in ipairs(village.buildings) do
            for _, g in ipairs(b.items) do
                if g.amt > 0 then
                    if not sums[g.Type] then sums[g.Type] = 0; order[#order + 1] = g.Type end
                    sums[g.Type] = sums[g.Type] + g.amt
                end
            end
        end
        local out = {}
        for _, kind in ipairs(order) do out[#out + 1] = good(kind, sums[kind]) end
        return out
    end)
    fg.set_method(region, "getTotalNumFamilies", function()
        local n = 0
        for _, f in ipairs(village.families) do if livingMembers(f) > 0 then n = n + 1 end end
        return n
    end)
    fg.set_method(region, "getNumTotalPopulation", function()
        local n = 0
        for _, f in ipairs(village.families) do n = n + livingMembers(f) end
        return n
    end)
    -- A region of another lord, listed first: the village must be found by its owner.
    local foreign = fg.object("Region", { ownerPawn = other, regionName = fg.text("Foreign") })
    local engine = fg.object("RTSMultiEngineCPP", { playerRef = player, regions = fg.array({ foreign, region }, { wrap = false }) })
    village.region, village.player, village.engine = region, player, engine
    return village
end
"""

BURN_OUT = """
function(village)
    for _, b in ipairs(village.buildings) do
        if b.onFire then
            b.onFire = false
            b.Data.bType = 75
            for _, g in ipairs(b.items) do g.amt = 0 end
        end
    end
end
"""

FORBIDDEN = re.compile(r"\b(loadstring|dofile|loadfile|os\.execute|io\.popen)\b|[^%w_.]load\s*\(")


def build(game, **options):
    return game.lua.eval(BUILD_VILLAGE)(game.fg, game.lua.table_from(options))


def sack(game):
    return game.lua.eval('(require("HarnessSack"))')


def run_command(game, command, **fields):
    folder = game.run_dir / "commands"
    folder.mkdir(exist_ok=True)
    number = len(list(folder.glob("*.json"))) // 2 + 1
    body = {"id": f"{number:04d}", "command": command, **fields}
    (folder / f"{number:04d}.json").write_text(json.dumps(body), encoding="utf-8")
    game.advance(1)
    return json.loads((folder / f"{number:04d}.result.json").read_text(encoding="utf-8"))


class CensusTests(unittest.TestCase):
    def test_counts_buildings_stock_stores_and_people(self):
        with FakeGame() as game:
            build(game)
            census = sack(game).census()
            self.assertEqual(dict(census.buildings), {"total": 4, "standing": 4, "rubble": 0, "burning": 0})
            self.assertEqual(census.stock.total, 8 + 70)
            self.assertEqual(census.stock.by_good[172], 20)
            self.assertEqual([store.goods for store in census.stores.values()], [8, 70])
            self.assertEqual(dict(census.people), {"families": 5, "population": 10})
            self.assertEqual(census.region, "Test Village")

    def test_the_village_is_found_by_its_owner_not_by_position(self):
        with FakeGame() as game:
            village = build(game)
            region = sack(game).playerRegion()
            self.assertEqual(region.regionName.ToString(), "Test Village")
            self.assertIsNotNone(village.player)

    def test_a_named_region_that_the_player_does_not_own_is_an_error_message(self):
        with FakeGame() as game:
            build(game)
            census, problem = sack(game).census("Foreign")
            self.assertIsNone(census)
            self.assertIn("does not own a region named Foreign", problem)
            result = sack(game).sack_people({"region": "Nowhere", "count": 1})
            self.assertFalse(result.ok)

    def test_no_player_region_is_an_error_message(self):
        with FakeGame() as game:
            game.obj("RTSMultiEngineCPP", playerRef=game.obj("PawnCPP"), regions=game.array([]))
            census, problem = sack(game).census()
            self.assertIsNone(census)
            self.assertIn("no region", problem)


class BuildingTests(unittest.TestCase):
    def test_collapse_makes_rubble_and_keeps_the_goods(self):
        with FakeGame() as game:
            build(game)
            answer = game.lua.eval('function(m) return m.sack_buildings({ count = 2, method = "collapse" }) end')(sack(game))
            self.assertEqual((answer.ok, answer.hit), (True, 2))
            self.assertEqual(dict(answer.after.buildings), {"total": 4, "standing": 2, "rubble": 2, "burning": 0})
            self.assertEqual(answer.after.stock.total, answer.before.stock.total)

    def test_percent_rounds_half_up(self):
        with FakeGame() as game:
            build(game)
            answer = game.lua.eval('function(m) return m.sack_buildings({ percent = 50 }) end')(sack(game))
            self.assertEqual(answer.hit, 2)  # 50% of 4
        with FakeGame() as game:
            build(game)
            self.assertEqual(game.lua.eval('function(m) return m.sack_buildings({ percent = 38 }) end')(sack(game)).hit, 2)  # 1.52 -> 2

    def test_fire_sets_the_flag_and_burn_out_leaves_ruins(self):
        with FakeGame() as game:
            village = build(game)
            answer = game.lua.eval('function(m) return m.sack_buildings({ count = 2, method = "fire" }) end')(sack(game))
            self.assertEqual(answer.after.buildings.burning, 2)
            game.lua.eval(BURN_OUT)(village)
            census = sack(game).census()
            self.assertEqual((census.buildings.burning, census.buildings.rubble, census.buildings.total), (0, 2, 4))
            self.assertEqual(census.stock.total, 70)  # the burned store with 8 timber lost its goods

    def test_only_standing_buildings_are_hit(self):
        with FakeGame() as game:
            build(game)
            module = sack(game)
            run = game.lua.eval('function(m, n) return m.sack_buildings({ count = n, method = "collapse" }) end')
            run(module, 3)
            self.assertEqual(run(module, 3).hit, 1)  # only one was standing
            self.assertEqual(run(module, 3).hit, 0)

    def test_a_bad_method_is_an_error_message(self):
        with FakeGame() as game:
            build(game)
            answer = game.lua.eval('function(m) return m.sack_buildings({ count = 1, method = "bomb" }) end')(sack(game))
            self.assertFalse(answer.ok)
            self.assertIn("method must be", answer.error)


class GoodsTests(unittest.TestCase):
    def test_remove_units_of_one_good(self):
        with FakeGame() as game:
            build(game)
            answer = game.lua.eval('function(m) return m.sack_goods({ good = 15, amount = 5 }) end')(sack(game))
            self.assertEqual(answer.removed, 5)
            self.assertEqual(answer.before.stock.total - answer.after.stock.total, 5)
            self.assertEqual(answer.after.stock.by_good[15], 15)

    def test_remove_cannot_take_more_than_there_is(self):
        with FakeGame() as game:
            build(game)
            answer = game.lua.eval('function(m) return m.sack_goods({ good = 16, amount = 99 }) end')(sack(game))
            self.assertEqual(answer.removed, 8)

    def test_percent_of_every_good(self):
        with FakeGame() as game:
            build(game)
            answer = game.lua.eval('function(m) return m.sack_goods({ percent = 50 }) end')(sack(game))
            self.assertEqual(answer.removed, 4 + 10 + 10 + 10 + 5)
            self.assertEqual(answer.after.stock.total, 39)

    def test_percent_of_one_store(self):
        with FakeGame() as game:
            village = build(game)
            module = sack(game)
            store_id = max(store.id for store in module.census().stores.values())
            answer = game.lua.eval('function(m, id) return m.sack_goods({ percent = 10, store = id }) end')(module, store_id)
            self.assertEqual(answer.removed, 7)
            first = module.census().stores
            self.assertEqual(sorted(store.goods for store in first.values()), [8, 63])
            self.assertIsNotNone(village)

    def test_an_unknown_store_is_an_error_message(self):
        with FakeGame() as game:
            build(game)
            answer = game.lua.eval('function(m) return m.sack_goods({ percent = 10, store = 999999 }) end')(sack(game))
            self.assertFalse(answer.ok)
            self.assertIn("no building with id 999999", answer.error)

    def test_a_game_that_refuses_to_consume_does_not_loop_forever(self):
        with FakeGame() as game:
            build(game, refuse_consume=True)
            answer = game.lua.eval('function(m) return m.sack_goods({ good = 15, amount = 5 }) end')(sack(game))
            self.assertEqual(answer.removed, 0)

    def test_one_call_is_capped(self):
        with FakeGame() as game:
            build(game)
            module = sack(game)
            self.assertEqual(module.MAX_GOODS_REMOVED, 5000)


class PeopleTests(unittest.TestCase):
    def test_kill_whole_families(self):
        with FakeGame() as game:
            build(game)
            answer = game.lua.eval('function(m) return m.sack_people({ count = 2 }) end')(sack(game))
            self.assertEqual((answer.families, answer.people), (2, 4))
            self.assertEqual(dict(answer.after.people), {"families": 3, "population": 6})

    def test_percent_of_families(self):
        with FakeGame() as game:
            build(game)
            answer = game.lua.eval('function(m) return m.sack_people({ percent = 40 }) end')(sack(game))
            self.assertEqual(answer.after.people.families, 3)

    def test_dead_members_are_not_killed_twice(self):
        with FakeGame() as game:
            build(game)
            module = sack(game)
            run = game.lua.eval('function(m) return m.sack_people({ count = 5 }) end')
            self.assertEqual(run(module).people, 10)
            self.assertEqual(run(module).people, 0)


class VillageTests(unittest.TestCase):
    def run_village(self, game, buildings, stock, people, method="collapse"):
        return game.lua.eval('function(m, b, s, p, mt) return m.sack_village({ buildings_pct = b, stock_pct = s, people_pct = p, method = mt }) end')(
            sack(game), buildings, stock, people, method)

    def test_all_three_shares(self):
        with FakeGame() as game:
            build(game)
            answer = self.run_village(game, 50, 50, 40)
            self.assertTrue(answer.ok, answer.error)
            self.assertEqual((answer.buildings_hit, answer.families_removed, answer.people_removed), (2, 2, 4))
            self.assertEqual(answer.after.buildings.rubble, 2)
            self.assertEqual(answer.after.stock.total, 39)
            self.assertEqual(answer.after.people.families, 3)

    def test_zero_percent_changes_nothing(self):
        with FakeGame() as game:
            build(game)
            answer = self.run_village(game, 0, 0, 0)
            self.assertEqual((answer.buildings_hit, answer.goods_removed, answer.families_removed), (0, 0, 0))
            self.assertEqual(dict(answer.after.buildings), dict(answer.before.buildings))

    def test_hundred_percent_takes_everything(self):
        with FakeGame() as game:
            build(game)
            answer = self.run_village(game, 100, 100, 100)
            self.assertEqual((answer.after.buildings.standing, answer.after.stock.total, answer.after.people.families), (0, 0, 0))

    def test_percent_out_of_range_is_refused(self):
        with FakeGame() as game:
            build(game)
            for args in ((101, 0, 0), (0, 101, 0), (0, 0, 101)):
                answer = self.run_village(game, *args)
                self.assertFalse(answer.ok)
                self.assertIn("must be 0 to 100", answer.error)
            self.assertEqual(sack(game).census().buildings.rubble, 0)  # nothing was done

    def test_goods_go_first_so_a_fire_does_not_hide_the_removal(self):
        with FakeGame() as game:
            village = build(game)
            answer = self.run_village(game, 50, 50, 0, "fire")
            game.lua.eval(BURN_OUT)(village)
            self.assertEqual(answer.goods_removed, 39)  # computed from the full stock before the fire


class CommandTests(unittest.TestCase):
    def test_commands_through_the_mod_HarnessActions(self):
        with FakeGame() as game:
            build(game)
            game.load_mod("HarnessActions")
            game.advance(1)
            census = run_command(game, "sack_census")["census"]
            self.assertEqual(census["buildings"]["standing"], 4)
            answer = run_command(game, "sack_village", buildings_pct=50, stock_pct=50, people_pct=40, method="collapse")
            self.assertTrue(answer["ok"], answer)
            self.assertEqual(answer["after"]["buildings"]["rubble"], 2)
            self.assertEqual(answer["after"]["people"]["families"], 3)

    def test_bad_input_through_the_command_channel(self):
        with FakeGame() as game:
            build(game)
            game.load_mod("HarnessActions")
            game.advance(1)
            self.assertIn("must be 0 to 100", run_command(game, "sack_village", buildings_pct=200, stock_pct=0, people_pct=0)["error"])
            self.assertIn("method must be", run_command(game, "sack_buildings", count=1, method="bomb")["error"])
            self.assertIn("good needs amount", run_command(game, "sack_goods", good=15)["error"])


class LootLedgerTests(unittest.TestCase):
    def setUp(self):
        self.game_context = FakeGame()
        self.game = self.game_context.__enter__()
        game = self.game
        game.obj("PawnCPP", isMainPlayer=False, isBandit=True, isAI=True, commandedSquads=game.array([game.struct(Value=5)]))
        self.units = [game.obj("SMUnit", dead=False, assignedSquadID=game.struct(Value=5), currentUnitRole=5, ItemsLooted=loot,
                               realPos=game.struct(X=100.0 * index + 0.5, Y=-20.0, Z=3.0)) for index, loot in enumerate((4, 0, 7))]
        for unit in self.units:
            game.method(unit, "just_die", game.lua.eval("function(self) self.dead = true end"))
        self.given = []
        cheat = game.obj("MLCheatManager")
        game.method(cheat, "GiveItemByID", lambda _self, kind, amount: self.given.append((kind, amount)))
        game.load_mod("HarnessActions")
        game.advance(1)

    def tearDown(self):
        self.game_context.__exit__(None, None, None)

    def test_a_pile_for_each_dead_looter_at_its_place(self):
        answer = run_command(self.game, "drop_loot", side="bandit", count=5, good=17)
        self.assertEqual(answer["killed"], 2)  # the unit with no loot is left alone
        self.assertEqual([(p["amount"], p["x"], p["y"], p["good"]) for p in answer["piles"]], [(4, 0, -20, 17), (7, 200, -20, 17)])
        self.assertEqual([unit.dead for unit in self.units], [True, False, True])
        self.assertEqual(run_command(self.game, "loot_piles")["piles"], answer["piles"])

    def test_recover_adds_the_goods_once(self):
        run_command(self.game, "drop_loot", side="bandit", count=2, good=17)
        answer = run_command(self.game, "recover_loot", pile=2)
        self.assertEqual((answer["ok"], answer["recovered"]["amount"]), (True, 7))
        self.assertEqual(self.given, [(17, 7)])
        self.assertIn("no pile with id 2", run_command(self.game, "recover_loot", pile=2)["error"])
        self.assertEqual([p["id"] for p in run_command(self.game, "loot_piles")["piles"]], [1])

    def test_bad_input_is_refused(self):
        self.assertIn("side must be", run_command(self.game, "drop_loot", side="king", count=1, good=17)["error"])
        self.assertIn("count must be", run_command(self.game, "drop_loot", side="bandit", count=999, good=17)["error"])
        self.assertIn("good must be", run_command(self.game, "drop_loot", side="bandit", count=1)["error"])
        self.assertEqual([unit.dead for unit in self.units], [False, False, False])


class SourceTests(unittest.TestCase):
    def test_no_eval_in_the_new_lua_files(self):
        for name in ("HarnessSack/HarnessSack.lua", "HarnessLoot/HarnessLoot.lua"):
            text = (REPO / "mod" / "shared" / name).read_text(encoding="utf-8")
            self.assertIsNone(FORBIDDEN.search(text), name)

    def test_no_save_function_is_called(self):
        for name in ("HarnessSack/HarnessSack.lua", "HarnessLoot/HarnessLoot.lua"):
            text = (REPO / "mod" / "shared" / name).read_text(encoding="utf-8")
            for banned in ("requestSaveFile", "SaveToDiskWithThumbnail", "SaveGameToSlot", "RequestMenuSave", "Autosave"):
                self.assertNotIn(banned, text, name)


if __name__ == "__main__":
    unittest.main()
