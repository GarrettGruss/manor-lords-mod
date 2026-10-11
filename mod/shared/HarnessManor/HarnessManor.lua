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
--
-- Worker slots (spec 12, question Q7, see implementation-notes/worker-slots.md):
--   The base game takes the number of worker families (`getMaxWorkerFamilies`) and the role (`getJobType`) of a building from the DataTable
--   `/Game/NotStronghold/Data/buildingStats`. The row name is the building type id. Fields: `workerTypes.Y` (slots), `job` (EJobType), `isWork`,
--   `buildingFunction`, `storageLimitGeneric`. A Storehouse (72) has job 45 and 3 slots, a Granary (80) job 44 and 3 slots, the Keep (57) none.
--   `worker_slot` writes the row of the Keep so that it has such slots (in memory only, it is lost when the game ends).
--   `assign_worker` calls `Region:assignFamily(familyID, building)`. The family id is the zero-based index in `Region.workerFamilies`.
--   The worker then carries goods into the Keep (seen in the real game). The slot, the role and the assignment are base game; the write is a mod-defined change.
--
-- Rules: call only on the game thread. No save function. Every input is checked. A change is read back.

local sack = require("HarnessSack")

local M = {}

M.MAX_GOOD = 200
M.MAX_AMOUNT = 1000
M.CAPACITY = 200   -- units of goods that one manor module holds through put (mod rule)
M.MAX_ROWS = 20
M.BUILDING_STATS = "/Game/NotStronghold/Data/buildingStats.buildingStats"
M.MAX_SLOTS = 6
-- EJobType values of storage workers, with the EBuildingFunction and the storage limit that a building of that role has in the base game.
M.STORAGE_JOBS = {
    [45] = { name = "WarehouseWorker", buildingFunction = 6, limitField = "storageLimitGeneric", limit = 250 },
    [44] = { name = "GranaryWorker", buildingFunction = 5, limitField = "storageLimitPantry", limit = 500 },
}
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

-- ---------------------------------------------------------------------------------------------
-- Worker slots
-- ---------------------------------------------------------------------------------------------

local function statsRow(kind)
    local stats = StaticFindObject(M.BUILDING_STATS)
    if not isValid(stats) then return nil, "the DataTable buildingStats is not loaded" end
    local ok, row = pcall(function() return stats:FindRow(tostring(kind)) end)
    if not ok or row == nil then return nil, "no buildingStats row " .. tostring(kind) end
    return row
end

