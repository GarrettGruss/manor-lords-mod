-- HarnessEncampment: find camp sites and spawn a placed mesh actor (spec 30, Wagenburg).
-- Why: the spike tests if a custom mesh can stand in for a bandit camp, or be spawned in neutral or AI territory.
-- Commands: encampment_sites and encampment_regions (read only), encampment_spawn, encampment_list, encampment_remove.
--
-- Rules: game thread only. No save function. Inputs are checked. The mod destroys only the actors it spawned itself.

local M = {}

M.MAX_SPAWNED = 8
M.MAX_COORDINATE = 1000000
M.MAX_SITES = 20
M.DEFAULT_SITE_TYPE = 100 -- the bandit camp row of buildingStats

local spawned = {}

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

-- The command parser of HarnessActions knows only a fixed list of fields, so each command reads its own fields from the raw JSON.
local function numberField(raw, name)
    return type(raw) == "string" and tonumber(raw:match('"' .. name .. '"%s*:%s*(-?[%d%.]+)')) or nil
end

local function stringField(raw, name)
    return type(raw) == "string" and raw:match('"' .. name .. '"%s*:%s*"([^"]*)"') or nil
end

local function nameOf(object)
    if not isValid(object) then return "<invalid>" end
    return read(function() return object:GetFName():ToString() end) or "<unnamed>"
end

local function point(vector)
    if not vector then return nil end
    return { x = math.floor(vector.X), y = math.floor(vector.Y), z = math.floor(vector.Z) }
end

local function siteRow(master)
    local parts = read(function() return master.buildings:GetArrayNum() end) or 0
    local first = parts > 0 and read(function() return unwrap(master.buildings[1]) end) or nil
    return {
        name = nameOf(master),
        type = read(function() return master.Data.bType end),
        constructed = read(function() return master:IsConstructed() end),
        class = read(function() return master:GetClass():GetFName():ToString() end),
        at = point(read(function() return master:K2_GetActorLocation() end)),
        first_part_at = first and point(read(function() return first:K2_GetActorLocation() end)) or nil,
        region = nameOf(read(function() return master.Region end)),
        owner = nameOf(read(function() return master.ownerPawn end)),
        parts = parts,
    }
end

-- Read only: the building masters of one type (default 100, the bandit camp).
function M.encampment_sites(_, raw)
    local wanted = numberField(raw, "type") or M.DEFAULT_SITE_TYPE
    local rows = {}
    for _, master in ipairs(FindAllOf("SMBuildingMaster") or {}) do
        local isDefault = read(function() return master:GetFullName():find("Default__", 1, true) end)
        if isValid(master) and not isDefault and read(function() return master.Data.bType end) == wanted then
            rows[#rows + 1] = siteRow(master)
            if #rows >= M.MAX_SITES then break end
        end
    end
    return { ok = true, type = wanted, sites = rows }
end

-- Read only: every region with its owner, its settled flag and the world point of the region actor (and of its town center).
-- Why: the spike spawns the encampment in a neutral region (no owner) and in an AI-owned region.
function M.encampment_regions()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local rows, list = {}, read(function() return engine.regions end)
    for i = 1, (read(function() return list:GetArrayNum() end) or 0) do
        local region = unwrap(list[i])
        if isValid(region) then
            local center = read(function() return region.townCenter end)
            rows[#rows + 1] = {
                region = nameOf(region), name = read(function() return region.regionName:ToString() end),
                owner = nameOf(read(function() return region.ownerPawn end)), settled = read(function() return region.isSettled end),
                at = point(read(function() return region:K2_GetActorLocation() end)),
                town_center_at = isValid(center) and point(read(function() return center:K2_GetActorLocation() end)) or nil,
            }
        end
    end
    return { ok = true, regions = rows }
end

local function checkedNumber(raw, field)
    local value = numberField(raw, field)
    if value == nil or math.abs(value) > M.MAX_COORDINATE then return nil end
    return value
end

local function rowOfSpawned(entry)
    local actor = entry.actor
    local alive = isValid(actor)
    local component = alive and (read(function() return actor.StaticMeshComponent end) or read(function() return actor.StaticMeshComponent0 end)) or nil
    local mesh = isValid(component) and read(function() return component.StaticMesh end) or nil
    return { name = entry.name, alive = alive, at = alive and point(read(function() return actor:K2_GetActorLocation() end)) or nil,
             class = entry.class, hidden = alive and read(function() return actor.bHidden end) or nil,
             component_visible = isValid(component) and read(function() return component:IsVisible() end) or nil,
             mesh = nameOf(mesh) }
end

-- Spawn one actor of a loaded class (for example /Game/HarnessMod/BM_Wagenburg.BM_Wagenburg_C) at x, y, z with a yaw in degrees.
function M.encampment_spawn(_, raw)
    local classPath = stringField(raw, "class")
    if type(classPath) ~= "string" or not classPath:match("^/Game/[%w_/%.]+$") then
        return { ok = false, error = "class must be a path like /Game/HarnessMod/BM_X.BM_X_C" }
    end
    local x, y, z = checkedNumber(raw, "x"), checkedNumber(raw, "y"), checkedNumber(raw, "z")
    if not (x and y and z) then return { ok = false, error = "x, y and z must be numbers within " .. M.MAX_COORDINATE } end
    if #spawned >= M.MAX_SPAWNED then return { ok = false, error = "at most " .. M.MAX_SPAWNED .. " spawned actors; remove one first" } end
    local class = read(function() return StaticFindObject(classPath) end)
    if not isValid(class) then return { ok = false, error = "class not loaded: " .. classPath .. " (run load_pak_blueprint first)" } end
    local controller = FindFirstOf("PlayerController")
    local world = isValid(controller) and read(function() return controller:GetWorld() end) or nil
    if not isValid(world) then return { ok = false, error = "no world" } end
    local ok, actor = pcall(function() return world:SpawnActor(class, { X = x, Y = y, Z = z }, { Pitch = 0, Yaw = numberField(raw, "yaw") or 0, Roll = 0 }) end)
    if not ok or not isValid(actor) then return { ok = false, error = "spawn failed: " .. tostring(actor) } end
    local entry = { actor = actor, name = nameOf(actor), class = classPath }
    spawned[#spawned + 1] = entry
    return { ok = true, spawned = rowOfSpawned(entry) }
end

function M.encampment_list()
    local rows = {}
    for _, entry in ipairs(spawned) do rows[#rows + 1] = rowOfSpawned(entry) end
    return { ok = true, spawned = rows }
end

-- Destroy one actor that this module spawned (by name), or all of them when name is "all".
function M.encampment_remove(_, raw)
    local wanted = stringField(raw, "name")
    if type(wanted) ~= "string" then return { ok = false, error = "name is required (an actor name, or all)" } end
    local removed, kept = 0, {}
    for _, entry in ipairs(spawned) do
        if wanted == "all" or entry.name == wanted then
            if isValid(entry.actor) then pcall(function() entry.actor:K2_DestroyActor() end) end
            removed = removed + 1
        else
            kept[#kept + 1] = entry
        end
    end
    spawned = kept
    if removed == 0 and wanted ~= "all" then return { ok = false, error = "no spawned actor named " .. wanted } end
    return { ok = true, removed = removed }
end

return M
