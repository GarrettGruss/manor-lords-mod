-- HarnessBattle: spawn units of a chosen type on a side, hire mercenaries, and count the units of those groups (spec 10, spikes S7, P5, C1, C2).
-- Why: the raid spawn calls cannot choose a unit type (spike S2). RTSMultiEngineCPP:spawnArmy takes a list of unit template names
-- (rows of DT_UnitTemplates) and an owner pawn, and it works from Lua. The owner pawn gives the side:
--   the player pawn -> side "player", the bandit pawn -> side "bandit". The call returns one squad id for each template name.
-- The units have no template property that can be read (unitTemp reads None), so this module keeps a registry:
--   squad id -> side, template, number of units at the start. A later count of the living units of a squad gives the casualties.
-- Dead units leave the unit list at once, so casualties = initial - alive.
-- The registry lives in the Lua state of the mod that loads this module (HarnessActions). A game restart empties it.
--
-- Rules: call only on the game thread. No save function. Every input is checked before it is used.

local datatable = require("HarnessDataTable")

local M = {}

M.MAX_GROUPS = 6          -- squads for one spawn call
M.MAX_OFFSET = 20000      -- distance from the player pawn in game units
M.MAX_DETAIL_UNITS = 64   -- unit rows for each squad in a detailed state
M.MAX_EXPERIENCE = 1000
M.SIDES = { player = true, bandit = true }

local registry = {}       -- squad id -> { side, template, initial, source }

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
    if value == nil then return nil end
    return read(function() return value:ToString() end) or tostring(value)
end

-- A TArray element can be a wrapper that needs :get(). Unwrap it only if that works.
local function unwrap(element)
    local ok, inner = pcall(function() return element:get() end)
    if ok and inner ~= nil then return inner end
    return element
end

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if isValid(found) then return found end
    return nil
end

local function pawnOf(side, engineObject)
    if side == "player" then
        local player = read(function() return engineObject.playerRef end)
        if isValid(player) then return player end
        return nil
    end
    for _, pawn in ipairs(FindAllOf("PawnCPP") or {}) do
        if isValid(pawn) and read(function() return pawn.isBandit end) == true then return pawn end
    end
    return nil
end

