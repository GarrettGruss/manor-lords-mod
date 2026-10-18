-- Pure rules of the tech tree feature (M12). No game access.
local tree_module = require("features.tech_tree.tree")
local M = {}

M.NO_PATH = "none"

local TOTAL_KEY = {
    public_order = "order_bonus", approval = "approval_bonus", buy_back_price = "buy_back_multiplier",
    militia_attack = "militia_attack_multiplier", militia_defence = "militia_defence_multiplier", manor_storage = "manor_storage_bonus", retinue_capacity = "retinue_bonus",
}

-- Decision 24: one node slot for each settlement level.
function M.slots_for_level(level, slots_per_level)
    return math.max(0, math.floor((level or 0) * slots_per_level))
end

-- The unlocked ids are saved as one text with dots between the ids (ModState allows only A-Z a-z 0-9 _ . -). No id may contain a dot.
function M.parse_ids(text)
    local ids = {}
    for id in string.gmatch(text or "", "[^.]+") do ids[#ids + 1] = id end
    return ids
end

function M.join_ids(ids) return table.concat(ids, ".") end

local function contains(list, value)
    for _, item in ipairs(list) do if item == value then return true end end
    return false
end

-- Returns nil when the path may be chosen, or the reason. The choice is final (decision 22).
function M.path_refusal(tree, current_path, wanted)
    if current_path ~= M.NO_PATH then return "the path is already chosen: " .. current_path end
    if tree.path_ids[wanted] == nil then return "unknown path '" .. tostring(wanted) .. "'" end
    return nil
end

-- Returns nil when the node may be unlocked, or the reason.
function M.unlock_refusal(tree, current_path, unlocked, slots, node_id)
    local node = tree.by_id[node_id]
    if node == nil then return "unknown node '" .. tostring(node_id) .. "'" end
    if current_path == M.NO_PATH then return "no path is chosen" end
    if node.path ~= current_path then return "node '" .. node_id .. "' belongs to the other path" end
    if contains(unlocked, node_id) then return "node '" .. node_id .. "' is already unlocked" end
    for _, required in ipairs(node.requires) do
        if not contains(unlocked, required) then return "node '" .. node_id .. "' needs '" .. required .. "' first" end
    end
    if #unlocked >= slots then return string.format("no free node slot (%d used of %d)", #unlocked, slots) end
    return nil
end

-- Sum the effects of the unlocked nodes.
-- Result: order_bonus and approval_bonus (sums); buy_back_multiplier, militia_attack_multiplier and militia_defence_multiplier (products).
-- An effect with min_garrison_squads counts only when garrison_squads reaches it.
function M.totals(tree, unlocked, garrison_squads)
    local totals = { order_bonus = 0, approval_bonus = 0, buy_back_multiplier = 1, militia_attack_multiplier = 1, militia_defence_multiplier = 1, manor_storage_bonus = 0, retinue_bonus = 0 }
    for _, id in ipairs(unlocked) do
        for _, effect in ipairs(tree.by_id[id].effects) do
            if effect.min_garrison_squads == nil or (garrison_squads or 0) >= effect.min_garrison_squads then
                local key = TOTAL_KEY[effect.kind]
                if tree_module.EFFECT_KINDS[effect.kind] == "add" then
                    totals[key] = totals[key] + effect.value
                else
                    totals[key] = totals[key] * (1 + effect.value)
                end
            end
        end
    end
    return totals
end

-- The text for the effect totals, for the menu. Neutral values are left out.
function M.describe_totals(totals)
    local parts = {}
    if totals.order_bonus ~= 0 then parts[#parts + 1] = string.format("Public Order %+d", totals.order_bonus) end
    if totals.approval_bonus ~= 0 then parts[#parts + 1] = string.format("Approval %+d", totals.approval_bonus) end
    if (totals.manor_storage_bonus or 0) ~= 0 then parts[#parts + 1] = string.format("Manor storage %+d", totals.manor_storage_bonus) end
    if (totals.retinue_bonus or 0) ~= 0 then parts[#parts + 1] = string.format("Retinue %+d", totals.retinue_bonus) end
    local factors = {
        { "Buy-back price", totals.buy_back_multiplier }, { "Militia attack", totals.militia_attack_multiplier },
        { "Militia defence", totals.militia_defence_multiplier },
    }
    for _, factor in ipairs(factors) do
        if math.abs(factor[2] - 1) > 1e-9 then parts[#parts + 1] = string.format("%s x%.2f", factor[1], factor[2]) end
    end
    if #parts == 0 then return "none" end
    return table.concat(parts, ", ")
end

-- The state of a node for the menu: "unlocked", "available", "other_path" or "locked" (with the reason of the refusal).
function M.node_status(tree, current_path, unlocked, slots, node_id)
    if contains(unlocked, node_id) then return "unlocked" end
    local reason = M.unlock_refusal(tree, current_path, unlocked, slots, node_id)
    if reason == nil then return "available" end
    if current_path ~= M.NO_PATH and tree.by_id[node_id].path ~= current_path then return "other_path", reason end
    return "locked", reason
end

return M
