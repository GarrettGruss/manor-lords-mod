-- Pure rules of the tribute feature (M08). No game access.
local M = {}

function M.production(families, units_per_family)
    return families * units_per_family
end

function M.amount(production, share)
    return math.floor(production * share + 0.5)
end

-- Split an amount over `count` goods. The remainder goes to the first goods.
function M.split(amount, count)
    local parts = {}
    local base, rest = math.floor(amount / count), amount % count
    for index = 1, count do parts[index] = base + (index <= rest and 1 or 0) end
    return parts
end

-- A tick runs when the season differs from the saved one. A saved -1 means "not known yet": no tick.
function M.season_changed(current, last)
    return last >= 0 and current ~= last
end

-- A subjugation raid on a vassal region takes the vassal when it has been active for `siege_days` game days
-- and keeps at least `min_living` (a share) of its units. Returns "taken", "failed" (too few units left) or nil (still going).
function M.siege_result(summary, today, siege)
    if summary.kind ~= "subjugation" or summary.state ~= "active" or today == nil then return nil end
    if summary.initial < 1 or summary.living / summary.initial < siege.min_living then return "failed" end
    if today - summary.start_day >= siege.days then return "taken" end
    return nil
end

return M
