-- HarnessSack: primitives to take a share of a village away: buildings, goods, people (spec 10, spike S6).
local core = require("ManorCore")

-- Each function takes a request table (numbers and words, already checked) and returns a result table.
-- Every change is read back: the census of the player village is taken before and after.
-- Rules: no eval, no save function, only the game calls listed here. Call only on the game thread.
--
-- Game facts (real game, 2026-10-10, see docs/harness/10-invasion-testability/implementation-notes/spike-S6.md):
--   Building: SMBuildingMaster:StartFire() burns it for a while, then it becomes type Rubble (75).
--             SMBuildingMaster:collapseBuilding() makes it Rubble at once. IsRubble() is true for both.
--             A burned or collapsed building keeps its place in Region:GetBuildings() until it is demolished.
--   Goods:    SMBuildingMaster:consumeGoodNoCheck(goodType) removes one unit from that building and from the region stock.
--   People:   SMUnit:just_die() on every member of a family. The family and its members leave the counts at once.

local M = {}

M.MAX_GOODS_REMOVED = 5000   -- one call never removes more units of goods than this
M.MAX_PERCENT = 100
M.RUBBLE_TYPE = 75           -- EBuildingType::Rubble
M.HUMAN_ROLES = { [0] = true, [1] = true, [2] = true, [3] = true }   -- Husband, Wife, Son, Daughter

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

-- A TArray element can be a wrapper that needs :get(). Unwrap it only if that works.
local function unwrap(element)
    local ok, inner = pcall(function() return element:get() end)
    if ok and inner ~= nil then return inner end
    return element
end

-- A property array is a TArray (GetArrayNum). The array that a function returns is a plain Lua table.
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

-- Round half up. A percent of a count gives a whole number of things.
function M.share(total, percent)
    return math.floor(total * percent / 100 + 0.5)
end

---------------------------------------------------------------------------------------------
-- The village of the player
---------------------------------------------------------------------------------------------

-- The region whose owner is the player pawn. The region the pawn stands in can be an AI region.
M.playerRegion = core.player_region

local function buildingId(building)
    local name = read(function() return building:GetFullName() end) or ""
    return tonumber(name:match("_(%d+)$"))
end

local function buildingType(building)
    return read(function() return building.Data.bType end)
end

local function isRubble(building)
    return read(function() return building:IsRubble() end) == true
end

-- Goods of one building: map good type -> amount.
local function goodsOf(building)
    local out = {}
    for _, good in ipairs(listOf(building.Inventory)) do
        local kind, amount = read(function() return good.Type end), read(function() return good.amt end)
        if kind and amount and amount > 0 then out[kind] = (out[kind] or 0) + amount end
    end
    return out
end

local function sumOf(goods)
    local total = 0
    for _, amount in pairs(goods) do total = total + amount end
    return total
end

