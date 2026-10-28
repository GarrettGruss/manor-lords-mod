-- Game access of the tech tree feature (M12). Every call runs on the game thread.
local core = require("ManorCore")

local M = {}

function M.settlement_level()
    local region = core.player_region()
    if region == nil then return nil end
    local ok, value = pcall(function() return region.settlementLevel end)
    if ok and type(value) == "number" then return math.floor(value) end
    return nil
end

-- The squads the player commands. TBD: this is the count that "garrison" means for Fear of the Lord (M13 may refine it).
function M.garrison_squads()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if engine == nil or not engine:IsValid() then return nil end
    local ok, value = pcall(function() return engine.playerRef.commandedSquads:GetArrayNum() end)
    if ok and type(value) == "number" then return value end
    return nil
end

function M.current_day()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if engine == nil or not engine:IsValid() then return nil end
    local ok, value = pcall(function() return engine.TemporalComponent.daysTotal end)
    if ok and type(value) == "number" then return math.floor(value) end
    return nil
end

local HOME_TYPE = 3        -- EBuildingType of a burgage plot (spike militia-weapon-rebellion, q3)
local STOREHOUSE_TYPES = { 6, 72 } -- storehouse first, then granary (the tier 1 stores of raid_behavior; the spike fixture had type 72)

-- The homes and the first tier 1 store of the player region. Returns homes (list) and storehouse (or nil), or nil and a message.
local function homes_and_store()
    local region = core.player_region()
    if region == nil then return nil, "no player region" end
    local homes, stores = {}, {}
    for _, building in ipairs(core.listOf(region:GetBuildings())) do
        if core.isValid(building) and core.read(function() return building:IsRubble() end) ~= true then
            local kind = core.read(function() return building.Data.bType end)
            if kind == HOME_TYPE then homes[#homes + 1] = building else stores[kind] = stores[kind] or building end
        end
    end
    for _, kind in ipairs(STOREHOUSE_TYPES) do
        if stores[kind] then return homes, stores[kind] end
    end
    return homes, nil
end

local function amount_of(building, good)
    local total = 0
    for _, row in ipairs(core.listOf(building.Inventory)) do
        if core.read(function() return row.Type end) == good then total = total + (core.read(function() return row.amt end) or 0) end
    end
    return total
end

-- Test: how much of one good the homes and the store hold, and put goods into the first home.
function M.home_goods(good)
    local homes, store = homes_and_store()
    if homes == nil then return nil, store end
    local in_homes = 0
    for _, home in ipairs(homes) do in_homes = in_homes + amount_of(home, good) end
    return { homes = in_homes, store = store and amount_of(store, good) or nil, home_count = #homes }
end

function M.fill_home(good, amount)
    local homes = homes_and_store()
    if homes == nil or homes[1] == nil then return nil, "no home" end
    local ok, why = pcall(function() homes[1]:addToInventory({ Type = good, amt = amount }) end)
    if not ok then return nil, tostring(why) end
    return true
end

-- Disarm the Peasantry: move every good with an id in `weapon_ids` from the homes to the first storehouse
-- (consumeGoodNoCheck removes one unit, addToInventory adds to the storehouse; both proven in the rebellion spike).
-- Returns { moved = { [good] = amount }, missed = n } or nil and a message.
function M.disarm_homes(weapon_ids)
    local wanted = {}
    for _, id in ipairs(weapon_ids) do wanted[id] = true end
    local homes, storehouse = homes_and_store()
    if homes == nil then return nil, storehouse end
    if storehouse == nil then return nil, "no storehouse" end
    local moved, missed = {}, 0
    for _, home in ipairs(homes) do
        local held = {}
        for _, good in ipairs(core.listOf(home.Inventory)) do
            local kind, amount = core.read(function() return good.Type end), core.read(function() return good.amt end)
            if wanted[kind] and type(amount) == "number" and amount > 0 then held[#held + 1] = { kind = kind, amount = amount } end
        end
        for _, row in ipairs(held) do
            for _ = 1, row.amount do
                if pcall(function() home:consumeGoodNoCheck(row.kind) end) then moved[row.kind] = (moved[row.kind] or 0) + 1 else missed = missed + 1 end
            end
        end
    end
    for kind, amount in pairs(moved) do
        local ok = pcall(function() storehouse:addToInventory({ Type = kind, amt = amount }) end)
        if not ok then missed = missed + amount; moved[kind] = nil end
    end
    return { moved = moved, missed = missed }
end

-- The data folder lies next to the Scripts folder of the mod. UE4SS puts that Scripts folder on package.path.
function M.data_path(relative)
    for entry in string.gmatch(package.path, "[^;]+") do
        local scripts = entry:gsub("\\", "/"):match("^(.*)/Scripts/%?%.lua$")
        if scripts and scripts:find("InvasionMod", 1, true) then return scripts .. "/" .. relative end
    end
    error("tech tree: the Scripts folder of the mod is not on package.path", 0)
end

return M
