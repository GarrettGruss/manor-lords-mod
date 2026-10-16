-- HarnessTune: live tuning of unit stats for a human-agent session (spec 28).
-- Why: set_unit_stat (spec 25) only reaches units that a harness spawn registered. In a normal game the levies, bandits and AI lords
-- are not registered. This module finds the side of EVERY living SMUnit from its squad: the squad id is in PawnCPP.commandedSquads
-- of the owner pawn, and the pawn flags give the side (HarnessUnits.squadMap, spec 10 spike S3).
-- Sides: player, bandit, ai_lord, other (a pawn with none of the flags). A unit with no squad (villager, animal) has no side and is skipped.
-- An override is stored for a scope (a side, or one squad) and a stat field. A timer applies the overrides again, so units that spawn later get them.
-- Before the first write to a unit this module records the original value, so tune_reset can restore it.
--
-- Rules: call only on the game thread. No save function. Every input is checked before it is used.

local units = require("HarnessUnits")
local battle = require("HarnessBattle")

local M = {}

M.SIDES = { player = true, bandit = true, ai_lord = true, other = true }
M.TIMER_MS = 2000
local EPSILON = 0.001

local overrides = {}      -- scope key ("side:player" or "squad:12") -> { field -> value }
local originals = {}      -- unit key -> { field -> value before the first write }
local timer = { started = false, applies = 0, last_error = nil }

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

local function round(value, digits)
    local scale = 10 ^ digits
    return math.floor(value * scale + 0.5) / scale
end

local function sideName(squadInfo)
    if squadInfo.side == "ai" then return "ai_lord" end
    return squadInfo.side
end

local function unitKey(unit)
    return read(function() return unit:GetFullName() end) or tostring(unit)
end

-- Visit every living unit that has an owner. fn(unit, side, squadId). Returns the number of living units without an owner.
local function eachOwnedUnit(fn)
    local map = units.squadMap()
    local unowned = 0
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) and read(function() return unit.dead end) ~= true then
            local id = read(function() return unit.assignedSquadID.Value end)
            local info = id ~= nil and map[id] or nil
            if info then fn(unit, sideName(info), id) else unowned = unowned + 1 end
        end
    end
    return unowned
end

local function overrideFor(side, squadId, field)
    local bySquad = overrides["squad:" .. tostring(squadId)]
    if bySquad and bySquad[field] ~= nil then return bySquad[field] end
    local bySide = overrides["side:" .. side]
    if bySide then return bySide[field] end
    return nil
end

local function writeStat(unit, field, value)
    local wrote = pcall(function() unit[field] = value end)
    local back = read(function() return unit[field] end)
    return wrote and type(back) == "number" and math.abs(back - value) < EPSILON
end

-- Write every override that a unit does not have yet. Returns the number of writes and the number that read back wrong.
local function applyToUnit(unit, side, squadId)
    local written, failed = 0, 0
    for _, field in ipairs(battle.STAT_ORDER) do
        local wanted = overrideFor(side, squadId, field)
        local current = wanted ~= nil and read(function() return unit[field] end) or nil
        if wanted ~= nil and type(current) == "number" and math.abs(current - wanted) >= EPSILON then
            local key = unitKey(unit)
            originals[key] = originals[key] or {}
            if originals[key][field] == nil then originals[key][field] = current end
            if writeStat(unit, field, wanted) then written = written + 1 else failed = failed + 1 end
        end
    end
    return written, failed
end

local function applyAll()
    local written, failed = 0, 0
    eachOwnedUnit(function(unit, side, squadId)
        local w, f = applyToUnit(unit, side, squadId)
        written, failed = written + w, failed + f
    end)
    timer.applies = timer.applies + 1
    return written, failed
end

local function hasOverrides()
    return next(overrides) ~= nil
end

local function startTimer()
    if timer.started then return end
    timer.started = true
    LoopAsync(M.TIMER_MS, function()
        if not hasOverrides() then return false end
        ExecuteInGameThread(function()
            local ok, err = pcall(applyAll)
            if not ok then timer.last_error = tostring(err) end
        end)
        return false
    end)
end

local function scopeOf(request)
    local side, squad = request.side, request.squad
    if side ~= nil and squad ~= nil then return nil, "give side or squad, not both" end
    if side ~= nil then
        if not M.SIDES[side] then return nil, "side must be player, bandit, ai_lord or other" end
        return { key = "side:" .. side, side = side }
    end
    if squad ~= nil then
        if type(squad) ~= "number" or squad ~= math.floor(squad) or squad < 0 then return nil, "squad must be a whole number" end
        return { key = "squad:" .. math.floor(squad), squad = squad }
    end
    return nil, "side or squad is required"
end

