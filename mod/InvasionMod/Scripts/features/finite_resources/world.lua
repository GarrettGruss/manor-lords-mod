-- Game access of the finite resources feature (M10). Every call runs on the game thread.
local core = require("ManorCore")

local M = {}

-- The result of getGoodsProducedOver is a table in the game and in the fake game. Its keys and values can be RemoteUnrealParam values (real game, run 20261018-103029-1c81).
local function plain(value)
    if type(value) == "number" then return value end
    local ok, inner = pcall(function() return value:get() end)
    if ok then return inner end
    return value
end

local function add_map(totals, map)
    local function add(key, value)
        local good, amount = plain(key), plain(value)
        if type(good) == "number" and type(amount) == "number" then totals[good] = (totals[good] or 0) + amount end
    end
    if type(map) == "table" then
        for key, value in pairs(map) do add(key, value) end
        return
    end
    map:ForEach(add)
end

-- Units produced for each good by the buildings of the player region over `window_days` (a total of all buildings now standing).
function M.produced_by_good(window_days)
    local region = core.player_region()
    if region == nil then return nil end
    local totals = {}
    for _, building in ipairs(core.listOf(core.read(function() return region:GetBuildings() end))) do
        local tracker = core.read(function() return building.ProductionTrackerComponent end)
        if core.isValid(tracker) then
            local ok, map = pcall(function() return tracker:getGoodsProducedOver(window_days) end)
            if ok and map ~= nil then add_map(totals, map) end
        end
    end
    return totals
end

-- The player production limit of one good (the game rule behind the workplace limits screen). Limit 0 means: produce nothing.
function M.set_limit(good, amount)
    local region = core.player_region()
    if region == nil then return nil, "no player region" end
    local ok, err = pcall(function() region:setProductionLimit(good, amount) end)
    if not ok then return nil, tostring(err) end
    return true
end

function M.clear_limit(good)
    local region = core.player_region()
    if region == nil then return nil, "no player region" end
    local ok, err = pcall(function() region:setProductionUnlimited(good) end)
    if not ok then return nil, tostring(err) end
    return true
end

-- The limit of a good, or nil when the good is not limited.
function M.limit_of(good)
    local region = core.player_region()
    if region == nil then return nil end
    local limited = core.read(function() return region:isProductionLimited(good) end)
    if limited ~= true then return nil end
    return core.read(function() return region:getProductionLimit(good, -1) end)
end

return M
