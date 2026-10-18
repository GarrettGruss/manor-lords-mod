-- Pure rules of the fallback capital (M06 iteration 03). No game access.
local M = {}

-- Silver price of the move: cost_base x difficulty (TBD, playtests).
function M.cost(difficulty, config)
    return config.cost_base * difficulty
end

-- Why the move is refused, or nil. `facts`: has_vassal, is_capital, buildings, silver, already.
function M.refusal(facts, cost, config)
    if not facts.has_vassal then return "the slot has no handed-over vassal" end
    if facts.already then return "a fallback capital exists already" end
    if facts.buildings < config.min_buildings then
        return string.format("the vassal is not fortified enough (%d buildings, need %d)", facts.buildings, config.min_buildings)
    end
    if facts.silver < cost then return string.format("not enough silver (%d, need %d)", facts.silver, cost) end
    return nil
end

return M
