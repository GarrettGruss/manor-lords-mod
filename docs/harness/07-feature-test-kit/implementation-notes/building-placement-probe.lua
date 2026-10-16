-- HarnessPlacement: EXPERIMENT (spec 07, building placement). Try to place a building without a real mouse.
-- Idea: PawnCPP:getMouse3d returns (0, 0, -100000) because no mouse ray hits the ground. A post hook on getMouse3d
-- replaces that value with a chosen world position, then the harness clicks (LMB_BP_pressed and released).
-- Nothing here saves. Every step is a small function that reports what it did.

local M = {}

local HOOK_PATH = "/Script/ManorLords.PawnCPP:getMouse3d"
local MAX_ABS_COORD = 1000000

local state = { hookInstalled = false, target = nil, hookCalls = 0, hookReplaced = 0, hookError = nil }

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function player()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil, "no RTSMultiEngineCPP" end
    local pawn = engine.playerRef
    if not isValid(pawn) then return nil, "the player pawn is not loaded" end
    return pawn
end

local function playerRegion()
    local pawn, problem = player()
    if not pawn then return nil, problem end
    local region = pawn.currentRegion
    if not isValid(region) then return nil, "no current region" end
    return region
end

-- A TArray returned by a function can be read with # and an index. An element may be wrapped, then it has get.
local function listOf(array)
    local out = {}
    if array == nil then return out end
    for i = 1, #array do
        local element = array[i]
        local okGet, inner = pcall(function() return element:get() end)
        out[i] = okGet and inner or element
    end
    return out
end

local function locationOf(actor)
    local ok, vector = pcall(function() return actor:K2_GetActorLocation() end)
    if not ok or vector == nil then return nil end
    return { x = vector.X, y = vector.Y, z = vector.Z }
end

