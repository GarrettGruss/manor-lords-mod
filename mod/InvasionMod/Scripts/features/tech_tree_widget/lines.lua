-- Pure text rules of the tech tree menu (M12 iteration 02, layout of change update-tech-tree-widget-layout). No game calls, so a test can run them.
local M = {}

M.COMMON_ROW = 2 -- the row of the common techs (rows 0 and 1 are the paths)
M.FIXED_TEXT = "One tech pick each spring. The path you swear to is final."
M.START_MESSAGE = "Pick a tech, or swear to a path."

local MARK = { unlocked = "[x] " }
local COLOR = {
    unlocked = { R = 0.89, G = 0.76, B = 0.48, A = 1 },
    available = { R = 0.61, G = 0.75, B = 0.48, A = 1 },
    locked = { R = 0.72, G = 0.66, B = 0.53, A = 1 },
    no_pick = { R = 0.72, G = 0.66, B = 0.53, A = 1 },
    no_path = { R = 0.72, G = 0.66, B = 0.53, A = 1 },
    other_path = { R = 0.4, G = 0.36, B = 0.3, A = 1 },
}
-- Flat colours of the path rings and rows (mockup: oppression, prosperity, common).
local PATH_COLOR = {
    oppression = { R = 0.82, G = 0.51, B = 0.35, A = 1 },
    prosperity = { R = 0.61, G = 0.75, B = 0.48, A = 1 },
    common = { R = 0.84, G = 0.78, B = 0.67, A = 1 },
}
local PATH_LETTER = { oppression = "O", prosperity = "P", common = "C" }
local LINK_LIT = { R = 0.89, G = 0.76, B = 0.48, A = 1 }
local LINK_DARK = { R = 0.23, G = 0.17, B = 0.1, A = 1 }
local COLUMN_HEAD = { "First tech", "Second tech", "Third tech", "Fourth tech" }
local NUMERALS = { "I", "II", "III", "IV" }

function M.color(status) return COLOR[status] or COLOR.locked end
function M.path_color(path) return PATH_COLOR[path] or PATH_COLOR.common end
function M.path_letter(path) return PATH_LETTER[path] or "?" end
function M.link_color(lit) return lit and LINK_LIT or LINK_DARK end

-- The text of a column head ("I  First tech"). Columns are by order, not by settlement level.
function M.column_head(column)
    return string.format("%s  %s", NUMERALS[column] or tostring(column), COLUMN_HEAD[column] or "")
end

-- The tech picks counter: "1 free (0 of 1 used)".
function M.picks_text(view)
    return string.format("%d free (%d of %d used)", view.free_picks, view.picks_earned - view.free_picks, view.picks_earned)
end

-- Status shown on a card: unlocked, available, locked, no_pick, no_path or other_path.
function M.display_status(row)
    if row.status == "locked" then
        if row.reason == "no free pick" then return "no_pick" end
        if row.reason == "no path is chosen" then return "no_path" end
    end
    return row.status
end

local STATUS_TEXT = {
    unlocked = "Unlocked", available = "Available", locked = "Needs earlier tech",
    no_pick = "No free pick", no_path = "Choose a path", other_path = "Other path",
}
function M.status_text(row) return STATUS_TEXT[M.display_status(row)] or "" end

