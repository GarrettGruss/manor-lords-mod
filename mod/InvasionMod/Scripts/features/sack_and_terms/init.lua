-- Feature sack_and_terms (M06). Iteration 01: a lost battle sacks the town and the game goes on.
-- The mod listens to raid_behavior. When a role raid begins to leave because it won (see rules.is_lost_battle),
-- the town loses a share of buildings, stock and families. The share grows with the difficulty.
local core = require("ManorCore")
local ModState = require("ModState")
local invasion = require("features.invasion.init")
local raid_behavior = require("features.raid_behavior.init")
local raid_world = require("features.raid_behavior.world")
local rules = require("features.sack_and_terms.rules")
local world = require("features.sack_and_terms.world")
local config = require("config").sack_and_terms
require("features.sack_and_terms.terms")
require("features.sack_and_terms.fallback")
local sack_config = config.sack

local TAG = "InvasionMod.sack_and_terms"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("sack_count", 0, "integer")         -- all sacks
state:register("sack_window_start", 0, "integer")  -- game day of the first sack in the window
state:register("sack_window_count", 0, "integer")  -- sacks in the window
state:register("sack_last_day", 0, "integer")

local fatal_enabled = sack_config.fatal.enabled -- a command changes it for one session
local history = {}                               -- results of the sacks of this session, for the state command

local function set_if_changed(key, value)
    if state:get(key) ~= value then state:set(key, value) end
end

---------------------------------------------------------------------------------------------
-- The sack
---------------------------------------------------------------------------------------------

-- Run one sack at `difficulty`. Returns the result table. Raises an error on a game problem (fail loudly).
local function run_sack(difficulty, reason, target)
    local today = raid_world.current_day()
    if today == nil then error("the game day is not available", 0) end
    local start, count, reached = rules.count_sack(state:get("sack_window_start"), state:get("sack_window_count"), today, sack_config)
    local fatal = reached and fatal_enabled
    local region = rules.sack_region(target, require("features.vassals.init").state:get("vassals_home_region"), world.player_region_names())
    local before = world.census(region)
    local plan = rules.plan(before, difficulty, sack_config, fatal)
    local taken = world.apply(plan, sack_config.method, region)
    local after = world.census(region)
    state:set("sack_count", state:get("sack_count") + 1)
    set_if_changed("sack_window_start", start)
    set_if_changed("sack_window_count", count)
    set_if_changed("sack_last_day", today)
    local result = {
        day = today, reason = reason, region = region, difficulty = difficulty, percent = plan.percent, window_count = count, limit_reached = reached,
        fatal = fatal, planned = { buildings = plan.buildings, families = plan.families }, taken = taken,
        before = { standing = before.buildings.standing, stock = before.stock.total, families = before.people.families, population = before.people.population },
        after = { standing = after.buildings.standing, stock = after.stock.total, families = after.people.families, population = after.people.population },
    }
    history[#history + 1] = result
    core.log.info(TAG, string.format(
        "SACK day=%d reason=%s difficulty=%d percent=%s window_count=%d limit_reached=%s fatal=%s buildings %d->%d stock %d->%d families %s->%s",
        today, reason, difficulty, tostring(plan.percent), count, tostring(reached), tostring(fatal), before.buildings.standing, after.buildings.standing,
        before.stock.total, after.stock.total, tostring(before.people.families), tostring(after.people.families)))
    core.show_banner("The town is sacked", string.format("%d buildings, %d families lost", taken.buildings_hit, taken.families_removed))
    return result
end

local function on_raid_leave(summary)
    if not rules.is_lost_battle(summary, sack_config) then
        return core.log.info(TAG, string.format("SACK none: raid %d leaves with reason %s (not a lost battle)", summary.id, tostring(summary.leave_reason)))
    end
    run_sack(invasion.state:get("difficulty"), summary.leave_reason, summary.target)
end

raid_behavior.watch_leave(on_raid_leave)

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local has_commands, commands = pcall(require, "HarnessCommands")

local function command_state()
    return {
        sack_count = state:get("sack_count"), window_start = state:get("sack_window_start"), window_count = state:get("sack_window_count"),
        last_day = state:get("sack_last_day"), fatal_enabled = fatal_enabled, history = history, limit = sack_config.limit, window_days = sack_config.window_days,
        share_percent = rules.share_percent(invasion.state:get("difficulty"), sack_config),
    }
end

if has_commands then
    commands.register("InvasionMod.sack_state", command_state, {})
    commands.register("InvasionMod.sack_now", function(args)
        return run_sack(args.difficulty or invasion.state:get("difficulty"), "command")
    end, { difficulty = { type = "integer", min = 1, max = 3 } })
    commands.register("InvasionMod.sack_set_fatal", function(args)
        fatal_enabled = args.enabled
        return command_state()
    end, { enabled = { type = "boolean", required = true } })
end

core.log.info(TAG, "feature sack_and_terms loaded")
return { state = state }
