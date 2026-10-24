-- Pure text rules of the tech tree menu (M12 iteration 02). No game calls, so a test can run them.
local M = {}

local MARK = { unlocked = "[x] ", available = "", locked = "", other_path = "" }
local COLOR = {
    unlocked = { R = 0.25, G = 0.7, B = 0.3, A = 1 },
    available = { R = 1, G = 1, B = 1, A = 1 },
    locked = { R = 0.45, G = 0.45, B = 0.45, A = 1 },
    other_path = { R = 0.3, G = 0.12, B = 0.12, A = 1 },
}

function M.color(status) return COLOR[status] or COLOR.locked end

function M.node_label(row)
    return (MARK[row.status] or "") .. row.name
end

-- Three lines: the path, the slots, the effects.
function M.header(view)
    local path = view.path_name and (view.path_name .. " (final)") or "not chosen yet"
    local slots = string.format("Node slots: %d free of %d (settlement level %d)", view.free_slots, view.slots, view.level)
    return { "Path: " .. path, slots, "Effects: " .. view.effects }
end

-- The line above the law buttons.
function M.laws_line(view)
    if view.path_name == nil then return "Laws: choose a path first" end
    return string.format("Laws: %d of %d in force", #M.enacted_names(view), view.max_laws)
end

function M.enacted_names(view)
    local names = {}
    for _, law in ipairs(view.laws) do
        if law.status == "enacted" then names[#names + 1] = law.name end
    end
    return names
end

-- A law button says what a click does: repeal a law in force, enact an open law, or why it is closed.
function M.law_label(law)
    if law.status == "enacted" then return "[in force] " .. law.name .. " (repeal)" end
    if law.status == "available" then return "Enact " .. law.name end
    return law.name .. " (closed)"
end

function M.path_label(path) return "Choose " .. path.name end

-- Pixel position of a node on the canvas from its layout data.
function M.position(layout, step_x, step_y)
    return { X = layout.x * step_x, Y = layout.y * step_y }
end

-- Tooltip text (add-tech-tooltip). The text comes from the effect data, so there is no second copy of the numbers.
-- A kind has a name. Its type (add or percent) comes from the tree data (tree.EFFECT_KINDS).
M.KIND_TEXT = {
    public_order = "Public Order",
    approval = "Approval",
    buy_back_price = "Buy-back price",
    militia_attack = "Militia attack",
    militia_defence = "Militia defence",
    retinue_capacity = "Retinue capacity",
    tribute_share = "Tribute share",
    manor_storage = "Manor storage capacity",
}

-- A percent value is a factor: 0.10 shows "+10%". A value that is not a whole percent shows one decimal.
local function percent_text(value)
    local percent = value * 100
    if math.abs(percent - math.floor(percent + 0.5)) < 1e-6 then return string.format("%+d%%", math.floor(percent + 0.5)) end
    return string.format("%+.1f%%", percent)
end

function M.effect_line(effect, kinds)
    local name = M.KIND_TEXT[effect.kind] or effect.kind
    local text
    if kinds[effect.kind] == "percent" then
        text = name .. " " .. percent_text(effect.value)
    else
        text = string.format("%s %+d", name, effect.value)
    end
    if effect.min_garrison_squads then
        text = text .. string.format(" (needs at least %d garrison squads)", effect.min_garrison_squads)
    end
    return text
end

-- All lines of a node or a law (`source` has `effects`), joined with a newline. `tree` has EFFECT_KINDS-like `kinds` and policy_gates.
-- `source_id` is the node id: a vassal policy that the node opens (it is the last required node of a gate) adds a line.
function M.effect_lines(source, tree, kinds)
    kinds = kinds or require("features.tech_tree.tree").EFFECT_KINDS
    local out = {}
    for _, effect in ipairs(source.effects or {}) do out[#out + 1] = M.effect_line(effect, kinds) end
    local policies = {}
    for policy, gate in pairs(tree.policy_gates or {}) do
        for _, required in ipairs(gate.requires) do
            if required == source.id then
                policies[#policies + 1] = policy
            end
        end
    end
    table.sort(policies)
    for _, policy in ipairs(policies) do out[#out + 1] = "Opens vassal policy " .. policy end
    return table.concat(out, "\n")
end

return M
