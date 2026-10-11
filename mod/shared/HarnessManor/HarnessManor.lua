-- HarnessManor: read the manor of the player village and keep goods in it (spec 12, criterion M1).
-- Why: the Invasion Mode plan needs a place that holds supplies and can be raided. The manor is the Keep (EBuildingType 57) and its modules.
--
-- Game facts (real game, 2026-10-11, see docs/specs/12-manor-exploration/implementation-notes/):
--   The manor is one SMBuildingMaster per module. The Keep site is placed with the real mouse (action place_building, type 57).
--   `Region.manor` holds one object. A region has at most one manor.
--   A Keep needs 40 builder units, so the 5 families of the test village never finish it ("not_enough_workers").
--   `finish_site` is a harness shortcut: it writes `Data.constructed = true` and calls `RTSMultiEngineCPP:setRegionsManor`.
--   Goods: `SMBuildingMaster:addToInventory(Good)` adds goods to the building and to the region stock.
--   `consumeGoodNoCheck(good)` removes one unit. The base game does not treat the Keep as a store (`isStorageTypeBuilding` is false),
--   so this is a mod-defined store on top of the building inventory. The capacity (M.CAPACITY) is a mod rule.
--
-- Rules: call only on the game thread. No save function. Every input is checked. A change is read back.

local sack = require("HarnessSack")

local M = {}

M.MAX_GOOD = 200
M.MAX_AMOUNT = 1000
M.CAPACITY = 200   -- units of goods that one manor module holds through put (mod rule)
M.MAX_ROWS = 20
-- EBuildingType values of the manor and its modules: Walls, Keep Lv1, TaxOffice, Palace/Gatehouse/Keep Lv3, Gate Lv1, Palace Lv1,
-- OuterTower Lv1, Palace Lv2, Keep Lv2, stone walls, Gate Lv2, OuterTower Lv2.
M.MANOR_TYPES = { [50] = true, [57] = true, [58] = true, [81] = true, [82] = true, [83] = true, [95] = true, [98] = true,
                  [472] = true, [474] = true, [475] = true, [476] = true, [477] = true, [478] = true, [479] = true }

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

local function typeOf(building) return read(function() return building.Data.bType end) end
local function isBuilt(building) return read(function() return building:IsConstructed() end) == true end

local function idOf(building)
    local name = read(function() return building:GetFullName() end) or ""
    return tonumber(name:match("_(%d+)$"))
end

