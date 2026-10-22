-- Feature tribute (M08). Iteration 01: at each season change each handed-over vassal pays goods into the player stores.
-- No goods move between regions (M00 decision 21): the mod adds goods to a home store, as a share of a production formula.
local core = require("ManorCore")
local ModState = require("ModState")
local vassals = require("features.vassals.init")
local raid_world = require("features.raid_behavior.world")
local raid_behavior = require("features.raid_behavior.init")
local vassal_rules = require("features.vassals.rules")
local rules = require("features.tribute.rules")
local config = require("config").tribute

local TAG = "InvasionMod.tribute"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("tribute_last_season", -1, "integer")
state:register("tribute_ticks", 0, "integer")
state:register("tribute_paid_total", 0, "integer")

local share_factor = 1     -- set by the tech tree laws (M12.04)
local finite_paid_session = {} -- good name -> units of finite goods (iron, salt) paid in this session (M10.02)
local history = {}          -- results of the ticks of this session
local failed_deposits = 0

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if core.isValid(found) then return found end
    return nil
end

local function read_number(path_fn)
    local ok, value = pcall(path_fn)
    if ok and type(value) == "number" then return math.floor(value) end
    return nil
end

local function current_season()
    local e = engine()
    return e and read_number(function() return e.TemporalComponent.Season end)
end

local function current_day()
    local e = engine()
    return e and read_number(function() return e.TemporalComponent.daysTotal end)
end

-- Put `amount` of one good into the first store that takes all of it.
local function pay_good(good, amount)
    if amount <= 0 then return true end
    for _, store in ipairs(raid_world.stores() or {}) do
        local ok, why = raid_world.deposit(store, good, amount)
        if ok then return true end
        core.log.warn(TAG, string.format("TRIBUTE deposit of %d of good %d refused: %s", amount, good, tostring(why)))
    end
    failed_deposits = failed_deposits + 1
    return false
end

local function pay_vassal(row)
    local families = vassals.region_families(row.region) or 0
    local production = rules.production(families, config.units_per_family)
    local factor = (require("config").vassals.policies[row.policy] or { tribute = 1.0 }).tribute -- vassal policy (M07.03)
    local share = config.share * factor * share_factor
    local amount = rules.amount(production, share)
    local parts = rules.split(amount, #config.goods)
    local paid = 0
    for index, good in ipairs(config.goods) do
        if pay_good(good.id, parts[index]) then paid = paid + parts[index] end
    end
    local finite = {}
    for _, good in ipairs(config.finite_goods or {}) do
        local units = rules.amount(rules.production(families, good.units_per_family), share)
        if pay_good(good.id, units) then finite[good.name] = units else finite[good.name] = 0 end
        finite_paid_session[good.name] = (finite_paid_session[good.name] or 0) + finite[good.name]
    end
    return { slot = row.slot, region = row.region, families = families, production = production,
        share = share, policy = row.policy, amount = amount, paid = paid, finite = finite }
end

local function run_tick()
    local day = current_day()
    local result = { day = day, payments = {} }
    for _, row in ipairs(vassals.slot_rows()) do
        if row and row.lord ~= "none" and not row.rebuilding then result.payments[#result.payments + 1] = pay_vassal(row) end
    end
    local total = 0
    for _, payment in ipairs(result.payments) do total = total + payment.paid end
    result.total = total
    state:set("tribute_ticks", state:get("tribute_ticks") + 1)
    state:set("tribute_paid_total", state:get("tribute_paid_total") + total)
    history[#history + 1] = result
    core.log.info(TAG, string.format("TRIBUTE tick day=%s vassals=%d total=%d", tostring(day), #result.payments, total))
    if total > 0 then core.show_banner("Tribute has arrived", string.format("Your vassals sent %d goods", total)) end
    return result
end

---------------------------------------------------------------------------------------------
-- Vassal targets and siege (M02 iteration 07)
---------------------------------------------------------------------------------------------

require("features.invasion.init").set_vassal_provider(vassals.target_regions)

local siege_resolved = {}   -- raid id -> "taken" or "failed"

local function vassal_slot(region)
    return vassal_rules.slot_of_region(vassals.slot_regions(), require("config").vassals.max_vassals, region)
end

local function resolve_siege(summary)
    local slot = summary.target and vassal_slot(summary.target)
    if slot == nil or siege_resolved[tostring(summary.id)] then return end
    local result = rules.siege_result(summary, raid_world.current_day(), config.siege)
    if result == nil then return end
    siege_resolved[tostring(summary.id)] = result
    core.log.info(TAG, string.format("TRIBUTE siege raid=%d region=%s slot=%d result=%s", summary.id, summary.target, slot, result))
    if result == "taken" then
        local started, why = vassals.start_sack(slot, "siege")
        if started == nil then core.log.error(TAG, "TRIBUTE sack did not start: " .. tostring(why)) end
    end
end

local function siege_poll()
    for _, summary in ipairs(raid_behavior.active_raids()) do resolve_siege(summary) end
end

require("scheduler").every(TAG .. ".siege", config.siege.poll_ms, siege_poll)

-- The saved season is set before the tick, so an error in the tick cannot make it run twice.
local function poll()
    if not state.loaded then return end
    local season = current_season()
    if season == nil then return end
    local last = state:get("tribute_last_season")
    if last < 0 then return state:set("tribute_last_season", season) end
    if not rules.season_changed(season, last) then return end
    state:set("tribute_last_season", season)
    core.log.info(TAG, string.format("TRIBUTE season change %d to %d", last, season))
    run_tick()
end

require("scheduler").every(TAG, config.poll_ms, poll)

local function stock()
    local by_good = {}
    for _, store in ipairs(raid_world.stores() or {}) do
        for good, amount in pairs(store.by_good) do by_good[tostring(good)] = (by_good[tostring(good)] or 0) + amount end
    end
    return by_good
end

local function command_state()
    return { day = current_day(), season = current_season(), last_season = state:get("tribute_last_season"),
        ticks = state:get("tribute_ticks"), paid_total = state:get("tribute_paid_total"), failed_deposits = failed_deposits,
        history = history, stock = stock(), finite_paid = finite_paid_session,
        siege = siege_resolved }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.tribute_state", command_state, {})
    commands.register("InvasionMod.tribute_tick_now", function()
        run_tick()
        return command_state()
    end, {})
end

core.log.info(TAG, "feature tribute loaded")
return { state = state, run_tick = run_tick, set_share_factor = function(value) share_factor = value end }
