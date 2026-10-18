-- Feature tech_tree (M12). Two exclusive paths (Oppression, Prosperity). The nodes come from data/tech_tree/tree.json.
-- The player picks one path, then unlocks nodes for free. One node slot opens for each settlement level (decisions 22 to 24).
-- Lua applies the effects through other features: bandits (Public Order, approval, buy-back price) and unit_balance (militia att and def).
-- A bad data file stops the load of this feature with a clear message.
local core = require("ManorCore")
local ModState = require("ModState")
local json = require("HarnessJson")
local bandits = require("features.bandits.init")
local unit_balance = require("features.unit_balance.init")
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

local last_applied = nil -- the last totals pushed to the other features, as text
local last_level = 0
local last_garrison = 0

local function unlocked_ids() return rules.parse_ids(state:get("tech_nodes")) end

local function slots() return rules.slots_for_level(last_level, config.slots_per_level) end

local function totals() return rules.totals(tree, unlocked_ids(), last_garrison) end

local function totals_text(values)
    return string.format("%s|%s|%s|%s|%s", values.order_bonus, values.approval_bonus, values.buy_back_multiplier,
        values.militia_attack_multiplier, values.militia_defence_multiplier)
end

-- Push the effects to the features that own the game values. Only a change is pushed.
local function apply_effects()
    local values = totals()
    local text = totals_text(values)
    if text == last_applied then return end
    last_applied = text
    bandits.set_modifiers({ order_bonus = values.order_bonus, approval_bonus = values.approval_bonus, buy_back_multiplier = values.buy_back_multiplier })
    unit_balance.set_militia(values.militia_attack_multiplier, values.militia_defence_multiplier)
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
        effects = rules.describe_totals(totals()), nodes = rows, paths = tree.paths,
    }
end

local function command_state()
    read_world()
    local unlocked = unlocked_ids()
    return {
        path = state:get("tech_path"), unlocked = unlocked, settlement_level = last_level, slots = slots(), free_slots = slots() - #unlocked,
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

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.tech_tree_state", command_state, {})
    commands.register("InvasionMod.tech_tree_choose_path", command_choose_path, { path = { type = "string", required = true } })
    commands.register("InvasionMod.tech_tree_unlock", command_unlock, { node = { type = "string", required = true } })
end

core.log.info(TAG, string.format("feature tech_tree loaded: %d nodes", #tree.nodes))
return { tree = tree, state = state, choose_path = choose_path, unlock = unlock, node_rows = node_rows, view = view }
