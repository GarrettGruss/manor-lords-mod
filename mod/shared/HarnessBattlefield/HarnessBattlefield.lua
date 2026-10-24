-- HarnessBattlefield: steer the battle place of a challenge (spec 10, spike for issue #99).
-- Why: initChallenge picks one battlefield_BP_C actor as the battle site. If every such actor stands at one anchor
-- at that moment, the challenge keeps the anchor. The actors go back to their places after a short delay.
-- The idea comes from a public mod (see openspec/changes/archive/2026-10-15-legacy-13-mod-inspection/implementation-notes/better-battlefield.md).
-- This code is our own.
--
-- Rules: call only on the game thread. No save function. Every input is checked before it is used.

local lords = require("HarnessLords")
local core = require("ManorCore")

local M = {}

M.BATTLEFIELD_CLASS = "battlefield_BP_C"
M.DEFAULT_DELAY_MS = 500
M.MAX_DELAY_MS = 30000
M.MAX_COORD = 1000000

local read, isValid, shortName = core.read, core.isValid, core.shortName

-- State of the last anchor. It lives in this Lua state only.
local pending = nil
local lastRestore = nil

local function xyz(at)
    if not at then return nil end
    return { X = at.X, Y = at.Y, Z = at.Z or 0 }
end

local function location(actor)
    return xyz(read(function() return actor:K2_GetActorLocation() end))
end

local function battlefields()
    local out = {}
    for _, actor in ipairs(FindAllOf(M.BATTLEFIELD_CLASS) or {}) do
        if isValid(actor) and not actor:GetFullName():find("Default__", 1, true) then out[#out + 1] = actor end
    end
    return out
end

local function round(at)
    if not at then return nil end
    return { x = math.floor(at.X + 0.5), y = math.floor(at.Y + 0.5), z = math.floor((at.Z or 0) + 0.5) }
end

-- The manor if the region has one, else the village centre, else the region actor.
local function regionAnchor(region)
    local manor = read(function() return region.manor end)
    if isValid(manor) then
        local at = location(manor)
        if at then return at, "manor" end
    end
    local centre = xyz(read(function() return region:getSettledRegionCenter() end))
    if centre and (centre.X ~= 0 or centre.Y ~= 0) then return centre, "village_centre" end
    local at = location(region)
    if at then return at, "region_actor" end
    return nil
end

-- The raid anchor: the manor of the player home region, else the average location of its buildings, else regionAnchor.
-- It never reads the camera (the current region of the pawn).
local function homeAnchor()
    local region, problem = core.player_region()
    if not region then return nil, problem end
    local manor = read(function() return region.manor end)
    if isValid(manor) then
        local at = location(manor)
        if at then return at, "manor" end
    end
    local sx, sy, sz, n = 0, 0, 0, 0
    for _, building in ipairs(core.listOf(read(function() return region:GetBuildings() end))) do
        local at = isValid(building) and location(building) or nil
        if at then sx, sy, sz, n = sx + at.X, sy + at.Y, sz + at.Z, n + 1 end
    end
    if n > 0 then return { X = sx / n, Y = sy / n, Z = sz / n }, "buildings_average" end
    local at, kind = regionAnchor(region)
    if at then return at, kind end
    return nil, "no anchor position in the home region"
end

local function targetRegion(request)
    local engineObject = FindFirstOf("RTSMultiEngineCPP")
    if request.region then
        for _, region in ipairs(core.listOf(read(function() return engineObject.regions end))) do
            if shortName(region) == request.region then return region end
        end
        return nil, "no region named " .. tostring(request.region)
    end
    local target = lords.pawn_by_number(request.target or 0)
    local region = target and read(function() return target.currentRegion end)
    if not isValid(region) then return nil, "the target has no current region" end
    return region
end

local function resolveAnchor(request)
    if request.x ~= nil or request.y ~= nil then
        if type(request.x) ~= "number" or type(request.y) ~= "number" then return nil, "x and y must both be numbers" end
        if math.abs(request.x) > M.MAX_COORD or math.abs(request.y) > M.MAX_COORD then return nil, "x and y are out of range" end
        return { X = request.x, Y = request.y, Z = request.z or 0 }, "xy"
    end
    if request.home then return homeAnchor() end
    local region, problem = targetRegion(request)
    if not region then return nil, problem end
    local at, kind = regionAnchor(region)
    if not at then return nil, "no anchor position in region " .. tostring(shortName(region)) end
    return at, kind
end

local function move(actor, at)
    return pcall(function() actor:K2_SetActorLocation({ X = at.X, Y = at.Y, Z = at.Z }, false, {}, true) end)
end

local function restore(saved)
    local failed = 0
    for _, entry in ipairs(saved) do
        if isValid(entry.actor) then
            if not move(entry.actor, entry.at) then failed = failed + 1 end
        else
            failed = failed + 1
        end
    end
    lastRestore = { restored = #saved - failed, failed = failed }
    pending = nil
end

local function moveAll(actors, at)
    local saved = {}
    for _, actor in ipairs(actors) do
        local original = location(actor)
        if original and move(actor, at) then saved[#saved + 1] = { actor = actor, at = original } end
    end
    return saved
end

local function checkedDelay(request)
    local delay = request.delay_ms or M.DEFAULT_DELAY_MS
    if type(delay) ~= "number" or delay < 0 or delay > M.MAX_DELAY_MS then
        return nil, "delay_ms must be a number from 0 to " .. M.MAX_DELAY_MS
    end
    return delay
end

-- Move all battlefield actors to the anchor, optionally start a challenge (lord, target) in the same step,
-- and put the actors back after delay_ms. The anchor is x,y or the manor of the region (region name, or the target's region).
-- With home = true the anchor is the player manor or, without one, the average of the home-region buildings.
function M.battlefield_anchor(request)
    if pending then return { ok = false, error = "an anchor is still active; wait for the restore" } end
    local delay, badDelay = checkedDelay(request)
    if not delay then return { ok = false, error = badDelay } end
    local at, kind = resolveAnchor(request)
    if not at then return { ok = false, error = kind } end
    local actors = battlefields()
    if #actors == 0 then return { ok = false, error = "no " .. M.BATTLEFIELD_CLASS .. " actor found" } end
    local saved = moveAll(actors, at)
    if #saved == 0 then return { ok = false, error = "no battlefield actor could be moved" } end
    pending = saved
    local answer = { ok = true, anchor = round(at), anchor_kind = kind, found = #actors, moved = #saved, delay_ms = delay }
    if request.lord ~= nil then
        answer.challenge = lords.lord_challenge({ lord = request.lord, target = request.target or 0 })
    end
    ExecuteWithDelay(delay, function() core.log.try("HarnessBattlefield", restore, saved) end)
    return answer
end

-- Read only: where the battlefield actors are now, the result of the last restore, and the anchor that
-- battlefield_anchor would use for the same request (x,y, region, or target; "anchor" is nil when none can be found).
function M.battlefield_state(request)
    local rows = {}
    for _, actor in ipairs(battlefields()) do rows[#rows + 1] = round(location(actor)) end
    local at, kind = resolveAnchor(request or {})
    return { ok = true, count = #rows, positions = rows, anchor_active = pending ~= nil, last_restore = lastRestore,
             would_anchor = round(at), would_anchor_kind = at and kind or nil, would_anchor_problem = (not at) and kind or nil }
end

return M
