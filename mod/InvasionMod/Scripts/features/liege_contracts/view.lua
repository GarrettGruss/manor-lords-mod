-- Pure text of the liege window (feature liege_contracts, change update-liege-contracts-tiers, #533). No game access.
local M = {}

M.TIER_NAMES = { small = "Small", medium = "Medium", large = "Large" }

local function good_name(names, good)
    return names[good] or ("goods " .. tostring(good))
end

-- "Deliver 40 firewood"
function M.requirement_text(contract, names)
    return string.format("Deliver %d %s", contract.amount, good_name(names, contract.good))
end

-- "In storage: 52 / 50"
function M.have_text(have, need)
    return string.format("In storage: %d / %d", math.floor(have or 0), need)
end

-- "+30 clay", "+60 regional wealth", "+200 treasury silver", "+1 tech point", "+1000 influence"
function M.reward_text(reward, names)
    local kind = reward.kind
    if kind == "goods" or kind == "weapons" then return string.format("+%d %s", reward.amount, good_name(names, reward.good)) end
    if kind == "regional_wealth" then return string.format("+%d regional wealth", reward.amount) end
    if kind == "silver" then return string.format("+%d treasury silver", reward.amount) end
    if kind == "tech_point" then return string.format("+%d tech point%s", reward.amount, reward.amount == 1 and "" or "s") end
    return string.format("+%d influence", reward.amount)
end

function M.tier_count_text(used, limit)
    return string.format("%d / %d", used, limit)
end

-- "Time to fulfil contracts: 210 days remaining" (the days until winter begins)
function M.remaining_text(days)
    if days == nil then return "Time to fulfil contracts: -" end
    return string.format("Time to fulfil contracts: %d days remaining", days)
end

function M.no_contracts_remaining_text()
    return "Time to fulfil contracts: no contracts now"
end

-- "In spring, in 300 days"
function M.refresh_text(days)
    if days == nil then return "Contracts refresh: In spring" end
    return string.format("Contracts refresh: In spring, in %d days", days)
end

M.NO_OFFER_TEXT = "The liege sends new contracts at the start of spring."

return M
