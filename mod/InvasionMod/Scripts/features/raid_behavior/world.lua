-- Game reads and writes of the raid tracker. Call only on the game thread.
local core = require("ManorCore")

local isValid, read, listOf, textOf = core.isValid, core.read, core.listOf, core.textOf

local M = {}

local function total_of_goods(by_good)
    local total = 0
    for _, held in pairs(by_good) do total = total + held end
    return total
end

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if isValid(found) then return found end
    return nil
end

-- Key of a unit for the tracker: its address. The address is stable while the unit exists.
local function unit_key(unit)
    return read(function() return unit:GetAddress() end)
end

-- Squad ids that the game unit census (HarnessUnits) knows. A unit whose squad is not in it is not counted by the census.
-- nil when the census module is missing: then no unit is filtered.
local function census_squads()
    local ok, units = pcall(require, "HarnessUnits")
    if not ok then return nil end
    return units.squadMap()
end

-- The units now: key -> { loot, x, y, dead, object }. With `tracked` (a set of keys) only those units are read.
-- Few reads on purpose: a read of every property of every unit once a second crashed the game in raids of 2 squads
-- (spike notes of M03.01). A dead unit is read for `dead` only. The place is read only for a unit that carries loot.
-- A tracked unit that the census does not count (no squad in the census) is read as dead: it is gone, also while the
-- game still lists the object (its death animation).
function M.read_units(tracked, all_places)
    local out = {}
    local squads = tracked ~= nil and census_squads() or nil
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) then
            local key = unit_key(unit)
            if key ~= nil and (tracked == nil or tracked[key]) then
                local row = { dead = read(function() return unit.dead end) == true, loot = 0, object = unit }
                if not row.dead and squads ~= nil then
                    local squad_id = read(function() return unit.assignedSquadID.Value end)
                    if squad_id == nil or squads[squad_id] == nil then row.dead = true end
                end
                if not row.dead then
                    local looted = read(function() return unit.ItemsLooted end)
                    row.loot = type(looted) == "number" and looted or 0 -- a unit of another class can return an actor here
                    if row.loot > 0 or all_places then
                        local at = read(function() return unit.realPos end)
                        row.x, row.y = at and read(function() return at.X end), at and read(function() return at.Y end)
                    end
                end
                out[key] = row
            end
        end
    end
    return out
end

