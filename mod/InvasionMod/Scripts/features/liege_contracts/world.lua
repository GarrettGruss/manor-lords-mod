-- Game access of the feature liege_contracts. Every call runs on the game thread (the scheduler tick or a command).
-- Reads return nil when the game does not answer; a write returns true, or nil and a message.
local core = require("ManorCore")

local M = {}
local isValid, read, listOf = core.isValid, core.read, core.listOf

local STOREHOUSE_TYPE = 72                   -- EBuildingType of the storehouse (wiki engine-limits.md)
local TIER1_STORES = { 6, 72 }               -- the stores that raid_behavior plunders first; a good is added to the first one
local TAKE_FROM_TYPES = { 6, 72, 50, 57, 58, 81, 82, 83, 95, 98 } -- stores in the order of taking (tier 1, then tier 2: config store_tiers of raid_behavior)
local HOME_TYPE = 3

function M.current_day()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil end
    local day = read(function() return engine.TemporalComponent.daysTotal end)
    return type(day) == "number" and math.floor(day) or nil
end

local function built_buildings(region)
    local list = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) and read(function() return building:IsRubble() end) ~= true then list[#list + 1] = building end
    end
    return list
end

local function building_type(building)
    local kind = read(function() return building.Data.bType end)
    return type(kind) == "number" and math.floor(kind) or nil
end

local function amount_of(building, good)
    local total = 0
    for _, row in ipairs(listOf(building.Inventory)) do
        if read(function() return row.Type end) == good then total = total + (read(function() return row.amt end) or 0) end
    end
    return total
end

function M.stock(good)
    local region = core.player_region()
    if region == nil then return nil end
    local value = read(function() return region:getStockOfGood(good, false, false) end)
    return type(value) == "number" and math.floor(value) or nil
end

-- Finished buildings of one type in the player region.
function M.building_count(kind)
    local region = core.player_region()
    if region == nil then return nil end
    local count = 0
    for _, building in ipairs(built_buildings(region)) do
        if building_type(building) == kind and read(function() return building.Data.constructed end) ~= false then count = count + 1 end
    end
    return count
end

-- The squads the player commands (the militia squads of spike #482 are in this list).
function M.squad_count()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil end
    local count = read(function() return engine.playerRef.commandedSquads:GetArrayNum() end)
    return type(count) == "number" and count or nil
end

-- Take `amount` units of a good from the stores of the player region (tier 1 stores first, then tier 2).
-- Returns the number of units taken (it can be less than `amount`), or nil and a message.
function M.take_goods(good, amount)
    local region, problem = core.player_region()
    if region == nil then return nil, problem end
    local rank = {}
    for position, kind in ipairs(TAKE_FROM_TYPES) do rank[kind] = position end
    local stores = {}
    for _, building in ipairs(built_buildings(region)) do
        local kind = building_type(building)
        if kind ~= nil and rank[kind] ~= nil and kind ~= HOME_TYPE then stores[#stores + 1] = { building = building, rank = rank[kind] } end
    end
    table.sort(stores, function(a, b) return a.rank < b.rank end)
    local taken = 0
    for _, store in ipairs(stores) do
        local held = amount_of(store.building, good)
        for _ = 1, math.min(held, amount - taken) do
            if not pcall(function() store.building:consumeGoodNoCheck(good) end) then break end
            taken = taken + 1
        end
        if taken >= amount then break end
    end
    return taken
end

-- Add goods to the first storehouse of the player region. Returns true, or nil and a message.
function M.add_goods(good, amount)
    local region, problem = core.player_region()
    if region == nil then return nil, problem end
    local by_type = {}
    for _, building in ipairs(built_buildings(region)) do
        local kind = building_type(building)
        if kind ~= nil then by_type[kind] = by_type[kind] or building end
    end
    for _, kind in ipairs(TIER1_STORES) do
        local store = by_type[kind]
        if store ~= nil then
            local before = amount_of(store, good)
            local ok, why = pcall(function() store:addToInventory({ Type = good, amt = amount }) end)
            if not ok then return nil, "addToInventory: " .. tostring(why) end
            if amount_of(store, good) - before < amount then return nil, "the storehouse kept less than " .. amount end
            return true
        end
    end
    return nil, "no storehouse"
end

-- The data folder lies next to the Scripts folder of the mod. UE4SS puts that Scripts folder on package.path.
function M.data_path(relative)
    for entry in string.gmatch(package.path, "[^;]+") do
        local scripts = entry:gsub("\\", "/"):match("^(.*)/Scripts/%?%.lua$")
        if scripts and scripts:find("InvasionMod", 1, true) then return scripts .. "/" .. relative end
    end
    error("liege contracts: the Scripts folder of the mod is not on package.path", 0)
end

M.STOREHOUSE_TYPE = STOREHOUSE_TYPE

return M
