-- Pure rules of the tech tree feature (M12). No game access.
local tree_module = require("features.tech_tree.tree")
local M = {}

M.NO_PATH = "none"

local TOTAL_KEY = {
    public_order = "order_bonus", approval = "approval_bonus", buy_back_price = "buy_back_multiplier",
    militia_attack = "militia_attack_multiplier", militia_defence = "militia_defence_multiplier", manor_storage = "manor_storage_bonus", retinue_capacity = "retinue_bonus",
    tribute_share = "tribute_share_multiplier",
}

-- Flag effects (law_*): the total is a boolean.
local FLAG_KEY = { law_corpse_loot = "corpse_loot", law_disarm_homes = "disarm_homes" }

-- Picks (change update-tech-tree-yearly-picks). `earned` -1 means the picks never started.
-- `info` is { season, no } from the invasion feature (nil when no season is seen yet). Returns the new earned and spring_no,
-- and the reason: "start" (first look), "spring" (a new spring) or nil (nothing changed).
function M.picks_step(earned, spring_no, info, cfg)
    if info == nil then return earned, spring_no, nil end
    if earned < 0 then return cfg.initial_picks, info.no, "start" end
    if info.season == cfg.spring_season and info.no > spring_no then return earned + cfg.picks_per_year, info.no, "spring" end
    return earned, spring_no, nil
end

function M.free_picks(earned, unlocked)
    return math.max(0, earned) - #unlocked
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
-- A common tech skips the path and order checks. `free` is the number of free picks.
function M.unlock_refusal(tree, current_path, unlocked, free, node_id)
    local node = tree.by_id[node_id]
    if node == nil then return "unknown node '" .. tostring(node_id) .. "'" end
    if contains(unlocked, node_id) then return "node '" .. node_id .. "' is already unlocked" end
    if node.path ~= tree_module.COMMON then
        if current_path == M.NO_PATH then return "no path is chosen" end
        if node.path ~= current_path then return "node '" .. node_id .. "' belongs to the other path" end
        for _, required in ipairs(node.requires) do
            if not contains(unlocked, required) then return "node '" .. node_id .. "' needs '" .. required .. "' first" end
        end
    end
    if free < 1 then return "no free pick" end
    return nil
end

-- Sum the effects of the unlocked nodes.
-- Result: order_bonus and approval_bonus (sums); buy_back_multiplier, militia_attack_multiplier and militia_defence_multiplier (products).
-- An effect with min_garrison_squads counts only when garrison_squads reaches it.
function M.totals(tree, unlocked, garrison_squads, enacted)
    local totals = { order_bonus = 0, approval_bonus = 0, buy_back_multiplier = 1, militia_attack_multiplier = 1, militia_defence_multiplier = 1, manor_storage_bonus = 0, retinue_bonus = 0,
        tribute_share_multiplier = 1,
        banditry_gain_multiplier = 1, corpse_loot = false, disarm_homes = false }
    local sources = {}
    for _, id in ipairs(unlocked) do sources[#sources + 1] = tree.by_id[id] end
    for _, id in ipairs(enacted or {}) do sources[#sources + 1] = tree.laws_by_id[id] end
    for _, source in ipairs(sources) do
        for _, effect in ipairs(source.effects) do
            if effect.min_garrison_squads == nil or (garrison_squads or 0) >= effect.min_garrison_squads then
                local key = TOTAL_KEY[effect.kind]
                if FLAG_KEY[effect.kind] then
                    totals[FLAG_KEY[effect.kind]] = true
                elseif effect.kind == "law_banditry_gain" then
                    totals.banditry_gain_multiplier = totals.banditry_gain_multiplier * effect.value
                elseif tree_module.EFFECT_KINDS[effect.kind] == "add" then
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
        { "Militia defence", totals.militia_defence_multiplier }, { "Tribute", totals.tribute_share_multiplier or 1 },
    }
    for _, factor in ipairs(factors) do
        if math.abs(factor[2] - 1) > 1e-9 then parts[#parts + 1] = string.format("%s x%.2f", factor[1], factor[2]) end
    end
    if totals.corpse_loot then parts[#parts + 1] = "Corpse loot" end
    if totals.disarm_homes then parts[#parts + 1] = "Homes disarmed" end
    if math.abs((totals.banditry_gain_multiplier or 1) - 1) > 1e-9 then parts[#parts + 1] = string.format("Banditry loss x%.2f", totals.banditry_gain_multiplier) end
    if #parts == 0 then return "none" end
    return table.concat(parts, ", ")
end

-- Returns nil when the law may be enacted, or the reason. `max_active` limits the laws in force at the same time (TBD).
function M.enact_refusal(tree, current_path, unlocked, enacted, max_active, law_id)
    local law = tree.laws_by_id[law_id]
    if law == nil then return "unknown law '" .. tostring(law_id) .. "'" end
    if law.path ~= tree_module.COMMON then
        if current_path == M.NO_PATH then return "no path is chosen" end
        if law.path ~= current_path then return "law '" .. law_id .. "' belongs to the other path" end
    end
    if contains(enacted, law_id) then return "law '" .. law_id .. "' is already in force" end
    for _, required in ipairs(law.requires) do
        if not contains(unlocked, required) then return "law '" .. law_id .. "' needs the node '" .. required .. "' first" end
    end
    if #enacted >= max_active then return string.format("no free law place (%d in force of %d)", #enacted, max_active) end
    return nil
end

-- Returns nil when the vassal policy may be set, or the reason. A policy without a gate is open.
function M.vassal_policy_refusal(tree, current_path, unlocked, policy)
    local gate = tree.policy_gates[policy]
    if gate == nil then return nil end
    if current_path ~= gate.path then return "policy '" .. policy .. "' belongs to the path " .. gate.path end
    for _, required in ipairs(gate.requires) do
        if not contains(unlocked, required) then return "policy '" .. policy .. "' needs the node '" .. required .. "' first" end
    end
    return nil
end

-- The state of a node for the menu: "unlocked", "available", "other_path" or "locked" (with the reason of the refusal).
function M.node_status(tree, current_path, unlocked, free, node_id)
    if contains(unlocked, node_id) then return "unlocked" end
    local reason = M.unlock_refusal(tree, current_path, unlocked, free, node_id)
    if reason == nil then return "available" end
    local node_path = tree.by_id[node_id].path
    if current_path ~= M.NO_PATH and node_path ~= tree_module.COMMON and node_path ~= current_path then return "other_path", reason end
    return "locked", reason
end

return M