local function manorBuildings(region)
    local out = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) and M.MANOR_TYPES[typeOf(building)] then out[#out + 1] = building end
    end
    return out
end

-- The goods of one building: a list of { good, amount } and the total number of units.
local function goodsOf(building)
    local goods, total = {}, 0
    for _, entry in ipairs(listOf(building.Inventory)) do
        local good, amount = read(function() return entry.Type end), read(function() return entry.amt end)
        if good and amount and amount > 0 then
            goods[#goods + 1] = { good = good, amount = amount }
            total = total + amount
        end
    end
    return goods, total
end

local function amountOf(building, good)
    local goods = goodsOf(building)
    for _, entry in ipairs(goods) do if entry.good == good then return entry.amount end end
    return 0
end

local function regionManor(region)
    local manor = read(function() return region.manor end)
    if isValid(manor) then return manor end
    return nil
end

local function row(building, region)
    local goods, total = goodsOf(building)
    local manor = regionManor(region)
    return { id = idOf(building), type = typeOf(building), built = isBuilt(building), goods = goods, total = total,
             capacity = M.CAPACITY, is_region_manor = manor ~= nil and idOf(manor) == idOf(building) }
end

local function pick(region, request)
    local candidates = manorBuildings(region)
    if request.manor ~= nil then
        for _, building in ipairs(candidates) do
            if idOf(building) == request.manor then return building end
        end
        return nil, "no manor module with id " .. tostring(request.manor)
    end
    for _, building in ipairs(candidates) do
        if isBuilt(building) then return building end
    end
    return nil, "no built manor module in the village"
end

local function checkedGood(request)
    local good = request.good
    if good == nil or good < 0 or good > M.MAX_GOOD then return nil, "good must be an item number up to " .. M.MAX_GOOD end
    return good
end

local function checkedAmount(request)
    local amount = request.amount
    if amount == nil or amount < 1 or amount > M.MAX_AMOUNT then return nil, "amount must be from 1 to " .. M.MAX_AMOUNT end
    return amount
end

-- The manor modules of the player village, with their goods.
function M.manor_state()
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local rows = {}
    for _, building in ipairs(manorBuildings(region)) do
        if #rows < M.MAX_ROWS then rows[#rows + 1] = row(building, region) end
    end
    local manor = regionManor(region)
    return { ok = true, count = #rows, modules = rows, region_has_manor = manor ~= nil, region_manor_id = manor and idOf(manor) or nil }
end

-- Harness shortcut: finish a Keep site at once and register it as the manor of the region.
function M.finish_site(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local kind = request.type
    if not kind or not M.MANOR_TYPES[kind] then return { ok = false, error = "type must be a manor type" } end
    local site
    for _, building in ipairs(manorBuildings(region)) do
        if typeOf(building) == kind and not isBuilt(building) then site = building; break end
    end
    if not site then return { ok = false, error = "no unfinished manor module of type " .. kind } end
    local ok, err = pcall(function()
        site.Data.constructed = true
        site.constructionGoods:Empty()
    end)
    if not ok then return { ok = false, error = "finish: " .. tostring(err) } end
    if not isBuilt(site) then return { ok = false, error = "the site is still not built after the write" } end
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local set, setErr = pcall(function() engine:setRegionsManor(site) end)
    if not set then return { ok = false, error = "setRegionsManor: " .. tostring(setErr) } end
    return { ok = true, module = row(site, region) }
end

-- Put goods into a built manor module. Refused above the capacity.
function M.manor_put(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local good, goodProblem = checkedGood(request)
    if not good then return { ok = false, error = goodProblem } end
    local amount, amountProblem = checkedAmount(request)
    if not amount then return { ok = false, error = amountProblem } end
    local manor, pickProblem = pick(region, request)
    if not manor then return { ok = false, error = pickProblem } end
    if not isBuilt(manor) then return { ok = false, error = "the manor module is not built" } end
    local _, total = goodsOf(manor)
    if total + amount > M.CAPACITY then
        return { ok = false, error = "the manor holds " .. total .. " of " .. M.CAPACITY .. " units; " .. amount .. " more do not fit" }
    end
    local before = amountOf(manor, good)
    local stockBefore = read(function() return region:getStockOfGood(good, false, false) end)
    local ok, err = pcall(function() manor:addToInventory({ Type = good, amt = amount }) end)
    if not ok then return { ok = false, error = "addToInventory: " .. tostring(err) } end
    return { ok = true, id = idOf(manor), good = good, before = before, after = amountOf(manor, good), wanted = amount,
             stock_before = stockBefore, stock_after = read(function() return region:getStockOfGood(good, false, false) end) }
end

-- Take goods out of a manor module. Refused when it holds less than the amount.
function M.manor_take(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local good, goodProblem = checkedGood(request)
    if not good then return { ok = false, error = goodProblem } end
    local amount, amountProblem = checkedAmount(request)
    if not amount then return { ok = false, error = amountProblem } end
    local manor, pickProblem = pick(region, request)
    if not manor then return { ok = false, error = pickProblem } end
    local before = amountOf(manor, good)
    if before < amount then
        return { ok = false, error = "the manor holds only " .. before .. " of good " .. good .. "; " .. amount .. " were asked" }
    end
    local stockBefore = read(function() return region:getStockOfGood(good, false, false) end)
    for _ = 1, amount do
        local ok, err = pcall(function() manor:consumeGoodNoCheck(good) end)
        if not ok then return { ok = false, error = "consumeGoodNoCheck: " .. tostring(err) } end
    end
    return { ok = true, id = idOf(manor), good = good, before = before, after = amountOf(manor, good), wanted = amount,
             stock_before = stockBefore, stock_after = read(function() return region:getStockOfGood(good, false, false) end) }
end

return M
