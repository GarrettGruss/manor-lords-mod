-- HarnessBuild: read the goods that a construction site needs, ruin a building, clear ruins, and lower the cost of a site (spec 10, spike R8).
-- Why: the base game has no repair or rebuild cost. A burned building becomes Rubble (type 75). The player demolishes the rubble and places a new
-- building. The new site lists the goods it needs in `SMBuildingMaster.constructionGoods` (entries with `Type` and `amt`).
-- Measured in the real game (spike-R8.md): a Dunghill site needs Planks (item 17) x 4, the stock falls by 4 when the building is built,
-- and a lower `amt` written to the site makes the builders use less (4 -> 2 used 2 planks). A mod can use this for a partial rebuild cost.
--
-- Rules: call only on the game thread. No save function. Every input is checked. A cost can only be lowered, never raised.
-- Placing a site needs the real OS mouse (action place_building). This module does not place buildings.

local sack = require("HarnessSack")

local M = {}

M.MAX_TYPE = 70000
M.MAX_GOOD = 200
M.MAX_ROWS = 40
M.METHODS = { fire = "StartFire", collapse = "collapseBuilding" }

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
    if type(array) == "table" then
        for i = 1, #array do out[#out + 1] = unwrap(array[i]) end
        return out
    end
    local count = read(function() return array:GetArrayNum() end) or 0
    for i = 1, count do out[#out + 1] = unwrap(array[i]) end
    return out
end

local function buildingsOf(region)
    local out = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) then out[#out + 1] = building end
    end
    return out
end

local function typeOf(building) return read(function() return building.Data.bType end) end
local function isRubble(building) return read(function() return building:IsRubble() end) == true end
local function isBuilt(building) return read(function() return building:IsConstructed() end) == true end

local function idOf(building)
    local name = read(function() return building:GetFullName() end) or ""
    return tonumber(name:match("_(%d+)$"))
end

-- What a site still needs: a list of { good, amount }. Built buildings have an empty list.
local function needsOf(building)
    local out = {}
    for _, entry in ipairs(listOf(building.constructionGoods)) do
        out[#out + 1] = { good = read(function() return entry.Type end), amount = read(function() return entry.amt end) }
    end
    return out
end

local function row(building)
    return { id = idOf(building), type = typeOf(building), built = isBuilt(building), rubble = isRubble(building),
             burning = read(function() return building.onFire end) == true, needs = needsOf(building) }
end

local function checkedType(request)
    local kind = request.type
    if not kind or kind > M.MAX_TYPE then return nil, "type must be a building type number up to " .. M.MAX_TYPE end
    return kind
end

local function firstWhere(region, kind, wanted)
    for _, building in ipairs(buildingsOf(region)) do
        if typeOf(building) == kind and wanted(building) then return building end
    end
    return nil
end

local function counts(region, kind)
    local out = { built = 0, sites = 0 }
    for _, building in ipairs(buildingsOf(region)) do
        if typeOf(building) == kind and not isRubble(building) then
            if isBuilt(building) then out.built = out.built + 1 else out.sites = out.sites + 1 end
        end
    end
    out.rubble = read(function() return region:getBuildingCount(sack.RUBBLE_TYPE, false) end) or 0
    return out
end

-- Buildings of the player village: all of them, or one type when "type" is given.
function M.building_sites(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local rows, total = {}, 0
    for _, building in ipairs(buildingsOf(region)) do
        if request.type == nil or typeOf(building) == request.type then
            total = total + 1
            if #rows < M.MAX_ROWS then rows[#rows + 1] = row(building) end
        end
    end
    local answer = { ok = true, total = total, buildings = rows }
    if request.type then answer.counts = counts(region, request.type) end
    return answer
end

-- Burn ("fire") or collapse the first built building of one type. It becomes Rubble (type 75).
function M.ruin_building(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local kind, typeProblem = checkedType(request)
    if not kind then return { ok = false, error = typeProblem } end
    local call = M.METHODS[request.method or "collapse"]
    if not call then return { ok = false, error = "method must be fire or collapse" } end
    local building = firstWhere(region, kind, function(b) return isBuilt(b) and not isRubble(b) end)
    if not building then return { ok = false, error = "no built building of type " .. kind } end
    local before = counts(region, kind)
    local ok, err = pcall(function() building[call](building) end)
    if not ok then return { ok = false, error = call .. ": " .. tostring(err) } end
    return { ok = true, id = idOf(building), method = request.method or "collapse", before = before, after = counts(region, kind),
             rubble_now = isRubble(building) }
end

-- Demolish every ruin of the village, so the place is free for a new site.
function M.demolish_ruins()
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local before = read(function() return region:getBuildingCount(sack.RUBBLE_TYPE, false) end) or 0
    local demolished = 0
    for _, building in ipairs(buildingsOf(region)) do
        if isRubble(building) then
            local ok, err = pcall(function() building:demolish(true) end)
            if not ok then return { ok = false, error = "demolish: " .. tostring(err) } end
            demolished = demolished + 1
        end
    end
    return { ok = true, before = before, demolished = demolished,
             after = read(function() return region:getBuildingCount(sack.RUBBLE_TYPE, false) end) or 0 }
end

-- Lower the amount of one good that a site of `type` still needs. The amount may be 0 and may not be above the current one.
function M.set_site_cost(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local kind, typeProblem = checkedType(request)
    if not kind then return { ok = false, error = typeProblem } end
    if not request.good or request.good > M.MAX_GOOD then return { ok = false, error = "good must be an item number up to " .. M.MAX_GOOD } end
    if request.amount == nil then return { ok = false, error = "amount is required" } end
    local site = firstWhere(region, kind, function(b) return not isBuilt(b) and not isRubble(b) end)
    if not site then return { ok = false, error = "no construction site of type " .. kind } end
    for _, entry in ipairs(listOf(site.constructionGoods)) do
        if read(function() return entry.Type end) == request.good then
            local before = read(function() return entry.amt end)
            if request.amount > before then return { ok = false, error = "the cost can only be lowered: " .. before .. " to " .. request.amount } end
            local ok, err = pcall(function() entry.amt = request.amount end)
            if not ok then return { ok = false, error = "write amt: " .. tostring(err) } end
            local after = needsOf(site)
            return { ok = true, id = idOf(site), good = request.good, before = before, wanted = request.amount, needs = after }
        end
    end
    return { ok = false, error = "the site of type " .. kind .. " does not need good " .. request.good }
end

return M
