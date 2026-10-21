-- ManorCore: the game calls that a player mod needs (spec 19, mod releases).
-- Why: a released mod must not need the harness. This module has no harness dependency. It holds
--   - a logger that uses HarnessLog when it exists and print otherwise,
--   - the player region and the region list,
--   - settle_region (PawnCPP:settleRegion, refused for a region the pawn does not own),
--   - forest_spot and tent_find_spot (read only spot finders),
--   - rebel_raid_rally (families leave and a raid starts),
--   - show_banner (PawnCPP:playEventMessage),
--   - policy_list, policy_name and set_policy_signed (Region:setPolicySigned).
-- The harness modules HarnessLords, HarnessHousing, HarnessSack and HarnessBandits call this module, so there is one copy of the code.
-- Rules: call only on the game thread. No save function. No eval.

local M = {}

---------------------------------------------------------------------------------------------
-- Helpers
---------------------------------------------------------------------------------------------

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

local function textOf(value)
    if type(value) == "string" then return value end
    if value == nil then return nil end
    return read(function() return value:ToString() end)
end

local function shortName(object)
    if not isValid(object) then return nil end
    return read(function() return object:GetFName():ToString() end)
end

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if isValid(found) then return found end
    return nil
end

M.isValid, M.read, M.listOf, M.textOf, M.shortName = isValid, read, listOf, textOf, shortName

---------------------------------------------------------------------------------------------
-- Logger
---------------------------------------------------------------------------------------------

-- HarnessLog writes a live file for the harness. A player has no HarnessLog, so the fallback prints to the UE4SS console.
local harnessLog = select(2, pcall(require, "HarnessLog"))
if type(harnessLog) ~= "table" then harnessLog = nil end

local function printLine(level, tag, message)
    print(string.format("[%s] %s %s\n", tag or "-", level, tostring(message)))
end

M.log = {}
function M.log.info(tag, message) if harnessLog then return harnessLog.info(tag, message) end printLine("INFO", tag, message) end
function M.log.warn(tag, message) if harnessLog then return harnessLog.warn(tag, message) end printLine("WARN", tag, message) end
function M.log.error(tag, message) if harnessLog then return harnessLog.error(tag, message) end printLine("ERROR", tag, message) end
function M.log.say(tag, message)
    if harnessLog then return harnessLog.say(tag, message) end
    printLine("INFO", tag, message)
end
-- Call a function. A Lua error is logged with a stack trace and does not stop the game thread.
function M.log.try(tag, fn, ...)
    if harnessLog then return harnessLog.try(tag, fn, ...) end
    local ok, result = xpcall(fn, debug.traceback, ...)
    if not ok then printLine("ERROR", tag, result) end
    return ok, result
end

---------------------------------------------------------------------------------------------
-- Regions
---------------------------------------------------------------------------------------------

-- The region whose owner is the player pawn. The region the pawn stands in can be an AI region.
function M.player_region()
    local engineObject = engine()
    if not engineObject then return nil, "no RTSMultiEngineCPP" end
    local player = read(function() return engineObject.playerRef end)
    if not isValid(player) then return nil, "no player pawn" end
    local playerAddress = read(function() return player:GetAddress() end)
    for _, region in ipairs(playerAddress and listOf(engineObject.regions) or {}) do
        local owner = read(function() return region.ownerPawn end)
        if isValid(region) and isValid(owner) and read(function() return owner:GetAddress() end) == playerAddress then return region end
    end
    local current = read(function() return player.currentRegion end)
    if isValid(current) then return current end
    return nil, "no region of the player"
end

