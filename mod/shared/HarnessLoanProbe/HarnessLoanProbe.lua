-- HarnessLoanProbe: spike spike-loan-units. Hide, disable and restore player squads and villagers.
-- Why: Liege contracts tier III may loan units or peasants for some days. The spike must find out what a script can take away and give back.
-- Research tool only. It calls no save function and never K2_DestroyActor. It keeps the hidden units in a Lua table so a later call can restore them.
--   {"command":"loan_probe","mode":"state","squad":19}            counts, hidden flags, collision, positions of the units of one squad
--   {"command":"loan_probe","mode":"hide","squad":19,"source":"plain|tick|far"}   hide units (and more, by source)
--   {"command":"loan_probe","mode":"show"}                        undo the last hide
--   {"command":"loan_probe","mode":"removereq","squad":19}   PawnCPP:addRemoveSquadRequest
--   {"command":"loan_probe","mode":"familystate"}                same as state, for the members of the first `count` families
--   {"command":"loan_probe","mode":"familyhide","count":2,"source":"plain|tick"}   hide the members of `count` families

local sack = require("HarnessSack")

local M = {}

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

local function unwrap(element)
    local ok, inner = pcall(function() return element:get() end)
    if ok and inner ~= nil then return inner end
    return element
end

local function listOf(array)
    local out = {}
    if array == nil then return out end
    local count = read(function() return array:GetArrayNum() end) or 0
    for i = 1, count do out[#out + 1] = unwrap(array[i]) end
    return out
end

local hidden = {}   -- { unit, source, before = { x, y, z } }
local MAX_UNITS = 80

local function unitsOfSquad(id)
    local found = {}
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if #found >= MAX_UNITS then break end
        if isValid(unit) and read(function() return unit.dead end) ~= true and read(function() return unit.assignedSquadID.Value end) == id then
            found[#found + 1] = unit
        end
    end
    return found
end

local function familyMembers(region, count)
    local members, families = {}, 0
    for _, family in ipairs(listOf(region.workerFamilies)) do
        if families >= count then break end
        for _, member in ipairs(listOf(family.familyMembers)) do members[#members + 1] = member end
        families = families + 1
    end
    return members, families
end

local function vec(v)
    if v == nil then return nil end
    return { x = math.floor((read(function() return v.X end) or 0) + 0.5), y = math.floor((read(function() return v.Y end) or 0) + 0.5),
             z = math.floor((read(function() return v.Z end) or 0) + 0.5) }
end

local function commandedCount()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local player = engine and read(function() return engine.playerRef end)
    return isValid(player) and read(function() return player.commandedSquads:GetArrayNum() end) or nil
end

local function describe(units)
    local out = { commanded = commandedCount(), count = 0, hidden = 0, collision_off = 0, tick_off = 0, dead = 0, rows = {} }
    for _, unit in ipairs(units) do
        if isValid(unit) then
            out.count = out.count + 1
            if read(function() return unit.bHidden end) == true then out.hidden = out.hidden + 1 end
            if read(function() return unit:GetActorEnableCollision() end) == false then out.collision_off = out.collision_off + 1 end
            if read(function() return unit:IsActorTickEnabled() end) == false then out.tick_off = out.tick_off + 1 end
            if read(function() return unit.dead end) == true then out.dead = out.dead + 1 end
            if #out.rows < 3 then
                out.rows[#out.rows + 1] = { real = vec(read(function() return unit.realPos end)), actor = vec(read(function() return unit:K2_GetActorLocation() end)),
                    squad = read(function() return unit.assignedSquadID.Value end) }
            end
        end
    end
    return out
end

local function hideUnits(units, source)
    local done = 0
    for _, unit in ipairs(units) do
        if isValid(unit) then
            local before = vec(read(function() return unit:K2_GetActorLocation() end))
            local ok = pcall(function() unit:SetActorHiddenInGame(true) end)
            pcall(function() unit:SetActorEnableCollision(false) end)
            if source == "tick" then pcall(function() unit:SetActorTickEnabled(false) end) end
            if source == "far" and before then
                pcall(function() unit:K2_SetActorLocation({ X = before.x, Y = before.y, Z = before.z - 50000 }, false, {}, true) end)
            end
            if ok then
                done = done + 1
                hidden[#hidden + 1] = { unit = unit, source = source, before = before }
            end
        end
    end
    return done
end

local function showAll()
    local done, skipped = 0, 0
    for _, row in ipairs(hidden) do
        local unit = row.unit
        if isValid(unit) and read(function() return unit.dead end) ~= true then
            pcall(function() unit:SetActorHiddenInGame(false) end)
            pcall(function() unit:SetActorEnableCollision(true) end)
            pcall(function() unit:SetActorTickEnabled(true) end)
            if row.source == "far" and row.before then
                pcall(function() unit:K2_SetActorLocation({ X = row.before.x, Y = row.before.y, Z = row.before.z }, false, {}, true) end)
            end
            done = done + 1
        else
            skipped = skipped + 1
        end
    end
    hidden = {}
    return done, skipped
end

function M.loan_probe(request)
    local mode = request.mode
    if mode == "state" then
        if request.squad == nil then return { ok = false, error = "squad is required" } end
        return { ok = true, state = describe(unitsOfSquad(request.squad)) }
    elseif mode == "hide" then
        if request.squad == nil then return { ok = false, error = "squad is required" } end
        local units = unitsOfSquad(request.squad)
        local done = hideUnits(units, request.source or "plain")
        return { ok = true, hidden = done, state = describe(units) }
    elseif mode == "show" then
        local done, skipped = showAll()
        return { ok = true, shown = done, skipped = skipped }
    elseif mode == "removereq" then
        if request.squad == nil then return { ok = false, error = "squad is required" } end
        local engine = FindFirstOf("RTSMultiEngineCPP")
        local player = engine and read(function() return engine.playerRef end)
        if not isValid(player) then return { ok = false, error = "no player pawn" } end
        local ok, err = pcall(function() player:addRemoveSquadRequest({ Value = request.squad }) end)
        return { ok = ok, error = (not ok) and tostring(err) or nil, commanded = read(function() return player.commandedSquads:GetArrayNum() end) }
    elseif mode == "familystate" or mode == "familyhide" then
        local region, problem = sack.playerRegion(nil)
        if not region then return { ok = false, error = problem } end
        local members, families = familyMembers(region, request.count or 1)
        local hiddenNow = 0
        if mode == "familyhide" then hiddenNow = hideUnits(members, request.source or "plain") end
        return { ok = true, families = families, hidden = hiddenNow, state = describe(members),
                 families_total = read(function() return region.workerFamilies:GetArrayNum() end) }
    end
    return { ok = false, error = "unknown mode " .. tostring(mode) }
end

return M
