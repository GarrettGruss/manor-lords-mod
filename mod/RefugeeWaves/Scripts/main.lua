-- RefugeeWaves: a random event that sends homeless refugee families to the player village (spec 15, issue #51).
-- Design (accepted by the user, 2026-10-12):
--   Trigger: each game month, a chance (CONFIG.chance_percent) when the village is big enough and no wave is active.
--   Wave: 1 to 3 calls of PawnCPP:settleRegion on the player region (HarnessLords.settle_region). The camp is near the woods
--     (forest_spot), else near the village (tent_find_spot). The game adds one family for each free home slot and puts up a tent
--     (immigration-surge.md, refugee-followups.md). The mod never houses the refugees.
--   Message: the banner of PawnCPP:playEventMessage (HarnessUi). It is logged too.
--   Pressure: the game itself. Homeless families lower approval by a one-time step (about 2 to 3 points each, in 3 game days).
--   End: the wave ends when the homeless count is back at the count from before the wave (the player built homes).
--   Bad outcome: refugees still homeless after CONFIG.homeless_days_limit game days, or approval under CONFIG.approval_floor.
--     Then a share of the wave families leaves and returns as a bandit raid (HarnessBandits.rebel_raid_rally). The game does nothing by itself.
--   Save and load: the mod keeps no state that the game cannot rebuild. A new Lua state after a load adopts the homeless families it finds
--     on its first check as the active wave (start = that day).
-- Rules: game objects are touched on the game thread only. No save function. No eval. No Region:AddNewFamily (it crashes the game).

-- This mod needs only ManorCore (a player-safe shared module). The harness command registry is optional:
-- without it the mod runs by itself and only the test commands are missing.
local core = require("ManorCore")
local log = core.log
local hasCommands, commands = pcall(require, "HarnessCommands")

local VERSION = "0.1.0"
local TAG = "RefugeeWaves"
local PREFIX = "RefugeeWaves."

-- Settings. A scenario changes them with the command RefugeeWaves.configure.
local CONFIG = {
    chance_percent = 15,        -- chance of a wave at each new game month
    min_families = 10,          -- no automatic wave in a smaller village
    families_per_extra_call = 10, -- the village size that allows one more settleRegion call
    max_calls = 3,              -- most settleRegion calls in one wave
    homeless_days_limit = 30,   -- game days the wave families may stay homeless
    approval_floor = 40,        -- approval under this value ends the patience of the refugees
    rebel_share_percent = 50,   -- share of the homeless wave families that turns into a raid
    adopt_on_start = true,      -- after a load, homeless families found at the first check are the active wave
    tick_ms = 2000,             -- real time between two checks
    seed = nil,                 -- seed of the random generator (nil: the Lua default)
}
local DAYS_PER_MONTH_FALLBACK = 30
local MAX_CALLS_LIMIT = 5

local S = { wave = nil, last_month = nil, waves_started = 0, rebellions = 0, waves_ended = 0, last_outcome = nil, adopted_checked = false }

local function read(fn)
    local ok, value = pcall(fn)
    if ok then return value end
    return nil
end

---------------------------------------------------------------------------------------------
-- Game reads
---------------------------------------------------------------------------------------------

local function currentDay()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    return read(function() return math.floor(engine.TemporalComponent.daysTotal) end)
end

-- A number that changes when a new game month starts.
local function monthKey()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local year = read(function() return engine.TemporalComponent.Year end)
    local month = read(function() return engine.TemporalComponent.month end)
    if year and month then return year * 12 + month end
    local day = currentDay()
    return day and math.floor(day / DAYS_PER_MONTH_FALLBACK) or nil
end

local function regionNumbers()
    local region, problem = core.player_region()
    if not region then return nil, problem end
    return {
        families = read(function() return region:getTotalNumFamilies() end),
        homeless = read(function() return region:getNumHomelessFamilies() end),
        approval = read(function() return region.Approval end),
        name = read(function() local n = region.regionName; return type(n) == "string" and n or n:ToString() end),
    }
end

---------------------------------------------------------------------------------------------
-- Wave start
---------------------------------------------------------------------------------------------

-- The first usable camp: near the woods, else near the village, else nil (the game uses the settled centre).
local function campSpot()
    local woods = read(function() return core.forest_spot({}) end)
    if woods and woods.ok and woods.spots and woods.spots[1] then return woods.spots[1], "woods" end
    local near = read(function() return core.tent_find_spot() end)
    if near and near.ok and near.spots and near.spots[1] then return near.spots[1], "village" end
    return nil, "centre"
end

-- How many settleRegion calls a village of this size gets, 1 to max_calls, chosen with the random generator.
local function callsFor(families)
    local allowed = math.max(1, math.floor((families or 0) / CONFIG.families_per_extra_call))
    return math.random(1, math.min(CONFIG.max_calls, allowed))
end

local function announce()
    local shown, problem = core.show_banner("Refugees have arrived", "They camp near the village. House them before winter.")
    if not shown then log.warn(TAG, "banner failed: " .. tostring(problem)) end
    log.say(TAG, "Refugees have arrived and camp near the village. House them before winter.")
end

local function settleCall(row, spot)
    local request = { target = 0, region = row.region, type = row.settlement_type or 1, supply = 0 }
    if spot then request.x, request.y, request.z = spot.x, spot.y, spot.z end
    return core.settle_region(request)
end

-- Start a wave of `calls` settleRegion calls. Returns the wave table, or nil and a message.
local function startWave(calls)
    if S.wave then return nil, "a wave is already active" end
    local before, problem = regionNumbers()
    if not before then return nil, problem end
    local row = core.region_row_by_name(before.name)
    if not row then return nil, "no region row for " .. tostring(before.name) end
    local spot, place = campSpot()
    local done = 0
    for _ = 1, calls do
        local answer = settleCall(row, spot)
        if not answer.ok then
            log.error(TAG, "settleRegion refused: " .. tostring(answer.error))
            break
        end
        done = done + 1
    end
    if done == 0 then return nil, "no settleRegion call worked" end
    local after = regionNumbers() or before
    S.wave = { start_day = currentDay(), calls = done, place = place, families_before = before.families, homeless_before = before.homeless,
               families_after = after.families, homeless_after = after.homeless, state = "active" }
    S.waves_started = S.waves_started + 1
    log.say(TAG, ("wave started: %d calls at %s, families %s -> %s, homeless %s -> %s"):format(done, place, tostring(before.families),
        tostring(after.families), tostring(before.homeless), tostring(after.homeless)))
    announce()
    return S.wave
end

---------------------------------------------------------------------------------------------
-- Wave follow-up
---------------------------------------------------------------------------------------------

local function waveHomeless(numbers)
    return math.max(0, (numbers.homeless or 0) - S.wave.homeless_before)
end

local function finishWave(outcome)
    S.wave.state = outcome
    S.last_outcome = outcome
    S.waves_ended = S.waves_ended + 1
    log.say(TAG, "wave ended: " .. outcome)
    S.wave = nil
end

local function startRebellion(numbers)
    local count = math.max(1, math.ceil(waveHomeless(numbers) * CONFIG.rebel_share_percent / 100))
    count = math.min(count, core.MAX_REBEL_FAMILIES)
    local answer = core.rebel_raid_rally({ count = count })
    if not answer.ok then
        log.error(TAG, "rebellion failed (a known gap): " .. tostring(answer.error))
        finishWave("rebellion_failed")
        return
    end
    S.rebellions = S.rebellions + 1
    log.say(TAG, ("rebellion: %d homeless wave families left and became a raid"):format(count))
    finishWave("rebelled")
end

-- One check of an active wave. Order: housed first, then the bad outcomes.
local function checkWave(numbers)
    local wave = S.wave
    if waveHomeless(numbers) == 0 then return finishWave("housed") end
    local day = currentDay()
    wave.days_homeless = day and wave.start_day and (day - wave.start_day) or 0
    if wave.days_homeless >= CONFIG.homeless_days_limit then
        log.say(TAG, "refugees stayed homeless for " .. wave.days_homeless .. " game days")
        return startRebellion(numbers)
    end
    if numbers.approval and numbers.approval < CONFIG.approval_floor then
        log.say(TAG, "approval fell to " .. tostring(numbers.approval))
        return startRebellion(numbers)
    end
end

-- After a load the mod has no memory. Homeless families that exist at the first check are the wave.
local function adoptHomeless(numbers)
    S.adopted_checked = true
    if not CONFIG.adopt_on_start or (numbers.homeless or 0) <= 0 or S.wave then return end
    S.wave = { start_day = currentDay(), calls = 0, place = "adopted", families_before = numbers.families, homeless_before = 0,
               families_after = numbers.families, homeless_after = numbers.homeless, state = "active" }
    log.say(TAG, "adopted " .. numbers.homeless .. " homeless families as the active wave")
end

local function rollWave(numbers)
    if (numbers.families or 0) < CONFIG.min_families then return end
    if math.random(1, 100) > CONFIG.chance_percent then return end
    local ok, reason = startWave(callsFor(numbers.families))
    if not ok then log.warn(TAG, "wave not started: " .. tostring(reason)) end
end

local function newMonth()
    local key = monthKey()
    if key == nil then return false end
    local changed = S.last_month ~= nil and key ~= S.last_month
    S.last_month = key
    return changed
end

-- The whole check. It runs on the game thread, every tick_ms and on the command `check`.
local function check()
    local numbers = regionNumbers()
    if not numbers then return end
    if not S.adopted_checked then adoptHomeless(numbers) end
    local monthStarted = newMonth()
    if S.wave then return checkWave(numbers) end
    if monthStarted then rollWave(numbers) end
end

---------------------------------------------------------------------------------------------
-- Commands and metrics
---------------------------------------------------------------------------------------------

local function status()
    local numbers = regionNumbers() or {}
    local wave = S.wave
    return { active = wave ~= nil, wave = wave, numbers = numbers, waves_started = S.waves_started, waves_ended = S.waves_ended,
             rebellions = S.rebellions, last_outcome = S.last_outcome, config = CONFIG }
end

local function configure(args)
    for name, value in pairs(args) do CONFIG[name] = value end
    if args.seed then math.randomseed(args.seed) end
    return { config = CONFIG }
end

local function commandStartWave(args)
    local wave, problem = startWave(args.calls or 1)
    if not wave then return nil, problem end
    return { wave = wave }
end

local function commandCheck()
    check()
    return status()
end

local function commandForget()
    S.wave, S.last_outcome = nil, nil
    return status()
end

local function integer(min, max, required) return { type = "integer", min = min, max = max, required = required } end

local COMMANDS = {
    configure = { run = configure, schema = { chance_percent = integer(0, 100), min_families = integer(0, 1000),
        families_per_extra_call = integer(1, 1000), max_calls = integer(1, MAX_CALLS_LIMIT), homeless_days_limit = integer(1, 1000),
        approval_floor = integer(0, 100), rebel_share_percent = integer(1, 100), adopt_on_start = { type = "boolean" },
        seed = integer(0, 2147483647) } },
    start_wave = { run = commandStartWave, schema = { calls = integer(1, MAX_CALLS_LIMIT) } },
    check = { run = commandCheck, schema = {} },
    status = { run = status, schema = {} },
    forget_wave = { run = commandForget, schema = {} },
}

local METRICS = {
    wave_active = function() return S.wave ~= nil end,
    waves_started = function() return S.waves_started end,
    waves_ended = function() return S.waves_ended end,
    rebellions = function() return S.rebellions end,
    last_outcome = function() return S.last_outcome end,
    wave_homeless = function() local n = regionNumbers(); return S.wave and n and waveHomeless(n) or 0 end,
}

if hasCommands then
    for name, definition in pairs(COMMANDS) do
        commands.unregister(PREFIX .. name) -- a hot reload runs this file again
        commands.register(PREFIX .. name, function(args) return definition.run(args) end, definition.schema)
    end
    for name, readValue in pairs(METRICS) do commands.metric(PREFIX .. name, readValue) end
end

LoopAsync(CONFIG.tick_ms, function()
    ExecuteInGameThread(function() log.try(TAG, check) end)
    return false
end)

log.say(TAG, "loaded version " .. VERSION)
