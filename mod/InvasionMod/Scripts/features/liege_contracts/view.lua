-- Pure text of the liege window (feature liege_contracts). No game access.
-- An item is an objective or a reward. In the game it shows as a letter box and a short amount text (owner decision 2026-10-28);
-- the tooltip holds the name and the description from the `items` map of the data file.
local rules = require("features.liege_contracts.rules")

local M = {}

local function item_entry(items, key, fallback_name)
    local entry = items[key]
    if entry then return entry.name, entry.description end
    return fallback_name, ""
end

local function good_name(items, good)
    local name = item_entry(items, "good:" .. good, "goods " .. good)
    return name
end

local function letter_of(text)
    return (tostring(text):sub(1, 1)):upper()
end

local OBJECTIVE_LETTERS = { kill_raiders = "K", build_count = "B", hold_public_order = "O", raise_militia_squads = "M" }
local REWARD_LETTERS = { influence = "I", silver = "S", public_order = "P", tech_pick = "T" }

-- Returns { letter, text, tooltip } for an objective.
function M.objective_item(objective, items)
    local kind, name, description = objective.type, item_entry(items, "objective:" .. objective.type, objective.type)
    local _, type_description = item_entry(items, "objective:" .. objective.type, "")
    description = type_description
    if kind == "deliver_goods" then
        local good = good_name(items, objective.good)
        return { letter = letter_of(good), text = string.format("%d %s", objective.amount, good),
                 tooltip = string.format("%s\n%s", name .. ": " .. good, description) }
    elseif kind == "build_count" then
        local building = item_entry(items, "building:" .. objective.building_type, "building " .. objective.building_type)
        return { letter = OBJECTIVE_LETTERS[kind], text = string.format("%d %s", objective.amount, building),
                 tooltip = string.format("%s\n%s", name .. ": " .. building, description) }
    elseif kind == "kill_raiders" then
        return { letter = OBJECTIVE_LETTERS[kind], text = string.format("%d raiders", objective.amount), tooltip = name .. "\n" .. description }
    elseif kind == "hold_public_order" then
        return { letter = OBJECTIVE_LETTERS[kind], text = string.format("%d order, %d days", objective.min, objective.days),
                 tooltip = string.format("%s\nAt least %d for %d days in a row.\n%s", name, objective.min, objective.days, description) }
    end
    return { letter = OBJECTIVE_LETTERS[kind] or "?", text = string.format("%d squads", objective.amount), tooltip = name .. "\n" .. description }
end

-- Returns { letter, text, tooltip } for a reward.
function M.reward_item(reward, items)
    local kind = reward.type
    local name, description = item_entry(items, "reward:" .. kind, kind)
    if kind == "goods" then
        local good = good_name(items, reward.good)
        return { letter = letter_of(good), text = string.format("+%d %s", reward.amount, good), tooltip = string.format("%s: %s\n%s", name, good, description) }
    elseif kind == "influence" then
        return { letter = REWARD_LETTERS[kind], text = string.format("+%d influence", reward.amount), tooltip = name .. "\n" .. description }
    elseif kind == "silver" then
        return { letter = REWARD_LETTERS[kind], text = string.format("+%d silver", reward.amount), tooltip = name .. "\n" .. description }
    elseif kind == "public_order" then
        return { letter = REWARD_LETTERS[kind], text = string.format("+%d order", reward.amount), tooltip = name .. "\n" .. description }
    end
    return { letter = REWARD_LETTERS[kind] or "?", text = string.format("+%d tech point", reward.amount), tooltip = name .. "\n" .. description }
end

-- One card of the offer.
function M.card(contract, items, penalty)
    local objectives, rewards = {}, {}
    for _, objective in ipairs(contract.objectives) do objectives[#objectives + 1] = M.objective_item(objective, items) end
    for _, reward in ipairs(contract.rewards) do rewards[#rewards + 1] = M.reward_item(reward, items) end
    return { id = contract.id, name = contract.name, quote = contract.quote, objectives = objectives, rewards = rewards,
             penalty = string.format("Fail: -%d influence", penalty) }
end

-- The lines of the active panel: one line for each objective ("Wood 12 / 60"), then the days left.
function M.active_lines(contract, progress)
    local lines = {}
    for index, objective in ipairs(contract.objectives) do
        local target = rules.target(objective)
        local label
        if objective.type == "deliver_goods" then label = "Deliver"
        elseif objective.type == "build_count" then label = "Build"
        elseif objective.type == "kill_raiders" then label = "Raiders killed"
        elseif objective.type == "hold_public_order" then label = string.format("Order %d or more (days)", objective.min)
        else label = "Militia squads" end
        lines[#lines + 1] = string.format("%s: %d / %d", label, math.min(progress[index] or 0, target), target)
    end
    return lines
end

-- Text of the time left. `deadline`: { kind = "winter_start" } or { kind = "days", left = n }.
function M.days_text(deadline)
    if deadline == nil then return "" end
    if deadline.kind == "days" then return string.format("%d days left", math.max(0, math.ceil(deadline.left))) end
    return "Ends when winter begins"
end

return M