-- The buildings of the village in the order of the game.
local function buildingsOf(region)
    local out = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) then out[#out + 1] = building end
    end
    return out
end

-- Standing buildings: not rubble. The ones a sack can take.
local function standing(buildings)
    local out = {}
    for _, building in ipairs(buildings) do
        if not isRubble(building) then out[#out + 1] = building end
    end
    return out
end

---------------------------------------------------------------------------------------------
-- Census (read only)
---------------------------------------------------------------------------------------------

local function censusBuildings(buildings)
    local counts = { total = #buildings, standing = 0, rubble = 0, burning = 0 }
    local stores = {}
    for _, building in ipairs(buildings) do
        if isRubble(building) then counts.rubble = counts.rubble + 1 else counts.standing = counts.standing + 1 end
        if read(function() return building.onFire end) == true then counts.burning = counts.burning + 1 end
        local goods = goodsOf(building)
        if next(goods) ~= nil then
            stores[#stores + 1] = { id = buildingId(building), type = buildingType(building), goods = sumOf(goods), by_good = goods }
        end
    end
    table.sort(stores, function(a, b) return (a.id or 0) < (b.id or 0) end)
    return counts, stores
end

local function censusStock(region)
    local by_good, total = {}, 0
    for _, good in ipairs(listOf(region:getStock(false))) do
        local kind, amount = read(function() return good.Type end), read(function() return good.amt end)
        if kind and amount and amount > 0 then
            by_good[kind] = (by_good[kind] or 0) + amount
            total = total + amount
        end
    end
    return { total = total, by_good = by_good }
end

local function censusPeople(region)
    return { families = read(function() return region:getTotalNumFamilies() end),
             population = read(function() return region:getNumTotalPopulation() end) }
end

-- The state of the village: buildings by state, stock, stores (buildings that hold goods), people.
function M.census()
    local region, problem = M.playerRegion()
    if not region then return nil, problem end
    local buildings = buildingsOf(region)
    local counts, stores = censusBuildings(buildings)
    return { buildings = counts, stock = censusStock(region), stores = stores, people = censusPeople(region),
             region = read(function() return region.regionName:ToString() end) }
end

---------------------------------------------------------------------------------------------
-- Buildings
---------------------------------------------------------------------------------------------

local METHODS = { fire = "StartFire", collapse = "collapseBuilding" }
M.METHODS = METHODS

-- Take `count` standing buildings out of use, in the order of the game. method: "fire" or "collapse".
function M.destroy_buildings(region, count, method)
    local call = METHODS[method]
    if not call then return nil, "method must be fire or collapse" end
    local hit = 0
    for _, building in ipairs(standing(buildingsOf(region))) do
        if hit >= count then break end
        local ok, err = pcall(function() building[call](building) end)
        if not ok then return nil, call .. ": " .. tostring(err) end
        hit = hit + 1
    end
    return hit
end

---------------------------------------------------------------------------------------------
-- Goods
---------------------------------------------------------------------------------------------

-- Remove up to `amount` units of one good from one building. Returns the units removed.
local function takeFromBuilding(building, goodType, amount)
    local removed = 0
    while removed < amount do
        local before = goodsOf(building)[goodType] or 0
        if before <= 0 then break end
        local ok = pcall(function() building:consumeGoodNoCheck(goodType) end)
        if not ok then break end
        local after = goodsOf(building)[goodType] or 0
        if after >= before then break end   -- the game refused: stop instead of looping
        removed = removed + (before - after)
    end
    return removed
end

-- Remove up to `amount` units of one good from the village, building by building. storeId limits it to one building.
function M.remove_goods(region, goodType, amount, storeId)
    local budget = math.min(amount, M.MAX_GOODS_REMOVED)
    local removed = 0
    for _, building in ipairs(buildingsOf(region)) do
        if removed >= budget then break end
        if storeId == nil or buildingId(building) == storeId then
            removed = removed + takeFromBuilding(building, goodType, budget - removed)
        end
    end
    return removed
end

-- Remove `percent` of every good in the stock (each good is rounded on its own).
-- storeId limits it to the goods of one building (a raid trip to one store).
function M.remove_stock_share(region, percent, storeId)
    local removed, budget = 0, M.MAX_GOODS_REMOVED
    local goods
    if storeId == nil then
        goods = censusStock(region).by_good
    else
        goods = M.storeGoods(region, storeId)
        if goods == nil then return nil, "no building with id " .. tostring(storeId) end
    end
    local kinds = {}
    for kind in pairs(goods) do kinds[#kinds + 1] = kind end
    table.sort(kinds)
    for _, kind in ipairs(kinds) do
        local want = math.min(M.share(goods[kind], percent), budget - removed)
        if want > 0 then removed = removed + M.remove_goods(region, kind, want, storeId) end
    end
    return removed
end

-- The goods of one building by its id, or nil when the village has no such building.
function M.storeGoods(region, storeId)
    for _, building in ipairs(buildingsOf(region)) do
        if buildingId(building) == storeId then return goodsOf(building) end
    end
    return nil
end

---------------------------------------------------------------------------------------------
-- People
---------------------------------------------------------------------------------------------

-- Where the first `count` families live: the position of the family home, else of the first member (spec 15, rebellion).
-- Same order as remove_families, so row i is the family that remove_families removes as number i.
function M.family_homes(region, count)
    local rows = {}
    for _, family in ipairs(listOf(region.workerFamilies)) do
        if #rows >= count then break end
        local at = read(function() return family.familyHome:K2_GetActorLocation() end)
        local source = "home"
        if not at then
            for _, member in ipairs(listOf(family.familyMembers)) do
                at = isValid(member) and read(function() return member.realPos end) or nil
                if at then source = "member"; break end
            end
        end
        local x, y, z = at and read(function() return at.X end), at and read(function() return at.Y end), at and read(function() return at.Z end)
        rows[#rows + 1] = x and { x = x, y = y, z = z, source = source } or { source = "unknown" }
    end
    return rows
end

-- The living members of the first `count` families, at most `limit` units (spec 15, turnToBandit on family members).
function M.family_members(region, count, limit)
    local rows, seen = {}, { families = 0, members = 0, dead = 0, invalid = 0 }
    for index, family in ipairs(listOf(region.workerFamilies)) do
        if index > count then break end
        seen.families = seen.families + 1
        for _, member in ipairs(listOf(family.familyMembers)) do
            seen.members = seen.members + 1
            if not isValid(member) then seen.invalid = seen.invalid + 1
            elseif read(function() return member.dead end) == true then seen.dead = seen.dead + 1
            elseif #rows < limit then rows[#rows + 1] = member end
        end
    end
    return rows, seen
end

-- Kill every member of `count` families (the first ones in the list). Returns families and people removed.
M.remove_families = core.remove_families

---------------------------------------------------------------------------------------------
-- Commands (called by HarnessActions)
---------------------------------------------------------------------------------------------

local function percentOf(request, name)
    local value = request[name] or 0
    if value < 0 or value > M.MAX_PERCENT then return nil, name .. " must be 0 to " .. M.MAX_PERCENT end
    return value
end

function M.sack_census()
    local census, problem = M.census()
    if not census then return { ok = false, error = problem } end
    return { ok = true, census = census }
end

-- Burn or collapse `count` standing buildings (or `percent` of them).
function M.sack_buildings(request)
    local region, problem = M.playerRegion()
    if not region then return { ok = false, error = problem } end
    local before = M.census()
    local count = request.count or M.share(before.buildings.standing, request.percent or 0)
    local hit, err = M.destroy_buildings(region, count, request.method or "collapse")
    if not hit then return { ok = false, error = err } end
    return { ok = true, wanted = count, hit = hit, method = request.method or "collapse", before = before, after = M.census() }
end

-- Remove goods: `amount` of `good` (from one building when `store` is given), or `percent` of every good (of one building when `store` is given).
function M.sack_goods(request)
    local region, problem = M.playerRegion()
    if not region then return { ok = false, error = problem } end
    local before = M.census()
    local removed
    if request.good then
        if not request.amount then return { ok = false, error = "good needs amount" } end
        removed = M.remove_goods(region, request.good, request.amount, request.store)
    else
        local err
        removed, err = M.remove_stock_share(region, request.percent or 0, request.store)
        if not removed then return { ok = false, error = err } end
    end
    return { ok = true, removed = removed, before = before, after = M.census() }
end

-- Kill `count` families (or `percent` of them).
function M.sack_people(request)
    local region, problem = M.playerRegion()
    if not region then return { ok = false, error = problem } end
    local before = M.census()
    local count = request.count or M.share(before.people.families or 0, request.percent or 0)
    local families, people = M.remove_families(region, count)
    return { ok = true, wanted = count, families = families, people = people, before = before, after = M.census() }
end

-- All three at once. Goods first: a fire takes the goods of a burning building by itself.
function M.sack_village(request)
    local region, problem = M.playerRegion()
    if not region then return { ok = false, error = problem } end
    local buildingsPercent, e1 = percentOf(request, "buildings_pct")
    local stockPercent, e2 = percentOf(request, "stock_pct")
    local peoplePercent, e3 = percentOf(request, "people_pct")
    if not (buildingsPercent and stockPercent and peoplePercent) then return { ok = false, error = e1 or e2 or e3 } end
    local before = M.census()
    local goodsRemoved = M.remove_stock_share(region, stockPercent)
    local families, people = M.remove_families(region, M.share(before.people.families or 0, peoplePercent))
    local hit, err = M.destroy_buildings(region, M.share(before.buildings.standing, buildingsPercent), request.method or "collapse")
    if not hit then return { ok = false, error = err } end
    return { ok = true, buildings_hit = hit, goods_removed = goodsRemoved, families_removed = families, people_removed = people,
             method = request.method or "collapse", before = before, after = M.census() }
end

return M
