-- HarnessRaids: raid and unit commands for the harness (spec 10, spikes S1, S2, S5 and S10).
-- Each function takes a request table (numbers and words, already checked) and returns a result table.
-- Rules: no eval, no save function, only the game calls listed here. Call only on the game thread.

local units = require("HarnessUnits")

local M = {}

M.MAX_SQUADS = 20       -- one spawn call never asks for more squads than this
M.MAX_KILLS = 400       -- one kill call never touches more units than this
M.SIDES = { player = true, ai = true, bandit = true, civil = true }

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function read(fn)
    local ok, value = pcall(fn)
    if ok then return value end
    return nil
end

local function textOf(value)
    if type(value) == "string" then return value end
    return read(function() return value:ToString() end)
end

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if isValid(found) then return found end
    return nil
end

local function namesOf(array)
    local out = {}
    local count = read(function() return array:GetArrayNum() end) or 0
    for i = 1, count do out[#out + 1] = textOf(read(function() return array[i] end)) end
    return out
end

---------------------------------------------------------------------------------------------
-- Raid state (read only)
---------------------------------------------------------------------------------------------

local function readTimer(engineObject)
    local calendar = read(function() return engineObject.TemporalComponent end)
    if not isValid(calendar) then return nil end
    local out = {}
    for _, name in ipairs({ "daysUntilNextRaid", "daysSinceLastRaid", "lastBanditCampSpawnedDay", "day", "daysTotal", "Year", "Season" }) do
        out[name] = read(function() return calendar[name] end)
    end
    return out
end

-- The raid part of the game setup. Only four byte fields are read: the setup struct also holds a soft object.
local function readSetup()
    local instance = FindFirstOf("MLGameInstance")
    if not isValid(instance) then return nil end
    local out = {}
    for _, name in ipairs({ "yearsUntilFirstRaid", "raidingFrequency", "maxBanditCamps", "initialBanditCamps", "AI_aggressiveness" }) do
        out[name] = read(function() return instance.gameSetup.currentGameSetup[name] end)
    end
    return out
end

local function readRaidIds()
    local settings = StaticFindObject("/Script/ManorLords.Default__RaidSettings")
    if not isValid(settings) then return nil end
    return { default = namesOf(settings.defaultRaidIDs), elite = namesOf(settings.eliteRaidIDs) }
end

-- Sizes of the lists where the game could announce a raid. Only counts are read (the elements may hold soft objects).
local function readAnnouncements(engineObject)
    local player = read(function() return engineObject.playerRef end)
    if not isValid(player) then return nil end
    local out = {}
    for _, name in ipairs({ "InBox", "outbox", "quests", "log" }) do
        out[name] = read(function() return player[name]:GetArrayNum() end)
    end
    return out
end

function M.raid_state()
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    return { ok = true, timer = readTimer(engineObject), setup = readSetup(), raid_ids = read(readRaidIds), lists = readAnnouncements(engineObject) }
end

---------------------------------------------------------------------------------------------
-- Spawn
---------------------------------------------------------------------------------------------

local function playerLocation(engineObject)
    local player = read(function() return engineObject.playerRef end)
    local at = isValid(player) and read(function() return player:K2_GetActorLocation() end)
    if not at then return nil end
    return { X = at.X, Y = at.Y, Z = at.Z }
end

-- The centre of the new force: the request x, y, z, or the position of the player pawn.
local function centerOf(request, engineObject)
    if request.x and request.y then return { X = request.x, Y = request.y, Z = request.z or 0 } end
    return playerLocation(engineObject)
end

local function counts() return units.counts() end

-- Run one spawn call and report the unit counts before and after.
local function measuredSpawn(label, call)
    local before = counts()
    local ok, err = pcall(call)
    if not ok then return { ok = false, error = label .. ": " .. tostring(err), before = before } end
    return { ok = true, call = label, before = before, after = counts() }
end

function M.spawn_raiders(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local squads = request.squads or 1
    if squads < 1 or squads > M.MAX_SQUADS then return { ok = false, error = "squads must be 1 to " .. M.MAX_SQUADS } end
    local center = centerOf(request, engineObject)
    if not center then return { ok = false, error = "no centre: give x and y, or load a player pawn" } end
    local result = measuredSpawn("spawnRaiders", function() engineObject:spawnRaiders(squads, center) end)
    result.center = center
    return result
end

function M.spawn_elite_raiders(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local center = centerOf(request, engineObject)
    if not center then return { ok = false, error = "no centre: give x and y, or load a player pawn" } end
    local result = measuredSpawn("spawnEliteRaiders", function() engineObject:spawnEliteRaiders(center) end)
    result.center = center
    return result
end

function M.spawn_bandit_camp()
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    return measuredSpawn("spawnBanditCamp", function() engineObject:spawnBanditCamp() end)
end

---------------------------------------------------------------------------------------------
-- Units
---------------------------------------------------------------------------------------------

-- request.trace = 1 logs every step before it runs. Use it to find a read that ends the game.
function M.units_census(request)
    local has_log, log = pcall(require, "HarnessLog") -- optional: a player release has no HarnessLog
    if request.trace == 1 and has_log then
        units.trace = function(text) log.info("HarnessUnits", text) end
    end
    local ok, answer = pcall(units.census, { sample = request.sample or 0 })
    if units.trace then units.trace("census returned") end
    units.trace = nil
    if not ok then return { ok = false, error = tostring(answer) } end
    return { ok = true, census = answer }
end

local function checkedSide(request)
    local side = request.side or "bandit"
    if not M.SIDES[side] then return nil, "side must be player, ai, bandit or civil" end
    return side
end

local function checkedCount(request)
    local count = request.count or 1
    if count < 1 or count > M.MAX_KILLS then return nil, "count must be 1 to " .. M.MAX_KILLS end
    return count
end

-- Number of actors by class name. Used to find what a death creates (for example a pile of goods).
function M.actor_class_counts()
    local counts = {}
    for _, actor in ipairs(FindAllOf("Actor") or {}) do
        local name = isValid(actor) and read(function() return actor:GetClass():GetFName():ToString() end) or "?"
        counts[name] = (counts[name] or 0) + 1
    end
    return counts
end

-- Only the classes whose count differs, as "name = {before, after}".
local function changedClasses(before, after)
    local out = {}
    for name, n in pairs(after) do
        if (before[name] or 0) ~= n then out[name] = { before[name] or 0, n } end
    end
    for name, n in pairs(before) do
        if after[name] == nil then out[name] = { n, 0 } end
    end
    return out
end

-- What a unit carries, read before it dies.
local function describeVictim(unit)
    local at = read(function() return unit.realPos end)
    return { loot = read(function() return unit.ItemsLooted end), inventory = read(function() return unit.Inventory:GetArrayNum() end),
             x = at and read(function() return math.floor(at.X) end), y = at and read(function() return math.floor(at.Y) end) }
end

-- Kill units of one side with SMUnit:just_die. request.with_loot = 1: only units that carry loot.
-- request.actors = 1: also report the actor classes whose count changed (finds objects that a death creates).
function M.kill_units(request)
    local side, sideProblem = checkedSide(request)
    if not side then return { ok = false, error = sideProblem } end
    local count, countProblem = checkedCount(request)
    if not count then return { ok = false, error = countProblem } end
    local victims = units.unitsOfSide(side, count, request.with_loot == 1)
    local before, loot, details = counts(), 0, {}
    local actorsBefore = request.actors == 1 and M.actor_class_counts() or nil
    for _, unit in ipairs(victims) do
        local info = describeVictim(unit)
        loot = loot + (info.loot or 0)
        if #details < 5 then details[#details + 1] = info end
        local ok, err = pcall(function() unit:just_die() end)
        if not ok then return { ok = false, error = "just_die: " .. tostring(err), killed = 0 } end
    end
    local result = { ok = true, killed = #victims, loot_carried = loot, victims = details, before = before, after = counts() }
    if actorsBefore then result.actor_changes = changedClasses(actorsBefore, M.actor_class_counts()) end
    return result
end

-- Write ItemsLooted on units of one side. Reports what was read back.
function M.set_unit_loot(request)
    local side, sideProblem = checkedSide(request)
    if not side then return { ok = false, error = sideProblem } end
    local count, countProblem = checkedCount(request)
    if not count then return { ok = false, error = countProblem } end
    local amount, changed = request.amount or 0, 0
    for _, unit in ipairs(units.unitsOfSide(side, count)) do
        local ok = pcall(function() unit.ItemsLooted = amount end)
        if ok and read(function() return unit.ItemsLooted end) == amount then changed = changed + 1 end
    end
    return { ok = true, wanted = count, changed = changed, amount = amount }
end

return M
