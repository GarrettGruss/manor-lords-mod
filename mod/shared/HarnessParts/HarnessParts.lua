-- HarnessParts: read, add and remove the SMBuilding parts of a built SMBuildingMaster (spec 18, composite buildings).
-- Why: a composite building is one master with a list of part actors (`buildings`, and `Extensions[].buildings`). The spike asks
-- whether Lua can change that list on a master that is already built.
-- Commands: master_parts (read only), master_part_remove and master_part_add (unsafe test commands, HARNESS_ALLOW_UNSAFE=1).
--
-- Rules: game thread only. No save function. Every input is checked. A part count is capped.

local M = {}

M.UNSAFE_ENV = "HARNESS_ALLOW_UNSAFE"
M.MAX_PARTS = 80
M.SPAWN_ALWAYS = 1       -- ESpawnActorCollisionHandlingMethod::AlwaysSpawn
M.MOBILITY_MOVABLE = 2
M.MODES = { hide = true, destroy = true, unlink = true }

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

local function arrayCount(array)
    return read(function() return array:GetArrayNum() end) or 0
end

local function numberField(raw, name)
    return tonumber((raw or ""):match('"' .. name .. '"%s*:%s*(-?[%d%.]+)'))
end

local function stringField(raw, name)
    return (raw or ""):match('"' .. name .. '"%s*:%s*"([%w_]+)"')
end

local function idOf(building)
    local name = read(function() return building:GetFullName() end) or ""
    return tonumber(name:match("_(%d+)$"))
end

local function typeOf(building) return read(function() return building.Data.bType end) end

local function findMaster(raw)
    local id, kind = numberField(raw, "building"), numberField(raw, "type")
    if not id and not kind then return nil, "give building (id) or type" end
    for _, building in ipairs(FindAllOf("SMBuildingMaster") or {}) do
        if isValid(building) and not building:GetFullName():find("Default__", 1, true) then
            if id and idOf(building) == id then return building end
            if not id and typeOf(building) == kind and read(function() return building:IsConstructed() end) then return building end
        end
    end
    return nil, "no matching building master"
end

local function meshNameOf(part)
    local mesh = read(function() return part.StaticMeshComponent0.StaticMesh end)
    if not isValid(mesh) then mesh = read(function() return part.StaticMeshComponent.StaticMesh end) end
    return isValid(mesh) and read(function() return mesh:GetFName():ToString() end) or nil
end

