-- HarnessHousing: read the housing of the player village and the homeless tents (spec 15, tent spike).
-- Why: a settle letter adds a family only when the region has a vacant home slot (spec 15, run s15-c). The mod needs to know
-- what a homeless tent (EBuildingType 87, class BM_HomelessTents_C) is and whether it counts as a slot.
-- Commands: building_stat (read only), building_stat_vector_write (unsafe test command), housing_state (read only), accommodate_homeless (Region:accomodateHomelessFamilies), family_state, family_eject, family_add (part 7).
--
-- Rules: call only on the game thread. No save function. Every input is checked. No struct with soft fields is read.

local sack = require("HarnessSack")
local json = require("HarnessJson")

local M = {}

M.BUILDING_STATS = "/Game/NotStronghold/Data/buildingStats.buildingStats"
M.TENT_TYPE = 87          -- buildingStats row "homeless_tents", function Temporary
M.MAX_TYPE = 300
M.MAX_ROWS = 40
-- Scalar fields of the buildingStats row that are safe to read (no soft object, no array of structs).
M.STAT_FIELDS = { "bWorkInProgress", "isWork", "job", "bSize", "maxHp", "needsRoad", "collidesWithRoads", "canRelocate", "constructionCost",
                  "RequiresSkilledBuilders", "maxInRegion", "settlementLevel", "AIcanBuild", "placedWithin", "flammable", "bVisibleInUi",
                  "isModule", "isPlaza", "buildingFunction", "BuildingCategory" }

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

local function textOf(value)
    if type(value) == "string" or type(value) == "number" or type(value) == "boolean" then return value end
    if value == nil then return nil end
    return read(function() return value:ToString() end) or tostring(value)
end

local function vector4(value)
    if value == nil then return nil end
    return { x = read(function() return value.X end), y = read(function() return value.Y end),
             z = read(function() return value.Z end), w = read(function() return value.W end) }
end

local function idOf(building)
    local name = read(function() return building:GetFullName() end) or ""
    return tonumber(name:match("_(%d+)$"))
end

local function typeOf(building) return read(function() return building.Data.bType end) end

-- Read only: scalar fields of the buildingStats row of one building type.
function M.building_stat(request)
    local kind = request.type
    if not kind or kind < 0 or kind > M.MAX_TYPE then return { ok = false, error = "type must be a building type number up to " .. M.MAX_TYPE } end
    local stats = StaticFindObject(M.BUILDING_STATS)
    if not isValid(stats) then return { ok = false, error = "the DataTable buildingStats is not loaded" } end
    local ok, row = pcall(function() return stats:FindRow(tostring(kind)) end)
    if not ok or row == nil then return { ok = false, error = "no buildingStats row " .. tostring(kind) } end
    local out = { ok = true, kind = kind, name = textOf(read(function() return row.DisplayName end)) }
    for _, field in ipairs(M.STAT_FIELDS) do out[field] = textOf(read(function() return row[field] end)) end
    out.workerTypes = vector4(read(function() return row.workerTypes end))
    out.occupantTypes = vector4(read(function() return row.occupantTypes end))
    return out
end

-- Unsafe test command (spec 15, tent-slot-limit.md). It changes game data in memory, so it is refused unless the game process
-- was started with HARNESS_ALLOW_UNSAFE=1. Test games only, never a user save.
M.UNSAFE_ENV = "HARNESS_ALLOW_UNSAFE"
M.VECTOR_FIELDS = { occupantTypes = true, workerTypes = true }
M.VECTOR_COMPONENTS = { X = true, Y = true, Z = true, W = true }
M.MAX_VECTOR_VALUE = 100

local function unsafe(name, handler)
    return function(...)
        if (os.getenv and os.getenv(M.UNSAFE_ENV)) ~= "1" then
            return { ok = false, error = name .. " is an unsafe test command: start the game with " .. M.UNSAFE_ENV .. "=1 (test games only)" }
        end
        return handler(...)
    end
