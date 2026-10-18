-- Game calls of the sack. Call only on the game thread. All changes go through HarnessSack (spike S6).
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

-- Apply a plan from rules.plan. Goods first (a fire takes goods by itself), then people, then buildings.
-- Returns the amounts that the game really took.
function M.apply(plan, method)
    local sack = sack_module()
    local goods_removed = 0
    for good, amount in pairs(plan.goods) do
        goods_removed = goods_removed + checked("sack_goods", sack.sack_goods({ good = good, amount = amount })).removed
    end
    local people = checked("sack_people", sack.sack_people({ count = plan.families }))
    local buildings = checked("sack_buildings", sack.sack_buildings({ count = plan.buildings, method = method }))
    return { goods_removed = goods_removed, families_removed = people.families, people_removed = people.people, buildings_hit = buildings.hit }
end

return M
