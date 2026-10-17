-- Game reads and writes of the raid tracker. Call only on the game thread.
local core = require("ManorCore")

local isValid, read, listOf, textOf = core.isValid, core.read, core.listOf, core.textOf

local M = {}

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if isValid(found) then return found end
    return nil
end

-- Key of a unit for the tracker: its address. The address is stable while the unit exists.
local function unit_key(unit)
    return read(function() return unit:GetAddress() end)
end

-- Every unit now: key -> { loot, x, y, dead, squad, object }.
function M.read_units()
    local out = {}
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) then
            local key = unit_key(unit)
            if key ~= nil then
                local at = read(function() return unit.realPos end)
                out[key] = {
                    loot = read(function() return unit.ItemsLooted end) or 0,
                    x = at and read(function() return at.X end), y = at and read(function() return at.Y end),
                    dead = read(function() return unit.dead end) == true,
                    squad = read(function() return unit.assignedSquadID.Value end),
                    object = unit,
                }
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
function M.stores()
    local region, problem = core.player_region()
    if region == nil then return nil, problem end
    local stores = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) and read(function() return building:IsRubble() end) ~= true then
            local by_good = goods_of(building)
            local x, y = building_place(building)
            if next(by_good) ~= nil and x ~= nil then
                local name = read(function() return building:GetFullName() end) or ""
                stores[#stores + 1] = { building = building, x = x, y = y, by_good = by_good, id = tonumber(name:match("_(%d+)$")) }
            end
        end
    end
    return stores
end

local function total_of(by_good)
    local total = 0
    for _, held in pairs(by_good) do total = total + held end
    return total
end

-- Put goods into one store. The deposit is read back from the building inventory.
function M.deposit(store, good, amount)
    local before = total_of(goods_of(store.building))
    local ok, problem = pcall(function() store.building:addToInventory({ Type = good, amt = amount }) end)
    if not ok then return false, "addToInventory: " .. tostring(problem) end
    local rise = total_of(goods_of(store.building)) - before
    if rise ~= amount then return false, string.format("store rose by %d, wanted %d", rise, amount) end
    return true
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

local MAX_NEW_LINES = 60   -- never read more new log lines than this in one look

local function ai_log()
    local found = engine()
    return found and read(function() return found.debugLog_AI_general end)
end

-- Number of lines in the AI general log. Reading only the length is cheap.
function M.ai_log_length()
    local lines = ai_log()
    if lines == nil then return nil end
    return read(function() return lines:GetArrayNum() end)
end

-- True when one of the lines after index `from` (1-based, at most MAX_NEW_LINES of the newest) holds the text.
-- The game writes the native leave line there. Only new lines are read, because a long read of a growing log each second is risky.
function M.ai_log_has_new(text, from, length)
    local lines = ai_log()
    if lines == nil then return false end
    for index = math.max(from + 1, length - MAX_NEW_LINES + 1), length do
        local content = textOf(read(function() return lines[index] end))
        if content and content:find(text, 1, true) then return true end
    end
    return false
end

function M.current_day()
    local found = engine()
    local calendar = found and read(function() return found.TemporalComponent end)
    local value = calendar and read(function() return calendar.daysTotal end)
    if type(value) ~= "number" then return nil end
    return math.floor(value)
end

return M
