-- Feature tech_tree (M12). Two exclusive paths (Oppression, Prosperity). The nodes come from data/tech_tree/tree.json.
-- The player picks one path, then unlocks nodes. Each unlock costs one pick: one pick at the start and one at each start of spring (change update-tech-tree-yearly-picks).
-- Three common techs (no path) open three common laws: Strip the Dead, Disarm the Peasantry, Curfew.
-- Lua applies the effects through other features: bandits (Public Order, approval, buy-back price) and unit_balance (militia att and def).
-- A bad data file stops the load of this feature with a clear message.
local core = require("ManorCore")
local ModState = require("ModState")
local json = require("HarnessJson")
local bandits = require("features.bandits.init")
local invasion = require("features.invasion.init")
local raid_behavior = require("features.raid_behavior.init")
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
local DISARM_IDS = require("config").bandits.rebellion_weapon_ids or config.disarm.weapon_ids -- the rebellion change owns the list

local tree = tree_module.load_file(world.data_path(config.tree_file), json.decode)

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("tech_path", rules.NO_PATH, "string")
state:register("tech_nodes", "", "string")
state:register("tech_laws", "", "string")
state:register("tech_picks_earned", -1, "integer") -- -1: the picks did not start yet
state:register("tech_spring_no", -1, "integer")    -- season counter of the last spring that gave a pick (or of the start)

local last_applied = nil -- the last totals pushed to the other features, as text
local last_level = 0
local last_garrison = 0

local function unlocked_ids() return rules.parse_ids(state:get("tech_nodes")) end

local function free_picks() return rules.free_picks(state:get("tech_picks_earned"), unlocked_ids()) end

local function enacted_ids() return rules.parse_ids(state:get("tech_laws")) end

local function totals() return rules.totals(tree, unlocked_ids(), last_garrison, enacted_ids()) end

local function totals_text(values)
    return string.format("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s", values.order_bonus, values.approval_bonus, values.buy_back_multiplier,
        values.militia_attack_multiplier, values.militia_defence_multiplier, values.manor_storage_bonus, values.retinue_bonus,
        values.tribute_share_multiplier, values.banditry_gain_multiplier, tostring(values.corpse_loot), tostring(values.disarm_homes))
end

-- Push the effects to the features that own the game values. Only a change is pushed.
local function apply_effects()
    local values = totals()
    local text = totals_text(values)
    if text == last_applied then return end
    last_applied = text
    bandits.set_modifiers({ order_bonus = values.order_bonus, approval_bonus = values.approval_bonus, buy_back_multiplier = values.buy_back_multiplier,
        banditry_gain_multiplier = values.banditry_gain_multiplier })
    raid_behavior.set_corpse_loot(values.corpse_loot)
    unit_balance.set_militia(values.militia_attack_multiplier, values.militia_defence_multiplier)
    manor_stronghold.set_modifiers({ storage_bonus = values.manor_storage_bonus, retinue_bonus = values.retinue_bonus })
    tribute.set_share_factor(values.tribute_share_multiplier)
    core.log.info(TAG, "TECH_TREE effects applied " .. text)
end

local function read_world()
    last_level = world.settlement_level() or last_level
    last_garrison = world.garrison_squads() or last_garrison
end

-- The start grant and the spring grant. The new numbers are saved before the log line, so a load cannot give a pick twice.
local function grant_picks()
    local earned, spring_no, why = rules.picks_step(state:get("tech_picks_earned"), state:get("tech_spring_no"), invasion.season_info(), config)
    if why == nil then return end
    state:set("tech_spring_no", spring_no)
    state:set("tech_picks_earned", earned)
    core.log.info(TAG, string.format("TECH_TREE picks %s earned=%d free=%d spring_no=%d", why, earned, free_picks(), spring_no))
end

-- Disarm the Peasantry: every `disarm.tick_days` game days the weapons of the homes go to the storehouse.
local last_disarm_day = nil

local function disarm_step()
    if not totals().disarm_homes then last_disarm_day = nil; return end
    local today = world.current_day()
    if today == nil or (last_disarm_day ~= nil and today - last_disarm_day < config.disarm.tick_days) then return end
    last_disarm_day = today
    local result, why = world.disarm_homes(DISARM_IDS)
    if result == nil then return core.log.warn(TAG, "TECH_TREE disarm skipped: " .. tostring(why)) end
    local count = 0
    for _, amount in pairs(result.moved) do count = count + amount end
    core.log.info(TAG, string.format("TECH_TREE disarm day=%d moved=%d", today, count))
    if result.missed > 0 then core.log.warn(TAG, string.format("TECH_TREE disarm_homes_missed=%d", result.missed)) end
end

