-- Pure rules of the feature liege_influence. No game access.
local M = {}

function M.gain(amount, influence_per_unit)
    return amount * influence_per_unit
end

-- Returns nil when the treasury can pay the amount, else the reason for the refusal.
function M.refusal(amount, silver)
    if type(amount) ~= "number" or amount < 1 or amount ~= math.floor(amount) then return "the amount must be a whole number of at least 1" end
    if silver == nil then return "the silver of the lord's treasury is not known" end
    if silver < amount then return string.format("not enough silver: %d needed, %d held", amount, silver) end
    return nil
end

return M