-- The cards in the pool order: the path nodes of the tree, then the common techs (row 2, one column each).
function M.cards(view)
    local cards = {}
    for _, row in ipairs(view.nodes) do cards[#cards + 1] = row end
    for i, row in ipairs(view.common_nodes or {}) do
        row.layout = { x = i - 1, y = M.COMMON_ROW }
        cards[#cards + 1] = row
    end
    return cards
end

-- The row of a node card: its path ("oppression", "prosperity" or "common").
function M.card_path(row) return row.path or "common" end

local function short_effects(source, tree)
    local text = M.effect_lines(source, tree)
    text = text:gsub(" %(needs at least (%d+) garrison squads%)", " (%1+ squads)")
    return text
end

-- Card text: name (with the unlock mark), status, effects ("No standing effect" when none).
function M.card_text(row, source, tree)
    local effects = source and short_effects(source, tree) or ""
    if effects == "" then effects = "No standing effect" end
    return (MARK[row.status] or "") .. row.name .. "\n" .. M.status_text(row) .. "\n" .. effects
end

-- The law a tech opens: the first law whose `requires` has the node id. Nil when none.
function M.law_of_node(node_id, tree)
    for _, law in ipairs(tree.laws) do
        if law.requires[1] == node_id then return law end
    end
    return nil
end

function M.card_law_text(law) return law and law.name or "No law" end

-- The button of a law on a card: "Repeal" in force, "Enact" when open, nil (hidden) otherwise.
-- A law of an unlocked tech with no free law place keeps its Enact button: a click is refused and the footer says why.
function M.law_button_label(law_row)
    if law_row == nil then return nil end
    if law_row.status == "enacted" then return "Repeal" end
    if law_row.status == "available" then return "Enact" end
    if law_row.reason and tostring(law_row.reason):find("^no free law place") then return "Enact" end
    return nil
end

-- The rows of the laws of the chosen path and the common laws, by id.
function M.law_rows_by_id(view)
    local by_id = {}
    for _, group in ipairs({ view.laws or {}, view.common_laws or {} }) do
        for _, law in ipairs(group) do by_id[law.id] = law end
    end
    return by_id
end

function M.enacted_laws(view)
    local list = {}
    for _, law in ipairs(view.laws or {}) do if law.status == "enacted" then list[#list + 1] = law end end
    for _, law in ipairs(view.common_laws or {}) do if law.status == "enacted" then list[#list + 1] = law end end
    return list
end

-- The strip count: "1 of 2 max" (laws in force of the most allowed).
function M.strip_count_text(view)
    return string.format("%d of %d max", #M.enacted_laws(view), view.max_laws)
end

-- Text of one place of the laws strip: name and effects of the law, or "Empty".
function M.strip_place_text(law, tree)
    if law == nil then return "Empty place" end
    local source = tree.laws_by_id[law.id]
    local effects = source and M.effect_lines(source, tree):gsub("\n", ", ") or ""
    return law.name .. "\n" .. effects
end

-- A reason of a refusal in short words for the footer.
function M.short_reason(reason)
    reason = tostring(reason)
    local in_force, most = reason:match("^no free law place %((%d+) in force of (%d+)%)")
    if in_force then return string.format("%s of %s laws are in force", in_force, most) end
    if reason:find("belongs to the other path", 1, true) then return "it belongs to the other path" end
    if reason:find("needs '", 1, true) then return "needs the earlier tech first" end
    if reason:find("is already unlocked", 1, true) then return "already unlocked" end
    if reason:find("is already in force", 1, true) then return "already in force" end
    return reason
end

-- Footer message of a click. `what` is the name of the tech, law or path.
-- kind: choose, unlock, enact or repeal. Success text first, refusal text with the reason otherwise.
local DONE = { choose = "You swore to %s. This is final.", unlock = "%s unlocked. 1 pick used.", enact = "%s enacted.", repeal = "%s repealed." }
function M.result_message(kind, what, ok, reason)
    if ok then return string.format(DONE[kind] or "%s done.", what) end
    return string.format("%s refused: %s.", what, M.short_reason(reason))
end

-- The status line of a row label: path rows and the common row.
function M.row_status_text(path_id, view)
    if path_id == "common" then return "For both paths, in any order" end
    if view.path == nil or view.path == "none" then return path_id == "oppression" and "Rule by fear, order and levies" or "Rule by law, trade and goodwill" end
    if view.path == path_id then return "Sworn path" end
    return "Closed"
end

function M.path_button_label() return "Swear to this path" end
-- Pixel position of a card on the canvas from its layout data. The origin is the top left of the first card.
function M.position(layout, step_x, step_y, origin_x, origin_y)
    return { X = (origin_x or 0) + layout.x * step_x, Y = (origin_y or 0) + layout.y * step_y }
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
    law_corpse_loot = "Corpse loot at the pit",
    law_disarm_homes = "Home weapons go to the storehouse",
    law_banditry_gain = "Banditry order loss",
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
    if kinds[effect.kind] == "flag" then
        text = name -- the value of a flag is ignored
    elseif kinds[effect.kind] == "factor" then
        text = string.format("%s x%s", name, tostring(effect.value))
    elseif kinds[effect.kind] == "percent" then
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
