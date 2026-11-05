-- Pure view rules of the Laws menu (change add-laws-menu, #563). No game calls, so a test can run them.
-- `build(model)` returns the header, the filter and the cards of the nine laws. The texts are the ones of the approved mockup.
local lines = require("features.tech_tree_widget.lines")
local tree_module = require("features.tech_tree.tree")
local M = {}

M.TITLE = "LAWS"
M.FILTERS = { { id = "all", text = "All" }, { id = "unlocked", text = "Unlocked" }, { id = "locked", text = "Locked" } }
M.NO_ENACT = "No enact action left this year."
M.NO_REVOKE = "No revoke action left this year."
M.SLOTS_FULL = "All law slots are used. Revoke a law first."
M.USES_ENACT = "Uses the enact action of this year."
M.USES_REVOKE = "Uses the revoke action of this year."
M.COST_ENACT = "This uses your 1 enact action of this year. The law takes effect at once."
M.COST_REVOKE = "This uses your 1 revoke action of this year. The effects end at once."

-- Tones of a text: the widget maps a tone to a colour.
-- gain (green), loss (red), neutral (grey), gold, warn (amber), bad (red), muted, soft.

local function contains(list, value)
    for _, item in ipairs(list) do if item == value then return true end end
    return false
end

-- Is the effect good for the player? A lower buy-back price and a lower banditry order loss are gains (the mockup).
local FLIPPED = { buy_back_price = true }
local ALWAYS = { law_corpse_loot = "gain", law_disarm_homes = "neutral" }

function M.effect_tone(effect)
    if ALWAYS[effect.kind] then return ALWAYS[effect.kind] end
    if effect.kind == "law_banditry_gain" then return effect.value < 1 and "gain" or "loss" end
    local value = effect.value
    if FLIPPED[effect.kind] then value = -value end
    if value > 0 then return "gain" end
    if value < 0 then return "loss" end
    return "neutral"
end

-- The effect lines of a law: { text, tone }.
function M.effect_rows(law)
    local rows = {}
    for _, effect in ipairs(law.effects or {}) do
        rows[#rows + 1] = { text = lines.effect_line(effect, tree_module.EFFECT_KINDS), tone = M.effect_tone(effect) }
    end
    return rows
end

-- The tech tree way to unlock a law: its node and (for a path law) the path.
local function node_text(tree, law)
    local node = tree.by_id[law.requires[1]]
    local node_name = node and node.name or law.requires[1]
    if law.path == tree_module.COMMON then return "Tech tree: " .. node_name, node_name, nil end
    local path = tree.path_ids[law.path]
    local path_name = path and path.name or law.path
    return "Tech tree: " .. path_name .. ", " .. node_name, node_name, path_name
end

-- The "unlocked by" line: the tech tree node, or the contract text when only a contract unlocked the law.
function M.source_text(tree, law, by_node, by_contract, contract_text)
    if by_contract and not by_node then return "Unlocked by: " .. (contract_text or "Contract") end
    return "Unlocked by: " .. (node_text(tree, law))
end

-- How to unlock a locked law, in one line.
function M.locked_hint(tree, law, path)
    local _, node_name, path_name = node_text(tree, law)
    if path_name ~= nil and path ~= "none" and path ~= law.path then
        return string.format("Belongs to the %s path. A contract can still unlock it.", path_name)
    end
    if path_name ~= nil then return string.format("Unlock %s on the %s path, or win it from a contract.", node_name, path_name) end
    return string.format("Unlock %s in the tech tree, or win it from a contract.", node_name)
end

local function days_text(days)
    if days == nil then return "Enact and revoke actions refresh in spring." end
    return string.format("Enact and revoke actions refresh in spring, in %d days.", days)
end

local function card_of(model, law, in_force, unlocked, by_node, by_contract)
    local status, tone = "Locked", "muted"
    if in_force then status, tone = "In force", "gain" elseif unlocked then status, tone = "Unlocked", "gold" end
    local card = {
        id = law.id, name = law.name, status = status, status_tone = tone, in_force = in_force, unlocked = unlocked or in_force,
        source = M.source_text(model.tree, law, by_node, by_contract, model.source_of and model.source_of(law.id)),
        effects = M.effect_rows(law), action = nil, button = "Locked", enabled = false,
    }
    if in_force then
        card.action, card.button, card.enabled = "revoke", "Revoke", model.revoke_left > 0
        card.hint, card.hint_tone = M.USES_REVOKE, "soft"
        if not card.enabled then card.hint, card.hint_tone = M.NO_REVOKE, "bad" end
    elseif unlocked then
        card.action, card.button = "enact", "Enact"
        if model.enact_left <= 0 then card.hint, card.hint_tone = M.NO_ENACT, "bad"
        elseif model.full then card.hint, card.hint_tone = M.SLOTS_FULL, "bad"
        else card.enabled, card.hint, card.hint_tone = true, M.USES_ENACT, "soft" end
    else
        card.hint, card.hint_tone = M.locked_hint(model.tree, law, model.path), "muted"
    end
    return card
end

local function shown(filter, card)
    if filter == "unlocked" then return card.unlocked end
    if filter == "locked" then return not card.unlocked end
    return true
end

-- model: { tree, path, unlocked (node ids), granted (law ids), source_of(id), enacted (law ids), slots, max_total, enacts_per_year,
--          revokes_per_year, enact_left, revoke_left, days_to_refresh, filter }
function M.build(model)
    local in_force_count = #model.enacted
    model.full = in_force_count >= model.slots
    local all, unlocked_count = {}, 0
    for _, law in ipairs(model.tree.laws) do
        local in_force = contains(model.enacted, law.id)
        local by_contract = contains(model.granted, law.id)
        local by_node = true
        for _, required in ipairs(law.requires) do
            if not contains(model.unlocked, required) then by_node = false end
        end
        local unlocked = by_node or by_contract
        local card = card_of(model, law, in_force, unlocked, by_node, by_contract)
        if card.unlocked then unlocked_count = unlocked_count + 1 end
        all[#all + 1] = card
    end
    local cards = {}
    for _, card in ipairs(all) do
        if shown(model.filter, card) then cards[#cards + 1] = card end
    end
    return {
        filter = model.filter, cards = cards, total = #all, unlocked_count = unlocked_count,
        header = {
            slots_text = string.format("%d / %d", in_force_count, model.slots), slots_tone = model.full and "warn" or "gold",
            max_text = string.format("(max %d)", model.max_total),
            enact_text = string.format("%d / %d", math.max(0, model.enact_left), model.enacts_per_year), enact_tone = model.enact_left <= 0 and "bad" or "gold",
            revoke_text = string.format("%d / %d", math.max(0, model.revoke_left), model.revokes_per_year), revoke_tone = model.revoke_left <= 0 and "bad" or "gold",
            unlocked_text = string.format("%d of %d", unlocked_count, #all),
            refresh_text = days_text(model.days_to_refresh),
        },
        in_force = in_force_count, slots = model.slots, over_cap = in_force_count > model.slots,
    }
end

-- The confirm dialog of one action on one card. `kind` is "enact" or "revoke".
function M.dialog(kind, card)
    local enact = kind == "enact"
    return {
        kind = kind, id = card.id, title = enact and "Enact law" or "Revoke law",
        question = (enact and "Enact " or "Revoke ") .. card.name .. "?",
        effects = card.effects, cost = enact and M.COST_ENACT or M.COST_REVOKE, confirm = enact and "Enact" or "Revoke", cancel = "Cancel",
    }
end

return M
