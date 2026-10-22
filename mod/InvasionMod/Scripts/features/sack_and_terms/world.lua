-- Game calls of the sack. Call only on the game thread. All changes go through HarnessSack (spike S6).
local core = require("ManorCore")
local TAG = "InvasionMod.sack_and_terms"
local M = {}

local function sack_module()
    local ok, module = pcall(require, "HarnessSack")
    if not ok then error("HarnessSack is not available: " .. tostring(module), 0) end
    return module
end

local function checked(label, answer)
    if answer == nil or answer.ok ~= true then error(label .. " failed: " .. tostring(answer and answer.error), 0) end
    return answer
end

-- `region` (optional): the object name of the player region to sack. Without it HarnessSack takes the first region of the player.
function M.census(region)
    return checked("sack_census", sack_module().sack_census({ region = region })).census
end

-- Object names of the regions that the player owns.
function M.player_region_names()
    local names = {}
    for _, row in ipairs(require("features.vassals.world").player_regions() or {}) do names[#names + 1] = row.region end
    return names
end


-- Apply a plan from rules.plan: people, then buildings. The mod takes no goods (a fire may destroy some; owner decision 2026-10-21).
-- Returns the amounts that the game really took.
function M.apply(plan, method, region)
    local sack = sack_module()
    core.log.info(TAG, "SACK step people")
    local people = checked("sack_people", sack.sack_people({ count = plan.families, region = region, light = true }))
    core.log.info(TAG, "SACK step buildings")
    local buildings = checked("sack_buildings", sack.sack_buildings({ count = plan.buildings, method = method, region = region, light = true }))
    return { goods_removed = 0, families_removed = people.families, people_removed = people.people, buildings_hit = buildings.hit }
end

return M
