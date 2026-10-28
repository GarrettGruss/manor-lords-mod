-- The Outlaws pawn (change update-banditry-rebellion-raid). The rebels belong to the bandit pawn "Outlaws".
-- With the game setting bandit camps 0 the game has no such pawn, so this module makes it and then removes the camp that comes with it.
--
-- Real-game facts (runs rb-init-4, rb-init-5 and a bridge spike): a camp is built by its 18 Brigands. If they die in the same tick, the camp
-- stays unbuilt (IsConstructed false) and demolish(true) does nothing. A built camp is demolished by demolish(true) at once.
-- So the cleanup has two steps on later polls: wait until the camp is built, then kill and hide the Brigands and demolish the camp.
local core = require("ManorCore")

local M = {}

local TAG = "InvasionMod.bandits"
local pending = nil   -- { camps = addresses, units = addresses, tries, killed }
local MAX_TRIES = 120 -- polls (one second each) before the mod kills the Brigands even if the camp is not built, and before it gives up

function M.default_deps()
    return { world = require("features.bandits.world"), log = core.log }
end

-- Idempotent. If the Outlaws pawn exists it does nothing and returns true.
-- Otherwise it calls spawnBanditCamp (the game picks the place) and addPawnRelations. The pawn exists then, so a rebellion may go on.
-- The camp cleanup runs in finish_camp_removal() on the next polls. Returns true and a record { created, camp_units, camps },
-- or nil and a message (a rebellion must not start then).
function M.ensure(deps)
    deps = deps or M.default_deps()
    local world, log = deps.world, deps.log
    if world.bandit_pawn_exists() then return true, { created = false } end
    local camp, problem = world.spawn_camp()
    if camp == nil then
        log.error(TAG, "OUTLAWS camp call failed: " .. tostring(problem))
        return nil, tostring(problem)
    end
    pending = { camps = camp.camps, units = camp.units, tries = 0, killed = false }
    log.info(TAG, string.format("OUTLAWS pawn created pawn_created=%s camp_units=%d camps=%d", tostring(camp.pawn_created), #camp.units, #camp.camps))
    return true, { created = true, camp_units = #camp.units, camps = #camp.camps }
end

-- True while the camp cleanup has work.
function M.camp_pending() return pending ~= nil end

-- One step of the camp cleanup. Call it on each poll while camp_pending(). Returns true while it still has work.
function M.finish_camp_removal(deps)
    if pending == nil then return false end
    deps = deps or M.default_deps()
    local world, log = deps.world, deps.log
    pending.tries = pending.tries + 1
    if not pending.killed then
        local built = world.camps_built(pending.camps)
        if not built and pending.tries < MAX_TRIES then return true end
        local killed = world.kill_units_by_address(pending.units)
        pending.killed = true
        log.info(TAG, string.format("OUTLAWS camp built=%s: killed %d camp Brigands after %d polls", tostring(built), killed, pending.tries))
    end
    local called, standing = world.demolish_camps(pending.camps)
    if called == nil then
        log.error(TAG, "OUTLAWS camp removal failed: " .. tostring(standing))
        pending = nil
        return false
    end
    if standing == 0 then
        log.info(TAG, string.format("OUTLAWS camp is gone after %d polls", pending.tries))
        pending = nil
        return false
    end
    if pending.tries >= 2 * MAX_TRIES then
        log.error(TAG, string.format("OUTLAWS camp still stands after %d polls", pending.tries))
        pending = nil
        return false
    end
    return true
end

return M
