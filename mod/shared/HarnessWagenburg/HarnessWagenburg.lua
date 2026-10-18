-- HarnessWagenburg: reskin the wall pieces and the keep of ONE manor (spec 32, part 2).
-- Why: a pak that replaces the palisade mesh by path changes every manor. Here the pak adds the wagon and tent meshes as new
-- assets, and Lua sets the static mesh of the SMBuilding actors that belong to one manor. The collision is native obstacle data
-- (spec 14), so the mesh change does not move it.
-- Commands: wagen_state (read only), wagen_apply, wagen_revert.
--
-- Rules: game thread only. No save function. The mod changes only the mesh of SMBuilding actors of the chosen manor.

local M = {}

M.WALL_MATCH = "PalisadeWallNarrow"
M.KEEP_MATCH = "MainTower_Lv1_New"
M.MANOR_TYPE = 98
M.MOBILITY_MOVABLE = 2
M.MAX_ROWS = 20
M.KEEP_RADIUS_CM = 6000 -- the keep is a module with its own master, so it is found by its distance to the manor

local originals = {} -- actor address -> original mesh object

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

local function stringField(raw, name)
    return type(raw) == "string" and raw:match('"' .. name .. '"%s*:%s*"([^"]*)"') or nil
end

local function numberField(raw, name)
    return type(raw) == "string" and tonumber(raw:match('"' .. name .. '"%s*:%s*(%d+)')) or nil
end

local function idOf(object)
    local name = isValid(object) and read(function() return object:GetFName():ToString() end)
    return name and tonumber(name:match("(%d+)$")) or nil
end

local function manors()
    local out = {}
    for _, master in ipairs(FindAllOf("SMBuildingMaster") or {}) do
        if isValid(master) and read(function() return master.Data.bType end) == M.MANOR_TYPE then out[#out + 1] = master end
    end
    return out
end

-- LoadAsset does not load pak assets. The asset registry call does (spec 16, pak-widget-spike.md). A vanilla mesh is found by name.
local function meshByPath(path)
    local name = path:match("([^/]+)$")
    local full = path .. "." .. name
    local found = read(function() return StaticFindObject(full) end)
    if isValid(found) then return found end
    local registry = StaticFindObject("/Script/AssetRegistry.Default__AssetRegistryHelpers")
    if isValid(registry) then
        local data = {
            PackageName = FName(path), PackagePath = FName(path:match("^(.*)/[^/]+$")), AssetName = FName(name),
            AssetClassPath = { PackageName = FName("/Script/Engine"), AssetName = FName("StaticMesh") },
        }
        pcall(function() return registry:GetAsset(data) end)
        found = read(function() return StaticFindObject(full) end)
        if isValid(found) then
            pcall(function() found:AddToRoot() end) -- Why: the garbage collector can free an asset that only this call loaded.
            return found
        end
    end
    return read(function() return LoadAsset(full) end)
end

local function meshNameOf(actor)
    return read(function() return actor.StaticMeshComponent.StaticMesh:GetFullName() end)
end

-- The SMBuilding actors of one manor: id, mesh and class of each wall or keep part.
local function partsOf(manorId)
    local rows = {}
    for _, actor in ipairs(FindAllOf("SMBuilding") or {}) do
        if isValid(actor) and not actor:GetFullName():find("Default__", 1, true) then
            local master = read(function() return actor.buildingMaster end)
            if isValid(master) and idOf(master) == manorId then
                local mesh = meshNameOf(actor)
                if mesh then rows[#rows + 1] = { actor = actor, mesh = mesh } end
            end
        end
    end
    return rows
end

local function manorById(manorId)
    for _, master in ipairs(manors()) do
        if idOf(master) == manorId then return master end
    end
    return nil
end

-- SMBuilding actors that show the keep mesh within KEEP_RADIUS_CM of the manor.
local function keepPartsNear(manorId)
    local rows = {}
    local manor = manorById(manorId)
    local at = manor and read(function() return manor:K2_GetActorLocation() end)
    if not at then return rows end
    -- The finished keep, the planner blueprint actor and the plan ghost all draw the keep mesh. Each one must change, or the old tower stays.
    for _, className in ipairs({ "SMBuilding", "StaticMeshActor", "GhostStaticMeshActor" }) do
        for _, actor in ipairs(FindAllOf(className) or {}) do
            local mesh = isValid(actor) and not actor:GetFullName():find("Default__", 1, true) and meshNameOf(actor)
            if mesh and mesh:find(M.KEEP_MATCH, 1, true) then
                local p = read(function() return actor:K2_GetActorLocation() end)
                if p and math.sqrt((p.X - at.X) ^ 2 + (p.Y - at.Y) ^ 2) <= M.KEEP_RADIUS_CM then rows[#rows + 1] = { actor = actor, mesh = mesh } end
            end
        end
    end
    return rows
end

function M.wagen_state()
    local rows = {}
    for _, master in ipairs(manors()) do
        local id = idOf(master)
        local counts = {}
        for _, part in ipairs(partsOf(id)) do
            local short = part.mesh:match("([^%.:]+)$") or part.mesh
            counts[short] = (counts[short] or 0) + 1
        end
        rows[#rows + 1] = { manor = id, parts = counts }
    end
    return { ok = true, manors = rows }
end

local function setMesh(actor, mesh)
    local component = actor.StaticMeshComponent
    component:SetMobility(M.MOBILITY_MOVABLE)
    component:SetStaticMesh(mesh)
end

-- Fields: manor (id), wall_mesh and keep_mesh (asset paths of meshes that a pak added). One of the two may be left out.
function M.wagen_apply(_, raw)
    local manorId = numberField(raw, "manor")
    if not manorId then return { ok = false, error = "manor must be a manor master id" } end
    local wallPath, keepPath = stringField(raw, "wall_mesh"), stringField(raw, "keep_mesh")
    local wall = wallPath and meshByPath(wallPath)
    local keep = keepPath and meshByPath(keepPath)
    if wallPath and not isValid(wall) then return { ok = false, error = "wall mesh not found: " .. wallPath } end
    if keepPath and not isValid(keep) then return { ok = false, error = "keep mesh not found: " .. keepPath } end
    local changed = { wall = 0, keep = 0 }
    local parts = partsOf(manorId)
    if keep then
        for _, part in ipairs(keepPartsNear(manorId)) do parts[#parts + 1] = part end
    end
    for _, part in ipairs(parts) do
        local target, kind
        if wall and part.mesh:find(M.WALL_MATCH, 1, true) then target, kind = wall, "wall" end
        if keep and part.mesh:find(M.KEEP_MATCH, 1, true) then target, kind = keep, "keep" end
        if target then
            local address = read(function() return part.actor:GetAddress() end)
            if address and not originals[address] then originals[address] = read(function() return part.actor.StaticMeshComponent.StaticMesh end) end
            if pcall(setMesh, part.actor, target) then changed[kind] = changed[kind] + 1 end
        end
    end
    return { ok = true, manor = manorId, changed = changed }
end

function M.wagen_revert()
    local restored = 0
    for _, actor in ipairs(FindAllOf("SMBuilding") or {}) do
        local address = isValid(actor) and read(function() return actor:GetAddress() end)
        local mesh = address and originals[address]
        if mesh and isValid(mesh) and pcall(setMesh, actor, mesh) then restored = restored + 1 end
    end
    originals = {}
    return { ok = true, restored = restored }
end

return M
