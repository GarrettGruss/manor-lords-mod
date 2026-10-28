-- The map border for armies that come in from the edge (change update-spawn-from-map-border).
-- Pure rules first (no game calls), then one reader of the game map bounds. A spawn point is outside the playable square, so the army walks in.
-- Facts (spike A, B, run 20261028-020728-5a13): spawnArmy ignores its arrival days, an army spawned 3000 units outside the edge walks in
-- on its own when its lord has a challenge at the manor, and the game has no navmesh to test walkable land.
local M = {}

local SIDES = { "west", "east", "south", "north" } -- the four edges; "south" is the edge with the smallest y

-- Compass words by 45 degree sector, counted from east (+x) to the left. `north_axis` "-y" (default): north is -y, east is +x.
-- The axis is the common top-down map convention of Unreal levels; it is not verified in the game (see notes/direction.md).
local COMPASS = { "east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east" }
local COMPASS_NORTH_PLUS_Y = { "east", "north-east", "north", "north-west", "west", "south-west", "south", "south-east" }

-- Bounds from a list of points ({ x, y }): { min_x, max_x, min_y, max_y }, or nil for an empty list.
function M.bounds_of(points)
    local bounds
    for _, point in ipairs(points) do
        if bounds == nil then
            bounds = { min_x = point.x, max_x = point.x, min_y = point.y, max_y = point.y }
        else
            bounds.min_x, bounds.max_x = math.min(bounds.min_x, point.x), math.max(bounds.max_x, point.x)
            bounds.min_y, bounds.max_y = math.min(bounds.min_y, point.y), math.max(bounds.max_y, point.y)
        end
    end
    return bounds
end

local function clamp(value, low, high)
    if low > high then return (low + high) / 2 end
    return math.max(low, math.min(high, value))
end

local function distance(a, b)
    return math.sqrt((a.x - b.x) ^ 2 + (a.y - b.y) ^ 2)
end

-- The border point of each side nearest to `target`, `margin` units outside the square. `inset` keeps it away from the corners.
function M.side_points(bounds, target, margin, inset)
    local x = clamp(target.x, bounds.min_x + inset, bounds.max_x - inset)
    local y = clamp(target.y, bounds.min_y + inset, bounds.max_y - inset)
    return {
        west = { x = bounds.min_x - margin, y = y, side = "west" },
        east = { x = bounds.max_x + margin, y = y, side = "east" },
        south = { x = x, y = bounds.min_y - margin, side = "south" },
        north = { x = x, y = bounds.max_y + margin, side = "north" },
    }
end

-- The border point for a raid on `target` ({ x, y }). Rule `nearest`: the nearest side whose point is at least `min_distance`
-- from the target; when no side is far enough, the farthest one. `avoid` (optional { x, y }) skips a side that is closer than
-- `avoid_distance` to that point (a second army from another side). Returns { x, y, side, distance }.
function M.pick(bounds, target, options)
    local points = M.side_points(bounds, target, options.margin or 3000, options.inset or 5000)
    local ranked = {}
    for _, name in ipairs(SIDES) do
        local point = points[name]
        point.distance = distance(point, target)
        if options.avoid ~= nil and distance(point, options.avoid) < (options.avoid_distance or 0) then point.skip = true end
        ranked[#ranked + 1] = point
    end
    table.sort(ranked, function(a, b) return a.distance < b.distance end)
    local min_distance = options.min_distance or 0
    local farthest
    for _, point in ipairs(ranked) do
        if not point.skip then
            if point.distance >= min_distance then return point end
            if farthest == nil or point.distance > farthest.distance then farthest = point end
        end
    end
    return farthest or ranked[#ranked]
end

-- Compass word (one of 8) for the direction from `from` to `to`. `north_axis` is "-y" (default) or "+y".
function M.direction(from, to, north_axis)
    local dx, dy = to.x - from.x, to.y - from.y
    local angle = math.deg(math.atan(dy, dx)) -- 0 = +x, counter-clockwise in x/y
    if angle < 0 then angle = angle + 360 end
    local sector = math.floor((angle + 22.5) / 45) % 8 + 1
    local words = north_axis == "+y" and COMPASS_NORTH_PLUS_Y or COMPASS
    return words[sector]
end

-- True when `point` is outside the playable square.
function M.is_outside(bounds, point)
    return point.x < bounds.min_x or point.x > bounds.max_x or point.y < bounds.min_y or point.y > bounds.max_y
end

---------------------------------------------------------------------------------------------
-- Game reader
---------------------------------------------------------------------------------------------

-- The map edge actor is a Blueprint (`Medium_Map_Bounds_C` on Jagged_Cliffs) with spline components Spline1 to Spline6. Each spline is
-- one side of the playable square (2 points). Class names of other map sizes are tried too.
local EDGE_CLASSES = { "Medium_Map_Bounds_C", "Small_Map_Bounds_C", "Large_Map_Bounds_C" }
local SPLINE_COUNT = 6
local WORLD_SPACE = 1 -- ESplineCoordinateSpace::World

-- Returns bounds, or nil and a message. Call only on the game thread.
function M.read_bounds()
    local actor
    for _, name in ipairs(EDGE_CLASSES) do
        local ok, found = pcall(FindFirstOf, name)
        if ok and found ~= nil and found:IsValid() then actor = found break end
    end
    if actor == nil then return nil, "no map edge actor (" .. table.concat(EDGE_CLASSES, ", ") .. ")" end
    local points = {}
    for index = 1, SPLINE_COUNT do
        local ok, spline = pcall(function() return actor["Spline" .. index] end)
        if ok and spline ~= nil and spline:IsValid() then
            for point = 0, spline:GetNumberOfSplinePoints() - 1 do
                local at = spline:GetLocationAtSplinePoint(point, WORLD_SPACE)
                points[#points + 1] = { x = at.X, y = at.Y }
            end
        end
    end
    local bounds = M.bounds_of(points)
    if bounds == nil then return nil, "the map edge actor has no spline points" end
    return bounds
end

return M