local function poll()
    if not state.loaded then return end
    read_world()
    grant_picks()
    apply_effects()
    disarm_step()
end

-- Strip the Dead: each corpse looted at the pit costs mod order.
raid_behavior.watch_looted(function(bodies)
    bandits.adjust_order(-config.strip_the_dead.order_loss * bodies)
end)

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
    local reason = rules.unlock_refusal(tree, state:get("tech_path"), unlocked, rules.free_picks(state:get("tech_picks_earned"), unlocked), node_id)
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

-- The common techs with a status: unlocked, available or locked (plus the reason).
local function common_rows(unlocked)
    local rows = {}
    for _, node in ipairs(tree.common_nodes) do
        local status, reason = rules.node_status(tree, state:get("tech_path"), unlocked, free_picks(), node.id)
        rows[#rows + 1] = { id = node.id, name = node.name, status = status, reason = reason, unlocked = status == "unlocked" }
    end
    return rows
end

-- The laws of one path ("common" for the common laws) with a status: enacted, available or locked (plus the reason).
local function law_rows(path, unlocked, law_path)
    local enacted, rows = enacted_ids(), {}
    local in_force = {}
    for _, id in ipairs(enacted) do in_force[id] = true end
    for _, law in ipairs(tree.laws) do
        if law.path == (law_path or path) then
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
        row.status, row.reason = rules.node_status(tree, path, unlocked, free_picks(), row.id)
    end
    local path_name = tree.path_ids[path] and tree.path_ids[path].name or nil
    return {
        -- slots and free_slots keep the old window working: they now show the picks earned and the picks free.
        path = path, path_name = path_name, level = last_level, slots = math.max(0, state:get("tech_picks_earned")), free_slots = free_picks(),
        picks_earned = math.max(0, state:get("tech_picks_earned")), free_picks = free_picks(), common_nodes = common_rows(unlocked),
        effects = rules.describe_totals(totals()), nodes = rows, paths = tree.paths, laws = law_rows(path, unlocked), common_laws = law_rows(path, unlocked, tree_module.COMMON), max_laws = config.max_active_laws,
    }
end

local function command_state()
    read_world()
    local unlocked = unlocked_ids()
    return {
        path = state:get("tech_path"), unlocked = unlocked, laws = enacted_ids(), settlement_level = last_level,
        picks_earned = math.max(0, state:get("tech_picks_earned")), free_picks = free_picks(), spring_no = state:get("tech_spring_no"),
        garrison_squads = last_garrison, totals = totals(), nodes = node_rows(), common_nodes = common_rows(unlocked),
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

-- Test: add picks at once (a test scenario cannot wait for a spring). The picks are saved with the state.
local function command_grant_picks(args)
    state:set("tech_picks_earned", math.max(0, state:get("tech_picks_earned")) + args.count)
    return command_state()
end

-- Test: put goods into the first home, and read the goods of the homes and the store (Disarm the Peasantry).
local function command_fill_home(args)
    local ok, why = world.fill_home(args.good, args.amount)
    if not ok then return nil, why end
    return world.home_goods(args.good)
end

local function command_home_goods(args) return world.home_goods(args.good) end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.tech_tree_state", command_state, {})
    commands.register("InvasionMod.tech_tree_test_grant_picks", command_grant_picks, { count = { type = "integer", required = true, min = 1, max = 20 } })
    commands.register("InvasionMod.tech_tree_test_fill_home", command_fill_home,
        { good = { type = "integer", required = true, min = 1, max = 400 }, amount = { type = "integer", required = true, min = 1, max = 50 } })
    commands.register("InvasionMod.tech_tree_test_home_goods", command_home_goods, { good = { type = "integer", required = true, min = 1, max = 400 } })
    commands.register("InvasionMod.tech_tree_choose_path", command_choose_path, { path = { type = "string", required = true } })
    commands.register("InvasionMod.tech_tree_unlock", command_unlock, { node = { type = "string", required = true } })
    commands.register("InvasionMod.tech_tree_enact_law", command_enact_law, { law = { type = "string", required = true } })
    commands.register("InvasionMod.tech_tree_repeal_law", command_repeal_law, { law = { type = "string", required = true } })
    commands.register("InvasionMod.tech_tree_set_vassal_policy", command_set_vassal_policy,
        { slot = { type = "integer", required = true }, policy = { type = "string", required = true } })
end

core.log.info(TAG, string.format("feature tech_tree loaded: %d nodes, %d common techs", #tree.nodes, #tree.common_nodes))
return { tree = tree, state = state, choose_path = choose_path, unlock = unlock, enact_law = enact_law, repeal_law = repeal_law, node_rows = node_rows, view = view }
