-- The rebellion (change update-banditry-rebellion-raid): armed families leave, take their goods and come back as Outlaws.
-- Order: ensure the Outlaws pawn, find the valid families, pick at random, take the goods, kill the families and hide the bodies,
-- spawn the squad at the first home, record the loot overrides. The pure rules are in rules.lua; the game calls are in world.lua.
local core = require("ManorCore")
local rules = require("features.bandits.rules")
local outlaws = require("features.bandits.outlaws")

local M = {}

local TAG = "InvasionMod.bandits"

function M.default_deps()
    local ok, overrides = pcall(function() return require("features.raid_behavior.init").loot_override end)
    return {
        world = require("features.bandits.world"), log = core.log, config = require("config").bandits,
        outlaws = outlaws, overrides = ok and overrides or nil, random = math.random,
    }
end

-- Put the loot overrides on the spawned units. Returns the number of units that got an entry.
local function record_overrides(deps, units, goods)
    if deps.overrides == nil then
        deps.log.error(TAG, "BANDITS no loot override state: the goods are not recorded")
        return 0
    end
    local per_unit, recorded = rules.spread_goods(goods, #units), 0
    for index, unit in ipairs(units) do
        if #per_unit[index] > 0 then
            if deps.overrides.set(unit, per_unit[index]) then recorded = recorded + 1 end
        end
    end
    return recorded
end

-- wanted: the number of families that must leave. Returns a record:
-- { wanted, removed, spawned, blocked (a message or nil), valid, taken, returned, squads, bandit_units, overrides, pawn_created, at, distance }
function M.run(region, wanted, deps)
    local world, log, config = deps.world, deps.log, deps.config
    local result = { wanted = wanted, removed = 0, spawned = false, taken = 0, returned = 0, squads = 0, bandit_units = 0, overrides = 0, pawn_created = false }
    local ready, info = deps.outlaws.ensure({ world = world, log = log })
    if not ready then
        result.blocked = "no Outlaws pawn: " .. tostring(info)
        return result
    end
    result.pawn_created = info.created == true
    local valid = world.armed_families(region, rules.id_set(config.rebellion_weapon_ids))
    result.valid = #valid
    local reason = rules.rebellion_block(#valid, wanted)
    if reason ~= nil then
        result.blocked = reason
        return result
    end
    local chosen = rules.pick_families(valid, wanted, deps.random)
    local taken, members = {}, {}
    result.take_failures = 0
    local emptied = {}   -- homes whose goods were taken already (families can share a home)
    for _, family in ipairs(chosen) do
        if not emptied[family.key] then
            emptied[family.key] = true
            local ids, failures = world.take_goods(family.home, family.goods)
            for _, id in ipairs(ids) do taken[#taken + 1] = { home = family.home, id = id } end
            if failures ~= nil and #failures > 0 then
                result.take_failures = result.take_failures + #failures
                log.warn(TAG, string.format("BANDITS %d of %d goods could not be taken from a home: %s", #failures, #family.goods, failures[1]))
            end
        end
        for _, member in ipairs(family.members) do members[#members + 1] = member end
    end
    result.taken = #taken
    world.kill_and_hide(members)
    result.removed = #chosen
    local spawned, problem = world.spawn_squads(config.rebellion_squads, chosen[1].at)
    if spawned == nil then
        result.returned = world.return_goods(taken)
        result.error = tostring(problem)
        log.error(TAG, string.format("BANDITS rebellion spawn failed: %s (goods returned: %d of %d)", tostring(problem), result.returned, #taken))
        return result
    end
    result.spawned, result.squads, result.bandit_units = true, #spawned.squads, #spawned.units
    result.at = { x = chosen[1].at.x, y = chosen[1].at.y }
    result.distance = world.distance and world.distance(result.at) or nil
    local ids = {}
    for _, row in ipairs(taken) do ids[#ids + 1] = row.id end
    result.overrides = record_overrides(deps, spawned.units, ids)
    return result
end

return M