local function regions(engineObject)
    local out = {}
    local list = read(function() return engineObject.regions end)
    local count = read(function() return list:GetArrayNum() end) or 0
    for i = 1, count do
        local region = read(function() return list[i] end)
        if isValid(region) then out[#out + 1] = region end
    end
    return out
end

-- A region named by its object name (for example "Goldhof").
local function namedRegion(name, engineObject)
    if type(name) ~= "string" or name == "" then return nil, "region (an object name) is required" end
    for _, region in ipairs(regions(engineObject)) do
        if shortName(region) == name then return region end
    end
    return nil, "no region named " .. name
end

local function buildingCount(region)
    local list = read(function() return region:GetBuildings() end)
    if list == nil then return nil end
    return read(function() return list:GetArrayNum() end) or read(function() return #list end)
end

function M.region_row(region)
    return {
        region = shortName(region), name = textOf(read(function() return region.regionName end)),
        owner = shortName(read(function() return region.ownerPawn end)),
        settled = read(function() return region.isSettled end), settlement_type = read(function() return region.settlementType end),
        level = read(function() return region.settlementLevel end), town_center = shortName(read(function() return region.townCenter end)),
        manor = shortName(read(function() return region.manor end)), buildings = buildingCount(region),
        planning = shortName(read(function() return region.CityPlanningComponent end)),
        families = read(function() return region:getTotalNumFamilies() end),
    }
end

-- Every region: owner, settled, settlement type and level, town center, manor, buildings, families. Read only.
function M.regions_state()
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local rows = {}
    for _, region in ipairs(regions(engineObject)) do rows[#rows + 1] = M.region_row(region) end
    return { ok = true, regions = rows }
end

-- The row of one region, found by its display name (regionName). Nil when there is none.
function M.region_row_by_name(name)
    for _, row in ipairs(M.regions_state().regions or {}) do
        if row.name == name then return row end
    end
    return nil
end

---------------------------------------------------------------------------------------------
-- Settle region
---------------------------------------------------------------------------------------------

local MAX_SETTLEMENT_TYPE = 5 -- ESettlementType: 1 Town, 2 FarmingVillage, 3 ForestVillage, 4 MiningOutpost, 5 Outpost

-- PawnCPP:settleRegion(region, camp transform, supply, type, outpostToRegion). It crashed the game 3 of 3 times with an
-- UNOWNED region (S13 part 1). This function refuses a region that the pawn does not own.
-- request: region (object name), type, supply, x, y, z (camp; default the settled centre), outpost (region name).
-- `pawn` is the settling pawn. It defaults to the player pawn.
function M.settle_region(request, pawn)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    if pawn == nil then pawn = read(function() return engineObject.playerRef end) end
    if not isValid(pawn) then return { ok = false, error = "no pawn for the settle call" } end
    local region, why = namedRegion(request.region, engineObject)
    if not region then return { ok = false, error = why } end
    if shortName(read(function() return region.ownerPawn end)) ~= shortName(pawn) then
        return { ok = false, error = "the pawn does not own the region (claim it first)" }
    end
    local settlementType = request.type or 1
    if settlementType < 1 or settlementType > MAX_SETTLEMENT_TYPE then
        return { ok = false, error = "type must be 1 to " .. MAX_SETTLEMENT_TYPE .. " (ESettlementType)" }
    end
    local outpost
    if request.outpost then
        outpost = namedRegion(request.outpost, engineObject)
        if not outpost then return { ok = false, error = "no region named " .. tostring(request.outpost) } end
    end
    local at = (request.x and { X = request.x, Y = request.y, Z = request.z or 0 })
        or read(function() return region:getSettledRegionCenter() end) or read(function() return region:K2_GetActorLocation() end)
    if not at then return { ok = false, error = "no camp position" } end
    local camp = { Rotation = { X = 0, Y = 0, Z = 0, W = 1 }, Translation = { X = at.X, Y = at.Y, Z = at.Z }, Scale3D = { X = 1, Y = 1, Z = 1 } }
    local before = M.region_row(region)
    local ok, err = pcall(function() pawn:settleRegion(region, camp, request.supply or 0, settlementType, outpost) end)
    if not ok then return { ok = false, error = "settleRegion: " .. tostring(err) } end
    return { ok = true, camp = { x = math.floor(at.X), y = math.floor(at.Y), z = math.floor(at.Z) }, before = before, after = M.region_row(region) }
end

---------------------------------------------------------------------------------------------
-- Spot finders (read only)
---------------------------------------------------------------------------------------------

-- Tent spot: rings of points around the village centre. A point is kept when the game says it is outside every building
-- border (RTSMultiEngineCPP:pointCollidesWithBuildingBorder) and it is at least MIN_GAP from every building of the region.
M.RING_STEP = 700
M.RING_COUNT = 8
M.ANGLES = 12
M.MIN_GAP = 900
M.MAX_SPOTS = 5

local function villageCentre(region, buildings)
    local centre = read(function() return region:getSettledRegionCenter() end)
    if centre and read(function() return centre.X end) and (centre.X ~= 0 or centre.Y ~= 0) then return centre.X, centre.Y end
    local sx, sy, n = 0, 0, 0
    for _, building in ipairs(buildings) do
        local at = read(function() return building:K2_GetActorLocation() end)
        if at then sx, sy, n = sx + at.X, sy + at.Y, n + 1 end
    end
    if n == 0 then return nil end
    return sx / n, sy / n
end

local function buildingPoints(buildings)
    local points = {}
    for _, building in ipairs(buildings) do
        local at = read(function() return building:K2_GetActorLocation() end)
        if at then points[#points + 1] = { x = at.X, y = at.Y, z = at.Z } end
    end
    return points
end

local function nearestBuilding(points, x, y)
    local best, bestDist = nil, math.huge
    for _, p in ipairs(points) do
        local d = math.sqrt((p.x - x) ^ 2 + (p.y - y) ^ 2)
        if d < bestDist then best, bestDist = p, d end
    end
    return best, bestDist
end

local function validBuildings(region)
    local buildings = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do if isValid(building) then buildings[#buildings + 1] = building end end
    return buildings
end

-- Forest finder. Trees are instances of FoliageInstancedStaticMeshComponent (one component per mesh, owned by the region actor).
-- Method: read the transform of the tree instances of the player region, group them in square cells, keep the cells that hold enough
-- trees and lie between min_dist and max_dist from the village centre and at least MIN_BUILDING_GAP from every building.
M.TREE_CELL = 1500
M.MAX_SAMPLES_PER_MESH = 3000
M.MIN_TREES_IN_CELL = 8
M.MIN_BUILDING_GAP = 1500
M.DEFAULT_MIN_DIST = 15000
M.DEFAULT_MAX_DIST = 40000

-- Oaks and firs are trees. Shrubs, stones, stumps and fallen logs are not.
local function isTreeMesh(name)
    local lower = (name or ""):lower()
    if lower:find("shrub", 1, true) or lower:find("fallen", 1, true) or lower:find("stump", 1, true) or lower:find("stone", 1, true) then return false end
    return lower:find("oak", 1, true) ~= nil or lower:find("fir_", 1, true) ~= nil or lower:find("pine", 1, true) ~= nil
end

local function meshName(component)
    local mesh = read(function() return component.StaticMesh end)
    return isValid(mesh) and textOf(read(function() return mesh:GetFName():ToString() end)) or nil
end

local function treesOfComponent(component, trees)
    local count = read(function() return component:GetInstanceCount() end) or 0
    local stride = math.max(1, math.ceil(count / M.MAX_SAMPLES_PER_MESH))
    for index = 0, count - 1, stride do
        local transform = {}
        local ok = read(function() return component:GetInstanceTransform(index, transform, true) end)
        local at = ok and transform.Translation
        if at and read(function() return at.X end) then trees[#trees + 1] = { x = at.X, y = at.Y, z = at.Z, weight = stride } end
    end
    return count
end

local function treesOfRegion(region)
    local trees, meshes, seen = {}, {}, { components = 0, owned = 0 }
    for _, component in ipairs(FindAllOf("FoliageInstancedStaticMeshComponent") or {}) do
        seen.components = seen.components + 1
        local outer = isValid(component) and read(function() return component:GetOuter() end)
        if outer and read(function() return outer:GetFName():ToString() end) == read(function() return region:GetFName():ToString() end) then
            seen.owned = seen.owned + 1
            local name = meshName(component)
            if isTreeMesh(name) then meshes[name] = treesOfComponent(component, trees) end
        end
    end
    return trees, meshes, seen
end

local function treeCells(trees)
    local cells = {}
    for _, tree in ipairs(trees) do
        local key = math.floor(tree.x / M.TREE_CELL) .. ":" .. math.floor(tree.y / M.TREE_CELL)
        local cell = cells[key] or { n = 0, sx = 0, sy = 0, sz = 0 }
        cell.n, cell.sx, cell.sy, cell.sz = cell.n + tree.weight, cell.sx + tree.x * tree.weight, cell.sy + tree.y * tree.weight, cell.sz + tree.z * tree.weight
        cells[key] = cell
    end
    return cells
end

-- Up to 5 forest spots (dense tree cells) in the player region, best first. Request: min_dist, max_dist (from the village centre).
function M.forest_spot(request)
    request = request or {}
    local minDist, maxDist = request.min_dist or M.DEFAULT_MIN_DIST, request.max_dist or M.DEFAULT_MAX_DIST
    if type(minDist) ~= "number" or type(maxDist) ~= "number" or minDist < 0 or maxDist <= minDist then
        return { ok = false, error = "min_dist must be 0 or more and max_dist must be larger" }
    end
    local region, problem = M.player_region()
    if not region then return { ok = false, error = problem } end
    local buildings = validBuildings(region)
    local cx, cy = villageCentre(region, buildings)
    if not cx then return { ok = false, error = "no village centre" } end
    local trees, meshes, seen = treesOfRegion(region)
    local points, spots = buildingPoints(buildings), {}
    for _, cell in pairs(treeCells(trees)) do
        local x, y, z = cell.sx / cell.n, cell.sy / cell.n, cell.sz / cell.n
        local dist = math.sqrt((x - cx) ^ 2 + (y - cy) ^ 2)
        local _, gap = nearestBuilding(points, x, y)
        if cell.n >= M.MIN_TREES_IN_CELL and dist >= minDist and dist <= maxDist and gap >= M.MIN_BUILDING_GAP then
            spots[#spots + 1] = { x = math.floor(x), y = math.floor(y), z = math.floor(z), trees = cell.n, dist = math.floor(dist), building_gap = math.floor(gap) }
        end
    end
    table.sort(spots, function(a, b) return a.trees > b.trees end)
    while #spots > 5 do table.remove(spots) end
    -- ok stays true with no spot, so the tree counts still reach the caller.
    return { ok = true, found = #spots, centre = { x = math.floor(cx), y = math.floor(cy) },
             foliage_components = seen, tree_samples = #trees, tree_meshes = meshes, spots = spots }
end

function M.tent_find_spot()
    local region, problem = M.player_region()
    if not region then return { ok = false, error = problem } end
    local engineObject = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engineObject) then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local buildings = validBuildings(region)
    local cx, cy = villageCentre(region, buildings)
    if not cx then return { ok = false, error = "no village centre" } end
    local points, spots, tried = buildingPoints(buildings), {}, 0
    for ring = 1, M.RING_COUNT do
        for step = 0, M.ANGLES - 1 do
            local angle = 2 * math.pi * step / M.ANGLES
            local x, y = cx + math.cos(angle) * ring * M.RING_STEP, cy + math.sin(angle) * ring * M.RING_STEP
            local near, dist = nearestBuilding(points, x, y)
            tried = tried + 1
            if near and dist >= M.MIN_GAP then
                local hit = read(function() return engineObject:pointCollidesWithBuildingBorder({ X = x, Y = y, Z = near.z }) end)
                -- A failed call (nil) is not a free spot: the check did not run.
                if hit == false then
                    spots[#spots + 1] = { x = math.floor(x), y = math.floor(y), z = math.floor(near.z), gap = math.floor(dist), ring = ring }
                    if #spots >= M.MAX_SPOTS then
                        return { ok = true, centre = { x = math.floor(cx), y = math.floor(cy) }, tried = tried, spots = spots }
                    end
                end
            end
        end
    end
    return { ok = #spots > 0, error = #spots == 0 and "no free spot found" or nil, centre = { x = math.floor(cx), y = math.floor(cy) }, tried = tried, spots = spots }
end

---------------------------------------------------------------------------------------------
-- Families and the rebel raid
---------------------------------------------------------------------------------------------

-- Kill every member of `count` families (the first ones in the list). Returns families and people removed.
-- Why two passes: a death changes the family array, so a family struct read after the first death can be stale.
-- That crashed the game (#357). Collect all members first, then kill.
function M.remove_families(region, count)
    local members, removedFamilies = {}, 0
    for _, family in ipairs(listOf(region.workerFamilies)) do
        if removedFamilies >= count then break end
        for _, member in ipairs(listOf(family.familyMembers)) do members[#members + 1] = member end
        removedFamilies = removedFamilies + 1
    end
    local removedPeople = 0
    for _, member in ipairs(members) do
        if isValid(member) and read(function() return member.dead end) ~= true then
            if pcall(function() member:just_die() end) then removedPeople = removedPeople + 1 end
        end
    end
    return removedFamilies, removedPeople
end

M.MAX_REBEL_FAMILIES = 6
M.AI_WAYPOINT = { x = -31000, y = -22500 }
M.RALLY_MIN_DIST, M.RALLY_MAX_DIST = 15000, 40000

-- The forest spot nearest to the AI waypoint. Why: the raid ignores its target, but the raiders pass the waypoint and wait there.
function M.rally_spot()
    local answer = M.forest_spot({ min_dist = M.RALLY_MIN_DIST, max_dist = M.RALLY_MAX_DIST })
    if not answer.ok then return nil, answer.error end
    local best, bestDist
    for _, spot in ipairs(answer.spots) do
        local dist = math.sqrt((spot.x - M.AI_WAYPOINT.x) ^ 2 + (spot.y - M.AI_WAYPOINT.y) ^ 2)
        if not bestDist or dist < bestDist then best, bestDist = spot, dist end
    end
    if not best then return nil, "no forest spot between " .. M.RALLY_MIN_DIST .. " and " .. M.RALLY_MAX_DIST .. " units from the village" end
    return best
end

-- RTSMultiEngineCPP:spawnRaiders(squads, centre): one real raid.
function M.spawn_raiders(squads, spot)
    local engineObject = engine()
    if not engineObject then return false, "no RTSMultiEngineCPP" end
    local ok, err = pcall(function() engineObject:spawnRaiders(squads, { X = spot.x, Y = spot.y, Z = spot.z }) end)
    if not ok then return false, "spawnRaiders: " .. tostring(err) end
    return true
end

-- The bandit lord: owner of raiders and bandits.
local function bandit_pawn()
    for _, pawn in ipairs(FindAllOf("PawnCPP") or {}) do
        if isValid(pawn) and not pawn:GetFullName():find("Default__", 1, true) and read(function() return pawn.isBandit end) == true then
            return pawn
        end
    end
    return nil
end

-- One bandit squad for each template name, at the point. spawnRaiders cannot choose a type (spike S2); spawnArmy can (spike S7).
-- Returns true and the list of squad ids (empty when the game does not return them), or false and a message.
function M.spawn_squads(templates, spot)
    local engineObject = engine()
    if not engineObject then return false, "no RTSMultiEngineCPP" end
    local owner = bandit_pawn()
    if not owner then return false, "no bandit pawn (isBandit)" end
    local names = {}
    for index, name in ipairs(templates) do names[index] = FName(name) end
    local ok, returned = pcall(function() return engineObject:spawnArmy({ X = spot.x, Y = spot.y, Z = spot.z }, names, owner, 0, 0) end)
    if not ok then return false, "spawnArmy: " .. tostring(returned) end
    local ids = {}
    for index = 1, #names do
        local element = read(function() return returned[index] end)
        local inner = read(function() return element:get() end)
        local id = read(function() return (inner or element).Value end)
        ids[index] = type(id) == "number" and id or false
    end
    return true, ids
end

-- Remove `count` families (they leave), then send one real raid with a forest spot as the target.
-- See implementation-notes/homeless-rebellion.md of spec 15: the raiders appear at the map edge, walk north, wait at the AI waypoint,
-- then attack the village.
function M.rebel_raid_rally(request)
    local count = request.count or 1
    if count < 1 or count > M.MAX_REBEL_FAMILIES then return { ok = false, error = "count must be 1 to " .. M.MAX_REBEL_FAMILIES } end
    local region, problem = M.player_region()
    if not region then return { ok = false, error = problem } end
    local spot, why = M.rally_spot()
    if not spot then return { ok = false, error = why } end
    local families, people = M.remove_families(region, count)
    local started, spawnProblem = M.spawn_raiders(1, spot)
    if not started then return { ok = false, error = spawnProblem, families_removed = families } end
    return { ok = true, families_removed = families, people_removed = people, spot = spot }
end

---------------------------------------------------------------------------------------------
-- Banner
---------------------------------------------------------------------------------------------

-- A text banner at the top of the screen. The message type must be an FName: a plain string crashes the game.
M.BANNER_TYPE = "Default"
function M.show_banner(text, subtext)
    local engineObject = engine()
    local pawn = engineObject and read(function() return engineObject.playerRef end)
    if not isValid(pawn) then return false, "the player pawn is not loaded" end
    local ok, err = pcall(function() pawn:playEventMessage(FName(M.BANNER_TYPE), text, subtext or "") end)
    if not ok then return false, tostring(err) end
    return true
end

---------------------------------------------------------------------------------------------
-- Policies (spec 16)
---------------------------------------------------------------------------------------------

-- Region:setPolicySigned(id, bool) is the call the game's own policy widget uses (enactPolicy returns false, see spec 16 notes).
M.MAX_POLICY_ID = 40
M.MAX_POLICIES = 40
M.POLICY_TABLE_PATH = "/Game/NotStronghold/Data/DT_PolicyTypes.DT_PolicyTypes"

-- Whole numbers from a TArray or a table. The elements may need :get().
local function numberList(array)
    local out = {}
    for _, element in ipairs(listOf(array)) do
        if type(element) == "number" then out[#out + 1] = element end
    end
    return out
end

-- The game name of a policy from the row Name of DT_PolicyTypes (row name = policy id).
-- Only the field Name is read. The row also has a soft object field (Icon) that must never be read.
function M.policy_name(id)
    local ok, policyTable = pcall(StaticFindObject, M.POLICY_TABLE_PATH)
    if not ok or not isValid(policyTable) then return nil end
    local row = read(function() return policyTable:FindRow(tostring(id)) end)
    if row == nil then return nil end
    local text = textOf(read(function() return row.Name end))
    if text == nil or text == "" then return nil end
    return text
end

-- The policies the player can sign now: { policies = { {id, name, signed}, ... }, max_slots }, in id order.
function M.policy_list()
    local region, problem = M.player_region()
    if not region then return nil, problem end
    local available = read(function() return region:getAllAvailablePolicies() end)
    local signedSet = {}
    for _, id in ipairs(numberList(read(function() return region.policiesSigned end))) do signedSet[id] = true end
    local ids = numberList(available)
    table.sort(ids)
    local entries = {}
    for i = 1, math.min(#ids, M.MAX_POLICIES) do
        local id = ids[i]
        entries[#entries + 1] = { id = id, name = M.policy_name(id) or ("Policy " .. id), signed = signedSet[id] == true }
    end
    return { policies = entries, max_slots = read(function() return region:getMaxPolicies() end) }
end

-- Sign or unsign one policy.
function M.set_policy_signed(id, signed)
    if type(id) ~= "number" or id ~= math.floor(id) or id < 1 or id > M.MAX_POLICY_ID then
        return false, "policy must be a whole number from 1 to " .. M.MAX_POLICY_ID
    end
    if type(signed) ~= "boolean" then return false, "signed must be true or false" end
    local region, problem = M.player_region()
    if not region then return false, problem end
    local ok, err = pcall(function() region:setPolicySigned(id, signed) end)
    if not ok then return false, "setPolicySigned: " .. tostring(err) end
    return true
end

return M
