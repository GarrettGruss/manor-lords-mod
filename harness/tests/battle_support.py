"""A fake world for the battle tests (spec 10, spikes S7, P5, C1, C2): unit templates, spawnArmy, mercenaries, a simple fight rule.

The rules copy what the real game did (spike notes spike-S7.md, spike-P5.md):
  - spawnArmy(position, template names, owner pawn, 0, 0) makes one squad for each name. The size is the field maxSize of the row.
    The squad ids are returned. The owner pawn gives the side (player or bandit).
  - hireMercs(company, pawn) does not check the cost, takes it from the silver, removes the offer and makes one squad for each unit name.
  - A dead unit leaves the unit list (here: the fake object becomes invalid).
The fight rule is only a stand-in for the game: each `tick` kills a fixed number of units on both sides and raises the experience of the
surviving player units. It tests the logic of the Lua module, the actions and the scenarios. It does NOT prove how the real game fights.
"""

from types import SimpleNamespace

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import sleep_in
from runlib.actions import Actions
from runlib.commands import CommandChannel
from runlib.expectations import Expectations
from runlib.waiting import WaitTimeout

BUILD_WORLD = """
function(fg, options)
    local world = { squads = {}, records = {}, nextSquad = 8, nextUid = 100, rows = {}, rowNames = {}, spawnCalls = 0 }
    local function row(name, maxSize, cost)
        world.rows[name] = fg.object("UnitTemplateRow", { cost = cost or 0.0, maxSize = maxSize, minMeleeTraining = 0.0, minArcheryTraining = 0.0,
                                                          minHouseLv = 1, combatExperience = 5.0, Name = name })
        world.rowNames[#world.rowNames + 1] = name
    end
    row("spearMilitia", 32); row("militiaFoot", 32); row("bowMilitia", 32)
    world.rowNames[#world.rowNames + 1] = "--------------------------"
    row("retinue_tier3", 36); row("mercenary_infantry", 36); row("Mercenary_Archers", 36); row("Brigands", 18); row("mercenary_spearmen", 36)
    for i = 1, 15 do row("filler_" .. i, 20) end   -- the real table has 25 rows without separators
    local dataTable = fg.object("DataTable", {}, "/Game/NotStronghold/Data/DT_UnitTemplates.DT_UnitTemplates")
    fg.set_method(dataTable, "GetRowNames", function() return world.rowNames end)
    fg.set_method(dataTable, "GetRowStruct", function() return fg.object("ScriptStruct", {}, "/Script/ManorLords.UnitTemplate") end)
    fg.set_method(dataTable, "FindRow", function(self, name) return world.rows[name] end)

    local player = fg.object("PawnCPP", { isMainPlayer = true, isBandit = false, isAI = false, silver = options.silver or 0,
                                          commandedSquads = fg.array({}, { wrap = false }) }, "/Game/Fake/Player")
    fg.set_method(player, "K2_GetActorLocation", function() return { X = 1000.0, Y = 2000.0, Z = 30.0 } end)
    local bandit = fg.object("PawnCPP", { isMainPlayer = false, isBandit = true, isAI = true, commandedSquads = fg.array({}, { wrap = false }) }, "/Game/Fake/Bandit")
    world.player, world.bandit = player, bandit

    local function newSquad(owner, side, name)
        local id = world.nextSquad
        world.nextSquad = id + 1
        world.squads[id] = { side = side, template = name }
        fg.array_add(owner.commandedSquads, { Value = id })
        for _ = 1, world.rows[name].maxSize do
            world.nextUid = world.nextUid + 1
            local unit = fg.object("SMUnit", { dead = false, assignedSquadID = { Value = id }, combatExperience = 0.0, UniqueID = world.nextUid,
                                               currentUnitRole = 5, ItemsLooted = 0, morale = 1.0 })
            local record = { unit = unit, squad = id, alive = true }
            fg.set_method(unit, "just_die", function(self)
                record.alive = false
                fg.invalidate(self)
            end)
            world.records[#world.records + 1] = record
        end
        return { Value = id }
    end

    local offers = {}
    local function offer(name, cost, arrives, units) offers[#offers + 1] = { Name = name, cost = cost, arrivesIn = arrives, units = fg.array(units, { wrap = false }) } end
    if not options.no_offers then
        offer("greencaps", 90, 11, { "mercenary_infantry", "mercenary_infantry", "Mercenary_Archers" })
        offer("battle_brothers", 50, 34, { "mercenary_infantry", "Brigands" })
    end
    world.offers = offers
    local hired = {}
    local engine = fg.object("RTSMultiEngineCPP", { playerRef = player, availableMercs = fg.array(offers, { wrap = false }),
                                                    hiredMercs = { ForEach = function(self, fn) for k, v in ipairs(hired) do fn(k, v) end end } })
    fg.set_method(engine, "spawnArmy", function(self, position, names, owner, companyId, days)
        world.spawnCalls = world.spawnCalls + 1
        if options.spawn_fails then error("spawnArmy failed") end
        local side = owner.isBandit and "bandit" or "player"
        local ids = {}
        for _, name in ipairs(names) do ids[#ids + 1] = newSquad(owner, side, name.fname) end
        return ids
    end)
    fg.set_method(engine, "hireMercs", function(self, company, pawn)
        pawn.silver = pawn.silver - company.cost - (options.overcharge or 0)   -- the game does not check it (spike P5)
        local ids = {}
        for i = 1, company.units:GetArrayNum() do ids[#ids + 1] = newSquad(pawn, "player", company.units[i]) end
        for i, entry in ipairs(offers) do if entry == company then table.remove(offers, i); break end end
        hired[#hired + 1] = company.Name
        return ids
    end)

    local function livingOf(side)
        local out = {}
        for _, record in ipairs(world.records) do
            if record.alive and world.squads[record.squad].side == side then out[#out + 1] = record end
        end
        return out
    end
    -- One step of the fake fight. Returns false when there is nothing to fight.
    function world.tick(killPlayers, killBandits, experience)
        local players, bandits = livingOf("player"), livingOf("bandit")
        if #players == 0 or #bandits == 0 then return false end
        for i = 1, math.min(killBandits, #bandits) do bandits[i].unit:just_die() end
        for i = 1, math.min(killPlayers, #players) do players[#players - i + 1].unit:just_die() end
        for _, record in ipairs(livingOf("player")) do record.unit.combatExperience = record.unit.combatExperience + experience end
        return true
    end
    function world.silver() return player.silver end
    function world.set_silver(value) player.silver = value end
    function world.living(side) return #livingOf(side) end
    return world
end
"""