-- Count and list (up to a limit) the buildings of the player region, with their locations.
function M.buildings(limit)
    local region, problem = playerRegion()
    if not region then return nil, problem end
    local items = listOf(region:GetBuildings())
    local sample = {}
    for i = 1, math.min(#items, limit or 5) do
        local building = items[i]
        sample[i] = { name = building:GetFullName(), location = locationOf(building) }
    end
    return { count = #items, sample = sample }
end

-- Where is the player pawn (the camera focus), and which settled regions have buildings?
function M.where()
    local pawn, problem = player()
    if not pawn then return nil, problem end
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local regions = {}
    for _, region in ipairs(listOf(engine.regions)) do
        if isValid(region) and region.isSettled then
            local items = listOf(region:GetBuildings())
            local list = {}
            for i = 1, math.min(#items, 30) do list[i] = { name = items[i]:GetFullName():match("[%w_]+$"), location = locationOf(items[i]) } end
            regions[#regions + 1] = { name = region:GetFullName(), count = #items, first = items[1] and locationOf(items[1]) or nil, items = list }
        end
    end
    return { pawn = locationOf(pawn), regions = regions }
end

local function installHook()
    if state.hookInstalled then return true end
    local ok, err = pcall(RegisterHook, HOOK_PATH, function() end, function(_, ...)
        state.hookCalls = state.hookCalls + 1
        if not state.target then return end
        local count = select("#", ...)
        local returnValue = select(count, ...)
        local okSet, setError = pcall(function()
            returnValue:set({ X = state.target.x, Y = state.target.y, Z = state.target.z })
        end)
        if okSet then state.hookReplaced = state.hookReplaced + 1 else state.hookError = tostring(setError) end
    end)
    if not ok then return false, tostring(err) end
    state.hookInstalled = true
    return true
end

-- The 2D mouse position is (10, 10) without a real mouse: over the HUD. Move it to the middle of the screen.
local SCREEN_POINT = { X = 1200, Y = 700 }
local MOUSE_PATH = "/Script/ManorLords.PawnCPP:getMouse"
local mouseHookInstalled = false

local function installMouseHook()
    if mouseHookInstalled then return true end
    local ok, err = pcall(RegisterHook, MOUSE_PATH, function() end, function(_, ...)
        if not state.target then return end
        local returnValue = select(select("#", ...), ...)
        pcall(function() returnValue:set(SCREEN_POINT) end)
    end)
    if not ok then return false, tostring(err) end
    mouseHookInstalled = true
    return true
end

-- Variant: tell the game that the left button is down while armed, and build the preview mesh by hand.
local lmbHookInstalled = false

function M.forceButton(typeId)
    if not lmbHookInstalled then
        local ok, err = pcall(RegisterHook, "/Script/ManorLords.PawnCPP:getLMBPressedB", function() end, function(_, ...)
            if not state.target then return end
            local args = table.pack(...)
            pcall(function() args[args.n]:set(true) end)
        end)
        if not ok then return nil, tostring(err) end
        lmbHookInstalled = true
    end
    local pawn, problem = player()
    if not pawn then return nil, problem end
    pawn:updatePlacebuildingMesh(typeId, false, 0)
    return { forced = true }
end

local function checkCoordinate(value, name)
    if type(value) ~= "number" or value ~= value or math.abs(value) > MAX_ABS_COORD then
        return nil, name .. " must be a number within " .. MAX_ABS_COORD
    end
    return value
end

-- Step 1: fix the mouse position and enter building mode for one building type.
function M.arm(typeId, x, y, z)
    for name, value in pairs({ x = x, y = y, z = z }) do
        local _, problem = checkCoordinate(value, name)
        if problem then return nil, problem end
    end
    if math.type(typeId) ~= "integer" or typeId < 0 or typeId > 1000 then return nil, "type must be an integer from 0 to 1000" end
    local pawn, problem = player()
    if not pawn then return nil, problem end
    local installed, hookProblem = installHook()
    if not installed then return nil, "cannot install the hook: " .. tostring(hookProblem) end
    local mouseOk, mouseProblem = installMouseHook()
    if not mouseOk then return nil, "cannot install the mouse hook: " .. tostring(mouseProblem) end
    state.target = { x = x, y = y, z = z }
    pawn:activateBuildingMode(typeId)
    return { in_mode = pawn:isInAnyConstructionMode() }
end

-- Step 2: press and release the left mouse button.
function M.click()
    local pawn, problem = player()
    if not pawn then return nil, problem end
    pawn:LMB_BP_pressed()
    pawn:LMB_BP_released()
    return { in_mode = pawn:isInAnyConstructionMode() }
end

-- The press and the release as two steps, so the game can run in between.
function M.press()
    local pawn, problem = player()
    if not pawn then return nil, problem end
    pawn:LMB_BP_pressed()
    return { in_mode = pawn:isInAnyConstructionMode() }
end

function M.release()
    local pawn, problem = player()
    if not pawn then return nil, problem end
    pawn:LMB_BP_released()
    return { in_mode = pawn:isInAnyConstructionMode() }
end

-- Step 3: leave building mode and stop replacing the mouse position.
function M.disarm()
    state.target = nil
    local pawn, problem = player()
    if not pawn then return nil, problem end
    pawn:resetBuildingMode()
    return { in_mode = pawn:isInAnyConstructionMode() }
end

-- BuildingSpawnParams has no reflected field in the jmap (152 bytes, 0 properties). This passes an empty table, so a zeroed struct.
function M.spawnRaw()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil, "no RTSMultiEngineCPP" end
    engine:finishSpawningSoloBuildingAsync({})
    return { called = true }
end

function M.status()
    local pawn = player()
    local mouse = pawn and pawn:getMouse3d()
    return {
        hook_installed = state.hookInstalled, hook_calls = state.hookCalls, hook_replaced = state.hookReplaced,
        hook_error = state.hookError, target = state.target,
        mouse3d = mouse and { x = mouse.X, y = mouse.Y, z = mouse.Z } or nil,
    }
end

return M