local function overrideList()
    local rows = {}
    for key, fields in pairs(overrides) do
        for field, value in pairs(fields) do rows[#rows + 1] = { scope = key, field = field, value = value } end
    end
    table.sort(rows, function(a, b) if a.scope ~= b.scope then return a.scope < b.scope end return a.field < b.field end)
    return rows
end

---------------------------------------------------------------------------------------------
-- Commands
---------------------------------------------------------------------------------------------

-- Per side and per squad: living units and mean of each stat. Read only.
function M.tune_state()
    local sides, squads = {}, {}
    local unowned = eachOwnedUnit(function(unit, side, squadId)
        local sideRow = sides[side] or { alive = 0, sum = {} }
        sides[side] = sideRow
        local squadRow = squads[squadId] or { squad = squadId, side = side, alive = 0, sum = {} }
        squads[squadId] = squadRow
        sideRow.alive, squadRow.alive = sideRow.alive + 1, squadRow.alive + 1
        for _, name in ipairs(battle.STAT_ORDER) do
            local value = read(function() return unit[name] end)
            if type(value) == "number" then
                sideRow.sum[name] = (sideRow.sum[name] or 0) + value
                squadRow.sum[name] = (squadRow.sum[name] or 0) + value
            end
        end
    end)
    local function means(row)
        local mean = {}
        for name, total in pairs(row.sum) do mean[name] = round(total / row.alive, 3) end
        return mean
    end
    local sideOut, squadOut = {}, {}
    for side, row in pairs(sides) do sideOut[side] = { alive = row.alive, mean = means(row) } end
    for _, row in pairs(squads) do squadOut[#squadOut + 1] = { squad = row.squad, side = row.side, alive = row.alive, mean = means(row) } end
    table.sort(squadOut, function(a, b) return a.squad < b.squad end)
    return { ok = true, sides = sideOut, squads = squadOut, overrides = overrideList(), unowned_units = unowned,
             timer = { started = timer.started, applies = timer.applies, period_ms = M.TIMER_MS, last_error = timer.last_error } }
end

-- request: side or squad, field, value. Stores the override, writes it on all living units of the scope, starts the timer.
function M.tune_set(request)
    local scope, why = scopeOf(request)
    if not scope then return { ok = false, error = why } end
    local field, value = request.field, request.value
    if not battle.STAT_FIELDS[field or ""] then return { ok = false, error = "field is not an allowed stat: " .. tostring(field) } end
    if type(value) ~= "number" or value < 0 or value > battle.MAX_STAT_VALUE then
        return { ok = false, error = "value must be a number from 0 to " .. battle.MAX_STAT_VALUE }
    end
    overrides[scope.key] = overrides[scope.key] or {}
    overrides[scope.key][field] = value
    local matched, written, failed = 0, 0, 0
    eachOwnedUnit(function(unit, side, squadId)
        if (scope.side and side == scope.side) or (scope.squad and squadId == scope.squad) then
            matched = matched + 1
            local w, f = applyToUnit(unit, side, squadId)
            written, failed = written + w, failed + f
        end
    end)
    startTimer()
    return { ok = true, scope = scope.key, field = field, value = value, alive = matched, changed = written, failed = failed,
             overrides = overrideList() }
end

-- Restore the recorded original value of one unit for the fields in resetFields.
local function restoreUnit(unit, resetFields)
    local key = unitKey(unit)
    local saved = originals[key]
    if not saved then return 0 end
    local restored = 0
    for field in pairs(resetFields) do
        if saved[field] ~= nil then
            if writeStat(unit, field, saved[field]) then restored = restored + 1 end
            saved[field] = nil
        end
    end
    if next(saved) == nil then originals[key] = nil end
    return restored
end

-- request: side or squad (optional), field (optional). Without arguments it removes all overrides.
function M.tune_reset(request)
    local scope, why
    if request.side ~= nil or request.squad ~= nil then
        scope, why = scopeOf(request)
        if not scope then return { ok = false, error = why } end
    end
    local wantField = request.field
    if wantField ~= nil and not battle.STAT_FIELDS[wantField] then return { ok = false, error = "field is not an allowed stat: " .. tostring(wantField) } end
    local removed = 0
    local touched = {}   -- field -> true, for the fields that lose an override
    for key, fields in pairs(overrides) do
        if not scope or key == scope.key then
            for field in pairs(fields) do
                if wantField == nil or field == wantField then
                    fields[field] = nil
                    touched[field] = true
                    removed = removed + 1
                end
            end
        end
        if next(fields) == nil then overrides[key] = nil end
    end
    local restored = 0
    eachOwnedUnit(function(unit, side, squadId)
        local fieldsToRestore = {}
        for field in pairs(touched) do
            -- A field that another scope still overrides stays: the apply below writes the other value.
            if overrideFor(side, squadId, field) == nil then fieldsToRestore[field] = true end
        end
        restored = restored + restoreUnit(unit, fieldsToRestore)
    end)
    applyAll()
    return { ok = true, removed = removed, restored = restored, overrides = overrideList() }
end

-- Run one apply pass now (used by tests).
function M.tune_apply()
    local written, failed = applyAll()
    return { ok = true, written = written, failed = failed }
end

return M
