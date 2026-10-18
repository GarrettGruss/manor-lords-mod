-- Pure rules of the manor stronghold feature (M13). No game access.
local M = {}

-- Capacity of one manor module in units of goods. The bonus comes from the tech tree.
function M.storage_capacity(base, bonus)
    return math.max(0, math.floor(base + (bonus or 0)))
end

-- Why a squad cannot be hired now, or nil. Each `bonus_per_squad` of the retinue bonus allows one extra squad.
function M.squad_refusal(bonus, squads_made, bonus_per_squad, silver, cost)
    if bonus_per_squad <= 0 then return "squads are off" end
    if squads_made >= math.floor((bonus or 0) / bonus_per_squad) then return "the retinue bonus allows no further squad" end
    if silver < cost then return string.format("not enough silver: %d needed, %d held", cost, silver) end
    return nil
end

return M
