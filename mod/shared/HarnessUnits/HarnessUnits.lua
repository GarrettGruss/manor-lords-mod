-- HarnessUnits: counts the units of the game by side, role, squad type and state (spec 10, spike S3).
-- Why: the bridge can list only a few objects and reads one property per call. A census of 300 units
-- needs one pass inside the game. The answer is small: counts, plus a short sample.
--
-- Side of a unit: a unit has no owner property. The owner is found through the squad:
--   unit.assignedSquadID.Value  ->  squad of a PawnCPP (pawn.commandedSquads)  ->  isMainPlayer / isBandit / isAI.
--   A unit with no squad (villager, animal, merchant) has the side "civil".
--
-- Rules: call it only on the game thread. Every property read has a guard. A failed read gives nil, never an error.

local M = {}

M.SAMPLE_LIMIT = 30   -- never return more sample rows than this, whatever the caller asks
M.SQUAD_LIMIT = 16    -- never return more squad rows than this

-- Enum names from the jmap (EUnitRole, ESquadType, ESquadControl).
local ROLE_NAMES = { [0] = "Husband", "Wife", "Son", "Daughter", "Retainer", "Soldier", "FreeMerchant", "FreeLivestockMerchant",
    "Deer", "Chicken", "Sheep", "Lamb", "Ox", "Goat", "Hound", "Horse", "Mule", "BanditRecruit", "None", "Pig", "Hare", "Cow", "Calf" }
local SQUAD_TYPE_NAMES = { [0] = "None", "Militia", "Mercenaries", "Retinue", "Bandits", "Wildlife", "Merchants", "Raiders" }
local CONTROL_NAMES = { [0] = "Full", "Engaged", "Partial", "Fleeing", "Encamped" }

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function textOf(value)
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

local function read(fn)
    local ok, value = pcall(fn)
    if ok then return value end
    return nil
end

-- Trace: set M.trace to a function(text) to log each step before it runs. A native crash leaves no Lua error,
-- so the last trace line shows which read ended the game. Off by default.
M.trace = nil
local function trace(text)
    if M.trace then M.trace(text) end
end

-- A read with a trace line before it. `label` names the property.
local function field(label, fn)
    trace(label)
    return read(fn)
end

local function round(value, digits)
    if type(value) ~= "number" then return nil end
    local scale = 10 ^ (digits or 0)
    return math.floor(value * scale + 0.5) / scale
end

local function add(counts, key, amount)
    counts[key] = (counts[key] or 0) + (amount or 1)
end