end

-- The HarnessActions parser keeps only known fields, so this command reads its own fields from the raw request text.
local function vectorWriteRequest(raw)
    local text = type(raw) == "string" and raw or ""
    local kind = tonumber(text:match('"type"%s*:%s*(%d+)'))
    local field = text:match('"field"%s*:%s*"([%w_]+)"')
    local component = text:match('"component"%s*:%s*"([%a])"')
    local value = tonumber(text:match('"value"%s*:%s*(-?[%d%.]+)'))
    if not kind or kind > M.MAX_TYPE then return nil, "type must be a building type number up to " .. M.MAX_TYPE end
    if not field or not M.VECTOR_FIELDS[field] then return nil, "field must be occupantTypes or workerTypes" end
    if not component or not M.VECTOR_COMPONENTS[component] then return nil, "component must be X, Y, Z or W" end
    if not value or value < 0 or value > M.MAX_VECTOR_VALUE then return nil, "value must be a number from 0 to " .. M.MAX_VECTOR_VALUE end
    return { kind = kind, field = field, component = component, value = value }
end

-- Write one component of a Vector4 field of one buildingStats row, in memory. It lasts until the game ends.
M.building_stat_vector_write = unsafe("building_stat_vector_write", function(_, raw)
    local want, problem = vectorWriteRequest(raw)
    if not want then return { ok = false, error = problem } end
    local stats = StaticFindObject(M.BUILDING_STATS)
    if not isValid(stats) then return { ok = false, error = "the DataTable buildingStats is not loaded" } end
    local okRow, row = pcall(function() return stats:FindRow(tostring(want.kind)) end)
    if not okRow or row == nil then return { ok = false, error = "no buildingStats row " .. want.kind } end
    local before = vector4(read(function() return row[want.field] end))
    local okWrite, err = pcall(function() row[want.field][want.component] = want.value end)
    if not okWrite then return { ok = false, error = "write failed: " .. tostring(err), before = before } end
    return { ok = true, kind = want.kind, field = want.field, component = want.component, before = before,
             after = vector4(read(function() return row[want.field] end)) }
end)

local function familyCount(building)
    return read(function() return building.occupantFamilyIDs:GetArrayNum() end)
end

local function buildingRow(building)
    return { id = idOf(building), type = typeOf(building), built = read(function() return building:IsConstructed() end) == true,
             rubble = read(function() return building:IsRubble() end) == true, tent = read(function() return building:isHomelessTent() end) == true,
             residential = read(function() return building:isResidentialBuilding() end) == true,
             class = textOf(read(function() return building:GetClass():GetFName():ToString() end)),
             families = familyCount(building) }
end

local function regionRow(region)
    local space = read(function() return region:getAvailableLivingSpace() end) or {}
    local living = read(function() return region:getLivingSpace() end) or {}
    return { name = textOf(read(function() return region.regionName end)),
             families = read(function() return region:getTotalNumFamilies() end), homeless = read(function() return region:getNumHomelessFamilies() end),
             residents = read(function() return region:getNumHumanResidents() end),
             approval = read(function() return region.Approval end), public_order = read(function() return region.publicOrder end),
             living = { constructed = living.constructed, unconstructed = living.unconstructed },
             vacant = { constructed = space.constructed, unconstructed = space.unconstructed },
             tents_by_count = read(function() return region:getBuildingCount(M.TENT_TYPE, false) end),
             tents_built = read(function() return region:getBuildingCount(M.TENT_TYPE, true) end) }
end

