-- Pure rules of the tribute terms (no game calls).
local M = {}

M.NONE, M.OFFERED, M.PAID, M.VASSAL = 0, 1, 2, 3

-- Amounts grow in a straight line with the difficulty, like the sack (decision 15). Counts round up (decision 28).
function M.payment(difficulty, cfg) return math.ceil(cfg.payment_base * difficulty) end
function M.tribute(difficulty, cfg) return math.ceil(cfg.tribute_base * difficulty) end

-- Returns nil when the player can accept, else the reason.
function M.refusal(kind, offered, silver, amount)
    if not offered then return "no offer is open" end
    if kind == "payment" and (type(silver) ~= "number" or silver < amount) then
        return string.format("silver %s is below the payment %d", tostring(silver), amount)
    end
    return nil
end

function M.tribute_due(terms_state, next_day, today)
    return terms_state == M.VASSAL and next_day > 0 and today >= next_day
end

-- The player pays what the silver allows (TBD rule).
function M.tribute_charge(silver, tribute)
    return math.max(0, math.min(silver, tribute))
end

return M
