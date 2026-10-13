-- HarnessSteer: move orders for squads (spec 10, spike #59).
-- Why: the harness can spawn squads but cannot send them to a point. PawnCPP:formALineArmy is the function behind the
-- player's "form a line" order. This module calls it for a chosen squad and reads where the squad goes.
-- Spec 15 found that it has no effect on a bandit squad. This module tests it on every side.
--
-- Rules: call only on the game thread. No save function. Every input is checked before it is used.

local M = {}

M.MAX_COORDINATE = 500000
M.MAX_HALF_WIDTH = 2000
M.MAX_HOOKS = 60
M.MAX_HOOK_LOG = 200
M.DEFAULT_FORMATION = "Line"

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

local function round(value)
    if type(value) ~= "number" then return nil end
    return math.floor(value + 0.5)
end

local function isNumberIn(value, limit)
    return type(value) == "number" and math.abs(value) <= limit
end

---------------------------------------------------------------------------------------------
-- Owner pawn of a squad
---------------------------------------------------------------------------------------------

local function sideOfPawn(pawn)
    if read(function() return pawn.isMainPlayer end) == true then return "player" end
    if read(function() return pawn.isBandit end) == true then return "bandit" end
    if read(function() return pawn.isAI end) == true then return "ai" end
    return "other"
end

-- The pawn that lists the squad id in commandedSquads. Returns pawn, side.
local function ownerOf(squadId)
    for _, pawn in ipairs(FindAllOf("PawnCPP") or {}) do
        if isValid(pawn) then
            local handles = read(function() return pawn.commandedSquads end)
            local count = handles and read(function() return handles:GetArrayNum() end) or 0
            for i = 1, count do
                if read(function() return unwrap(handles[i]).Value end) == squadId then return pawn, sideOfPawn(pawn) end
            end
        end
    end
    return nil, nil
end

---------------------------------------------------------------------------------------------
-- Read: where is the squad, and where do its units want to go
---------------------------------------------------------------------------------------------

local function vectorOf(vector)
    if vector == nil then return nil end
    local x, y = read(function() return vector.X end), read(function() return vector.Y end)
    if x == nil or y == nil then return nil end
    return { x = x, y = y, z = read(function() return vector.Z end) }
end

local function average(sum, count)
    if count == 0 then return nil end
    return { x = round(sum.x / count), y = round(sum.y / count) }
end

local function distance(a, b)
    if not a or not b then return nil end
    return round(math.sqrt((a.x - b.x) ^ 2 + (a.y - b.y) ^ 2))
end

-- Centre of the living units, mean of their target positions, and the number of units.
local function squadReading(squadId)
    local pos, target = { x = 0, y = 0 }, { x = 0, y = 0 }
    local units, targets = 0, 0
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) and read(function() return unit.assignedSquadID.Value end) == squadId and read(function() return unit.dead end) ~= true then
            local at = vectorOf(read(function() return unit.realPos end))
            if at then pos.x, pos.y, units = pos.x + at.x, pos.y + at.y, units + 1 end
            local goal = vectorOf(read(function() return unit:getTargetPos():get() end) or read(function() return unit:getTargetPos() end))
            if goal then target.x, target.y, targets = target.x + goal.x, target.y + goal.y, targets + 1 end
        end
    end
    return { units = units, center = average(pos, units), target_mean = average(target, targets) }
end

-- request.squad: squad id. Result: owner side, unit count, centre, mean unit target.
function M.steer_state(request)
    local squadId = request.squad
    if type(squadId) ~= "number" or squadId < 1 then return { ok = false, error = "squad must be a squad id (a whole number above 0)" } end
    local _, side = ownerOf(squadId)
    local reading = squadReading(squadId)
    reading.ok, reading.squad, reading.side = true, squadId, side
    return reading
end

---------------------------------------------------------------------------------------------
-- Order
---------------------------------------------------------------------------------------------

local function checkedMove(request)
    local limit = M.MAX_COORDINATE
    if type(request.squad) ~= "number" or request.squad < 1 then return nil, "squad must be a squad id (a whole number above 0)" end
    if not isNumberIn(request.x, limit) or not isNumberIn(request.y, limit) then return nil, "x and y are required numbers within " .. limit end
    local z = request.z or 0
    if not isNumberIn(z, limit) then return nil, "z must be a number within " .. limit end
    local half = request.half_width or 300
    if not isNumberIn(half, M.MAX_HALF_WIDTH) or half < 0 then return nil, "half_width must be a number from 0 to " .. M.MAX_HALF_WIDTH end
    local formation = request.formation or M.DEFAULT_FORMATION
    if type(formation) ~= "string" or formation == "" then return nil, "formation must be a name such as Line" end
    return { squad = request.squad, x = request.x, y = request.y, z = z, half = half, formation = formation }
