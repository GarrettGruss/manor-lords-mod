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

-- How a raid ended for the protection of a vassal: "defended" when the player killed the raid or made it leave by losses,
-- "undefended" for any other end. A raid that does not target a vassal region gives nil.
function M.protection_outcome(summary, is_vassal_region)
    if summary.target == nil or not is_vassal_region then return nil end
    if summary.state == "destroyed" or summary.leave_reason == "losses" then return "defended" end
    return "undefended"
end

function M.loyalty_change(outcome, protection)
    if outcome == "defended" then return protection.defended end
    return protection.undefended
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
