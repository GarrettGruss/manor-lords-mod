-- Pure text of the liege window (feature liege_contracts, changes update-liege-contracts-tiers, #533, and update-liege-contracts-tier-goods, #569). No game access.
local M = {}

M.TIER_NAMES = { small = "Small", medium = "Medium", large = "Large" }

local function good_name(names, good)
    return names[good] or ("goods " .. tostring(good))
end

-- The text of a Large cost: "1 squad for 60 days", "3 families, for good", "tribute for 3 months".
function M.cost_text(cost, amount, loan_days)
    if cost == "loan_units" then
        return string.format("%d squad%s for %d days", amount, amount == 1 and "" or "s", loan_days or 0)
    elseif cost == "send_families" then
        return string.format("%d famil%s, for good", amount, amount == 1 and "y" or "ies")
    elseif cost == "tribute_season" then
        return string.format("tribute for %d month%s", amount, amount == 1 and "" or "s")
    end
    return string.format("%d of %s", amount, tostring(cost))
end

-- "Deliver 40 firewood" for a Small or Medium contract, "Cost: 3 families, for good" for a Large contract.
function M.requirement_text(contract, names, loan_days)
    if contract.cost then return "Cost: " .. M.cost_text(contract.cost, contract.amount, loan_days) end
    return string.format("Deliver %d %s", contract.amount, good_name(names, contract.good))
end

M.NEEDS_RETINUE_TEXT = "Needs a retinue squad"

-- The banner when a loaned squad comes back.
function M.loan_return_text(men)
    return string.format("The liege returns your squad (%d men)", men)
end

-- "In storage: 52 / 50"
function M.have_text(have, need)
    return string.format("In storage: %d / %d", math.floor(have or 0), need)
end

-- The line under a Large cost: what the player has now ("Families: 5").
function M.cost_have_text(cost, held)
    local label = cost == "loan_units" and "Retinue squads" or cost == "send_families" and "Families" or "Vassals"
    return string.format("%s: %d", label, math.floor(held or 0))
end

-- "+30 clay", "+10 King's Favour", "a new law", "+1 law slot", "+5 squads in the relief army"
function M.reward_text(reward, names)
    local kind = reward.kind
    if kind == "goods" or kind == "weapons" or kind == "armor" then return string.format("+%d %s", reward.amount, good_name(names, reward.good)) end
    if kind == "law" then return "a new law" end
    if kind == "kings_favour" then return string.format("+%d King's Favour", reward.amount) end
    if kind == "law_slot" then return string.format("+%d law slot%s", reward.amount, reward.amount == 1 and "" or "s") end
    if kind == "retinue_squad" then return string.format("+%d retinue squad%s", reward.amount, reward.amount == 1 and "" or "s") end
    if kind == "relief_promise" then return string.format("+%d relief squads", reward.amount) end
    return string.format("+%d %s", reward.amount, tostring(kind))
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

-- The widget draws a white label and a gold value. "Time to fulfil contracts: 210 days remaining" -> "Time to fulfil contracts:", "210 days remaining"
function M.split_label(text)
    local label, value = text:match("^(.-:)%s*(.*)$")
    if label == nil then return text, "" end
    return label, value
end

-- "Deliver 50 planks" -> "Deliver", "50 PLANKS" (goods in gold capitals)
function M.split_requirement(text)
    local verb, rest = text:match("^(%S+)%s+(.+)$")
    if verb == nil then return "", text:upper() end
    return verb, rest:upper()
end

-- "+30 clay" -> "Reward:", "+30 CLAY"
function M.split_reward(text)
    return "Reward:", text:upper()
end

M.TITLE_TEXT = "CONTRACTS OF THE LIEGE"

M.NO_OFFER_TEXT = "The liege sends new contracts at the start of spring."

return M