class BattleWorld:
    """The fake world and the game that holds it."""

    def __init__(self, **options):
        self.game = FakeGame()
        self.game.start()
        self.game.exec("FName = function(text) return { fname = text } end")
        self.world = self.game.lua.eval(BUILD_WORLD)(self.game.fg, self.game.lua.table_from(options))
        self.game.load_mod("HarnessActions")
        self.game.advance(1)

    def close(self):
        self.game.close()

    def tick(self, kill_players=3, kill_bandits=4, experience=0.4):
        return self.world.tick(kill_players, kill_bandits, experience)


class FakeBattleBridge:
    """The bridge calls that the battle scenarios make: the silver of the player pawn."""

    def __init__(self, world):
        self.world = world

    def engine_path(self):
        return "engine"

    def player_path(self):
        return "player"

    def read_property(self, ref, name):
        if name == "silver":
            return self.world.silver()
        raise KeyError(name)

    def write_property(self, ref, name, value):
        if name != "silver":
            raise KeyError(name)
        self.world.set_silver(value)


class FakeBattleTime:
    """Time passes in `run_until`: each poll that is not true ends with one fight step while the game runs."""

    def __init__(self):
        self.running = False
        self.calls = []

    def set_speed(self, speed):
        self.running = True
        self.calls.append(("set_speed", speed))

    def pause(self):
        self.running = False
        self.calls.append(("pause",))

    def run_game_days(self, days, speed=1):
        self.calls.append(("run_game_days", days, speed))

    def run_game_seconds(self, seconds, speed=1):
        self.calls.append(("run_game_seconds", seconds, speed))


class BattleContext:
    """The parts of a scenario context that the battle scenarios use."""

    def __init__(self, world: BattleWorld, variant=None, kills=(3, 4, 0.4), max_polls=300):
        game = world.game
        sleep = sleep_in(game)
        self.world = world
        self.expect = Expectations(sleep=sleep, monotonic=game.now)
        self.notes = []
        self.metrics = {}
        self.logged = []
        self.log = SimpleNamespace(info=self.logged.append)
        self.bridge = FakeBattleBridge(world.world)
        self.commands = CommandChannel(game.run_dir / "commands", sleep=sleep, monotonic=game.now)
        self.actions = Actions(self.bridge, self.expect, self.notes, commands=self.commands)
        self.time = FakeBattleTime()
        self.popups = lambda: None
        self._variant = dict(variant or {})
        self._kills = kills
        self._max_polls = max_polls

    def variant_option(self, name, default):
        return self._variant.get(name, default)

    def metric(self, name, value):
        self.metrics[name] = value

    def run_until(self, predicate, timeout_s, **options):
        for polls in range(1, self._max_polls + 1):
            if predicate():
                return SimpleNamespace(value=True, wall_s=float(polls), game_s=None, polls=polls)
            if self.time.running:
                self.world.tick(*self._kills)
        raise WaitTimeout(f"timeout: {options.get('what', 'the condition')} was not true")

    def result(self):
        result = self.expect.result()
        result["notes"] = list(self.notes)
        return result
