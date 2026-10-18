-- Feature vassals (M07). Iteration 01: the game goal is Endless, so a claim never ends the game (spec 26).
-- The mod keeps a registry of vassal slots in ModState (pawn Tags). Each slot has a region, a lord name, a loyalty and a start day.
local core = require("ManorCore")
local ModState = require("ModState")
local rules = require("features.vassals.rules")
local world = require("features.vassals.world")
local config = require("config").vassals

local TAG = "InvasionMod.vassals"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("vassals_goal_writes", 0, "integer")
for slot = 1, config.max_vassals do
    state:register("vassal" .. slot .. "_region", rules.NO_REGION, "string")
    state:register("vassal" .. slot .. "_lord", rules.NO_REGION, "string")
    state:register("vassal" .. slot .. "_loyalty", config.loyalty_start, "integer")
    state:register("vassal" .. slot .. "_since_day", 0, "integer")
end

local last_goal = nil        -- the goal as read at the last poll
local goal_error = nil

local function set_if_changed(key, value)
    if state:get(key) ~= value then state:set(key, value) end
end

local function slot_key(slot, name) return "vassal" .. slot .. "_" .. name end

local function slot_regions()
    local regions = {}
    for slot = 1, config.max_vassals do regions[slot] = state:get(slot_key(slot, "region")) end
    return regions
end

---------------------------------------------------------------------------------------------
-- Goal = Endless
---------------------------------------------------------------------------------------------

-- Runs on every poll: a start, a load and a game reset all end with the goal written again.
local function ensure_goal()
    local setup, problem = world.setup_state()
    if setup == nil then goal_error = problem; return end
    goal_error = nil
    last_goal = setup.goals
    if not rules.goal_needs_write(setup.goals, config.goal) then return end
    local answer, why = world.set_goal(config.goal)
    if answer == nil then goal_error = why; return core.log.error(TAG, "VASSALS goal write failed: " .. tostring(why)) end
    state:set("vassals_goal_writes", state:get("vassals_goal_writes") + 1)
    last_goal = answer.after and answer.after.goals
    core.log.info(TAG, string.format("VASSALS goal written %s -> %s", tostring(setup.goals), tostring(last_goal)))
end

local function poll()
    if not state.loaded then return end
    ensure_goal()
end

require("scheduler").every(TAG, config.poll_ms, poll)

---------------------------------------------------------------------------------------------
-- Registry
---------------------------------------------------------------------------------------------

local function slot_row(slot)
    local region = state:get(slot_key(slot, "region"))
    if region == rules.NO_REGION then return nil end
    return { slot = slot, region = region, lord = state:get(slot_key(slot, "lord")),
        loyalty = state:get(slot_key(slot, "loyalty")), since_day = state:get(slot_key(slot, "since_day")) }
end

local function slot_rows()
    local rows = {}
    for slot = 1, config.max_vassals do rows[#rows + 1] = slot_row(slot) end
    return rows
end

local function register_vassal(region_name)
    local slot = rules.free_slot(slot_regions(), config.max_vassals)
    if slot == nil then return nil, "all " .. config.max_vassals .. " vassal slots are used" end
    state:set(slot_key(slot, "region"), region_name)
    state:set(slot_key(slot, "loyalty"), rules.clamp_loyalty(config.loyalty_start))
    state:set(slot_key(slot, "since_day"), world.current_day() or 0)
    core.log.info(TAG, string.format("VASSALS slot %d registered region=%s loyalty=%d", slot, region_name, config.loyalty_start))
    return slot
end

local function set_loyalty(slot, value)
    state:set(slot_key(slot, "loyalty"), rules.clamp_loyalty(value))
end

local function command_state()
    local setup = world.setup_state()
    return {
        day = world.current_day(), goal = last_goal, goal_error = goal_error, goal_writes = state:get("vassals_goal_writes"),
        victory_status = setup and setup.victory_status, count = rules.count_used(slot_regions(), config.max_vassals),
        vassals = slot_rows(),
    }
end

local function command_claim(args)
    if rules.slot_of_region(slot_regions(), config.max_vassals, args.region) then return nil, args.region .. " is already a vassal" end
    local row, problem = world.region_row(args.region)
    if row == nil then return nil, problem end
    if row.owner ~= nil then return nil, args.region .. " already has an owner: " .. tostring(row.owner) end
    local claimed, why = world.claim_for_player(args.region)
    if claimed == nil then return nil, why end
    local slot, reason = register_vassal(args.region)
    if slot == nil then return nil, reason end
    local result = command_state()
    result.claimed_slot = slot
    return result
end

local function command_set_loyalty(args)
    local row = slot_row(args.slot)
    if row == nil then return nil, "slot " .. args.slot .. " is empty" end
    set_loyalty(args.slot, args.value)
    return command_state()
end

local function command_set_goal(args)
    local answer, why = world.set_goal(args.goal)
    if answer == nil then return nil, why end
    return command_state()
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.vassals_state", command_state, {})
    commands.register("InvasionMod.vassals_claim", command_claim, { region = { type = "string", required = true } })
    commands.register("InvasionMod.vassals_set_loyalty", command_set_loyalty,
        { slot = { type = "integer", required = true, min = 1, max = config.max_vassals }, value = { type = "number", required = true, min = -1000, max = 1000 } })
    commands.register("InvasionMod.vassals_set_goal", command_set_goal, { goal = { type = "integer", required = true, min = 0, max = 3 } })
end

core.log.info(TAG, "feature vassals loaded")
return { state = state, register_vassal = register_vassal, set_loyalty = set_loyalty, slot_rows = slot_rows, slot_regions = slot_regions }
