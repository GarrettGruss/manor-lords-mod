-- HarnessTelemetry: samples game state and appends one JSON line per sample to telemetry.jsonl.
-- Spec: openspec/changes/archive/2026-10-15-legacy-04-telemetry-and-assertions/README.md
--
-- Settings (environment variables):
--   HARNESS_RUN_DIR                 folder for telemetry.jsonl (same default as HarnessLog)
--   HARNESS_TELEMETRY_INTERVAL_S    wall seconds between samples. Default 5. 0 turns sampling off.
--
-- Rules:
--   Game objects are touched only on the game thread.
--   Every field is read with a guard. A field that cannot be read is null, and it is counted in "errors".
--   One bad field never stops a sample, and one bad sample never stops sampling.
--   The sampler uses wall time, so it also works while the game is paused.
--
-- Other mods can add metrics: HarnessTelemetry.register("name", function() return value end).
-- The function runs on the game thread, and its result goes into the sample under "custom".

local log = require("HarnessLog")
local loop = require("HarnessLoop")
local json = require("HarnessJson")

local M = {}

local TAG = "Telemetry"
local DEFAULT_INTERVAL_S = 5

local FILE_NAME = "telemetry.jsonl"
local custom = {}          -- name -> function
local lastClock = nil      -- game clock of the previous sample, to tell if the game is paused
local sampleCount = 0
local file = nil
local started = false

---------------------------------------------------------------------------------------------
-- Small helpers
---------------------------------------------------------------------------------------------

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

-- Turn an FString, FName or Lua string into a Lua string. Returns nil if that is not possible.
local function asText(value)
    if type(value) == "string" then return value end
    if value == nil then return nil end
    local ok, text = pcall(function() return value:ToString() end)
    if ok then return text end
    return nil
end

-- A TArray element can be a wrapper that needs :get(). Unwrap it only if that works.
local function unwrap(element)
    local ok, inner = pcall(function() return element:get() end)
    if ok and inner ~= nil then return inner end
    return element
end

