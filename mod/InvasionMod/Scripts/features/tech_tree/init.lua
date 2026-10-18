-- Feature tech_tree (M12). Two exclusive paths (Oppression, Prosperity). The nodes come from data/tech_tree/tree.json.
-- The player picks one path, then unlocks nodes for free. One node slot opens for each settlement level (decisions 22 to 24).
-- Lua applies the effects through other features: bandits (Public Order, approval, buy-back price) and unit_balance (militia att and def).
-- A bad data file stops the load of this feature with a clear message.
local core = require("ManorCore")
local ModState = require("ModState")
local json = require("HarnessJson")
local bandits = require("features.bandits.init")
local unit_balance = require("features.unit_balance.init")
local manor_stronghold = require("features.manor_stronghold.init")
local vassals = require("features.vassals.init")
local tribute = require("features.tribute.init")
local tree_module = require("features.tech_tree.tree")
local rules = require("features.tech_tree.rules")
local world = require("features.tech_tree.world")
local config = require("config").tech_tree

local TAG = "InvasionMod.tech_tree"
local STATE_VERSION = 1

local tree = tree_module.load_file(world.data_path(config.tree_file), json.decode)

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("tech_path", rules.NO_PATH, "string")
state:register("tech_nodes", "", "string")
state:register("tech_laws", "", "string")

local last_applied = nil -- the last totals pushed to the other features, as text
local last_level = 0
local last_garrison = 0

local function unlocked_ids() return rules.parse_ids(state:get("tech_nodes")) end

local function slots() return rules.slots_for_level(last_level, config.slots_per_level) end

local function enacted_ids() return rules.parse_ids(state:get("tech_laws")) end

local function totals() return rules.totals(tree, unlocked_ids(), last_garrison, enacted_ids()) end

local function totals_text(values)
    return string.format("%s|%s|%s|%s|%s|%s|%s|%s|%s", values.order_bonus, values.approval_bonus, values.buy_back_multiplier,
        values.militia_attack_multiplier, values.militia_defence_multiplier, values.manor_storage_bonus, values.retinue_bonus,
        values.tribute_share_multiplier, values.vassal_loyalty_bonus)
end

-- Push the effects to the features that own the game values. Only a change is pushed.
local function apply_effects()
    local values = totals()
    local text = totals_text(values)
    if text == last_applied then return end
    last_applied = text
    bandits.set_modifiers({ order_bonus = values.order_bonus, approval_bonus = values.approval_bonus, buy_back_multiplier = values.buy_back_multiplier })
    unit_balance.set_militia(values.militia_attack_multiplier, values.militia_defence_multiplier)
    manor_stronghold.set_modifiers({ storage_bonus = values.manor_storage_bonus, retinue_bonus = values.retinue_bonus })
    tribute.set_share_factor(values.tribute_share_multiplier)
    vassals.set_loyalty_bonus(values.vassal_loyalty_bonus)
    core.log.info(TAG, "TECH_TREE effects applied " .. text)
end

local function read_world()
    last_level = world.settlement_level() or last_level
    last_garrison = world.garrison_squads() or last_garrison
end

local function poll()
    if not state.loaded then return end
    read_world()
    apply_effects()
end

require("scheduler").every(TAG, config.poll_ms, poll)

---------------------------------------------------------------------------------------------
-- Choices
---------------------------------------------------------------------------------------------

local function choose_path(path_id)
    local reason = rules.path_refusal(tree, state:get("tech_path"), path_id)
    if reason ~= nil then return nil, reason end
    state:set("tech_path", path_id)
    core.log.info(TAG, "TECH_TREE path chosen " .. path_id)
    return true
end

