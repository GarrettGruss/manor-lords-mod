-- HarnessLeads: probes for the five community mod leads (change spike-community-mod-leads, issue #280).
-- Why: spec 13 found five calls in community mods that no game test has checked. Each command here is a small probe.
-- It reads or calls one thing and returns what the game answers. None of them saves the game.
--   lead_unit_gear     R3 loot: GetEquippedID of the units of one squad (slots 0..3), alive or dead
--   lead_stance        stances: read Squad.behaviourStance, optionally call SquadComponent:SetBehaviourStance
--   lead_spawn_unit    unit growth: RTSMultiEngineCPP:spawnCompleteUnit for one lord, one squad per call
--   lead_squad_camp    camp state: Squad.camp, campLocation and rallyingStatus of every squad of a lord
--   lead_mesh_list     mesh swap: building mesh components (mesh, bounds, collision, socket count)
--   lead_mesh_swap     mesh swap: load a mesh and SetStaticMesh on one building component; "restore" puts the old one back
-- Rules: call only on the game thread. No save function. The only Lua string that goes to an FName argument is the template
-- name of spawnCompleteUnit on the engine object. Socket names are counted, never passed back. Only plain fields are read.

local datatable = require("HarnessDataTable")
local lords = require("HarnessLords")

local M = {}

M.MAX_SLOT = 3
M.MAX_UNITS = 40
M.MAX_COMPONENTS = 60
M.MAX_SPAWN = 6
M.MAX_OFFSET = 60000
M.READ_SQUAD_STRUCT = false   -- never true: see stanceOf
M.STANCES = { neutral = 0, aggressive = 1, defensive = 2 }

local swapped = {}   -- component full name -> { mesh } of the mesh before the swap

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

-- A plain value for the result file. Numbers, booleans and strings stay. A vector becomes x, y, z. An object becomes its name.
local function plain(value)
    local kind = type(value)
    if kind == "number" or kind == "boolean" or kind == "string" or kind == "nil" then return value end
    local x, y = read(function() return value.X end), read(function() return value.Y end)
    if type(x) == "number" and type(y) == "number" then
        return { x = math.floor(x), y = math.floor(y), z = math.floor(read(function() return value.Z end) or 0) }
    end
    local name = read(function() return value:GetFullName() end)
    if name then return "object " .. tostring(name) end
    return read(function() return value:ToString() end) or ("<" .. kind .. ">")
end

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if isValid(found) then return found end
    return nil
end

local function wholeNumber(value, low, high)
    return type(value) == "number" and value == math.floor(value) and value >= low and value <= high
end

local function squadComponent()
    local found = FindFirstOf("SquadComponent")
    if isValid(found) then return found end
    return nil
end

---------------------------------------------------------------------------------------------
-- 1.1 gear of units
---------------------------------------------------------------------------------------------

-- request.squad: squad id. Result: for each unit (at most MAX_UNITS) dead flag, ItemsLooted and the answer of GetEquippedID for slots 0..3.
-- A slot call that raises an error gives the error text, so the probe sees the signature the game accepts.
function M.lead_unit_gear(request)
    if not wholeNumber(request.squad, 1, 1000000) then return { ok = false, error = "squad must be a squad id (a whole number above 0)" } end
    local rows, seen, dead = {}, 0, 0
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if #rows >= M.MAX_UNITS then break end
        if isValid(unit) and read(function() return unit.assignedSquadID.Value end) == request.squad then
            seen = seen + 1
            local isDead = read(function() return unit.dead end) == true
            if isDead then dead = dead + 1 end
            local gear = {}
            for slot = 0, M.MAX_SLOT do
                local ok, answer = pcall(function() return unit:GetEquippedID(slot) end)
                if ok then
                    answer = unwrap(answer)
                    gear[#gear + 1] = plain(read(function() return answer.Value end) or answer)
                else
                    gear[#gear + 1] = "error: " .. tostring(answer):sub(1, 120)
                end
            end
            rows[#rows + 1] = { dead = isDead, looted = read(function() return unit.ItemsLooted end), gear = gear }
        end
    end
    return { ok = true, squad = request.squad, units = seen, dead = dead, rows = rows }
end

---------------------------------------------------------------------------------------------
-- 1.2 stance
---------------------------------------------------------------------------------------------

local function squadOf(component, id)
    return read(function() return unwrap(component:GetSquad({ Value = id })) end)
end

local function stanceOf(component, id)
    -- GetSquad returns a Squad struct by value. Reading it ended the game (run 20261021-041541-74de, same as getSquadByID).
    if not M.READ_SQUAD_STRUCT then return nil end
    local squad = squadOf(component, id)
    if squad == nil then return nil end
    return plain(read(function() return squad.behaviourStance end))
end

-- request.squad: squad id. request.stance (optional): neutral, aggressive or defensive. Without stance the command only reads.
function M.lead_stance(request)
    if not wholeNumber(request.squad, 1, 1000000) then return { ok = false, error = "squad must be a squad id (a whole number above 0)" } end
    local component = squadComponent()
    if not component then return { ok = false, error = "no SquadComponent" } end
    local answer = { ok = true, squad = request.squad, before = stanceOf(component, request.squad) }
    if request.stance ~= nil then
        local value = M.STANCES[request.stance]
        if value == nil then return { ok = false, error = "stance must be neutral, aggressive or defensive" } end
        local ok, err = pcall(function() component:SetBehaviourStance({ Value = request.squad }, value, false) end)
        if not ok then return { ok = false, error = "SetBehaviourStance: " .. tostring(err), before = answer.before } end
        answer.called, answer.after = request.stance, stanceOf(component, request.squad)
    end
    return answer
end

---------------------------------------------------------------------------------------------
-- 1.3 unit growth
---------------------------------------------------------------------------------------------

-- request.lord: lord number. template: row of DT_UnitTemplates. count: calls (1..MAX_SPAWN). dx, dy: offset from the player pawn.
-- request.company: company id (default 0). One spawnCompleteUnit call for each count; the arrival time is 0 days.
function M.lead_spawn_unit(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    if not wholeNumber(request.lord, 1, 100) then return { ok = false, error = "lord must be a number from 1" } end
    local lord = lords.pawn_by_number(request.lord)
    if not isValid(lord) then return { ok = false, error = "no AI lord number " .. tostring(request.lord) } end
    local template = request.template
    if type(template) ~= "string" or not datatable.has_row(template, "units") then
        return { ok = false, error = "no unit template named " .. tostring(template) .. " (rows of DT_UnitTemplates)" }
    end
    local count = request.count or 1
    if not wholeNumber(count, 1, M.MAX_SPAWN) then return { ok = false, error = "count must be 1 to " .. M.MAX_SPAWN } end
    local dx, dy, company = request.dx or 0, request.dy or 0, request.company or 0
    if math.abs(dx) > M.MAX_OFFSET or math.abs(dy) > M.MAX_OFFSET then return { ok = false, error = "dx and dy must be within " .. M.MAX_OFFSET } end
    if not wholeNumber(company, 0, 1000000) then return { ok = false, error = "company must be a whole number from 0" } end
    local home = read(function() return engineObject.playerRef:K2_GetActorLocation() end)
    if not home then return { ok = false, error = "no player position" } end
    local squads, errors = {}, {}
    for i = 1, count do
        local at = { X = home.X + dx + (i - 1) * 1500, Y = home.Y + dy, Z = home.Z }
        local ok, returned = pcall(function()
            return engineObject:spawnCompleteUnit(FName(template), at, { Pitch = 0, Yaw = 0, Roll = 0 }, lord, company, 0)
        end)
        if ok then
            returned = unwrap(returned)
            squads[#squads + 1] = read(function() return returned.squadID.Value end) or plain(returned)
        else
            errors[#errors + 1] = tostring(returned):sub(1, 160)
        end
    end
    return { ok = #errors == 0, template = template, calls = count, squads = squads, errors = errors }
end

---------------------------------------------------------------------------------------------
-- 1.4 camp state
---------------------------------------------------------------------------------------------

-- request.lord: lord number. Result: for each commanded squad the plain fields camp, campLocation, rallyingStatus and WeightedCenter.
function M.lead_squad_camp(request)
    if not wholeNumber(request.lord, 1, 100) then return { ok = false, error = "lord must be a number from 1" } end
    local lord = lords.pawn_by_number(request.lord)
    if not isValid(lord) then return { ok = false, error = "no AI lord number " .. tostring(request.lord) } end
    local component = squadComponent()
    if not component then return { ok = false, error = "no SquadComponent" } end
    local rows = {}
    local handles = read(function() return lord.commandedSquads end)
    local count = handles and read(function() return handles:GetArrayNum() end) or 0
    for i = 1, math.min(count, M.MAX_UNITS) do
        local id = read(function() return unwrap(handles[i]).Value end)
        local squad = id and M.READ_SQUAD_STRUCT and squadOf(component, id)
        if id and not M.READ_SQUAD_STRUCT then
            rows[#rows + 1] = { squad = id }   -- the Squad struct is not read (see stanceOf)
        elseif squad then
            rows[#rows + 1] = { squad = id, camp = plain(read(function() return squad.camp end)),
                                camp_location = plain(read(function() return squad.campLocation end)),
                                rallying_status = plain(read(function() return squad.rallyingStatus end)),
                                center = plain(read(function() return squad.WeightedCenter end)) }
        end
    end
    return { ok = true, lord = request.lord, squads = count, rows = rows }
end

---------------------------------------------------------------------------------------------
-- 1.5 mesh swap
---------------------------------------------------------------------------------------------

local function buildingComponents()
    local out = {}
    for _, component in ipairs(FindAllOf("StaticMeshComponent") or {}) do
        if #out >= M.MAX_COMPONENTS then break end
        local full = read(function() return component:GetFullName() end)
        local owner = read(function() return component:GetOwner() end)
        local class = owner and read(function() return owner:GetFullName():match("^(%S+)") end)
        if full and class and not full:find("Default__", 1, true) and class:find("SMBuilding", 1, true)
            and isValid(read(function() return component.StaticMesh end)) then
            out[#out + 1] = { component = component, full = full, owner = owner, class = class }
        end
    end
    return out
end

-- Object path of the mesh ("/Game/.../Name.Name"): GetFullName is "StaticMesh <path>".
local function meshPath(component)
    local full = read(function() return component.StaticMesh:GetFullName() end)
    return full and (full:match("^%S+ (.+)$") or full) or nil
end

-- Half size of the bounds. Each axis is read on its own, the Bounds struct is never passed on.
local function extentOf(component)
    local x = read(function() return component.Bounds.BoxExtent.X end)
    if type(x) ~= "number" then return nil end
    return { x = math.floor(x), y = math.floor(read(function() return component.Bounds.BoxExtent.Y end) or 0), z = math.floor(read(function() return component.Bounds.BoxExtent.Z end) or 0) }
end

-- Number of simple collision shapes of the mesh body setup (array sizes only, no element is read).
local function shapesOf(component)
    local geom = read(function() return component.StaticMesh.BodySetup.AggGeom end)
    if geom == nil then return nil end
    local function count(name) return read(function() return geom[name]:GetArrayNum() end) end
    return { box = count("BoxElems"), sphere = count("SphereElems"), sphyl = count("SphylElems"), convex = count("ConvexElems") }
end

local function meshRow(entry)
    local component = entry.component
    local sockets = read(function() return component:GetAllSocketNames() end)
    return { full = entry.full, class = entry.class,
             mesh = meshPath(component),
             at = plain(read(function() return entry.owner:K2_GetActorLocation() end)),
             extent = extentOf(component),
             shapes = shapesOf(component),
             collision = plain(read(function() return component:GetCollisionEnabled() end)),
             sockets = sockets and read(function() return sockets:GetArrayNum() end) or nil,
             swapped = swapped[entry.full] ~= nil }
end

-- Read only. Rows of building mesh components (at most MAX_COMPONENTS). The socket names are counted, not read.
function M.lead_mesh_list()
    local rows = {}
    for _, entry in ipairs(buildingComponents()) do rows[#rows + 1] = meshRow(entry) end
    return { ok = true, total = #rows, components = rows }
end

-- A mesh by object path "/Game/.../Name.Name": StaticFindObject first, then LoadAsset.
local function loadMesh(path)
    local how = "StaticFindObject"
    local found = read(function() return StaticFindObject(path) end)
    if not isValid(found) then
        how = "LoadAsset"
        found = read(function() return LoadAsset(path) end)
    end
    if not isValid(found) then return nil, "mesh not found: " .. path end
    return found, how
end

-- request.component: full name from lead_mesh_list. request.mesh: object path of the new mesh (a path from lead_mesh_list works).
-- request.restore = true puts the old mesh back instead. Result: the row before and after.
function M.lead_mesh_swap(request)
    if type(request.component) ~= "string" then return { ok = false, error = "component must be a full name from lead_mesh_list" } end
    local target
    for _, entry in ipairs(buildingComponents()) do
        if entry.full == request.component then target = entry end
    end
    if not target then return { ok = false, error = "no building component with that name" } end
    local before = meshRow(target)
    local mesh, how
    if request.restore then
        local saved = swapped[target.full]
        if not saved then return { ok = false, error = "this component was not swapped", before = before } end
        mesh, how = saved.mesh, "saved"
    else
        if type(request.mesh) ~= "string" or request.mesh == "" then return { ok = false, error = "mesh must be an object path", before = before } end
        mesh, how = loadMesh(request.mesh)
        if not mesh then return { ok = false, error = how, before = before } end
        swapped[target.full] = swapped[target.full] or { mesh = target.component.StaticMesh }
    end
    local ok, err = pcall(function() target.component:SetStaticMesh(mesh) end)
    if not ok then return { ok = false, error = "SetStaticMesh: " .. tostring(err), before = before } end
    if request.restore then swapped[target.full] = nil end
    return { ok = true, loaded_with = how, before = before, after = meshRow(target) }
end

return M
