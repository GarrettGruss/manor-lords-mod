-- Pure rules of the tribute feature (M08). No game access.
local M = {}

function M.production(families, units_per_family)
    return families * units_per_family
end

-- Share of the production that the vassal sends. Grows with loyalty from share_min (loyalty 0) to share_max (loyalty 100).
function M.share(loyalty, share_min, share_max)
    local clamped = math.max(0, math.min(100, loyalty))
    return share_min + (share_max - share_min) * clamped / 100
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

return M