end

-- Order one squad to a line centred on (x, y). The line is perpendicular to the way from the squad to the point.
-- The owner pawn of the squad gives the order (the player pawn for a player squad).
function M.steer_move(request)
    local wanted, problem = checkedMove(request)
    if not wanted then return { ok = false, error = problem } end
    local pawn, side = ownerOf(wanted.squad)
    if not pawn then return { ok = false, error = "no pawn lists squad " .. wanted.squad .. " in commandedSquads" } end
    local before = squadReading(wanted.squad)
    if before.units == 0 or not before.center then return { ok = false, error = "squad " .. wanted.squad .. " has no living unit" } end
    local dx, dy = wanted.x - before.center.x, wanted.y - before.center.y
    local length = math.sqrt(dx * dx + dy * dy)
    if length < 1 then return { ok = false, error = "the squad is already at the point" } end
    -- Unit vector across the way of march.
    local ax, ay = -dy / length * wanted.half, dx / length * wanted.half
    local line = { A = { X = wanted.x - ax, Y = wanted.y - ay, Z = wanted.z }, B = { X = wanted.x + ax, Y = wanted.y + ay, Z = wanted.z } }
    local ok, err = pcall(function() pawn:formALineArmy({ { Value = wanted.squad } }, line, FName(wanted.formation), line) end)
    if not ok then return { ok = false, error = "formALineArmy: " .. tostring(err), side = side } end
    return { ok = true, squad = wanted.squad, side = side, formation = wanted.formation, target = { x = wanted.x, y = wanted.y },
             before = before, distance_before = distance(before.center, wanted) }
end

-- Select one squad for its owner (what a click on the unit card does). The next right click of the mouse orders the selection.
function M.steer_select(request)
    local squadId = request.squad
    if type(squadId) ~= "number" or squadId < 1 then return { ok = false, error = "squad must be a squad id (a whole number above 0)" } end
    local pawn, side = ownerOf(squadId)
    if not pawn then return { ok = false, error = "no pawn lists squad " .. squadId .. " in commandedSquads" } end
    local ok, err = pcall(function() pawn:selectSquad({ Value = squadId }, true, false) end)
    if not ok then return { ok = false, error = "selectSquad: " .. tostring(err) } end
    local selected = read(function() return pawn:isSquadSelected({ Value = squadId }):get() end)
    return { ok = true, squad = squadId, side = side, selected = selected }
end

---------------------------------------------------------------------------------------------
-- Order through the game's own right-click handler (no OS click)
---------------------------------------------------------------------------------------------
-- The real right click moved the squad (run s59-e) and called no UFunction that a hook saw. So the order is native code that
-- reads the terrain point under the cursor. This path puts the cursor on a world point (PlayerController:SetMouseLocation),
-- waits for the game to update the point, then calls the pawn's right-click events.

local function playerPawn()
    for _, pawn in ipairs(FindAllOf("PawnCPP") or {}) do
        if isValid(pawn) and sideOfPawn(pawn) == "player" then return pawn end
    end
    return nil
end

local function playerController(pawn)
    local controller = read(function() return pawn:GetController() end)
    if isValid(controller) then return controller end
    return read(function() return FindFirstOf("PlayerController") end)
end

-- Put the cursor on screen over the world point (x, y, z). Reads back the terrain point under the cursor of the pawn.
function M.steer_cursor(request)
    if not isNumberIn(request.x, M.MAX_COORDINATE) or not isNumberIn(request.y, M.MAX_COORDINATE) then
        return { ok = false, error = "x and y are required numbers within " .. M.MAX_COORDINATE }
    end
    local pawn = playerPawn()
    local controller = pawn and playerController(pawn)
    if not controller then return { ok = false, error = "no player pawn or controller" } end
    local screen = {}
    local ok, projected = pcall(function() return controller:ProjectWorldLocationToScreen({ X = request.x, Y = request.y, Z = request.z or 0 }, screen, false) end)
    if not ok then return { ok = false, error = "ProjectWorldLocationToScreen: " .. tostring(projected) } end
    local sx, sy = read(function() return screen.X end), read(function() return screen.Y end)
    if sx == nil or sy == nil then return { ok = false, error = "the point has no screen position", projected = tostring(read(function() return projected:get() end)) } end
    local set, err = pcall(function() controller:SetMouseLocation(math.floor(sx), math.floor(sy)) end)
    if not set then return { ok = false, error = "SetMouseLocation: " .. tostring(err), screen = { x = sx, y = sy } } end
    return { ok = true, screen = { x = round(sx), y = round(sy) }, on_screen = read(function() return projected:get() end) }