-- Read one value with a guard. A failed read is counted in `errors` and gives json.null (an explicit null in the file).
-- Only numbers, booleans and strings are stored. Anything else (an object, nil) counts as a failed read.
local function guarded(errors, label, fn)
    local ok, value = pcall(fn)
    if ok and (type(value) == "number" or type(value) == "boolean" or type(value) == "string") then return value end
    errors[#errors + 1] = label
    return json.null
end

---------------------------------------------------------------------------------------------
-- Sampling
---------------------------------------------------------------------------------------------

local function readRegion(region, errors, index)
    local prefix = "region" .. index .. "."
    return {
        name = guarded(errors, prefix .. "name", function() return asText(region.regionName) end),
        settled = guarded(errors, prefix .. "settled", function() return region.isSettled end),
        approval = guarded(errors, prefix .. "approval", function() return region.Approval end),
        publicOrder = guarded(errors, prefix .. "publicOrder", function() return region.publicOrder end),
        wealth = guarded(errors, prefix .. "wealth", function() return region.regionalWealth end),
        food = guarded(errors, prefix .. "food", function() return region.supplies_food end),
        population = guarded(errors, prefix .. "population", function() return region:getNumTotalPopulation() end),
        homeless = guarded(errors, prefix .. "homeless", function() return region:getNumHomelessFamilies() end),
    }
end

local function readRegions(engine, errors)
    local list = {}
    local okRegions, regions = pcall(function() return engine.regions end)
    if not okRegions or regions == nil then
        errors[#errors + 1] = "regions"
        return list
    end
    local okCount, count = pcall(function() return regions:GetArrayNum() end)
    if not okCount then
        errors[#errors + 1] = "regions.count"
        return list
    end
    for i = 1, count do
        local region = unwrap(regions[i])
        if isValid(region) then list[#list + 1] = readRegion(region, errors, i) end
    end
    return list
end

local function readDate(engine, errors)
    local okTc, tc = pcall(function() return engine.TemporalComponent end)
    if not okTc or not isValid(tc) then
        errors[#errors + 1] = "date"
        return json.object({})
    end
    return {
        day = guarded(errors, "date.day", function() return tc.day end),
        month = guarded(errors, "date.month", function() return tc.month end),
        year = guarded(errors, "date.year", function() return tc.Year end),
        season = guarded(errors, "date.season", function() return tc.Season end),
    }
end

local function readPlayer(engine, errors)
    local okPlayer, player = pcall(function() return engine.playerRef end)
    if not okPlayer or not isValid(player) then
        errors[#errors + 1] = "player"
        return json.object({})
    end
    return {
        silver = guarded(errors, "player.silver", function() return player.silver end),
        influence = guarded(errors, "player.influence", function() return player.influence end),
        kingsFavour = guarded(errors, "player.kingsFavour", function() return player.kingsFavour end),
    }
end

local function readCustom(errors)
    local values = json.object({})
    for name, fn in pairs(custom) do
        local ok, value = pcall(fn)
        if ok then
            values[name] = value
        else
            errors[#errors + 1] = "custom." .. name
        end
    end
    return values
end

-- Build one sample, or return nil when the game is not in a game map (the main menu has no engine actor).
function M.sample()
    local okFind, engine = pcall(FindFirstOf, "RTSMultiEngineCPP")
    if not okFind or not isValid(engine) then return nil end

    local errors = {}
    local clock = guarded(errors, "clock", function() return engine:getGameTimeAdjusted() end)
    -- The clock tells if the game is paused: it did not move since the last sample.
    local paused = json.null
    local clockKnown = type(clock) == "number"
    if clockKnown and lastClock ~= nil then paused = math.abs(clock - lastClock) < 0.001 end
    if clockKnown then lastClock = clock end

    sampleCount = sampleCount + 1
    return {
        n = sampleCount,
        t = os.time(),
        clock = clock,
        paused = paused,
        date = readDate(engine, errors),
        player = readPlayer(engine, errors),
        regions = readRegions(engine, errors),
        custom = readCustom(errors),
        errors = errors,
    }
end

---------------------------------------------------------------------------------------------
-- Output
---------------------------------------------------------------------------------------------

local function openFile()
    if file then return file end
    local path = log.dir() .. "/" .. FILE_NAME
    local f, err = io.open(path, "a")
    if not f then
        log.error(TAG, "cannot open " .. path .. ": " .. tostring(err))
        return nil
    end
    file = f
    return f
end

function M.writeSample(sample)
    local f = openFile()
    if not f then return false end
    local okEncode, line = pcall(json.encode, sample)
    if not okEncode then
        log.error(TAG, "cannot encode sample " .. tostring(sample.n) .. ": " .. tostring(line))
        return false
    end
    f:write(line .. "\n")
    f:flush()
    return true
end

---------------------------------------------------------------------------------------------
-- Public API
---------------------------------------------------------------------------------------------

-- Add a metric to every sample. `fn` runs on the game thread. Its result is stored under custom[name].
function M.register(name, fn)
    if type(name) ~= "string" or name == "" then error("register needs a non-empty string name") end
    if type(fn) ~= "function" then error("register needs a function") end
    custom[name] = fn
end

function M.intervalSeconds()
    local text = os.getenv and os.getenv("HARNESS_TELEMETRY_INTERVAL_S")
    if text == nil or text == "" then return DEFAULT_INTERVAL_S end
    local value = tonumber(text)
    if value == nil or value < 0 then
        log.warn(TAG, "bad HARNESS_TELEMETRY_INTERVAL_S '" .. text .. "'; using " .. DEFAULT_INTERVAL_S)
        return DEFAULT_INTERVAL_S
    end
    return value
end

-- Start the sampler. Safe to call twice: the second call does nothing.
function M.start()
    if started then return false end
    local interval = M.intervalSeconds()
    if interval == 0 then
        log.info(TAG, "off (HARNESS_TELEMETRY_INTERVAL_S is 0)")
        return false
    end
    started = true
    log.say(TAG, "sampling every " .. interval .. " s into " .. log.dir() .. "/" .. FILE_NAME)
    loop.every(math.floor(interval * 1000), function()
        ExecuteInGameThread(function()
            local ok, err = pcall(function()
                local sample = M.sample()
                if sample ~= nil then M.writeSample(sample) end
            end)
            if not ok then log.error(TAG, "sample failed: " .. tostring(err)) end
        end)
        return false
    end)
    return true
end

return M
