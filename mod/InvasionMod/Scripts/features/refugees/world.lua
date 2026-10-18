-- Game access of the refugees feature (M09). Every call runs on the game thread.
local core = require("ManorCore")

local M = {}

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if core.isValid(found) then return found end
    return nil
end

function M.current_day()
    local e = engine()
    if e == nil then return nil end
    local ok, value = pcall(function() return e.TemporalComponent.daysTotal end)
    if ok and type(value) == "number" then return math.floor(value) end
    return nil
end

local function region_object(name)
    local e = engine()
    if e == nil then return nil end
    for _, region in ipairs(core.listOf(e.regions)) do
        if core.shortName(region) == name then return region end
    end
    return nil
end

-- Families, homeless families and approval of one region. Nil when the region is not found.
function M.numbers(name)
    local region = region_object(name)
    if region == nil then return nil end
    return {
        families = core.read(function() return region:getTotalNumFamilies() end),
        homeless = core.read(function() return region:getNumHomelessFamilies() end),
        approval = core.read(function() return region.Approval end),
    }
end

-- The first usable camp: the woods, else near the village, else nil (the game uses the settled centre).
local function camp_spot()
    local woods = core.read(function() return core.forest_spot({}) end)
    if woods and woods.ok and woods.spots and woods.spots[1] then return woods.spots[1], "woods" end
    local near = core.read(function() return core.tent_find_spot() end)
    if near and near.ok and near.spots and near.spots[1] then return near.spots[1], "village" end
    return nil, "centre"
end

local function region_row(name)
    for _, row in ipairs(core.regions_state().regions or {}) do
        if row.region == name then return row end
    end
    return nil
end

-- `calls` settleRegion calls on the home region. Returns the number of calls that worked and the camp place.
function M.send_settlers(home, calls)
    local row = region_row(home)
    if row == nil then return nil, "no row for region " .. tostring(home) end
    local spot, place = camp_spot()
    local done = 0
    for _ = 1, calls do
        local request = { target = 0, region = home, type = row.settlement_type or 1, supply = 0 }
        if spot then request.x, request.y, request.z = spot.x, spot.y, spot.z end
        local answer = core.settle_region(request)
        if not answer.ok then
            if done == 0 then return nil, "settleRegion refused: " .. tostring(answer.error) end
            break
        end
        done = done + 1
    end
    return done, place
end

return M