-- Keys that are in `after` and not in `before`: the units that a spawn call made.
function M.new_keys(before, after)
    local keys = {}
    for key in pairs(after) do
        if before[key] == nil then keys[#keys + 1] = key end
    end
    table.sort(keys)
    return keys
end

function M.write_loot(unit_object, amount)
    local ok, problem = pcall(function() unit_object.ItemsLooted = amount end)
    if not ok then return false, tostring(problem) end
    return true
end

-- Give a region back to the player pawn (a won challenge writes the lord as owner, run 20261018-015009-371a).
-- The region is found by its object name (as regions_state prints it).
local function find_region(region_name)
    local found = engine()
    for _, region in ipairs(found and listOf(found.regions) or {}) do
        local name = isValid(region) and read(function() return region:GetFullName() end) or ""
        if name:match("%.([^%.]+)$") == region_name then return region end
    end
    return nil
end

function M.give_region_to_player(region_name)
    local player = engine() and read(function() return engine().playerRef end)
    if not isValid(player) then return false, "no player pawn" end
    local region = find_region(region_name)
    if region == nil then return false, "no region " .. tostring(region_name) end
    local ok, problem = pcall(function() region.ownerPawn = player end)
    if not ok then return false, tostring(problem) end
    return true
end

-- Test only: write another pawn as the owner of a region (what a won challenge does).
function M.set_region_owner(region_name, pawn)
    local region = find_region(region_name)
    if region == nil then return false, "no region " .. tostring(region_name) end
    local ok, problem = pcall(function() region.ownerPawn = pawn end)
    if not ok then return false, tostring(problem) end
    return true
end

-- true when the player owns the region, false when not, nil when it cannot be read.
function M.region_is_players(region_name)
    local player = engine() and read(function() return engine().playerRef end)
    local region = find_region(region_name)
    if not isValid(player) or region == nil then return nil end
    local owner = read(function() return region.ownerPawn end)
    if not isValid(owner) then return false end
    return read(function() return owner:GetAddress() end) == read(function() return player:GetAddress() end)
end

-- Take `amount` goods out of the tier 1 stores of the village (`tiers` maps a building type to a tier; a store of another
-- tier or of no tier is never touched), from the store that holds most first. Returns the amount taken.
-- consumeGoodNoCheck removes one unit (HarnessSack, spike S6).
function M.plunder(amount, tiers)
    local all, stores = M.stores(), {}
    if all == nil then return 0 end
    for _, store in ipairs(all) do
        if store.type ~= nil and tiers[store.type] == 1 then stores[#stores + 1] = store end
    end
    table.sort(stores, function(a, b) return total_of_goods(a.by_good) > total_of_goods(b.by_good) end)
    local taken = 0
    for _, store in ipairs(stores) do
        for good, held in pairs(store.by_good) do
            for _ = 1, held do
                if taken >= amount then return taken end
                if pcall(function() store.building:consumeGoodNoCheck(good) end) then taken = taken + 1 end
            end
        end
    end
    return taken
end

-- Take a raider off the map: the loot goes first (it leaves with the raider), then the unit dies.
-- just_die is the proven removal (harness kill_units, bandit_kill_squads). A move order is not obeyed (spec 15).
function M.remove_unit(unit_object)
    local ok, problem = pcall(function()
        unit_object.ItemsLooted = 0
        unit_object:just_die()
    end)
    if not ok then return false, tostring(problem) end
    return true
end

---------------------------------------------------------------------------------------------
-- The village
---------------------------------------------------------------------------------------------

local function building_place(building)
    local at = read(function() return building:K2_GetActorLocation() end)
    if at == nil then return nil end
    return read(function() return at.X end), read(function() return at.Y end)
end

local function goods_of(building)
    local by_good = {}
    for _, good in ipairs(listOf(building.Inventory)) do
        local kind, amount = read(function() return good.Type end), read(function() return good.amt end)
        if kind and amount and amount > 0 then by_good[kind] = (by_good[kind] or 0) + amount end
    end
    return by_good
end

-- Standing buildings that hold goods: { building, x, y, by_good, id }.
-- `region_name` (optional): the player region to read. Without it: the first region of the player.
function M.stores(region_name)
    local region, problem
    if region_name == nil then region, problem = core.player_region() else region, problem = require("HarnessSack").playerRegion(region_name) end
    if region == nil then return nil, problem end
    local stores = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) and read(function() return building:IsRubble() end) ~= true then
            local by_good = goods_of(building)
            local x, y = building_place(building)
            if next(by_good) ~= nil and x ~= nil then
                local name = read(function() return building:GetFullName() end) or ""
                local kind = read(function() return building.Data.bType end)
                stores[#stores + 1] = { building = building, x = x, y = y, by_good = by_good, id = tonumber(name:match("_(%d+)$")), type = type(kind) == "number" and kind or nil }
            end
        end
    end
    return stores
end

-- Burned buildings: ruins and buildings on fire, now.
function M.burned_count()
    local region = core.player_region()
    if region == nil then return nil end
    local count = 0
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) then
            local rubble = read(function() return building:IsRubble() end) == true
            local burning = read(function() return building.onFire end) == true
            if rubble or burning then count = count + 1 end
        end
    end
    return count
end

function M.population()
    local region = core.player_region()
    if region == nil then return nil end
    return read(function() return region:getNumTotalPopulation() end)
end

---------------------------------------------------------------------------------------------
-- The AI log
---------------------------------------------------------------------------------------------

local TAIL_LINES = 60   -- the log is read from its end, never more than this many lines in one look

-- Number of lines among the newest TAIL_LINES of the AI general log that hold the text.
-- The game writes the native leave line there. The log can keep a fixed length, so the caller compares counts, not lengths.
function M.ai_log_tail_count(text)
    local found = engine()
    local lines = found and read(function() return found.debugLog_AI_general end)
    local length = lines and read(function() return lines:GetArrayNum() end)
    if length == nil then return nil end
    local count = 0
    for index = math.max(1, length - TAIL_LINES + 1), length do
        local content = textOf(read(function() return lines[index] end))
        if content and content:find(text, 1, true) then count = count + 1 end
    end
    return count
end

function M.current_day()
    local found = engine()
    local calendar = found and read(function() return found.TemporalComponent end)
    local value = calendar and read(function() return calendar.daysTotal end)
    if type(value) ~= "number" then return nil end
    return math.floor(value)
end

return M