-- Read only: the housing numbers of the player region, its tents and its residential buildings (rows capped).
function M.housing_state()
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local out = { ok = true, region = regionRow(region), tents = {}, residential = {}, residential_total = 0 }
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) then
            local row = buildingRow(building)
            if row.tent or row.type == M.TENT_TYPE then out.tents[#out.tents + 1] = row end
            if row.residential then
                out.residential_total = out.residential_total + 1
                if #out.residential < M.MAX_ROWS then out.residential[#out.residential + 1] = row end
            end
        end
    end
    out.world_tents = M.world_tents()
    return out
end

-- Every homeless tent in the world (all regions), with the region it belongs to.
function M.world_tents()
    local rows = {}
    for _, building in ipairs(FindAllOf("SMBuildingMaster") or {}) do
        if isValid(building) and not building:GetFullName():find("Default__", 1, true)
            and (typeOf(building) == M.TENT_TYPE or read(function() return building:isHomelessTent() end) == true) then
            local row = buildingRow(building)
            row.region = textOf(read(function() return building.currentRegion.regionName end))
            local at = read(function() return building:K2_GetActorLocation() end)
            row.x, row.y = at and read(function() return math.floor(at.X) end), at and read(function() return math.floor(at.Y) end)
            rows[#rows + 1] = row
        end
    end
    return rows
end

-- Region:accomodateHomelessFamilies(nil): the game moves homeless families into free homes. Reports the housing before and after.
function M.accommodate_homeless()
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local before = regionRow(region)
    local ok, err = pcall(function() region:accomodateHomelessFamilies(nil) end)
    if not ok then return { ok = false, error = "accomodateHomelessFamilies: " .. tostring(err) } end
    return { ok = true, before = before, after = regionRow(region) }
end

-- Test only (spec 15, burgage-placement-events.md): does the plot commit read the plain Vector outline of the pawn?
-- The user draws and closes a plot field. This moves fieldSmoothPoints, fieldSmoothPointsClosed and fieldCenter by (dx, dy) and,
-- with commit=true, calls PawnCPP:addCommitFieldRequest. If the plots appear at the moved place, the commit reads these vectors.
M.MAX_FIELD_SHIFT = 10000

local function playerPawn()
    local found = FindFirstOf("MyPawnCPP_BP3_C") or FindFirstOf("PawnCPP")
    if isValid(found) then return found end
    return nil
end

local function shiftVectors(array, dx, dy)
    local count = read(function() return array:GetArrayNum() end) or 0
    for i = 1, count do
        local point = array[i]
        point.X = point.X + dx
        point.Y = point.Y + dy
    end
    return count
end

-- ExtractedPlot (400 bytes) is fully reflected (jmap): vector lists, three Transforms and a Segment. Move every position in it.
local PLOT_VECTOR_LISTS = { "SmoothBorder", "Corners", "extensionSmoothBorder", "extensionCorners" }
local PLOT_TRANSFORMS = { "primaryBuildingTransform", "secondaryBuildingTransform", "extensionTransform" }

local function shiftExtractedPlots(plots, dx, dy)
    local count = read(function() return plots:GetArrayNum() end) or 0
    for i = 1, count do
        local plot = plots[i]
        for _, name in ipairs(PLOT_VECTOR_LISTS) do shiftVectors(plot[name], dx, dy) end
        for _, name in ipairs(PLOT_TRANSFORMS) do
            local translation = plot[name].Translation
            translation.X = translation.X + dx
            translation.Y = translation.Y + dy
        end
        local facade = plot.backFacade
        facade.A.X = facade.A.X + dx
        facade.A.Y = facade.A.Y + dy
        facade.B.X = facade.B.X + dx
        facade.B.Y = facade.B.Y + dy
    end
    return count
end

-- The HarnessActions parser keeps only known fields, so read the flags of this test command from the raw request text.
local function rawFlag(raw, name)
    return type(raw) == "string" and raw:match('"' .. name .. '"%s*:%s*true') ~= nil
end

function M.plot_field_shift(request, raw)
    request.plots = request.plots == true or rawFlag(raw, "plots")
    request.commit = request.commit == true or rawFlag(raw, "commit")
    local dx, dy = tonumber(request.dx), tonumber(request.dy)
    if not dx or not dy or math.abs(dx) > M.MAX_FIELD_SHIFT or math.abs(dy) > M.MAX_FIELD_SHIFT then
        return { ok = false, error = "plot_field_shift needs numbers dx and dy, each at most " .. M.MAX_FIELD_SHIFT }
    end
    local pawn = playerPawn()
    if not pawn then return { ok = false, error = "no player pawn" } end
    if read(function() return pawn.fieldClosed end) ~= true then
        return { ok = false, error = "no closed plot field: draw and close one first (fieldClosed is false)" }
    end
    local ok, result = pcall(function()
        local smooth = shiftVectors(pawn.fieldSmoothPoints, dx, dy)
        local closed = shiftVectors(pawn.fieldSmoothPointsClosed, dx, dy)
        local centre = pawn.fieldCenter
        centre.X = centre.X + dx
        centre.Y = centre.Y + dy
        return { smooth = smooth, closed = closed }
    end)
    if not ok then return { ok = false, error = "shift: " .. tostring(result) } end
    if request.plots == true then
        local okPlots, plots = pcall(function() return shiftExtractedPlots(pawn.extractedPlots, dx, dy) end)
        if not okPlots then return { ok = false, error = "shift extractedPlots: " .. tostring(plots) } end
        result.plots = plots
    end
    local committed = false
    if request.commit == true then
        local okCommit, err = pcall(function() pawn:addCommitFieldRequest() end)
        if not okCommit then return { ok = false, error = "addCommitFieldRequest: " .. tostring(err) } end
        committed = true
    end
    return { ok = true, moved = result, center = { x = pawn.fieldCenter.X, y = pawn.fieldCenter.Y }, committed = committed }
end

-- Test only (spec 15): write plots into an empty pawn field, with no outline drawn. The request carries the plots as numbers:
-- {"plots":[{"corners":[[x,y,z],...],"border":[...],"ext_corners":[...],"ext_border":[...],
--   "primary":[x,y,z,qx,qy,qz,qw],"extension":[x,y,z,qx,qy,qz,qw],"facade":[[x,y,z],[x,y,z]]}]}
-- It sets fieldClosed and expectedNumPlots. The commit is a separate call (PawnCPP:addCommitFieldRequest).
M.MAX_PLACE_PLOTS = 12
M.MAX_PLOT_POINTS = 32

local function setVector(target, point)
    target.X, target.Y, target.Z = point[1], point[2], point[3]
end

-- UE4SS grows a TArray by one when Lua writes the index after the last element.
local function fillVectors(array, points)
    array:Empty()
    for i, point in ipairs(points or {}) do
        array[i] = { X = point[1], Y = point[2], Z = point[3] }
    end
    return array:GetArrayNum()
end

local function setTransform(transform, values)
    values = values or { 0, 0, 0, 0, 0, 0, 1 }
    setVector(transform.Translation, values)
    local rotation = transform.Rotation
    rotation.X, rotation.Y, rotation.Z, rotation.W = values[4], values[5], values[6], values[7]
    setVector(transform.Scale3D, { 1, 1, 1 })
end

local function writePlot(plot, data)
    local counts = {}
    counts.corners = fillVectors(plot.Corners, data.corners)
    counts.border = fillVectors(plot.SmoothBorder, data.border)
    counts.ext_corners = fillVectors(plot.extensionCorners, data.ext_corners)
    counts.ext_border = fillVectors(plot.extensionSmoothBorder, data.ext_border)
    setTransform(plot.primaryBuildingTransform, data.primary)
    setTransform(plot.secondaryBuildingTransform, nil)
    setTransform(plot.extensionTransform, data.extension)
    setVector(plot.backFacade.A, data.facade[1])
    setVector(plot.backFacade.B, data.facade[2])
    return counts
end

local function checkPlotData(plots)
    if type(plots) ~= "table" or #plots == 0 or #plots > M.MAX_PLACE_PLOTS then
        return "plots must be a list of 1 to " .. M.MAX_PLACE_PLOTS .. " plots"
    end
    for i, plot in ipairs(plots) do
        for _, key in ipairs({ "corners", "border", "ext_corners", "ext_border" }) do
            if type(plot[key]) ~= "table" or #plot[key] > M.MAX_PLOT_POINTS then return "plot " .. i .. ": bad " .. key end
        end
        if type(plot.primary) ~= "table" or #plot.primary ~= 7 then return "plot " .. i .. ": primary needs 7 numbers" end
        if type(plot.extension) ~= "table" or #plot.extension ~= 7 then return "plot " .. i .. ": extension needs 7 numbers" end
        if type(plot.facade) ~= "table" or #plot.facade ~= 2 then return "plot " .. i .. ": facade needs 2 points" end
    end
    return nil
end

-- Spike: a plot upgrade without the mouse. The building panel calls PawnCPP:addUpgradeRequest or addExtensionChangeRequest with
-- UpgradeRequest {buildingMaster, upgradeID, Slot} (seen by hooks, 2026-10-12). Ids seen from the panel: 2 level 2 (peasant house),
-- 12 second-family wing, 30 carrot seeds. They are not positions in RTSMultiEngineCPP.upgrades (likely DT_Upgrades row keys); a
-- wrong id is only recorded in upgradesDone and builds nothing. An extension request takes the plain extension number (8 vegetable
-- garden, 0 plain yard); the game stores it as number + 100 in upgradesDone. Sending 108 made an invalid extension.
-- The game charges the normal costs but skips the panel's plot size check. The target is the building under the mouse.
-- Request: upgrade (id), slot (default 0), extension (true/false).
M.MAX_UPGRADE_ID = 1000

local function intField(raw, name)
    return tonumber((raw or ""):match('"' .. name .. '"%s*:%s*(%d+)'))
end

function M.plot_upgrade(_, raw)
    local upgrade, slot = intField(raw, "upgrade"), intField(raw, "slot") or 0
    if not upgrade or upgrade > M.MAX_UPGRADE_ID then return { ok = false, error = "upgrade must be an id from 0 to " .. M.MAX_UPGRADE_ID } end
    local pawn = playerPawn()
    if not pawn then return { ok = false, error = "no player pawn" } end
    local building = read(function() return pawn:getHitBuilding() end)
    if not isValid(building) then return { ok = false, error = "no building under the mouse" } end
    local before = {}
    for _, id in ipairs(listOf(read(function() return building.upgradesDone end))) do before[#before + 1] = id end
    local request = { buildingMaster = building, upgradeID = upgrade, Slot = slot }
    local extension = (raw or ""):match('"extension"%s*:%s*true') ~= nil
    local ok, err = pcall(function()
        if extension then pawn:addExtensionChangeRequest(request) else pawn:addUpgradeRequest(request) end
    end)
    if not ok then return { ok = false, error = "upgrade request: " .. tostring(err) } end
    return { ok = true, building = read(function() return building:GetFullName() end), type = read(function() return building.Data.bType end),
             call = extension and "addExtensionChangeRequest" or "addUpgradeRequest", upgrade = upgrade, slot = slot,
             upgrades_before = before, being_upgraded = read(function() return building.isBeingUpgraded end) }
end

function M.plot_field_place(_, raw)
    local okDecode, decoded = pcall(json.decode, raw)
    if not okDecode or type(decoded) ~= "table" then return { ok = false, error = "request is not valid JSON" } end
    local problem = checkPlotData(decoded.plots)
    if problem then return { ok = false, error = problem } end
    local pawn = playerPawn()
    if not pawn then return { ok = false, error = "no player pawn" } end
    local steps = {}
    local ok, err = pcall(function()
        local plots = pawn.extractedPlots
        plots:Empty()
        steps.emptied = plots:GetArrayNum()
        for i, data in ipairs(decoded.plots) do
            plots[i] = {}
            steps["plot" .. i] = writePlot(plots[i], data)
        end
        steps.count = plots:GetArrayNum()
        pawn.expectedNumPlots = #decoded.plots
        pawn.fieldClosed = true
    end)
    if not ok then return { ok = false, error = tostring(err), steps = steps } end
    return { ok = true, steps = steps, field_closed = pawn.fieldClosed, place_field_mode = pawn.placeFieldMode,
             place_plot_type = pawn.placePlotType }
end

-- Spot finder for a tent (spec 15). The mod has no mouse-free way to place a building yet (see implementation-notes/tent-placement.md),
-- so this command only picks a spot. A test step places the tent there with the real mouse.
-- Method: rings of points around the village centre. A point is kept when the game says it is outside every building border
-- (RTSMultiEngineCPP:pointCollidesWithBuildingBorder), and it is at least MIN_GAP from every building of the region.
-- Not checked: water, steep ground, roads, the manor area. The real preview check of the game does that when the click comes.
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

-- Forest finder (spec 15, rally in the woods). Trees are instances of FoliageInstancedStaticMeshComponent (one component per mesh,
-- owned by the region actor). The single choppable trees (`Resource` actors, resType res_tree) are only a few and are not used.
-- Method: read the transform of the tree instances of the player region, group them in square cells, keep the cells that hold enough
-- trees and lie between min_dist and max_dist from the village centre and at least MIN_BUILDING_GAP from every building. Read only.
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

-- Read only: up to 5 forest spots (dense tree cells) in the player region, best first. Request: min_dist, max_dist (from the village centre).
function M.forest_spot(request)
    local minDist, maxDist = request.min_dist or M.DEFAULT_MIN_DIST, request.max_dist or M.DEFAULT_MAX_DIST
    if type(minDist) ~= "number" or type(maxDist) ~= "number" or minDist < 0 or maxDist <= minDist then
        return { ok = false, error = "min_dist must be 0 or more and max_dist must be larger" }
    end
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local buildings = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do if isValid(building) then buildings[#buildings + 1] = building end end
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
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local buildings = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do if isValid(building) then buildings[#buildings + 1] = building end end
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
                local hit = read(function() return engine:pointCollidesWithBuildingBorder({ X = x, Y = y, Z = near.z }) end)
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


-- Families (spec 15, part 7, implementation-notes/homeless-refugees.md) -----------------------------------------------------
-- family_state reads. family_eject sets housed families homeless (Region:SetFamilyHome with an empty home).
-- family_add makes a new family from a villager (Region:AddNewFamily). Both change game state in a way a mod may use, so they are
-- normal commands, not unsafe ones. They only touch the player region and cap the number of families.
M.MAX_FAMILY_CHANGE = 10

local function rawBool(raw, name, default)
    local text = type(raw) == "string" and raw or ""
    local value = text:match('"' .. name .. '"%s*:%s*(%a+)')
    if value == nil then return default end
    return value == "true"
end

-- Housed families as { id, building } rows, in the order of the residential buildings.
local function housedFamilies(region)
    local rows = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) and read(function() return building:isResidentialBuilding() end) == true then
            for _, id in ipairs(listOf(read(function() return building.occupantFamilyIDs end))) do
                if type(id) == "number" then rows[#rows + 1] = { id = id, building = building } end
            end
        end
    end
    return rows
end

local function housedIds(rows)
    local ids = {}
    for _, row in ipairs(rows) do ids[#ids + 1] = row.id end
    return ids
end

-- The monthly growth modifiers as { [EGrowthModifier number] = value } (1 Base, 2 NoBurgagePlotAvailability, 3 Approval).
-- Read only. On a failure it returns { error = text } so the cause shows in the answer.
local function growthModifiers(region)
    local okCall, map = pcall(function() return region:GetMonthlyPopGrowthModifiersWithValues() end)
    if not okCall then return { error = "call: " .. tostring(map) } end
    map = unwrap(map)
    local out = { kind = type(map) }
    local okEach, err = pcall(function()
        for key, value in pairs(map) do out[tostring(unwrap(key))] = unwrap(value) end
    end)
    if not okEach then out.error = "pairs: " .. tostring(err) end
    return out
end

function M.family_state()
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local rows = housedFamilies(region)
    return { ok = true, region = regionRow(region), housed_ids = housedIds(rows), growth = growthModifiers(region) }
end

-- Read only (spec 15, #61): who lives where. One row per family (index in workerFamilies, living members, roles, the building that
-- Family.familyHome points to) and one row per building that lists occupant families (residential buildings and tents).
-- Compare the two lists to find families that no building lists, and buildings that list a family twice.
M.MAX_CENSUS_ROWS = 80

local function familyRow(index, family)
    local members, roles, ages = 0, {}, {}
    for _, member in ipairs(listOf(family.familyMembers)) do
        if isValid(member) and read(function() return member.dead end) ~= true then
            members = members + 1
            roles[#roles + 1] = read(function() return member.role end)
            ages[#ages + 1] = read(function() return member.Age end)
        end
    end
    local home = read(function() return family.familyHome end)
    local homeValid = isValid(home)
    return { index = index - 1, living = members, roles = roles, ages = ages, has_home = homeValid,
             home_id = homeValid and idOf(home) or nil, home_type = homeValid and typeOf(home) or nil }
end

local function occupantRow(building)
    local row = buildingRow(building)
    row.occupants = {}
    for _, id in ipairs(listOf(read(function() return building.occupantFamilyIDs end))) do
        if type(id) == "number" then row.occupants[#row.occupants + 1] = id end
    end
    return row
end

function M.family_census()
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local families, buildings = {}, {}
    for index, family in ipairs(listOf(region.workerFamilies)) do
        if #families < M.MAX_CENSUS_ROWS then families[#families + 1] = familyRow(index, family) end
    end
    for _, building in ipairs(listOf(region:GetBuildings())) do
        local isHome = isValid(building) and (read(function() return building:isResidentialBuilding() end) == true
            or read(function() return building:isHomelessTent() end) == true)
        if isHome and #buildings < M.MAX_CENSUS_ROWS then buildings[#buildings + 1] = occupantRow(building) end
    end
    return { ok = true, region = regionRow(region), families = families, buildings = buildings }
end

-- Read only (spec 15, #61): the property names of one family member with the value of the plain ones (number, bool, enum). The roles of
-- all members are 3, so this looks for the field that tells an adult from a child. `count` is the zero-based family index.
M.PLAIN_PROPERTY_KINDS = { IntProperty = true, FloatProperty = true, DoubleProperty = true, BoolProperty = true, ByteProperty = true,
                           EnumProperty = true, Int64Property = true, UInt32Property = true }
M.MAX_MEMBER_FIELDS = 200

local function plainFields(member)
    local fields = {}
    local class = member:GetClass()
    while class and #fields < M.MAX_MEMBER_FIELDS do
        class:ForEachProperty(function(property)
            local name = property:GetFName():ToString()
            local kind = property:GetClass():GetFName():ToString()
            local value = nil
            if M.PLAIN_PROPERTY_KINDS[kind] then value = read(function() return member[name] end) end
            fields[#fields + 1] = { name = name, kind = kind, value = value }
        end)
        class = class:GetSuperStruct()
        if class and class:GetFName():ToString() == "Object" then break end
    end
    return fields
end

function M.member_fields(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local family = listOf(region.workerFamilies)[(request.count or 0) + 1]
    if not family then return { ok = false, error = "no family with index " .. tostring(request.count or 0) } end
    local rows = {}
    for _, member in ipairs(listOf(family.familyMembers)) do
        if isValid(member) and #rows < 1 then
            local okFields, fields = pcall(plainFields, member)
            rows[#rows + 1] = okFields and { class = textOf(read(function() return member:GetClass():GetFName():ToString() end)), fields = fields }
                or { error = tostring(fields) }
        end
    end
    return { ok = #rows > 0, error = #rows == 0 and "family has no member" or nil, members = rows }
end

-- The first homeless tent of the region, or nil.
local function regionTent(region)
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) and read(function() return building:isHomelessTent() end) == true then return building end
    end
    return nil
end

-- "home":"none" (default) leaves the families without a home. "home":"tent" moves them into the first homeless tent.
-- request.count families leave their homes. suppress (default true) stops the game from resorting them to a free home.
function M.family_eject(request, raw)
    local count = request.count
    if not count or count < 1 or count > M.MAX_FAMILY_CHANGE then
        return { ok = false, error = "count must be a whole number from 1 to " .. M.MAX_FAMILY_CHANGE }
    end
    local suppress = rawBool(raw, "suppress", true)
    local homeKind = type(raw) == "string" and raw:match('"home"%s*:%s*"(%a+)"') or "none"
    if homeKind ~= "none" and homeKind ~= "tent" then return { ok = false, error = "home must be none or tent" } end
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local rows = housedFamilies(region)
    if #rows < count then return { ok = false, error = "only " .. #rows .. " housed families, count is " .. count } end
    local target = nil
    if homeKind == "tent" then
        target = regionTent(region)
        if not target then return { ok = false, error = "home is tent, but the region has no homeless tent" } end
    end
    local before = regionRow(region)
    local ejected, errors = {}, {}
    for i = 1, count do
        local ok, err = pcall(function() region:SetFamilyHome(rows[i].id, target, suppress) end)
        if ok then ejected[#ejected + 1] = rows[i].id else errors[#errors + 1] = tostring(err) end
    end
    local after = regionRow(region)
    return { ok = #errors == 0, error = errors[1], suppress = suppress, home = homeKind, ejected = ejected, before = before, after = after,
             housed_after = housedIds(housedFamilies(region)) }
end

-- The first living member of a family that has more than one living member, never the only member.
-- With wantAdult, the member is the one with the highest `Age` of its family. Spec 15 #61: on fixture base all members have role 3 and Age 1, so
-- neither field tells an adult from a child there.
local function oldestOf(members)
    local best, bestAge = members[#members], -1
    for _, member in ipairs(members) do
        local age = read(function() return member.Age end) or 0
        if age > bestAge then best, bestAge = member, age end
    end
    return best
end

local function spareMember(region, wantAdult)
    for _, family in ipairs(listOf(region.workerFamilies)) do
        local living = {}
        for _, member in ipairs(listOf(family.familyMembers)) do
            if isValid(member) and read(function() return member.dead end) ~= true then living[#living + 1] = member end
        end
        if #living >= 2 then return wantAdult and oldestOf(living) or living[#living] end
    end
    return nil
end

-- A new family from a spare villager of an existing family. The new family has no home, so it is homeless.
function M.family_add(request, raw)
    local wantAdult = rawBool(raw, "adult", false)
    local count = request.count or 1
    if count < 1 or count > M.MAX_FAMILY_CHANGE then
        return { ok = false, error = "count must be a whole number from 1 to " .. M.MAX_FAMILY_CHANGE }
    end
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local before = regionRow(region)
    local added, errors = {}, {}
    for _ = 1, count do
        local member = spareMember(region, wantAdult)
        if not member then errors[#errors + 1] = "no family with 2 living members is left" .. (wantAdult and " (adult wanted)" or ""); break end
        local role = read(function() return member.role end)
        local okLeave, errLeave = pcall(function() member:removeFromFamilyIfHasOne(false) end)
        if not okLeave then errors[#errors + 1] = "removeFromFamilyIfHasOne: " .. tostring(errLeave); break end
        local okAdd, id = pcall(function() return region:AddNewFamily({ member }) end)
        if not okAdd then errors[#errors + 1] = "AddNewFamily: " .. tostring(id); break end
        added[#added + 1] = { family_id = unwrap(id), role = role }
    end
    return { ok = #errors == 0, error = errors[1], added = added, before = before, after = regionRow(region) }
end

return M
