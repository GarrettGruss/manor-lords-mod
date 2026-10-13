-- HarnessWalls: build and read walls outside the manor system (spec 14).
-- Why: a wall is a `Road` actor with roadType 3 (Wall) and a wallType (1 Fence, 2 Wooden, 3 StoneLow, 4 StoneHigh).
-- The road tool makes a plain road (roadType 0, wallType 0). Writing roadType and wallType on it and rebuilding its meshes
-- makes a wall mesh at once, with no manor, no goods and no builders (spike result, see implementation-notes/free-walls.md).
-- Plan of use: road_mode on, click the points with the real mouse, road_commit, wall_make.
--
-- Rules: call only on the game thread. No save function. Every input is checked before it is used.

local M = {}

M.ROAD_TYPE_WALL = 3
M.MAX_ROWS = 40
M.WALL_TYPES = { fence = 1, wooden = 2, stone_low = 3, stone_high = 4 }

local WALL_NAMES = { [0] = "none", "fence", "wooden", "stone_low", "stone_high" }

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

-- The shared request parser of HarnessActions knows only its own fields, so the wall fields are read from the raw request text.
local function numberField(raw, name)
    return tonumber((raw or ""):match('"' .. name .. '"%s*:%s*(%d+)'))
end

local function flagField(raw, name)
    local text = (raw or ""):match('"' .. name .. '"%s*:%s*(%w+)')
    if text == "true" or text == "1" then return true end
    if text == "false" or text == "0" then return false end
    return nil
end

local function player()
    local found = FindFirstOf("MyPawnCPP_BP3_C") or FindFirstOf("PawnCPP")
    if isValid(found) then return found end
    return nil
end

local function roadId(road)
    local name = read(function() return road:GetFName():ToString() end)
    return name and tonumber(name:match("(%d+)$")) or nil
end