local function workerReads(building)
    local assigned = read(function() return building.assignedFamilyIDs:GetArrayNum() end) or 0
    local workers = read(function() return #listOf(building:getAllWorkers()) end) or 0
    return { max_slots = read(function() return building:getMaxWorkerFamilies() end), job = read(function() return building:getJobType() end),
             assigned = assigned, workers = workers, is_storage = read(function() return building:isStorageTypeBuilding() end) == true }
end

local function workerRow(building, region)
    local out = row(building, region)
    for key, value in pairs(workerReads(building)) do out[key] = value end
    return out
end

-- The built manor module (or the one with this id) for a worker command.
local function pickBuilt(region, request)
    local manor, problem = pick(region, { manor = request.building or request.manor })
    if not manor then return nil, problem end
    if not isBuilt(manor) then return nil, "the manor module is not built" end
    return manor
end

-- Give the manor module the worker slots of a Storehouse (job 45) or a Granary (job 44).
function M.worker_slot(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local job = M.STORAGE_JOBS[request.job]
    if not job then return { ok = false, error = "job must be 45 (WarehouseWorker) or 44 (GranaryWorker)" } end
    local slots = request.slots
    if slots == nil or slots < 1 or slots > M.MAX_SLOTS then return { ok = false, error = "slots must be from 1 to " .. M.MAX_SLOTS } end
    local manor, pickProblem = pickBuilt(region, request)
    if not manor then return { ok = false, error = pickProblem } end
    local kind = typeOf(manor)
    local stats, statsProblem = statsRow(kind)
    if not stats then return { ok = false, error = statsProblem } end
    local before = workerReads(manor)
    local written, err = pcall(function()
        stats.isWork = true
        stats.job = request.job
        stats.workerTypes.Y = slots + 0.0
        stats.buildingFunction = job.buildingFunction
        stats[job.limitField] = job.limit
        manor.buildingFunction = job.buildingFunction
        manor[job.limitField] = job.limit
    end)
    if not written then return { ok = false, error = "write buildingStats: " .. tostring(err) } end
    local after = workerReads(manor)
    if after.max_slots ~= slots or after.job ~= request.job then
        return { ok = false, error = "the building reads " .. tostring(after.max_slots) .. " slots and job " .. tostring(after.job) .. " after the write" }
    end
    return { ok = true, id = idOf(manor), type = kind, job_name = job.name, before = before, after = after }
end

local function isAssigned(family)
    local target = read(function() return family.assignedTo end)
    return isValid(target)
end

-- Assign one family to the manor module. Without `family` the first family with no workplace is taken.
function M.assign_worker(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local manor, pickProblem = pickBuilt(region, request)
    if not manor then return { ok = false, error = pickProblem } end
    local reads = workerReads(manor)
    if (reads.max_slots or 0) < 1 then return { ok = false, error = "the manor module has no worker slot (use worker_slot first)" } end
    if reads.assigned >= reads.max_slots then return { ok = false, error = "all " .. reads.max_slots .. " worker slots are taken" } end
    local families = listOf(region.workerFamilies)
    local index = request.family
    if index == nil then
        for i, family in ipairs(families) do
            if not isAssigned(family) then index = i - 1; break end
        end
        if index == nil then return { ok = false, error = "no family without a workplace" } end
    elseif index < 0 or index >= #families then
        return { ok = false, error = "family must be from 0 to " .. (#families - 1) }
    elseif isAssigned(families[index + 1]) then
        return { ok = false, error = "family " .. index .. " already has a workplace" }
    end
    local ok, err = pcall(function() region:assignFamily(index, manor) end)
    if not ok then return { ok = false, error = "assignFamily: " .. tostring(err) } end
    local now = workerReads(manor)
    local target = read(function() return families[index + 1].assignedTo end)
    local held = isValid(target) and idOf(target) == idOf(manor)
    if not held or now.assigned ~= reads.assigned + 1 then
        return { ok = false, error = "the family is not assigned after assignFamily (assigned " .. now.assigned .. ")" }
    end
    return { ok = true, id = idOf(manor), family = index, before = reads, after = now }
end

-- Take every family off the manor module (the control step of a test).
function M.unassign_workers(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local manor, pickProblem = pickBuilt(region, request)
    if not manor then return { ok = false, error = pickProblem } end
    local before = workerReads(manor)
    for i, family in ipairs(listOf(region.workerFamilies)) do
        local target = read(function() return family.assignedTo end)
        if isValid(target) and idOf(target) == idOf(manor) then
            local ok, err = pcall(function() region:unassignFamily(i - 1) end)
            if not ok then return { ok = false, error = "unassignFamily: " .. tostring(err) } end
        end
    end
    local after = workerReads(manor)
    if after.assigned ~= 0 then return { ok = false, error = "families are still assigned: " .. after.assigned } end
    return { ok = true, id = idOf(manor), before = before, after = after }
end

-- The worker slots, the role and the goods of the manor modules. Read only.
function M.worker_state(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local rows = {}
    for _, building in ipairs(manorBuildings(region)) do
        if #rows < M.MAX_ROWS then rows[#rows + 1] = workerRow(building, region) end
    end
    return { ok = true, count = #rows, modules = rows, unassigned_families = read(function() return region:getNumUnassignedFamilies() end) }
end

return M