local function tagsOf(part)
    local tags = {}
    local array = read(function() return part.Tags end)
    for i = 1, array and arrayCount(array) or 0 do
        tags[#tags + 1] = read(function() return unwrap(array[i]):ToString() end)
    end
    return tags
end

local function partRow(index, part, detail)
    if not isValid(part) then return { index = index, valid = false } end
    local at = read(function() return part:K2_GetActorLocation() end)
    local row = { index = index, valid = true, name = read(function() return part:GetFullName() end),
                  class = read(function() return part:GetClass():GetFName():ToString() end), mesh = meshNameOf(part),
                  hidden = read(function() return part:IsHidden() end),
                  x = at and read(function() return math.floor(at.X) end), y = at and read(function() return math.floor(at.Y) end),
                  z = at and read(function() return math.floor(at.Z) end) }
    -- Opt-in: reading Tags and Data.bType made the command time out in the real game (spike #65, runs s65d-2, s65d-3).
    if detail then
        row.tags = tagsOf(part)
        row.btype = read(function() return part.Data.bType end)
    end
    return row
end

local function partRows(array, limit, from, detail)
    local rows = {}
    for i = from, math.min(arrayCount(array), from + limit - 1) do rows[#rows + 1] = partRow(i, unwrap(array[i]), detail) end
    return rows
end

local function validCount(array)
    local n = 0
    for i = 1, arrayCount(array) do
        if isValid(unwrap(array[i])) then n = n + 1 end
    end
    return n
end

-- Read only: the parts of one master and of its extensions. `limit` (default 5) caps the rows that are listed in full.
function M.master_parts(_, raw)
    local master, problem = findMaster(raw)
    if not master then return { ok = false, error = problem } end
    local limit = math.min(numberField(raw, "limit") or 5, M.MAX_PARTS)
    local out = { ok = true, building = idOf(master), type = typeOf(master), built = read(function() return master:IsConstructed() end),
                  parts = arrayCount(master.buildings), valid_parts = validCount(master.buildings),
                  rows = partRows(master.buildings, limit, math.max(numberField(raw, "from") or 1, 1), (numberField(raw, "detail") or 0) ~= 0),
                  extensions = {} }
    for i = 1, arrayCount(master.Extensions) do
        local extension = master.Extensions[i]
        out.extensions[#out.extensions + 1] = { index = i, type = read(function() return extension.Type end),
                                                parts = arrayCount(extension.buildings), valid_parts = validCount(extension.buildings) }
    end
    return out
end

-- Issue 94: a placed Siege Camp (type 483) site has no Region and is never built. These two commands read a site (built or not) and
-- write its Region. They change one property in memory and call no save function.
local function findSite(raw)
    local id, kind = numberField(raw, "building"), numberField(raw, "type")
    if not id and not kind then return nil, "give building (id) or type" end
    for _, building in ipairs(FindAllOf("SMBuildingMaster") or {}) do
        if isValid(building) and not building:GetFullName():find("Default__", 1, true) then
            if (id and idOf(building) == id) or (not id and typeOf(building) == kind) then return building end
        end
    end
    return nil, "no matching building master"
end

local function nameOf(object)
    if not isValid(object) then return "<invalid>" end
    return read(function() return object:GetFName():ToString() end) or "<unnamed>"
end

local function listSize(field) return read(function() return field:GetArrayNum() end) end

function M.master_site(_, raw)
    local site, problem = findSite(raw)
    if not site then return { ok = false, error = problem } end
    local region = read(function() return site.Region end)
    return { ok = true, building = idOf(site), type = typeOf(site), constructed = read(function() return site:IsConstructed() end),
             region = nameOf(region), owner = nameOf(read(function() return site.ownerPawn end)),
             goods = listSize(site.constructionGoods), resources = listSize(site.Resources), parts = listSize(site.buildings),
             hp = read(function() return site.Data.hp end), max_hp = read(function() return site.Data.maxHp end),
             builders = read(function() return region and region:getRegionBuilders() end),
             function_id = read(function() return site.buildingFunction end) }
end

-- Write site.Region = the region the player pawn is in. Reads it back.
function M.master_set_region(_, raw)
    local site, problem = findSite(raw)
    if not site then return { ok = false, error = problem } end
    local pawn = FindFirstOf("MyPawnCPP_BP3_C")
    local region = isValid(pawn) and read(function() return pawn.currentRegion end) or nil
    if not isValid(region) then return { ok = false, error = "the player pawn has no current region" } end
    local before = nameOf(read(function() return site.Region end))
    local ok, err = pcall(function() site.Region = region end)
    if not ok then return { ok = false, error = "write Region: " .. tostring(err), before = before } end
    return { ok = true, building = idOf(site), before = before, after = nameOf(read(function() return site.Region end)) }
end

-- Harness shortcut for a Siege Camp site that no builder finishes: write Data.constructed = true and read it back.
function M.master_finish(_, raw)
    local site, problem = findSite(raw)
    if not site then return { ok = false, error = problem } end
    local ok, err = pcall(function() site.Data.constructed = true end)
    if not ok then return { ok = false, error = "write constructed: " .. tostring(err) } end
    local built = read(function() return site:IsConstructed() end)
    if built ~= true then return { ok = false, error = "the site is still not constructed after the write" } end
    return { ok = true, building = idOf(site), constructed = built }
end

local function unsafe(name, handler)
    return function(...)
        if (os.getenv and os.getenv(M.UNSAFE_ENV)) ~= "1" then
            return { ok = false, error = name .. " is an unsafe test command: start the game with " .. M.UNSAFE_ENV .. "=1 (test games only)" }
        end
        return handler(...)
    end
end

-- Remove one part of the master list. mode "hide": hide the actor and keep it in the list. mode "destroy": destroy the actor.
-- mode "unlink": remove the entry from the list and keep the actor. Reports the counts before and after.
M.master_part_remove = unsafe("master_part_remove", function(_, raw)
    local master, problem = findMaster(raw)
    if not master then return { ok = false, error = problem } end
    local index, mode = numberField(raw, "index"), stringField(raw, "mode") or "hide"
    if not index or index < 1 or index > arrayCount(master.buildings) then return { ok = false, error = "index must be a part number from 1 to " .. arrayCount(master.buildings) } end
    if not M.MODES[mode] then return { ok = false, error = "mode must be hide, destroy or unlink" } end
    local part = unwrap(master.buildings[index])
    if not isValid(part) then return { ok = false, error = "part " .. index .. " is not valid" } end
    local before = { parts = arrayCount(master.buildings), valid = validCount(master.buildings), row = partRow(index, part) }
    local ok, err
    if mode == "hide" then ok, err = pcall(function() part:SetActorHiddenInGame(true) end)
    elseif mode == "destroy" then ok, err = pcall(function() part:K2_DestroyActor() end)
    else
        -- TArray has no RemoveAt in this UE4SS build: keep the other entries, empty the list, append them again.
        ok, err = pcall(function()
            local keep = {}
            for i = 1, arrayCount(master.buildings) do
                if i ~= index then keep[#keep + 1] = unwrap(master.buildings[i]) end
            end
            master.buildings:Empty()
            for i, entry in ipairs(keep) do master.buildings[i] = entry end
        end)
    end
    if not ok then return { ok = false, error = mode .. " failed: " .. tostring(err), before = before } end
    local state = { valid = isValid(part), hidden = read(function() return part:IsHidden() end),
                    being_destroyed = read(function() return part:IsActorBeingDestroyed() end) }
    return { ok = true, mode = mode, building = idOf(master), before = before, part_after = state,
             after = { parts = arrayCount(master.buildings), valid = validCount(master.buildings) } }
end)

local function spawnTransform(source, raw)
    local at = read(function() return source:K2_GetActorLocation() end)
    if not at then return nil end
    return { Translation = { X = at.X + (numberField(raw, "dx") or 0), Y = at.Y + (numberField(raw, "dy") or 0),
                             Z = at.Z + (numberField(raw, "dz") or 0) },
             Rotation = { X = 0, Y = 0, Z = 0, W = 1 }, Scale3D = { X = 1, Y = 1, Z = 1 } }
end

local function statics()
    local ok, found = pcall(StaticFindObject, "/Script/Engine.Default__GameplayStatics")
    return ok and isValid(found) and found or nil
end

-- Add one part to the master list: spawn an actor of the class of part `from`, copy its mesh, move it by dx, dy, dz, append it.
M.master_part_add = unsafe("master_part_add", function(_, raw)
    local master, problem = findMaster(raw)
    if not master then return { ok = false, error = problem } end
    local from = numberField(raw, "from") or 1
    if from < 1 or from > arrayCount(master.buildings) then return { ok = false, error = "from must be a part number from 1 to " .. arrayCount(master.buildings) } end
    if arrayCount(master.buildings) >= M.MAX_PARTS * 4 then return { ok = false, error = "the part list is too long" } end
    local source = unwrap(master.buildings[from])
    if not isValid(source) then return { ok = false, error = "part " .. from .. " is not valid" } end
    local transform, gameplay = spawnTransform(source, raw), statics()
    if not transform or not gameplay then return { ok = false, error = "no source location or no GameplayStatics" } end
    local before = { parts = arrayCount(master.buildings), valid = validCount(master.buildings) }
    local class = source:GetClass()
    local actor = gameplay:BeginDeferredActorSpawnFromClass(master, class, transform, M.SPAWN_ALWAYS, nil, 0)
    if not isValid(actor) then return { ok = false, error = "spawn gave no actor", before = before } end
    gameplay:FinishSpawningActor(actor, transform, 0)
    local component = read(function() return actor.StaticMeshComponent0 end) or read(function() return actor.StaticMeshComponent end)
    local mesh = read(function() return source.StaticMeshComponent0.StaticMesh end) or read(function() return source.StaticMeshComponent.StaticMesh end)
    if not isValid(component) then
        -- A bare SMBuilding has no mesh component: add one at run time.
        local classObject = read(function() return StaticFindObject("/Script/Engine.StaticMeshComponent") end)
        local added = read(function() return actor:AddComponentByClass(classObject, false, transform, false) end)
        if isValid(added) then component = added end
    end
    local meshOk, meshErr = false, "no mesh component"
    if isValid(component) and isValid(mesh) then
        meshOk, meshErr = pcall(function() component:SetMobility(M.MOBILITY_MOVABLE); component:SetStaticMesh(mesh) end)
    end
    local linkOk, linkErr = pcall(function() actor.buildingMaster = master end)
    master.buildings[before.parts + 1] = actor
    return { ok = true, building = idOf(master), before = before, class = read(function() return class:GetFName():ToString() end),
             after = { parts = arrayCount(master.buildings), valid = validCount(master.buildings) },
             new_part = partRow(before.parts + 1, actor), mesh_set = meshOk, mesh_error = meshOk and nil or tostring(meshErr),
             master_linked = linkOk, link_error = linkOk and nil or tostring(linkErr) }
end)

return M
