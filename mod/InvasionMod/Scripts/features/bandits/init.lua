-- Feature bandits (M04, iteration 01): low approval lowers Public Order, low Public Order turns families into bandits.
-- The mod writes Region.publicOrder = natural - debuff. The game rewrites the value now and then (it falls back to its own value),
-- and the mod takes the new value as the natural one. The conversion uses the proven homeless_rebel route.
-- The tick runs once per season change (iteration 02). The last season is saved in ModState, so a load does not repeat a season.
local core = require("ManorCore")
local ModState = require("ModState")
local invasion = require("features.invasion.init")
local rules = require("features.bandits.rules")
local world = require("features.bandits.world")
local config = require("config").bandits

local TAG = "InvasionMod.bandits"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("bandits_converted_families", 0, "integer")
state:register("bandits_last_tick_day", 0, "integer")
state:register("bandits_last_season", -1, "integer")
state:register("bandits_rolls", 0, "integer")
state:register("bandits_natural_order", -1, "integer")
state:register("bandits_written_order", -1, "integer")

math.randomseed(os.time() + 7)

local natural_order = nil -- the game's own value, as far as the mod knows
local written_order = nil -- the last value the mod wrote
local debuff = 0
local last_ticks = {}     -- the tick results, for the state command
local overwrites = 0      -- how often the game replaced the mod's value

local function difficulty()
    return invasion.state:get("difficulty")
end

-- Every set writes the Tags of the player pawn, so write only a change.
local function set_if_changed(key, value)
    if state:get(key) ~= value then state:set(key, value) end
end

-- After a load the saved Public Order can be the mod's debuffed value. The saved pair tells the mod which one it is.
local function restore_memory()
    local natural, written = state:get("bandits_natural_order"), state:get("bandits_written_order")
    if natural >= 0 and written >= 0 then natural_order, written_order = natural, written end
end

---------------------------------------------------------------------------------------------
-- Public Order debuff
---------------------------------------------------------------------------------------------

local function apply_debuff()
    local region = world.region()
    if region == nil then return nil end
    local values = world.read_values(region)
    if values == nil then return nil end
    local natural = rules.natural_order(values.order, written_order, natural_order)
    if written_order ~= nil and values.order ~= written_order then
        overwrites = overwrites + 1
        core.log.info(TAG, string.format("BANDITS game rewrote order mod_value=%d game_value=%d", written_order, values.order))
    end
    natural_order = natural
    debuff = rules.debuff(values.approval, difficulty())
    local target = rules.debuffed_order(natural, values.approval, difficulty())
    if values.order ~= target then
        local ok, why = world.write_order(region, target)
        if not ok then return core.log.error(TAG, "order write failed: " .. why) end
    end
    written_order = target
    if state.loaded then
        set_if_changed("bandits_natural_order", natural)
        set_if_changed("bandits_written_order", target)
    end
    return { region = region, order = target, approval = values.approval }
end

---------------------------------------------------------------------------------------------
-- Conversion
---------------------------------------------------------------------------------------------

local function convert(region, today, order, roll)
    state:set("bandits_rolls", state:get("bandits_rolls") + 1)
    local chance = rules.chance_for(order, config.bands)
    local record = { day = today, order = order, chance = chance, roll = roll, converted = 0 }
    last_ticks[#last_ticks + 1] = record
    if not rules.should_convert(order, config.bands, roll) then
        return core.log.info(TAG, string.format("BANDITS tick day=%d order=%d chance=%.2f roll=%.2f no conversion", today, order, chance, roll))
    end
    local families = world.families(region) or 0
    local count = math.min(config.families_per_conversion, families - config.min_families_left)
    if count < 1 then
        return core.log.info(TAG, string.format("BANDITS tick day=%d order=%d too few families (%d) to convert", today, order, families))
    end
    local answer, problem = world.rebel(count, config.families_per_squad)
    if answer == nil then return core.log.error(TAG, "BANDITS conversion failed: " .. tostring(problem)) end
    record.converted = answer.families_removed or count
    state:set("bandits_converted_families", state:get("bandits_converted_families") + record.converted)
    core.log.info(TAG, string.format("BANDITS converted day=%d order=%d chance=%.2f roll=%.2f families=%d squads=%d bandit_units=%d",
        today, order, chance, roll, record.converted, #answer.squads, answer.bandit_units_spawned or -1))
    core.show_banner("Families have turned to banditry", string.format("%d families left their homes", record.converted))
end

local function run_tick(today, roll)
    local applied = apply_debuff()
    if applied == nil then return core.log.warn(TAG, "BANDITS tick skipped: no region values") end
    convert(applied.region, today, applied.order, roll)
    state:set("bandits_last_tick_day", today)
end

-- The saved season is set before the tick, so an error in the tick cannot make it run twice.
local function check_season(today)
    local season = world.current_season()
    if season == nil then return end
    local last = state:get("bandits_last_season")
    if not rules.season_changed(season, last) then
        if last < 0 then state:set("bandits_last_season", season) end
        return
    end
    state:set("bandits_last_season", season)
    core.log.info(TAG, string.format("BANDITS season change %d to %d on day %d", last, season, today))
    run_tick(today, math.random())
end

local function poll()
    if not state.loaded then return end
    if natural_order == nil and written_order == nil then restore_memory() end
    apply_debuff()
    local today = world.current_day()
    if today == nil then return end
    check_season(today)
end

require("scheduler").every(TAG, config.poll_ms, poll)

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local has_commands, commands = pcall(require, "HarnessCommands")

local function command_state()
    local region = world.region()
    local values = region and world.read_values(region)
    return {
        day = world.current_day(), difficulty = difficulty(), order = values and values.order, approval = values and values.approval,
        natural_order = natural_order, written_order = written_order, debuff = debuff, overwrites = overwrites,
        families = region and world.families(region), converted_families = state:get("bandits_converted_families"),
        season = world.current_season(), last_season = state:get("bandits_last_season"), rolls = state:get("bandits_rolls"), last_tick_day = state:get("bandits_last_tick_day"), ticks = last_ticks,
    }
end

local function command_set_approval(args)
    local region, problem = world.region()
    if region == nil then return nil, problem end
    local ok, why = world.write_approval(region, args.value)
    if not ok then return nil, why end
    apply_debuff()
    return command_state()
end

local function command_tick_now(args)
    local today = world.current_day()
    if today == nil then return nil, "the game day is not available" end
    run_tick(today, args.roll or math.random())
    return command_state()
end

if has_commands then
    commands.register("InvasionMod.bandits_state", command_state, {})
    commands.register("InvasionMod.bandits_set_approval", command_set_approval, { value = { type = "integer", required = true, min = 0, max = 100 } })
    commands.register("InvasionMod.bandits_tick_now", command_tick_now, { roll = { type = "number", required = false, min = 0, max = 1 } })
end

core.log.info(TAG, "feature bandits loaded")
return { state = state }