end

-- The terrain point under the cursor, as the pawn sees it.
function M.steer_mouse3d()
    local pawn = playerPawn()
    if not pawn then return { ok = false, error = "no player pawn" } end
    local point = vectorOf(read(function() return pawn:getMouse3d():get() end) or read(function() return pawn:getMouse3d() end))
    return { ok = true, point = point }
end

-- Call the right-click events of the pawn (press, then release). The selected squads walk to the terrain point under the cursor.
function M.steer_rmb()
    local pawn = playerPawn()
    if not pawn then return { ok = false, error = "no player pawn" } end
    local before = vectorOf(read(function() return pawn:getMouse3d():get() end) or read(function() return pawn:getMouse3d() end))
    local ok, err = pcall(function() pawn:RMB_BP_pressed() end)
    if not ok then return { ok = false, error = "RMB_BP_pressed: " .. tostring(err) } end
    ok, err = pcall(function() pawn:RMB_BP_released() end)
    if not ok then return { ok = false, error = "RMB_BP_released: " .. tostring(err) } end
    return { ok = true, point = before }
end

---------------------------------------------------------------------------------------------
-- Hook recorder: shows which functions the game calls while a person (or the OS mouse) gives an order
---------------------------------------------------------------------------------------------

local hooked = {}
local hookLog = {}
local hookCounts = {}

local function describe(param)
    local value = read(function() return param:get() end)
    if value == nil then return "?" end
    if type(value) ~= "userdata" then return tostring(value) end
    local fields = {}
    for _, name in ipairs({ "Value", "X", "Y", "Z" }) do
        local part = read(function() return value[name] end)
        if part ~= nil then fields[#fields + 1] = name .. "=" .. tostring(part) end
    end
    local a, b = read(function() return value.A end), read(function() return value.B end)
    if a and b then
        local av, bv = vectorOf(a), vectorOf(b)
        if av and bv then fields[#fields + 1] = string.format("A=(%d,%d) B=(%d,%d)", av.x, av.y, bv.x, bv.y) end
    end
    if #fields == 0 then return read(function() return value:GetFullName() end) or "userdata" end
    return table.concat(fields, " ")
end

local function record(path, ...)
    hookCounts[path] = (hookCounts[path] or 0) + 1
    if #hookLog >= M.MAX_HOOK_LOG then return end
    local args = {}
    for i = 1, select("#", ...) do args[#args + 1] = describe(select(i, ...)) end
    hookLog[#hookLog + 1] = { path = path, n = hookCounts[path], args = table.concat(args, " | "), clock = round(os.clock() * 1000) }
end

-- request.functions: function paths joined by commas, such as "/Script/ManorLords.PawnCPP:formALineArmy,/Script/ManorLords.PawnCPP:selectSquad".
-- A string, because the command reader does not pass lists.
function M.steer_hook(request)
    local list = {}
    if type(request.functions) == "string" then
        for path in request.functions:gmatch("[^,]+") do list[#list + 1] = path end
    end
    if #list == 0 or #list > M.MAX_HOOKS then return { ok = false, error = "functions must be 1 to " .. M.MAX_HOOKS .. " function paths joined by commas" } end
    local added, failed = 0, {}
    for _, path in ipairs(list) do
        if type(path) ~= "string" or not path:match("^/[%w_/%.]+:[%w_ ]+$") then
            failed[#failed + 1] = tostring(path) .. ": not a function path"
        elseif not hooked[path] then
            local ok, err = pcall(function() RegisterHook(path, function(self, ...) record(path, ...) end) end)
            if ok then hooked[path] = true; added = added + 1 else failed[#failed + 1] = path .. ": " .. tostring(err) end
        end
    end
    return { ok = true, added = added, failed = failed }
end

-- Read the recorded calls. request.clear = true empties the log. The counts keep every call (the log keeps the first MAX_HOOK_LOG).
function M.steer_hook_log(request)
    local out = { ok = true, log = hookLog, counts = hookCounts }
    if request.clear == true then hookLog, hookCounts = {}, {} end
    return out
end

return M
