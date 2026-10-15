-- HarnessPlace: place a normal building at a world point without a mouse device (issues #104, #115, spec 18).
-- Why: Windows has no mouse here. The native pawn tick writes a failed cursor hit (0, 0, -100000) into the preview component
-- DummyBuilding every frame. This mod is opt-in: it does nothing until the command HarnessPlace.place_building_at runs.
-- Then it hooks the pawn Blueprint tick (ReceiveTick) and the cursor reads (getMouse3d, getMouse), and after each tick
-- it writes the target point into DummyBuilding. A short script then presses and releases the left mouse button event.
-- Notes: docs/specs/18-composite-buildings/implementation-notes/mousefree-preview-hook.md
-- Rules: game objects are touched on the game thread only. No save function. No eval.

local log = require("HarnessLog")
local commands = require("HarnessCommands")

local VERSION = "11"
local TAG = "HarnessPlace"
local PREFIX = "HarnessPlace."
local MAX_TYPE = 600
local WORLD_LIMIT = 200000
local TRACE_LIMIT = 30

local S = {
    armed = false,
    target = nil,
    buildingType = nil,
    hooked = false,
    counts = { tick = 0, mouse3d = 0, mouse = 0, cursor = 0, mesh = 0 },
    trace = {},
}

local function read(fn)
    local ok, value = pcall(fn)
    if ok then return value end
    return nil
end

local function pawn()
    local found = FindFirstOf("MyPawnCPP_BP3_C")
    if found ~= nil and read(function() return found:IsValid() end) then return found end
    return nil
end

local function previewComponent(player)
    local path = read(function() return player:GetFullName() end)
    if not path then return nil end
    local component = StaticFindObject(path:gsub("^%S+%s+", "") .. ".DummyBuilding")
    if component ~= nil and read(function() return component:IsValid() end) then return component end
    return nil
end

local function vectorText(v)
    if v == nil then return "nil" end
    return string.format("(%.0f, %.0f, %.0f)", v.X, v.Y, v.Z)
end

local function addTrace(text)
    if #S.trace < TRACE_LIMIT then S.trace[#S.trace + 1] = text end
end

local function moveGhost(player)
    local component = previewComponent(player)
    if not component then return end
    local before = read(function() return component:K2_GetComponentLocation() end)
    pcall(function() component:K2_SetWorldLocation(S.target, false, {}, true) end)
    local after = read(function() return component:K2_GetComponentLocation() end)
    addTrace("tick " .. S.counts.tick .. " before " .. vectorText(before) .. " after " .. vectorText(after))
end

local function onTickStart(self)
    if not S.armed then return end
    local component = previewComponent(self:get())
    local seen = component and read(function() return component:K2_GetComponentLocation() end)
    S.counts.tick = S.counts.tick + 1
    if S.probe then pcall(function() self:get().LastMousePos = { X = 1290, Y = 748 } end) end
    addTrace("pre-tick " .. S.counts.tick .. " ghost " .. vectorText(seen))
    if not S.noWrite then log.try(TAG, moveGhost, self:get()) end
end

local function onTick(self)
    if not S.armed then return end
    S.counts.post = (S.counts.post or 0) + 1
end

local function overrideVector(counterName, returnValue)
    if not S.armed then return end
    S.counts[counterName] = S.counts[counterName] + 1
    returnValue:set(S.target)
end

local function overrideScreen(returnValue)
    if not S.armed then return end
    S.counts.mouse = S.counts.mouse + 1
    returnValue:set({ X = 1200, Y = 700 })
end

local function registerHooks(player)
    if S.hooked then return end
    local classPath = read(function() return player:GetClass():GetFullName():gsub("^%S+%s+", "") end)
    if not classPath then error("cannot read the class path of the pawn") end
    RegisterHook(classPath .. ":ReceiveTick", function(self) onTickStart(self) end, function(self) onTick(self) end)
    RegisterHook("/Script/ManorLords.PawnCPP:getMouse3d", function() end, function(_self, returnValue) overrideVector("mouse3d", returnValue) end)
    RegisterHook("/Script/ManorLords.PawnCPP:getMouse", function() end, function(_self, returnValue) overrideScreen(returnValue) end)
    pcall(RegisterHook, "/Script/ManorLords.PawnCPP:updateCursor", function() S.counts.cursor = S.counts.cursor + 1 end, function() end)
    pcall(RegisterHook, "/Script/ManorLords.PawnCPP:updatePlacebuildingMesh", function() S.counts.mesh = S.counts.mesh + 1 end, function() end)
    S.hooked = true
end

-- The game checks "Cannot build in this Region" with the region under the cursor, which the failed cursor hit leaves empty.
local function setRegion(player)
    local region = player.currentRegion
    if S.regionName == nil then
        S.regionName = read(function() return region:GetFullName() end)
        S.regionBefore = read(function() return player.regionUnderCursor:GetFullName() end)
    end
    player.regionUnderCursor = region
end

-- A late writer: another actor that ticks AFTER the pawn writes the ghost. The pawn is a tick prerequisite of that actor.
local function lateTick(self)
    if not (S.armed and S.late) then return end
    local player = pawn()
    if not player then return end
    local component = previewComponent(player)
    local seen = component and read(function() return component:K2_GetComponentLocation() end)
    S.counts.late = (S.counts.late or 0) + 1
    addTrace("late-tick " .. S.counts.late .. " ghost " .. vectorText(seen))
    if S.probe then return end
    log.try(TAG, moveGhost, player)
    if S.region then log.try(TAG, setRegion, player) end
end

local function registerLateHook(player)
    if S.lateHooked then return end
    local controller = FindFirstOf("MLPlayerController_C")
    if not controller then error("no MLPlayerController_C") end
    local path = controller:GetClass():GetFullName():gsub("^%S+%s+", "")
    log.info(TAG, "late hook on " .. path .. ":ReceiveTick")
    RegisterHook(path .. ":ReceiveTick", function(self) lateTick(self) end, function() end)
    controller:AddTickPrerequisiteActor(player)
    log.info(TAG, "pawn is now a tick prerequisite of the controller")
    S.lateHooked = true
end

local function arm(args)
    local player = pawn()
    if not player then return nil, "no player pawn" end
    S.target = { X = args.x, Y = args.y, Z = args.z }
    S.buildingType = args.type
    registerHooks(player)
    S.counts = { tick = 0, mouse3d = 0, mouse = 0, cursor = 0, mesh = 0 }
    S.trace = {}
    S.armed = true
    S.noWrite = args.late == true
    S.late = args.late == true
    S.probe = args.probe == true
    S.region = args.region == true
    if S.late then registerLateHook(player) end
    player:activateBuildingMode(args.type)
    player:updatePlacebuildingMesh(args.type, false, 0)
    return { armed = true }
end

local function disarm()
    S.armed = false
    local player = pawn()
    if player then player:resetBuildingMode() end
    return { armed = false }
end

local function state()
    local player = pawn()
    local result = { armed = S.armed, counts = S.counts, trace = S.trace }
    if not player then return result end
    local component = previewComponent(player)
    result.requestBuild = read(function() return player.requestBuild end)
    result.placeBuilding = read(function() return player.placeBuilding end)
    result.ghostLocation = component and vectorText(read(function() return component:K2_GetComponentLocation() end)) or "no component"
    result.ghostMesh = component and read(function() return component.StaticMesh:GetFullName() end) or "none"
    result.ghostVisible = component and read(function() return component:IsVisible() end)
    local parent = component and read(function() return component.AttachParent end)
    result.ghostParent = parent and read(function() return parent:GetFullName() end) or "none"
    result.ghostRelative = component and vectorText(read(function() return component.RelativeLocation end)) or "none"
    result.ghostAbsolute = component and read(function() return component.bAbsoluteLocation end)
    result.mobility = component and read(function() return component.Mobility end)
    result.pawnLocation = vectorText(read(function() return player:K2_GetActorLocation() end))
    result.regionUnderCursor = read(function() return player.regionUnderCursor:GetFullName() end)
    result.regionBefore = S.regionBefore
    result.currentRegion = read(function() return player.currentRegion:GetFullName() end)
    result.mouse3d = vectorText(read(function() return player:getMouse3d():get() end))
    return result
end

local function press()
    local player = pawn()
    if not player then return nil, "no player pawn" end
    player:LMB_BP_pressed()
    return { pressed = true }
end

local function release()
    local player = pawn()
    if not player then return nil, "no player pawn" end
    player:LMB_BP_released()
    return { released = true }
end

local function number(min, max) return { type = "number", min = min, max = max, required = true } end

local DEFINITIONS = {
    arm = { run = arm, schema = { x = number(-WORLD_LIMIT, WORLD_LIMIT), y = number(-WORLD_LIMIT, WORLD_LIMIT),
        z = number(-WORLD_LIMIT, WORLD_LIMIT), type = { type = "integer", min = 1, max = MAX_TYPE, required = true },
        late = { type = "boolean" }, probe = { type = "boolean" }, region = { type = "boolean" } } },
    disarm = { run = disarm, schema = {} },
    state = { run = state, schema = {} },
    bp = { run = require("blueprint_route")({ read = read, pawn = pawn, vectorText = vectorText }),
        schema = { mode = { type = "string", required = true }, type = { type = "integer", min = 1, max = MAX_TYPE },
            master_type = { type = "integer", min = 1, max = MAX_TYPE }, index = { type = "integer", min = 0, max = 50 },
            mesh_fragment = { type = "string" }, x = { type = "number", min = -WORLD_LIMIT, max = WORLD_LIMIT },
            y = { type = "number", min = -WORLD_LIMIT, max = WORLD_LIMIT }, z = { type = "number", min = -WORLD_LIMIT, max = WORLD_LIMIT } } },
    press = { run = press, schema = {} },
    release = { run = release, schema = {} },
}

for name, definition in pairs(DEFINITIONS) do
    commands.unregister(PREFIX .. name)
    commands.register(PREFIX .. name, function(args) return definition.run(args) end, definition.schema)
end

log.info(TAG, "loaded version " .. VERSION)