local function listOf(array)
    local out = {}
    local count = read(function() return array:GetArrayNum() end) or 0
    for i = 1, count do out[#out + 1] = unwrap(array[i]) end
    return out
end

local function vectorOf(vector)
    if vector == nil then return nil end
    return { x = round(read(function() return vector.X end)), y = round(read(function() return vector.Y end)),
             z = round(read(function() return vector.Z end)) }
end

---------------------------------------------------------------------------------------------
-- Sides and squads
---------------------------------------------------------------------------------------------

local function sideOfPawn(pawn)
    if read(function() return pawn.isMainPlayer end) == true then return "player" end
    if read(function() return pawn.isBandit end) == true then return "bandit" end
    if read(function() return pawn.isAI end) == true then return "ai" end
    return "other"
end

-- A squad record. Its size and centre are filled while the units are counted.
-- Do NOT call getSquadByID (it returns a Squad struct and ended the game) and do not use GetSquadUnits (it gave 0 members).
local function readSquad(pawn, handle, side)
    return { side = side, type = "?", control = "?", size = 0 }
end

-- Map: squad id -> squad info, for the squads of every pawn.
function M.squadMap()
    local map, pawns = {}, FindAllOf("PawnCPP") or {}
    trace("pawns " .. #pawns)
    for _, pawn in ipairs(pawns) do
        if isValid(pawn) then
            local side = sideOfPawn(pawn)
            trace("pawn side " .. side)
            local handles = field("pawn.commandedSquads", function() return pawn.commandedSquads end)
            for _, handle in ipairs(handles and listOf(handles) or {}) do
                local id = read(function() return handle.Value end)
                if id ~= nil then map[id] = readSquad(pawn, handle, side) end
            end
        end
    end
    return map
end

---------------------------------------------------------------------------------------------
-- One unit
---------------------------------------------------------------------------------------------

local regionNames = {}   -- region address -> name

local function regionNameOf(unit)
    local region = field("unit.currentRegion", function() return unit.currentRegion end)
    if not isValid(region) then return nil end
    local address = read(function() return region:GetAddress() end)
    if address and regionNames[address] then return regionNames[address] end
    local name = textOf(read(function() return region.regionName end)) or "?"
    if address then regionNames[address] = name end
    return name
end

local function readUnit(unit, squads)
    local squadId = field("unit.assignedSquadID", function() return unit.assignedSquadID.Value end)
    local squad = squadId and squads[squadId]
    local role = field("unit.currentUnitRole", function() return unit.currentUnitRole end)
    return {
        squad_id = squadId,
        side = squad and squad.side or "civil",
        squad_type = squad and squad.type or nil,
        control = squad and squad.control or nil,
        role = ROLE_NAMES[role] or tostring(role),
        template = textOf(field("unit.unitTemp", function() return unit.unitTemp end)),
        dead = field("unit.dead", function() return unit.dead end) == true,
        morale = round(field("unit.morale", function() return unit.morale end), 1),
        experience = round(field("unit.combatExperience", function() return unit.combatExperience end), 2),
        loot = field("unit.ItemsLooted", function() return unit.ItemsLooted end) or 0,
        region = regionNameOf(unit),
        pos = vectorOf(field("unit.realPos", function() return unit.realPos end)),
    }
end

---------------------------------------------------------------------------------------------
-- Census
---------------------------------------------------------------------------------------------

local function newTotals()
    return { by_side = {}, by_role = {}, by_squad_type = {}, by_state = {}, by_region = {},
             loot = { carriers = 0, total = 0, max = 0 }, sample = {} }
end

local function addUnitToTotals(totals, row, sampleWanted)
    if row.dead then add(totals.by_state, "dead"); return end
    add(totals.by_side, row.side)
    add(totals.by_role, row.role)
    if row.squad_type then add(totals.by_squad_type, row.squad_type) end
    add(totals.by_state, row.control or "no_squad")
    if row.region then add(totals.by_region, row.region) end
    if row.loot > 0 then
        totals.loot.carriers = totals.loot.carriers + 1
        totals.loot.total = totals.loot.total + row.loot
        totals.loot.max = math.max(totals.loot.max, row.loot)
    end
    if row.side ~= "civil" and #totals.sample < sampleWanted then totals.sample[#totals.sample + 1] = row end
end

local function squadRows(squads)
    local rows = {}
    for id, squad in pairs(squads) do
        if #rows < M.SQUAD_LIMIT and squad.side ~= "player" then
            rows[#rows + 1] = { id = id, side = squad.side, type = squad.type, control = squad.control, size = squad.size,
                                center = squad.center, region = squad.region }
        end
    end
    table.sort(rows, function(a, b) return a.id < b.id end)
    return rows
end

-- opts.sample: number of unit rows to return (0 to M.SAMPLE_LIMIT). Rows are units that are not civil.
function M.census(opts)
    opts = opts or {}
    local sampleWanted = math.min(tonumber(opts.sample) or 0, M.SAMPLE_LIMIT)
    local started = os.clock()
    local squads = M.squadMap()
    local totals = newTotals()
    local units = FindAllOf("SMUnit") or {}
    trace("units " .. #units)
    local seen = 0
    for _, unit in ipairs(units) do
        if isValid(unit) then
            seen = seen + 1
            local row = readUnit(unit, squads)
            local squad = row.squad_id and squads[row.squad_id]
            if squad and not row.dead then
                squad.size = squad.size + 1
                squad.center = squad.center or row.pos
                squad.region = squad.region or row.region
            end
            addUnitToTotals(totals, row, sampleWanted)
        end
    end
    trace("loop done")
    totals.units = seen
    totals.squads = squadRows(squads)
    trace("squad rows done")
    totals.ms = round((os.clock() - started) * 1000, 1)
    return totals
end

-- Only the counts that a telemetry line needs.
function M.counts()
    local totals = M.census({ sample = 0 })
    return { units = totals.units, by_side = totals.by_side, by_squad_type = totals.by_squad_type,
             dead = totals.by_state.dead or 0, loot_carriers = totals.loot.carriers, loot_total = totals.loot.total, ms = totals.ms }
end

---------------------------------------------------------------------------------------------
-- Pick units (for the actions that act on them)
---------------------------------------------------------------------------------------------

-- Live units of one side that are not dead (with onlyWithLoot: only those with ItemsLooted above 0). `limit` caps the list. Units of the side "bandit" include raiders.
function M.unitsOfSide(side, limit, onlyWithLoot)
    local squads, found = M.squadMap(), {}
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if #found >= (limit or 1000) then break end
        if isValid(unit) and read(function() return unit.dead end) ~= true then
            local squad = squads[read(function() return unit.assignedSquadID.Value end)]
            local wanted = (squad and squad.side or "civil") == side
            if wanted and onlyWithLoot and (read(function() return unit.ItemsLooted end) or 0) <= 0 then wanted = false end
            if wanted then found[#found + 1] = unit end
        end
    end
    return found
end

-- Telemetry metric: M.register_telemetry(HarnessTelemetry) adds custom.units to each sample.
function M.register_telemetry(telemetry)
    telemetry.register("units", M.counts)
end

return M
