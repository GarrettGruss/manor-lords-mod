-- Game access of the tribute feature: the rich resources of each region (change update-vassal-tribute-rich-resources).
-- Reads only the decal material, the decal size and position, and the class and capacity of the clumps of each ResourceNode.
-- It never reads a struct with soft object fields (see DANGEROUS_ACTIONS.md). Every call runs on the game thread.
local core = require("ManorCore")
local rules = require("features.tribute.rules")

local TAG = "InvasionMod.tribute"
local M = {}

local cache = { engine = nil, regions = nil } -- region object name -> set of good names, valid for one engine object (one loaded game)
local scans = 0

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if core.isValid(found) then return found end
    return nil
end

local function name_of(object)
    if object == nil then return nil end
    return core.read(function() return object:GetFName():ToString() end)
end

local function read_node(node)
    local decal = core.read(function() return node.ResourceZoneDecal end)
    local data = { clumps = {} }
    if core.isValid(decal) then
        local material = core.read(function() return decal:GetDecalMaterial() end)
        if core.isValid(material) then data.material = name_of(material) end
        data.decal_x = core.read(function() return decal.DecalSize.X end)
        data.position = core.read(function()
            local at = decal:K2_GetComponentLocation()
            return { X = at.X, Y = at.Y, Z = at.Z }
        end)
    end
    for _, clump in ipairs(core.listOf(core.read(function() return node.resourceClumps end))) do
        if core.isValid(clump) then
            local class = core.read(function() return clump:GetClass():GetFName():ToString() end)
            local capacity = core.read(function() return clump.capacity end)
            if class and type(capacity) == "number" then data.clumps[#data.clumps + 1] = { class = class, capacity = capacity } end
        end
    end
    return data
end

local function scan(e, rich)
    local regions, count = {}, 0
    for _, node in ipairs(FindAllOf("ResourceNode") or {}) do
        local data = read_node(node)
        local goods = rules.node_goods(data, rich)
        if #goods > 0 and data.position then
            local region = core.read(function() return e:getRegionByPos(data.position, true) end)
            local key = core.isValid(region) and core.shortName(region)
            if key then
                regions[key] = regions[key] or {}
                for _, good in ipairs(goods) do regions[key][good] = true end
            end
        end
        count = count + 1
    end
    scans = scans + 1
    return regions, count
end

-- The set of rich good names (name -> true) of a region (object name such as "immenreuth"), or nil when the game is not there.
-- The first call after a game load reads all nodes; later calls use the cache.
function M.rich_goods(region, rich)
    local e = engine()
    if e == nil then return nil end
    if cache.engine ~= e or cache.regions == nil then
        local regions, count = scan(e, rich)
        if count == 0 then -- no node loaded yet: pay the fill goods this time, but do not cache
            core.log.warn(TAG, "TRIBUTE no resource node found: the region pays the fill goods, nothing is cached")
            return {}
        end
        cache.engine, cache.regions = e, regions
        core.log.info(TAG, string.format("TRIBUTE scanned %d resource nodes", count))
    end
    return cache.regions[region] or {}
end

function M.scan_count() return scans end

return M
