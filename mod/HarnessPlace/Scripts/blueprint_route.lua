-- Blueprint route (issue #104): turn a blueprint actor into a building without a mouse.
-- Spike modes. Notes: docs/specs/18-composite-buildings/implementation-notes/mousefree-blueprint-route.md
-- The caller passes the helpers `read`, `pawn` and `vectorText` of HarnessPlace.

local SPAWN_ALWAYS = 1
local MOBILITY_MOVABLE = 2

return function(helpers)
    local read, pawn, vectorText = helpers.read, helpers.pawn, helpers.vectorText

    local function masterList(buildingType)
        local found = {}
        for _, master in ipairs(FindAllOf("SMBuildingMaster") or {}) do
            if read(function() return master:IsValid() end) and read(function() return master.Data.bType end) == buildingType then
                found[#found + 1] = master
            end
        end
        return found
    end

    -- A function return value is a wrapper. Plain values are returned as they are.
    local function value(fn)
        local result = read(fn)
        if type(result) == "userdata" then result = read(function() return result:get() end) end
        local kind = type(result)
        if kind == "number" or kind == "boolean" or kind == "string" or kind == "nil" then return result end
        return "<" .. kind .. ">"
    end

    local function describeMaster(master)
        return {
            path = read(function() return master:GetFullName() end),
            constructed = value(function() return master.Data.constructed end),
            buildings = value(function() return master.buildings:GetArrayNum() end),
            blueprints = value(function() return master.blueprints:GetArrayNum() end),
            location = vectorText(read(function() return master:K2_GetActorLocation() end)),
            region = read(function() return master.Region:GetFullName() end),
            buildingType = value(function() return master.buildings[1].Data.bType end),
            progress = value(function() return master:getConstructionProgress() end),
            builders = value(function() return master:getNumBuilders() end),
            paused = value(function() return master:getConstructionPaused() end),
            queueId = value(function() return master:getConstructionQueueID() end),
        }
    end

    local function findMeshByName(fragment)
        for _, mesh in ipairs(FindAllOf("StaticMesh") or {}) do
            local name = read(function() return mesh:GetFullName() end)
            if name and name:find(fragment, 1, true) then return mesh, name end
        end
        return nil
    end

    -- The preview mesh of a type is loaded when the placement ghost shows it. Read it from the pawn preview component.
    local function previewMesh(buildingType)
        local player = pawn()
        if not player then return nil end
        player:updatePlacebuildingMesh(buildingType, false, 0)
        local path = read(function() return player:GetFullName():gsub("^%S+%s+", "") end)
        local component = path and StaticFindObject(path .. ".DummyBuilding")
        local mesh = component and read(function() return component.StaticMesh end)
        if mesh then return mesh, read(function() return mesh:GetFullName() end) end
        return nil
    end

    local function meshForType(args)
        if args.mesh_fragment then return findMeshByName(args.mesh_fragment) end
        return previewMesh(args.type)
    end

    local function scan(args)
        local result = { masters = {} }
        for _, master in ipairs(masterList(args.type)) do result.masters[#result.masters + 1] = describeMaster(master) end
        local _, name = meshForType(args)
        result.mesh = name
        return result
    end

    local function spawnMeshActor(owner, mesh, at, tag)
        local statics = StaticFindObject("/Script/Engine.Default__GameplayStatics")
        local class = StaticFindObject("/Script/Engine.StaticMeshActor")
        local transform = { Translation = at, Rotation = { X = 0, Y = 0, Z = 0, W = 1 }, Scale3D = { X = 1, Y = 1, Z = 1 } }
        local actor = statics:BeginDeferredActorSpawnFromClass(owner, class, transform, SPAWN_ALWAYS, nil, 0)
        statics:FinishSpawningActor(actor, transform, 0)
        actor.StaticMeshComponent:SetMobility(MOBILITY_MOVABLE)
        actor.StaticMeshComponent:SetStaticMesh(mesh)
        actor.Tags[1] = FName(tag)
        return actor
    end

    -- Option (a): add a blueprint to an existing master of `master_type`, then convert it.
    local function extend(args)
        local master = masterList(args.master_type)[(args.index or 0) + 1]
        if not master then return nil, "no master of type " .. args.master_type end
        local mesh, name = meshForType(args)
        if not mesh then return nil, "mesh not found" end
        local before = describeMaster(master)
        local actor = spawnMeshActor(master, mesh, { X = args.x, Y = args.y, Z = args.z }, "bType_" .. args.type)
        master.blueprints[before.blueprints + 1] = actor
        local player = pawn()
        if player then player:setPlacedBuilding(0) end
        master:convertBlueprintsToBuildings(false)
        return { mesh = name, before = before, after = describeMaster(master) }
    end

    -- Option (a) with a new master: spawn a fresh SMBuildingMaster, give it a type, add the blueprint, convert.
    local function newMaster(args)
        local class = StaticFindObject("/Script/ManorLords.SMBuildingMaster")
        local mesh, name = meshForType(args)
        if not mesh then return nil, "mesh not found" end
        local player = pawn()
        local statics = StaticFindObject("/Script/Engine.Default__GameplayStatics")
        local at = { X = args.x, Y = args.y, Z = args.z }
        local transform = { Translation = at, Rotation = { X = 0, Y = 0, Z = 0, W = 1 }, Scale3D = { X = 1, Y = 1, Z = 1 } }
        local master = statics:BeginDeferredActorSpawnFromClass(player, class, transform, SPAWN_ALWAYS, nil, 0)
        if not master then return nil, "spawn gave no master" end
        master.Data.bType = args.type
        master.Data.constructed = false
        master.ownerPawn = player
        master.Region = player.currentRegion
        master.masterPtr = FindFirstOf("RTSMultiEngineCPP")
        statics:FinishSpawningActor(master, transform, 0)
        local actor = spawnMeshActor(master, mesh, at, "bType_" .. args.type)
        master.blueprints[1] = actor
        player:setPlacedBuilding(0)
        master:convertBlueprintsToBuildings(false)
        return { mesh = name, master = describeMaster(master) }
    end

    local MODES = { scan = scan, extend = extend, newmaster = newMaster }

    return function(args)
        local run = MODES[args.mode]
        if not run then return nil, "mode must be scan, extend or newmaster" end
        return run(args)
    end
end