local function squadIds(returned)
    local ids = {}
    for i = 1, #returned do
        local id = read(function() return unwrap(returned[i]).Value end)
        if id == nil then return nil, "a returned squad has no id" end
        ids[#ids + 1] = id
    end
    return ids
end

---------------------------------------------------------------------------------------------
-- Counting
---------------------------------------------------------------------------------------------

-- One pass over all units: per registered squad the living units, the experience and (optionally) a row for each unit.
local function scan(detail)
    local per = {}
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) then
            local id = read(function() return unit.assignedSquadID.Value end)
            if id ~= nil and registry[id] and read(function() return unit.dead end) ~= true then
                local row = per[id] or { alive = 0, xp_sum = 0, xp_max = 0, units = {} }
                per[id] = row
                local xp = read(function() return unit.combatExperience end) or 0
                row.alive = row.alive + 1
                row.xp_sum = row.xp_sum + xp
                row.xp_max = math.max(row.xp_max, xp)
                if detail and #row.units < M.MAX_DETAIL_UNITS then
                    row.units[#row.units + 1] = { uid = read(function() return unit.UniqueID end), xp = xp }
                end
            end
        end
    end
    return per
end

local function round(value, digits)
    local scale = 10 ^ digits
    return math.floor(value * scale + 0.5) / scale
end

local function addTo(map, key, initial, alive)
    local entry = map[key] or { initial = 0, alive = 0 }
    map[key] = entry
    entry.initial = entry.initial + initial
    entry.alive = entry.alive + alive
end

-- The state of every registered squad. request.detail = 1 adds { uid, xp } rows (at most MAX_DETAIL_UNITS for each squad).
function M.battle_state(request)
    local started = os.clock()
    local per = scan(request and request.detail == 1)
    local squads, bySide, byTemplate = {}, {}, {}
    for id, info in pairs(registry) do
        local seen = per[id] or { alive = 0, xp_sum = 0, xp_max = 0, units = {} }
        local row = { id = id, side = info.side, template = info.template, initial = info.initial, alive = seen.alive,
                      xp_mean = seen.alive > 0 and round(seen.xp_sum / seen.alive, 3) or 0, xp_max = round(seen.xp_max, 3) }
        if request and request.detail == 1 then row.units = seen.units end
        squads[#squads + 1] = row
        addTo(bySide, info.side, info.initial, seen.alive)
        addTo(byTemplate, info.side .. ":" .. info.template, info.initial, seen.alive)
    end
    table.sort(squads, function(a, b) return a.id < b.id end)
    return { ok = true, squads = squads, by_side = bySide, by_template = byTemplate, ms = round((os.clock() - started) * 1000, 1) }
end

---------------------------------------------------------------------------------------------
-- Spawn
---------------------------------------------------------------------------------------------

local function checkedSpawn(request)
    if not M.SIDES[request.side or ""] then return nil, "side must be player or bandit" end
    if not request.template then return nil, "template is required" end
    local count = request.count or 1
    if count < 1 or count > M.MAX_GROUPS then return nil, "count must be 1 to " .. M.MAX_GROUPS end
    local dx, dy = request.dx or 0, request.dy or 0
    if math.abs(dx) > M.MAX_OFFSET or math.abs(dy) > M.MAX_OFFSET then return nil, "dx and dy must be within " .. M.MAX_OFFSET end
    if not datatable.has_row(request.template, "units") then
        return nil, "no unit template named " .. tostring(request.template) .. " (rows of DT_UnitTemplates)"
    end
    return { side = request.side, template = request.template, count = count, dx = dx, dy = dy }
end

local function register(ids, side, templates, source)
    local added = {}
    for i, id in ipairs(ids) do
        registry[id] = { side = side, template = templates[i] or templates[1], initial = 0, source = source }
        added[#added + 1] = id
    end
    -- The units exist at once after the call (seen in the real game). Count them to get the start size.
    local per = scan(false)
    local rows = {}
    for _, id in ipairs(added) do
        registry[id].initial = per[id] and per[id].alive or 0
        rows[#rows + 1] = { id = id, side = side, template = registry[id].template, units = registry[id].initial }
    end
    return rows
end

-- spawnArmy(position, template names, owner pawn, company id 0, arrives in 0 days). One squad for each name.
-- Spawn `count` squads of `template` for `side` at an absolute point. Used by spawn_units and by the rebellion command (spec 15).
-- Returns { squads, units } or nil and a message.
function M.spawn_at(side, template, count, point)
    local engineObject = engine()
    if not engineObject then return nil, "no RTSMultiEngineCPP" end
    local owner = pawnOf(side, engineObject)
    if not owner then return nil, "no pawn for side " .. side end
    local names = {}
    for i = 1, count do names[i] = FName(template) end
    local ok, returned = pcall(function() return engineObject:spawnArmy({ X = point.x, Y = point.y, Z = point.z }, names, owner, 0, 0) end)
    if not ok then return nil, "spawnArmy: " .. tostring(returned) end
    local ids, why = squadIds(returned)
    if not ids then return nil, why end
    local templates = {}
    for i = 1, #ids do templates[i] = template end
    local squads = register(ids, side, templates, "spawn")
    local total = 0
    for _, squad in ipairs(squads) do total = total + squad.units end
    return { squads = squads, units = total }
end

function M.spawn_units(request)
    local wanted, problem = checkedSpawn(request)
    if not wanted then return { ok = false, error = problem } end
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local at = read(function() return engineObject.playerRef:K2_GetActorLocation() end)
    if not at then return { ok = false, error = "no player position" } end
    local point = { x = at.X + wanted.dx, y = at.Y + wanted.dy, z = at.Z }
    local spawned, why = M.spawn_at(wanted.side, wanted.template, wanted.count, point)
    if not spawned then return { ok = false, error = why } end
    return { ok = true, squads = spawned.squads, units = spawned.units, center = { x = point.x, y = point.y } }
end

-- The living units of the squads that this module spawned for one side (at most `limit`).
function M.registered_units(side, limit)
    local rows = {}
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if #rows >= limit then break end
        local id = isValid(unit) and read(function() return unit.assignedSquadID.Value end) or nil
        if id ~= nil and registry[id] and registry[id].side == side and read(function() return unit.dead end) ~= true then rows[#rows + 1] = unit end
    end
    return rows
end

---------------------------------------------------------------------------------------------
-- Clear and experience
---------------------------------------------------------------------------------------------

-- Kill the living units of the registered squads (of one side when request.side is set) and forget those squads.
function M.clear_battle(request)
    local side = request and request.side
    if side ~= nil and not M.SIDES[side] then return { ok = false, error = "side must be player or bandit" } end
    local killed = 0
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) then
            local id = read(function() return unit.assignedSquadID.Value end)
            if id ~= nil and registry[id] and (side == nil or registry[id].side == side) and read(function() return unit.dead end) ~= true then
                local ok, err = pcall(function() unit:just_die() end)
                if not ok then return { ok = false, error = "just_die: " .. tostring(err), killed = killed } end
                killed = killed + 1
            end
        end
    end
    local forgotten = 0
    for id, info in pairs(registry) do
        if side == nil or info.side == side then registry[id] = nil; forgotten = forgotten + 1 end
    end
    return { ok = true, killed = killed, squads_forgotten = forgotten }
end

-- Write combatExperience on the living units of one registered squad. Reads the value back from each unit.
function M.set_squad_experience(request)
    local id, value = request.squad, request.value
    if id == nil or not registry[id] then return { ok = false, error = "no registered squad " .. tostring(id) } end
    if type(value) ~= "number" or value < 0 or value > M.MAX_EXPERIENCE then
        return { ok = false, error = "value must be a number from 0 to " .. M.MAX_EXPERIENCE }
    end
    local alive, changed = 0, 0
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) and read(function() return unit.assignedSquadID.Value end) == id and read(function() return unit.dead end) ~= true then
            alive = alive + 1
            local wrote = pcall(function() unit.combatExperience = value end)
            local back = read(function() return unit.combatExperience end)
            if wrote and back and math.abs(back - value) < 0.001 then changed = changed + 1 end
        end
    end
    return { ok = true, squad = id, alive = alive, changed = changed, value = value }
end

---------------------------------------------------------------------------------------------
-- Combat stats and the CombatHit probe (spec 25)
---------------------------------------------------------------------------------------------

-- Fields of SMUnit that the lethality levers use (levers.md). Only these may be read or written.
M.STAT_FIELDS = { att = true, def = true, block = true, armorPierce = true, morale = true, baseDefence = true, baseBlock = true, charge = true }
local STAT_ORDER = { "att", "def", "block", "armorPierce", "morale", "baseDefence", "baseBlock", "charge" }
local MAX_STAT_VALUE = 1000
M.MAX_STAT_VALUE = MAX_STAT_VALUE
M.STAT_ORDER = STAT_ORDER

local function sideOfUnit(unit)
    local id = read(function() return unit.assignedSquadID.Value end)
    if id ~= nil and registry[id] then return registry[id].side, id end
    return nil, id
end

-- Mean stat values of the living units of one side, by squad. Read only.
function M.unit_stats(request)
    local side = request and request.side
    if side ~= nil and not M.SIDES[side] then return { ok = false, error = "side must be player or bandit" } end
    local per = {}
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) and read(function() return unit.dead end) ~= true then
            local unitSide, id = sideOfUnit(unit)
            if unitSide and (side == nil or unitSide == side) then
                local row = per[id] or { squad = id, side = unitSide, template = registry[id].template, alive = 0, sum = {} }
                per[id] = row
                row.alive = row.alive + 1
                for _, name in ipairs(STAT_ORDER) do
                    local value = read(function() return unit[name] end)
                    if type(value) == "number" then row.sum[name] = (row.sum[name] or 0) + value end
                end
            end
        end
    end
    local squads = {}
    for _, row in pairs(per) do
        local mean = {}
        for name, total in pairs(row.sum) do mean[name] = round(total / row.alive, 3) end
        squads[#squads + 1] = { squad = row.squad, side = row.side, template = row.template, alive = row.alive, mean = mean }
    end
    table.sort(squads, function(a, b) return a.squad < b.squad end)
    return { ok = true, squads = squads }
end

-- Write one stat field on every living unit of one side. Reads each value back. request: side, field, value.
function M.set_unit_stat(request)
    local side, field, value = request.side, request.field, request.value
    if not M.SIDES[side or ""] then return { ok = false, error = "side must be player or bandit" } end
    if not M.STAT_FIELDS[field or ""] then return { ok = false, error = "field is not an allowed stat: " .. tostring(field) } end
    if type(value) ~= "number" or value < 0 or value > MAX_STAT_VALUE then
        return { ok = false, error = "value must be a number from 0 to " .. MAX_STAT_VALUE }
    end
    local alive, changed = 0, 0
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) and read(function() return unit.dead end) ~= true and sideOfUnit(unit) == side then
            alive = alive + 1
            local wrote = pcall(function() unit[field] = value end)
            local back = read(function() return unit[field] end)
            if wrote and type(back) == "number" and math.abs(back - value) < 0.001 then changed = changed + 1 end
        end
    end
    return { ok = true, side = side, field = field, value = value, alive = alive, changed = changed }
end

-- Observe-only hook on SMUnit:CombatHit. It counts calls and samples the stats of attacker and defender. It changes nothing.
local hook = { registered = false, error = nil, enabled = false, calls = 0, by_side = {}, samples = {} }
local MAX_HOOK_SAMPLES = 40

local function statsOf(unit)
    local out = {}
    for _, name in ipairs(STAT_ORDER) do out[name] = read(function() return unit[name] end) end
    return out
end

local function onCombatHit(_self, attacker, defender)
    if not hook.enabled then return end
    hook.calls = hook.calls + 1
    local a = read(function() return attacker:get() end)
    local d = read(function() return defender:get() end)
    local aSide = a and sideOfUnit(a) or "?"
    local dSide = d and sideOfUnit(d) or "?"
    local key = tostring(aSide) .. ">" .. tostring(dSide)
    hook.by_side[key] = (hook.by_side[key] or 0) + 1
    if #hook.samples < MAX_HOOK_SAMPLES and a and d then
        hook.samples[#hook.samples + 1] = { attacker = statsOf(a), defender = statsOf(d), key = key }
    end
end

local function registerHook()
    if hook.registered then return true end
    local ok, err = pcall(RegisterHook, "/Script/ManorLords.SMUnit:CombatHit", onCombatHit, function() end)
    if not ok then hook.error = tostring(err); return false end
    hook.registered = true
    return true
end

-- request.mode: start (reset counters and enable), stop (disable) or read.
function M.combat_hook(request)
    local action = request and request.mode
    if action == "start" then
        if not registerHook() then return { ok = false, error = "RegisterHook: " .. tostring(hook.error) } end
        hook.calls, hook.by_side, hook.samples, hook.enabled = 0, {}, {}, true
    elseif action == "stop" then
        hook.enabled = false
    elseif action ~= "read" then
        return { ok = false, error = "action must be start, stop or read" }
    end
    return { ok = true, enabled = hook.enabled, registered = hook.registered, calls = hook.calls, by_side = hook.by_side, samples = hook.samples }
end

---------------------------------------------------------------------------------------------
-- Mercenaries (spike P5)
---------------------------------------------------------------------------------------------

local function companyRow(company)
    local units = {}
    local list = read(function() return company.units end)
    local count = list and read(function() return list:GetArrayNum() end) or 0
    for i = 1, count do units[#units + 1] = textOf(read(function() return list[i] end)) end
    return { name = textOf(read(function() return company.Name end)), cost = read(function() return company.cost end),
             arrives_in = read(function() return company.arrivesIn end), units = units }
end

local function offers(engineObject)
    local out = {}
    local list = read(function() return engineObject.availableMercs end)
    local count = list and read(function() return list:GetArrayNum() end) or 0
    for i = 1, count do
        local entry = read(function() return list[i] end)
        if entry ~= nil then out[#out + 1] = { row = companyRow(entry), object = entry } end
    end
    return out
end

local function hiredCount(engineObject)
    local n = 0
    local ok = pcall(function() engineObject.hiredMercs:ForEach(function() n = n + 1 end) end)
    if ok then return n end
    return nil
end

local function silverOf(engineObject)
    return read(function() return engineObject.playerRef.silver end)
end

-- The companies that can be hired now: name, cost in silver, days until arrival and the unit templates. Read only.
function M.mercenary_offers()
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local rows = {}
    for _, offer in ipairs(offers(engineObject)) do rows[#rows + 1] = offer.row end
    return { ok = true, offers = rows, silver = silverOf(engineObject), hired = hiredCount(engineObject) }
end

-- Hire one offered company with RTSMultiEngineCPP:hireMercs. The game does NOT check the cost (the UI does): silver went to -100 in a probe.
-- So this command refuses when the silver is below the cost. The units appear at once (arrives_in is not waited for).
function M.hire_mercenaries(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    if not request.company then return { ok = false, error = "company is required" } end
    local chosen
    for _, offer in ipairs(offers(engineObject)) do
        if offer.row.name == request.company then chosen = offer end
    end
    if not chosen then return { ok = false, error = "no offered company named " .. tostring(request.company) } end
    local silver = silverOf(engineObject)
    if type(silver) ~= "number" or type(chosen.row.cost) ~= "number" then return { ok = false, error = "cannot read silver or cost" } end
    if silver < chosen.row.cost then
        return { ok = false, error = "not enough silver: " .. silver .. " is below the cost " .. chosen.row.cost }
    end
    local hiredBefore = hiredCount(engineObject)
    local ok, returned = pcall(function() return engineObject:hireMercs(chosen.object, engineObject.playerRef) end)
    if not ok then return { ok = false, error = "hireMercs: " .. tostring(returned) } end
    local ids, why = squadIds(returned)
    if not ids then return { ok = false, error = why } end
    local squads = register(ids, "player", chosen.row.units, "mercenary")
    local total = 0
    for _, squad in ipairs(squads) do total = total + squad.units end
    return { ok = true, company = chosen.row, silver_before = silver, silver_after = silverOf(engineObject), squads = squads, units = total,
             hired_before = hiredBefore, hired_after = hiredCount(engineObject), offers_after = #offers(engineObject) }
end

return M
