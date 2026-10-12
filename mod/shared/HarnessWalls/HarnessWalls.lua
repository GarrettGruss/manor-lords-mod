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
