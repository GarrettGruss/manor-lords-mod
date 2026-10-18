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

-- The units now: key -> { loot, x, y, dead, object }. With `tracked` (a set of keys) only those units are read.
-- Few reads on purpose: a read of every property of every unit once a second crashed the game in raids of 2 squads
-- (spike notes of M03.01). A dead unit is read for `dead` only. The place is read only for a unit that carries loot.
function M.read_units(tracked)
    local out = {}
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) then
            local key = unit_key(unit)
            if key ~= nil and (tracked == nil or tracked[key]) then
                local row = { dead = read(function() return unit.dead end) == true, loot = 0, object = unit }
                if not row.dead then
                    row.loot = read(function() return unit.ItemsLooted end) or 0
                    if row.loot > 0 then
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
