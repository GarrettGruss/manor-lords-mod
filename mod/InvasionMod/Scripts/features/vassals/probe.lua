-- Spike commands for the change add-vassal-sack-wipe (tasks 1.1, 1.2). They are for the hidden probe scenario only.
-- They touch AI regions (kill villagers, collapse houses), so the feature must not use them. Remove them after the spike.
local core = require("ManorCore")
local TAG = "InvasionMod.vassals.probe"

local function region_object(name)
    local e = FindFirstOf("RTSMultiEngineCPP")
    if not core.isValid(e) then return nil end
    for _, region in ipairs(core.listOf(e.regions)) do
        if core.shortName(region) == name then return region end
    end
    return nil
end

local function read_region(region)
    local buildings = core.listOf(core.read(function() return region:GetBuildings() end))
    local rubble, standing = 0, 0
    for _, building in ipairs(buildings) do
        if core.isValid(building) then
            if core.read(function() return building:IsRubble() end) == true then rubble = rubble + 1 else standing = standing + 1 end
        end
    end
    local alive = 0
    for _, family in ipairs(core.listOf(core.read(function() return region.workerFamilies end))) do
        for _, member in ipairs(core.listOf(family.familyMembers)) do
            if core.isValid(member) and core.read(function() return member.dead end) ~= true then alive = alive + 1 end
        end
    end
    return {
        region = core.shortName(region), owner = core.shortName(core.read(function() return region.ownerPawn end)),
        settled = core.read(function() return region.isSettled end), buildings = rubble + standing, standing = standing, rubble = rubble,
        families = core.read(function() return region:getTotalNumFamilies() end), population = core.read(function() return region:getNumTotalPopulation() end),
        homeless = core.read(function() return region:getNumHomelessFamilies() end), members_alive = alive,
        approval = core.read(function() return region.Approval end),
    }
end

-- Collect the living members of the first `count` families as objects, then kill them. Why: remove_families walks the family array while
-- the deaths change it, and that crashed the game (runs 20261021-050845-d295 and 20261021-051155-a6a4).
local function kill_members_first(region, count)
    local members, families = {}, 0
    for _, family in ipairs(core.listOf(core.read(function() return region.workerFamilies end))) do
        if families >= count then break end
        families = families + 1
        for _, member in ipairs(core.listOf(family.familyMembers)) do members[#members + 1] = member end
    end
    local killed = 0
    for _, member in ipairs(members) do
        if core.isValid(member) and core.read(function() return member.dead end) ~= true then
            if pcall(function() member:just_die() end) then killed = killed + 1 end
        end
    end
    return families, killed
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.probe_region", function(args)
        local region = region_object(args.region)
        if region == nil then return nil, "no region " .. args.region end
        return read_region(region)
    end, { region = { type = "string", required = true } })
    commands.register("InvasionMod.probe_kill_villagers", function(args)
        local region = region_object(args.region)
        if region == nil then return nil, "no region " .. args.region end
        local before = read_region(region)
        core.log.info(TAG, "PROBE kill start " .. args.region .. " count=" .. tostring(args.count))
        local families, people = kill_members_first(region, args.count)
        core.log.info(TAG, string.format("PROBE killed families=%d people=%d in %s", families, people, args.region))
        return { before = before, families_removed = families, people_removed = people, after = { families = core.read(function() return region:getTotalNumFamilies() end), population = core.read(function() return region:getNumTotalPopulation() end) } }
    end, { region = { type = "string", required = true }, count = { type = "integer", required = true, min = 1, max = 1000 } })
    commands.register("InvasionMod.probe_collapse", function(args)
        local region = region_object(args.region)
        if region == nil then return nil, "no region " .. args.region end
        local before, hit = read_region(region), 0
        for _, building in ipairs(core.listOf(core.read(function() return region:GetBuildings() end))) do
            if hit >= args.count then break end
            if core.isValid(building) and core.read(function() return building:IsRubble() end) ~= true then
                if pcall(function() building:collapseBuilding() end) then hit = hit + 1 end
            end
        end
        return { before = before, hit = hit, after = read_region(region) }
    end, { region = { type = "string", required = true }, count = { type = "integer", required = true, min = 1, max = 100 } })
end

return {}
