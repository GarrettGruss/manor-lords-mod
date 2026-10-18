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

function M.census()
    return checked("sack_census", sack_module().sack_census()).census
end

-- Take the goods of a plan out of the stores. The stores are read once and then only consumed, with no read between two calls:
-- HarnessSack.sack_goods read the inventories again after each unit and crashed the game on a real village (run 20261018-050233-020f).
-- Returns the units taken.
local function take_goods(goods)
    local stores = require("features.raid_behavior.world").stores() or {}
    local taken = 0
    for good, amount in pairs(goods) do
        local left = amount
        for _, store in ipairs(stores) do
            local held = store.by_good[good] or 0
            for _ = 1, math.min(held, left) do
                if not pcall(function() store.building:consumeGoodNoCheck(good) end) then break end
                left, taken = left - 1, taken + 1
            end
            if left <= 0 then break end
        end
    end
    return taken
end

-- Apply a plan from rules.plan. Goods first (a fire takes goods by itself), then people, then buildings.
-- Returns the amounts that the game really took.
function M.apply(plan, method)
    local sack = sack_module()
    core.log.info(TAG, "SACK step goods")
    local goods_removed = take_goods(plan.goods)
    core.log.info(TAG, "SACK step people")
    local people = checked("sack_people", sack.sack_people({ count = plan.families }))
    core.log.info(TAG, "SACK step buildings")
    local buildings = checked("sack_buildings", sack.sack_buildings({ count = plan.buildings, method = method }))
    return { goods_removed = goods_removed, families_removed = people.families, people_removed = people.people, buildings_hit = buildings.hit }
end

return M
