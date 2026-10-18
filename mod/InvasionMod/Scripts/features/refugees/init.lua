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

math.randomseed(os.time() + 11)

local last_wave = nil -- the numbers of the last wave, for the state command

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

local function command_state()
    local home = home_region()
    return { active = state:get("refugee_active"), waves = state:get("refugee_waves"), base_homeless = state:get("refugee_base_homeless"),
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
    commands.register("InvasionMod.refugees_vassal_lost", command_vassal_lost,
        { slot = { type = "integer", required = true, min = 1, max = 3 }, share = share })
    commands.register("InvasionMod.refugees_send_wave", command_send_wave,
        { families = { type = "integer", required = true, min = 1, max = 100 }, share = share })
end

core.log.info(TAG, "feature refugees loaded")
return { state = state, send_wave = send_wave }
