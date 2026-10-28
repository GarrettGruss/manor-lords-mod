-- The Outlaws pawn (change update-banditry-rebellion-raid). The rebels belong to the bandit pawn "Outlaws".
-- With the game setting bandit camps 0 the game has no such pawn, so this module makes it and removes the camp that comes with it.
local core = require("ManorCore")

local M = {}

local TAG = "InvasionMod.bandits"

function M.default_deps()
    return { world = require("features.bandits.world"), log = core.log }
end

-- Idempotent. If the Outlaws pawn exists it does nothing and returns true.
-- Otherwise: spawnBanditCamp (the game picks the place) and addPawnRelations, kill the 18 camp Brigands and hide their bodies,
-- demolish the camp (SMBuildingMaster:demolish(true)). Returns true and a record, or nil and a message (a rebellion must not start then).
-- The record: { created, killed, demolished }.
function M.ensure(deps)
    deps = deps or M.default_deps()
    local world, log = deps.world, deps.log
    if world.bandit_pawn_exists() then return true, { created = false } end
    local camp, problem = world.spawn_camp()
    if camp == nil then
        log.error(TAG, "OUTLAWS camp call failed: " .. tostring(problem))
        return nil, tostring(problem)
    end
    local killed = world.kill_and_hide(camp.units)
    local demolished, why = world.demolish_camps(camp.camps)
    if demolished == nil then
        log.error(TAG, "OUTLAWS camp removal failed: " .. tostring(why))
        return nil, tostring(why)
    end
    log.info(TAG, string.format("OUTLAWS pawn created pawn_created=%s camp_units=%d killed=%d camps_demolished=%d",
        tostring(camp.pawn_created), #camp.units, killed, demolished))
    return true, { created = true, killed = killed, demolished = demolished, camp_units = #camp.units }
end

return M