local function allRoads()
    local out = {}
    for _, road in ipairs(FindAllOf("Road") or {}) do
        if isValid(road) and not road:GetFullName():find("Default__", 1, true) then out[#out + 1] = road end
    end
    return out
end

local function roadById(id)
    for _, road in ipairs(allRoads()) do
        if roadId(road) == id then return road end
    end
    return nil
end

-- removeRoad empties the road (no spline length, no meshes) and leaves the actor in the world, so an empty road is not a wall.
local function isEmpty(road)
    local length = read(function() return road.Spline:GetSplineLength() end)
    return length == nil or length <= 0
end

local function isWall(road)
    if isEmpty(road) then return false end
    local roadType = read(function() return road.roadType end)
    local wallType = read(function() return road.wallType end)
    return roadType == M.ROAD_TYPE_WALL or (wallType or 0) ~= 0
end

local function middleOf(road)
    local length = read(function() return road.Spline:GetSplineLength() end)
    if not length then return nil, nil end
    local point = read(function() return road.Spline:GetLocationAtDistanceAlongSpline(length / 2, 1) end)
    if not point then return length, nil end
    return length, { x = math.floor(point.X), y = math.floor(point.Y), z = math.floor(point.Z) }
end

local function rowOf(road)
    local wallType = read(function() return road.wallType end) or 0
    local length, middle = middleOf(road)
    return {
        id = roadId(road),
        road_type = read(function() return road.roadType end),
        wall_type = wallType,
        wall_name = WALL_NAMES[wallType] or tostring(wallType),
        blueprint = read(function() return road.isBlueprint end) == true,
        meshes = read(function() return road.StaticMeshes:GetArrayNum() end),
        length = length and math.floor(length) or nil,
        middle = middle,
    }
end

-- Count the wall roads and list the first rows. `counts` has one number for each wall type name.
function M.wall_state()
    local rows, counts = {}, { none = 0, fence = 0, wooden = 0, stone_low = 0, stone_high = 0 }
    local total = 0
    for _, road in ipairs(allRoads()) do
        if isWall(road) then
            total = total + 1
            local row = rowOf(road)
            counts[row.wall_name] = (counts[row.wall_name] or 0) + 1
            if #rows < M.MAX_ROWS then rows[#rows + 1] = row end
        end
    end
    return { ok = true, total = total, counts = counts, walls = rows, roads = #allRoads() }
end

-- Turn the road mode of the player on or off. Road mode shows the road preview, so clicks place road points.
function M.road_mode(_, raw)
    local on = flagField(raw, "on")
    if on == nil then return { ok = false, error = "on must be true, false, 1 or 0" } end
    local pawn = player()
    if not pawn then return { ok = false, error = "no player pawn" } end
    pawn:setRoadMode(on, { X = 0, Y = 0, Z = 0 }, false)
    return { ok = true, road_mode = read(function() return pawn.roadmode end) }
end

-- Commit the road that the player is drawing. The answer is the new road id.
function M.road_commit()
    local pawn = player()
    if not pawn then return { ok = false, error = "no player pawn" } end
    local road = pawn:commitRoad()
    if not isValid(road) then return { ok = false, error = "commitRoad made no road (place at least 2 points first)" } end
    return { ok = true, road = roadId(road), wall = rowOf(road) }
end

-- Make a committed road a wall: the request has `road` (the road id) and `wall_type`: 2 (wooden), 3 or 4.
-- Fence (1) is refused: the mesh rebuild gives it no mesh.
function M.wall_make(_, raw)
    local id = numberField(raw, "road")
    local wallType = numberField(raw, "wall_type") or M.WALL_TYPES.wooden
    if type(id) ~= "number" then return { ok = false, error = "road must be a road id (see wall_state, road_commit)" } end
    if wallType ~= 2 and wallType ~= 3 and wallType ~= 4 then
        return { ok = false, error = "wall_type must be 2 (wooden), 3 (stone_low) or 4 (stone_high)" }
    end
    local road = roadById(id)
    if not road then return { ok = false, error = "no road with id " .. tostring(id) } end
    local before = rowOf(road)
    road.roadType = M.ROAD_TYPE_WALL
    road.wallType = wallType
    road:cleanSplineMeshes()
    road:spawnRoadMeshes()
    return { ok = true, before = before, after = rowOf(road) }
end

---------------------------------------------------------------------------------------------
-- Wall pieces: the part of a planner wall that blocks units
---------------------------------------------------------------------------------------------
-- Why: a planner bailey wall is a plan road plus a row of GhostStaticMeshActor pieces (buildingType 470, WoodenWallPiece)
-- with the palisade mesh and collision BlockAll. Bandits path around those pieces. A road made a wall by wall_make has
-- no pieces and does not block (run s14-wallblock-1, s14-bailey-block-1). The game has no reflected function that makes pieces,
-- so the mod spawns them itself along a road spline.

M.PIECE_CLASS = "/Script/ManorLords.GhostStaticMeshActor"
M.PIECE_MESH = "/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam.SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam"
M.PIECE_BUILDING_TYPE = 470
M.PIECE_MESH_LENGTH = 200   -- cm at scale 1: bailey pieces are about 240 cm apart at X scale 1.22
M.PIECE_STEP_DEFAULT = 200
M.PIECE_STEP_MIN = 50
M.PIECE_LIMIT = 400
M.SPAWN_ALWAYS = 1          -- ESpawnActorCollisionHandlingMethod::AlwaysSpawn
M.MOBILITY_MOVABLE = 2

local spawnedPieces = {}    -- road id -> list of piece actors made by this module

local function findObject(path)
    local ok, found = pcall(StaticFindObject, path)
    if ok and isValid(found) then return found end
    return nil
end

-- Points along the spline every `step` cm, the last point at the end of the spline.
local function pointsAlong(road, step)
    local length = read(function() return road.Spline:GetSplineLength() end)
    if not length or length <= 0 then return nil, "the road has no spline length" end
    local points, distance = {}, 0
    while distance < length do
        points[#points + 1] = road.Spline:GetLocationAtDistanceAlongSpline(distance, 1)
        distance = distance + step
    end
    points[#points + 1] = road.Spline:GetLocationAtDistanceAlongSpline(length, 1)
    return points
end

-- A bailey piece stands at a point, faces back to the previous point and is stretched along X to the gap.
local function pieceTransform(from, to)
    local dx, dy = from.X - to.X, from.Y - to.Y
    local yaw = math.atan(dy, dx)
    return {
        Translation = { X = from.X, Y = from.Y, Z = from.Z },
        Rotation = { X = 0, Y = 0, Z = math.sin(yaw / 2), W = math.cos(yaw / 2) },
        Scale3D = { X = math.sqrt(dx * dx + dy * dy) / M.PIECE_MESH_LENGTH, Y = 1, Z = 1 },
    }
end

local function spawnPiece(statics, class, mesh, worldContext, transform)
    local actor = statics:BeginDeferredActorSpawnFromClass(worldContext, class, transform, M.SPAWN_ALWAYS, nil, 0)
    if not isValid(actor) then error("BeginDeferredActorSpawnFromClass gave no actor") end
    statics:FinishSpawningActor(actor, transform, 0)
    local component = actor.StaticMeshComponent
    component:SetMobility(M.MOBILITY_MOVABLE)
    component:SetStaticMesh(mesh)
    component:SetCollisionProfileName(FName("BlockAll"), true)
    actor.buildingType = M.PIECE_BUILDING_TYPE
    actor.wallType = M.WALL_TYPES.wooden
    return actor
end

-- Spawn palisade wall pieces along a road: the request has `road` (a road id) and `step` (cm between pieces, default 200).
-- The road may be a plain road or a wall road. The pieces are the same class, mesh and collision as the planner's bailey pieces.
function M.wall_pieces(_, raw)
    local id = numberField(raw, "road")
    local step = numberField(raw, "step") or M.PIECE_STEP_DEFAULT
    if type(id) ~= "number" then return { ok = false, error = "road must be a road id (see wall_state, road_commit)" } end
    if step < M.PIECE_STEP_MIN then return { ok = false, error = "step must be at least " .. M.PIECE_STEP_MIN .. " cm" } end
    local road = roadById(id)
    if not road then return { ok = false, error = "no road with id " .. tostring(id) } end
    local statics = findObject("/Script/Engine.Default__GameplayStatics")
    local class = findObject(M.PIECE_CLASS)
    local mesh = findObject(M.PIECE_MESH)
    if not statics or not class then return { ok = false, error = "GameplayStatics or " .. M.PIECE_CLASS .. " not found" } end
    if not mesh then return { ok = false, error = "palisade mesh not loaded: " .. M.PIECE_MESH } end
    local points, why = pointsAlong(road, step)
    if not points then return { ok = false, error = why } end
    if #points - 1 > M.PIECE_LIMIT then return { ok = false, error = "too many pieces: " .. (#points - 1) .. " (limit " .. M.PIECE_LIMIT .. ")" } end
    spawnedPieces[id] = spawnedPieces[id] or {}
    local made = 0
    for i = 2, #points do
        local actor = spawnPiece(statics, class, mesh, road, pieceTransform(points[i], points[i - 1]))
        table.insert(spawnedPieces[id], actor)
        made = made + 1
    end
    return { ok = true, road = id, pieces = made, step = step, total_for_road = #spawnedPieces[id] }
end

-- Destroy the pieces that wall_pieces made for a road.
function M.wall_pieces_clear(_, raw)
    local id = numberField(raw, "road")
    if type(id) ~= "number" then return { ok = false, error = "road must be a road id" } end
    local removed = 0
    for _, actor in ipairs(spawnedPieces[id] or {}) do
        if isValid(actor) then
            actor:K2_DestroyActor()
            removed = removed + 1
        end
    end
    spawnedPieces[id] = nil
    return { ok = true, road = id, removed = removed }
end

-- Read the size of the global obstacle list (RTSGameManager.SpatialComponent.Obstacles, struct Obstacle2D).
-- Why only the size: Obstacle2D has no reflected fields, and reading a struct element through the bridge (:get()) can crash the game.
function M.path_state()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local spatial = read(function() return engine.SpatialComponent end)
    if not isValid(spatial) then return { ok = false, error = "the engine has no SpatialComponent" } end
    return {
        ok = true,
        obstacles = read(function() return spatial.Obstacles:GetArrayNum() end),
        draw_pathfinding_debug = read(function() return engine.drawPathfindingDebug end),
    }
end

M.STAT_FIELDS = { "bWorkInProgress", "BuildingCategory", "bVisibleInUi", "isPlaza", "bSize", "bCircularBorder", "isWork", "job",
    "garrisonLimit", "buildingFunction", "maxHp", "range", "rangeType", "needsRoad", "collidesWithRoads", "canRelocate", "upgradedFrom",
    "flammable", "constructionCost", "RequiresSkilledBuilders", "maxInRegion", "settlementLevel", "AIcanBuild", "moduleCategory",
    "isModule", "placedWithin" }

-- Spike, read only: the scalar fields of one buildingStats row (`kind` = row name, the building type number).
function M.building_stat(_, raw)
    local kind = numberField(raw, "kind")
    if type(kind) ~= "number" then return { ok = false, error = "kind must be a building type number" } end
    local stats = findObject("/Game/NotStronghold/Data/buildingStats.buildingStats")
    if not stats then return { ok = false, error = "buildingStats is not loaded" } end
    local okRow, row = pcall(function() return stats:FindRow(tostring(kind)) end)
    if not okRow or row == nil then return { ok = false, error = "no buildingStats row " .. kind } end
    local values = {}
    for _, name in ipairs(M.STAT_FIELDS) do
        local value = read(function() return row[name] end)
        if type(value) == "number" or type(value) == "boolean" then values[name] = value end
    end
    return { ok = true, kind = kind, values = values }
end

local function textField(raw, name)
    return (raw or ""):match('"' .. name .. '"%s*:%s*"([^"]*)"')
end

-- Spike, read only: every mesh component whose static mesh path contains `mesh` (text). Groups by owner class and
-- component class, with counts, collision and visibility. The bridge lists at most 500 objects of a class; this scans all.
function M.mesh_users(_, raw)
    local wanted = textField(raw, "mesh")
    if not wanted or wanted == "" then return { ok = false, error = "mesh must be a text, for example PalisadeWall" } end
    local groups, total, scanned = {}, 0, 0
    for _, className in ipairs({ "StaticMeshComponent", "InstancedStaticMeshComponent", "HierarchicalInstancedStaticMeshComponent",
                                 "SplineMeshComponent" }) do
        for _, component in ipairs(FindAllOf(className) or {}) do
            scanned = scanned + 1
            local mesh = read(function() return component.StaticMesh:GetFullName() end)
            if mesh and mesh:find(wanted, 1, true) and not component:GetFullName():find("Default__", 1, true) then
                local owner = read(function() return component:GetOwner() end)
                local ownerClass = owner and read(function() return owner:GetClass():GetFName():ToString() end) or "none"
                local key = className .. " on " .. ownerClass
                local group = groups[key] or { count = 0, instances = 0, collision = {}, visible = 0, example = nil }
                group.count = group.count + 1
                group.instances = group.instances + (read(function() return component:GetInstanceCount() end) or 1)
                local collision = tostring(read(function() return component:GetCollisionEnabled() end))
                group.collision[collision] = (group.collision[collision] or 0) + 1
                if read(function() return component:IsVisible() end) then group.visible = group.visible + 1 end
                group.example = group.example or component:GetFullName()
                groups[key] = group
                total = total + 1
            end
        end
    end
    return { ok = true, mesh = wanted, total = total, scanned = scanned, groups = groups }
end

local function buildingById(id)
    for _, building in ipairs(FindAllOf("SMBuildingMaster") or {}) do
        if isValid(building) and roadId(building) == id then return building end
    end
    return nil
end

-- Spike, read only: health and fire state of one building (`building` = id): type, hp, maxHp, onFire, fireAmt, rubble, built, collapse chance.
-- Why: to see whether the game damages or burns a wall (spec 14, "Fire and damage as a breach").
function M.building_health(_, raw)
    local id = numberField(raw, "building")
    if type(id) ~= "number" then return { ok = false, error = "building must be a building id" } end
    local building = buildingById(id)
    if not building then return { ok = false, error = "no building with id " .. tostring(id) } end
    return {
        ok = true, building = id,
        type = read(function() return building.Data.bType end),
        hp = read(function() return building.Data.hp end),
        max_hp = read(function() return building.Data.maxHp end),
        on_fire = read(function() return building.onFire end),
        fire_amount = read(function() return building.fireAmt end),
        rubble = read(function() return building:IsRubble() end),
        built = read(function() return building:IsConstructed() end),
        collapse_chance = read(function() return building:GetCollapseChance() end),
    }
end

-- Unsafe spike commands (spec 14, "Unsafe commands and tools"). They change game data outside the normal game flow (one crashed the
-- game), so they are refused unless the game process was started with HARNESS_ALLOW_UNSAFE=1. Test games only, never a user save.
M.UNSAFE_ENV = "HARNESS_ALLOW_UNSAFE"

local function unsafeAllowed()
    return (os.getenv and os.getenv(M.UNSAFE_ENV)) == "1"
end

local function unsafe(name, handler)
    return function(...)
        if not unsafeAllowed() then
            return { ok = false, error = name .. " is an unsafe spike command: start the game with " .. M.UNSAFE_ENV .. "=1 (test games only)" }
        end
        return handler(...)
    end
end

-- Empty the global obstacle list (TArray:Empty) to test whether path finding reads it.
-- It also removes the entries of buildings and map features. The next squad spawn crashed the game (null read).
M.path_obstacles_clear = unsafe("path_obstacles_clear", function()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local spatial = isValid(engine) and read(function() return engine.SpatialComponent end) or nil
    if not isValid(spatial) then return { ok = false, error = "no SpatialComponent on the engine" } end
    local before = read(function() return spatial.Obstacles:GetArrayNum() end)
    local ok, err = pcall(function() spatial.Obstacles:Empty() end)
    if not ok then return { ok = false, error = "Obstacles:Empty failed: " .. tostring(err), before = before } end
    return { ok = true, before = before, after = read(function() return spatial.Obstacles:GetArrayNum() end) }
end)

M.STAT_WRITABLE = { isModule = "boolean", moduleCategory = "number", placedWithin = "number", needsRoad = "boolean",
    bVisibleInUi = "boolean", BuildingCategory = "number" }

-- Write one field of a buildingStats row in memory (`kind`, `field`, `value`). Lasts until the game ends.
M.building_stat_write = unsafe("building_stat_write", function(_, raw)
    local kind = numberField(raw, "kind")
    local field = (raw or ""):match('"field"%s*:%s*"([%w_]+)"')
    local kindOfField = field and M.STAT_WRITABLE[field]
    if type(kind) ~= "number" then return { ok = false, error = "kind must be a building type number" } end
    if not kindOfField then return { ok = false, error = "field must be one of isModule, moduleCategory, placedWithin, needsRoad, bVisibleInUi, BuildingCategory" } end
    local value
    if kindOfField == "boolean" then value = flagField(raw, "value") else value = numberField(raw, "value") end
    if value == nil then return { ok = false, error = "value is missing or has the wrong type for " .. field } end
    local stats = findObject("/Game/NotStronghold/Data/buildingStats.buildingStats")
    if not stats then return { ok = false, error = "buildingStats is not loaded" } end
    local okRow, row = pcall(function() return stats:FindRow(tostring(kind)) end)
    if not okRow or row == nil then return { ok = false, error = "no buildingStats row " .. kind } end
    local before = read(function() return row[field] end)
    row[field] = value
    return { ok = true, kind = kind, field = field, before = before, after = read(function() return row[field] end) }
end)

-- Call the game's own completion routine PawnCPP:constructionComplete(building) on one building (`building` = id).
-- Why: finish_manor_site only writes Data.constructed; a planner wall is part of the manor's construction, and its path block
-- (obstacle entries) appears only when builders build it. It calls a game state change outside the normal build flow.
M.construction_complete = unsafe("construction_complete", function(_, raw)
    local id = numberField(raw, "building")
    if type(id) ~= "number" then return { ok = false, error = "building must be a building id" } end
    local building = buildingById(id)
    if not building then return { ok = false, error = "no building with id " .. tostring(id) } end
    local pawn = player()
    if not pawn then return { ok = false, error = "no player pawn" } end
    local before = M.path_state().obstacles
    pawn:constructionComplete(building)
    return { ok = true, building = id, obstacles_before = before, obstacles_after = M.path_state().obstacles,
             built = read(function() return building:IsConstructed() end) }
end)

-- Remove a wall road with the game's own remove call.
function M.wall_remove(_, raw)
    local id = numberField(raw, "road")
    if type(id) ~= "number" then return { ok = false, error = "road must be a road id" } end
    local road = roadById(id)
    if not road then return { ok = false, error = "no road with id " .. tostring(id) } end
    if not isWall(road) then return { ok = false, error = "road " .. id .. " is not a wall" } end
    local pawn = player()
    if not pawn then return { ok = false, error = "no player pawn" } end
    pawn:removeRoad(road)
    return { ok = true, empty = isEmpty(road) }
end

return M