local function unlock(node_id)
    read_world()
    local unlocked = unlocked_ids()
    local reason = rules.unlock_refusal(tree, state:get("tech_path"), unlocked, slots(), node_id)
    if reason ~= nil then return nil, reason end
    unlocked[#unlocked + 1] = node_id
    state:set("tech_nodes", rules.join_ids(unlocked))
    apply_effects()
    core.log.info(TAG, "TECH_TREE node unlocked " .. node_id)
    return true
end

---------------------------------------------------------------------------------------------
-- Laws and vassal policies (M12.04). Mod-owned; the game policy system is not used.
---------------------------------------------------------------------------------------------

local function enact_law(law_id)
    local reason = rules.enact_refusal(tree, state:get("tech_path"), unlocked_ids(), enacted_ids(), config.max_active_laws, law_id)
    if reason ~= nil then return nil, reason end
    local enacted = enacted_ids()
    enacted[#enacted + 1] = law_id
    state:set("tech_laws", rules.join_ids(enacted))
    apply_effects()
    core.log.info(TAG, "TECH_TREE law enacted " .. law_id)
    return true
end

local function repeal_law(law_id)
    local kept, found = {}, false
    for _, id in ipairs(enacted_ids()) do
        if id == law_id then found = true else kept[#kept + 1] = id end
    end
    if not found then return nil, "law '" .. tostring(law_id) .. "' is not in force" end
    state:set("tech_laws", rules.join_ids(kept))
    apply_effects()
    core.log.info(TAG, "TECH_TREE law repealed " .. law_id)
    return true
end

local function set_vassal_policy(slot, policy)
    local reason = rules.vassal_policy_refusal(tree, state:get("tech_path"), unlocked_ids(), policy)
    if reason ~= nil then return nil, reason end
    return vassals.set_policy(slot, policy)
end

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local function node_rows()
    local unlocked, rows = {}, {}
    for _, id in ipairs(unlocked_ids()) do unlocked[id] = true end
    for _, node in ipairs(tree.nodes) do
        rows[#rows + 1] = { id = node.id, path = node.path, name = node.name, requires = node.requires, unlocked = unlocked[node.id] == true,
            layout = node.layout }
    end
    return rows
end

-- The laws of the chosen path with a status: enacted, available or locked (plus the reason).
local function law_rows(path, unlocked)
    local enacted, rows = enacted_ids(), {}
    local in_force = {}
    for _, id in ipairs(enacted) do in_force[id] = true end
    for _, law in ipairs(tree.laws) do
        if law.path == path then
            local reason = rules.enact_refusal(tree, path, unlocked, enacted, config.max_active_laws, law.id)
            local status = in_force[law.id] and "enacted" or (reason == nil and "available" or "locked")
            rows[#rows + 1] = { id = law.id, name = law.name, status = status, reason = reason }
        end
    end
    return rows
end

-- Everything the menu shows, in one table. Status per node: unlocked, available, locked or other_path.
local function view()
    read_world()
    local unlocked, path = unlocked_ids(), state:get("tech_path")
    local rows = node_rows()
    for _, row in ipairs(rows) do
        row.status, row.reason = rules.node_status(tree, path, unlocked, slots(), row.id)
    end
    local path_name = tree.path_ids[path] and tree.path_ids[path].name or nil
    return {
        path = path, path_name = path_name, level = last_level, slots = slots(), free_slots = slots() - #unlocked,
        effects = rules.describe_totals(totals()), nodes = rows, paths = tree.paths, laws = law_rows(path, unlocked), max_laws = config.max_active_laws,
    }
end

local function command_state()
    read_world()
    local unlocked = unlocked_ids()
    return {
        path = state:get("tech_path"), unlocked = unlocked, laws = enacted_ids(), settlement_level = last_level, slots = slots(), free_slots = slots() - #unlocked,
        garrison_squads = last_garrison, totals = totals(), nodes = node_rows(),
        militia = unit_balance.militia_summary(),
    }
end

local function command_choose_path(args)
    local ok, why = choose_path(args.path)
    if not ok then return nil, why end
    apply_effects()
    return command_state()
end

local function command_unlock(args)
    local ok, why = unlock(args.node)
    if not ok then return nil, why end
    return command_state()
end

local function command_enact_law(args)
    local ok, why = enact_law(args.law)
    if not ok then return nil, why end
    return command_state()
end

local function command_repeal_law(args)
    local ok, why = repeal_law(args.law)
    if not ok then return nil, why end
    return command_state()
end

local function command_set_vassal_policy(args)
    local ok, why = set_vassal_policy(args.slot, args.policy)
    if not ok then return nil, why end
    return command_state()
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.tech_tree_state", command_state, {})
    commands.register("InvasionMod.tech_tree_choose_path", command_choose_path, { path = { type = "string", required = true } })
    commands.register("InvasionMod.tech_tree_unlock", command_unlock, { node = { type = "string", required = true } })
    commands.register("InvasionMod.tech_tree_enact_law", command_enact_law, { law = { type = "string", required = true } })
    commands.register("InvasionMod.tech_tree_repeal_law", command_repeal_law, { law = { type = "string", required = true } })
    commands.register("InvasionMod.tech_tree_set_vassal_policy", command_set_vassal_policy,
        { slot = { type = "integer", required = true }, policy = { type = "string", required = true } })
end

core.log.info(TAG, string.format("feature tech_tree loaded: %d nodes", #tree.nodes))
return { tree = tree, state = state, choose_path = choose_path, unlock = unlock, enact_law = enact_law, repeal_law = repeal_law, node_rows = node_rows, view = view }
