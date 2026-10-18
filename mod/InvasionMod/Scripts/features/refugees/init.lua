-- Feature refugees (M09). Iteration 01: a lost vassal sends a wave of refugee families to the home region.
-- The families arrive through settleRegion (5 families a call, the homeless tent). The game lowers approval and feeds them.
-- Another feature calls send_wave(vassal_families) when a vassal is lost. The command refugees_vassal_lost is the test path.
local core = require("ManorCore")
local ModState = require("ModState")
local vassals = require("features.vassals.init")
local rules = require("features.refugees.rules")
local world = require("features.refugees.world")
local config = require("config").refugees

local TAG = "InvasionMod.refugees"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("refugee_active", false, "boolean")
state:register("refugee_start_day", 0, "integer")        -- day + 1 (a new game starts at day 0); 0 when no wave
state:register("refugee_base_homeless", 0, "integer")    -- homeless families before the wave
state:register("refugee_wave_families", 0, "integer")    -- families the wave added
state:register("refugee_waves", 0, "integer")
state:register("refugee_last_outcome", "none", "string")  -- housed or rebelled
state:register("refugee_housed", 0, "integer")
state:register("refugee_rebelled", 0, "integer")
state:register("refugee_bandit_families", 0, "integer")

math.randomseed(os.time() + 11)

local last_wave = nil -- the numbers of the last wave, for the state command
local timeout_days = config.timeout_days -- a test command changes it for one session

local function home_region()
    local home = vassals.state:get("vassals_home_region")
    if home == "none" then return nil end
    return home
end

local function announce(families)
    local shown, problem = core.show_banner("Refugees have arrived", string.format("%d families camp near the village. House them.", families))
    if not shown then core.log.warn(TAG, "REFUGEES banner failed: " .. tostring(problem)) end
end

-- Send a wave for a vassal of `vassal_families` families. `share` is 0 to 1; nil draws one. Returns the wave table or nil and a message.
local function send_wave(vassal_families, share)
    if state:get("refugee_active") then return nil, "a wave is already active" end
    local home = home_region()
    if home == nil then return nil, "the home region is not known yet" end
    share = share or rules.share_from_roll(math.random(), config.share_min, config.share_max)
    local wanted = rules.wave_families(vassal_families, share)
    local calls = rules.calls_for(wanted, config.families_per_call, config.max_calls)
    local before = world.numbers(home)
    if before == nil then return nil, "cannot read the home region " .. home end
    local done, place = world.send_settlers(home, calls)
    if done == nil then return nil, place end
    local after = world.numbers(home) or before
    state:set("refugee_base_homeless", before.homeless or 0)
    state:set("refugee_wave_families", (after.families or 0) - (before.families or 0))
    state:set("refugee_start_day", (world.current_day() or 0) + 1)
    state:set("refugee_waves", state:get("refugee_waves") + 1)
    state:set("refugee_active", true)
    last_wave = { share = share, wanted = wanted, calls = done, place = place, before = before, after = after }
    core.log.info(TAG, string.format("REFUGEES wave share=%.2f wanted=%d calls=%d at %s families %s -> %s homeless %s -> %s",
        share, wanted, done, place, tostring(before.families), tostring(after.families), tostring(before.homeless), tostring(after.homeless)))
    announce(state:get("refugee_wave_families"))
    return last_wave
end

---------------------------------------------------------------------------------------------
-- End of a wave (iteration 02): housed, or turned into bandits after the timeout
---------------------------------------------------------------------------------------------

local function finish(outcome)
    state:set("refugee_active", false)
    state:set("refugee_last_outcome", outcome)
    local key = outcome == "housed" and "refugee_housed" or "refugee_rebelled"
    state:set(key, state:get(key) + 1)
    core.log.info(TAG, "REFUGEES wave ended: " .. outcome)
end

-- The homeless families above the base are the unhoused refugees. They leave as bandits (the M04 homeless_rebel route).
local function rebel(unhoused)
    local count = math.min(unhoused, config.max_rebel_families)
    local answer, problem = require("features.bandits.world").rebel(count, config.families_per_squad)
    if answer == nil then
        core.log.error(TAG, "REFUGEES rebellion failed: " .. tostring(problem))
        return false
    end
    state:set("refugee_bandit_families", state:get("refugee_bandit_families") + (answer.families_removed or count))
    core.log.info(TAG, string.format("REFUGEES %d unhoused families became bandits (%d squads)", answer.families_removed or count, #answer.squads))
    core.show_banner("Refugees turned to banditry", string.format("%d families left their camp", answer.families_removed or count))
    return true
end

local function check_wave()
    local home = home_region()
    local numbers = home and world.numbers(home)
    if numbers == nil then return end
    local unhoused = (numbers.homeless or 0) - state:get("refugee_base_homeless")
    if unhoused <= 0 then return finish("housed") end
    local today = world.current_day()
    if today == nil then return end
    if rules.timed_out(state:get("refugee_start_day"), today, timeout_days) then
        if rebel(unhoused) then finish("rebelled") end
    end
end

local function poll()
    if not state.loaded or not state:get("refugee_active") then return end
    check_wave()
end

require("scheduler").every(TAG, config.poll_ms, poll)

local function command_state()
    local home = home_region()
    return { active = state:get("refugee_active"), waves = state:get("refugee_waves"), last_outcome = state:get("refugee_last_outcome"), housed = state:get("refugee_housed"), rebelled = state:get("refugee_rebelled"), bandit_families = state:get("refugee_bandit_families"), timeout_days = timeout_days, base_homeless = state:get("refugee_base_homeless"),
        wave_families = state:get("refugee_wave_families"), start_day = state:get("refugee_start_day"), day = world.current_day(),
        home = home, numbers = home and world.numbers(home), last_wave = last_wave }
end

local function command_vassal_lost(args)
    local families = vassals.region_families(vassals.slot_regions()[args.slot])
    if families == nil then return nil, "slot " .. args.slot .. " has no readable region" end
    local wave, problem = send_wave(families, args.share and args.share / 100)
    if wave == nil then return nil, problem end
    return command_state()
end

local function command_send_wave(args)
    local wave, problem = send_wave(args.families, args.share and args.share / 100)
    if wave == nil then return nil, problem end
    return command_state()
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    local share = { type = "integer", required = false, min = 1, max = 100 }
    commands.register("InvasionMod.refugees_state", command_state, {})
    commands.register("InvasionMod.refugees_set_timeout", function(args)
        timeout_days = args.days
        return command_state()
    end, { days = { type = "integer", required = true, min = 1, max = 120 } })
    commands.register("InvasionMod.refugees_vassal_lost", command_vassal_lost,
        { slot = { type = "integer", required = true, min = 1, max = 3 }, share = share })
    commands.register("InvasionMod.refugees_send_wave", command_send_wave,
        { families = { type = "integer", required = true, min = 1, max = 100 }, share = share })
end

-- A lost vassal sends refugees (M00: a wave of 30 to 60 percent of its families).
vassals.on_lost(function(event)
    local wave, problem = send_wave(event.families)
    if wave == nil then core.log.warn(TAG, "REFUGEES no wave for the lost vassal " .. event.region .. ": " .. tostring(problem)) end
end)

core.log.info(TAG, "feature refugees loaded")
return { state = state, send_wave = send_wave }
