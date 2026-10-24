-- Feature bandits: the mod keeps its own public order (mod order) and applies its own rules.
-- Every tick_days game days: order = order + manor term - homeless term. Order under the threshold starts a timer.
-- When the timer expires, villagers leave to become bandits and the order rises. The mod writes Region.publicOrder = mod order.
-- State (mod order, last tick day, timer start) is in ModState, so a load goes on where the save was.
local core = require("ManorCore")
local ModState = require("ModState")
local rules = require("features.bandits.rules")
local world = require("features.bandits.world")
local config = require("config").bandits

local TAG = "InvasionMod.bandits"
local STATE_VERSION = 2

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("bandits_converted_families", 0, "integer")
state:register("bandits_outstanding_families", 0, "integer") -- families that turned to bandits and have not come back
state:register("bandits_returned_families", 0, "integer")
state:register("bandits_mod_order", config.start_order, "integer")
state:register("bandits_last_tick_day", -1, "integer")
state:register("bandits_timer_start", -1, "integer")
state:register("bandits_warned", 0, "integer") -- 1 when the 30 day warning showed for this timer
state:register("bandits_ticks", 0, "integer")
state:register("bandits_leaves", 0, "integer")

local last_tick = nil     -- the last tick record, for the state command and the telemetry
local last_leave = nil    -- the last leave record
local overwrites = 0      -- how often the game replaced the mod's value
local written = nil       -- the last value the mod wrote
local pending = nil       -- a sent buy-back that is not finished
local buy_backs = {}      -- the results, for the state command
-- Set by the tech tree: order_bonus is added to the manor term of each tick. buy_back_multiplier is a price factor.
local modifiers = { order_bonus = 0, buy_back_multiplier = 1 }

-- Every set writes the Tags of the player pawn, so write only a change.
local function set_if_changed(key, value)
    if state:get(key) ~= value then state:set(key, value) end
end

local function mod_order() return state:get("bandits_mod_order") end

---------------------------------------------------------------------------------------------
-- Public order
---------------------------------------------------------------------------------------------

-- Overwrite the game value with the mod order. The game rewrites it now and then, so this runs at every poll.
local function write_order()
    local region = world.region()
    if region == nil then return nil end
    local values = world.read_values(region)
    if values == nil then return nil end
    local target = mod_order()
    if values.order ~= target then
        if written ~= nil and values.order ~= written then
            overwrites = overwrites + 1
            core.log.info(TAG, string.format("BANDITS game rewrote order mod_value=%d game_value=%d", target, values.order))
        end
        local ok, why = world.write_order(region, target)
        if not ok then return core.log.error(TAG, "order write failed: " .. tostring(why)) end
    end
    written = target
    return region
end

local function set_mod_order(value)
    set_if_changed("bandits_mod_order", rules.clamp_order(value))
    write_order()
end

local function run_tick(today)
    local region = world.region()
    if region == nil then return core.log.warn(TAG, "BANDITS tick skipped: no region") end
    local record = rules.tick_order(mod_order(), world.homeless(region) or 0, modifiers.order_bonus, config)
    record.day = today
    last_tick = record
    state:set("bandits_last_tick_day", today)
    state:set("bandits_ticks", state:get("bandits_ticks") + 1)
    set_mod_order(record.order_after)
    core.log.info(TAG, string.format("BANDITS tick day=%d order_before=%d manor_term=%d homeless=%d homeless_term=%d order_after=%d",
        today, record.order_before, record.manor_term, record.homeless_count, record.homeless_term, record.order_after))
end

---------------------------------------------------------------------------------------------
-- Banditry timer and leave
---------------------------------------------------------------------------------------------

local function start_timer(today)
    state:set("bandits_timer_start", today)
    state:set("bandits_warned", 0)
    core.log.info(TAG, string.format("BANDITS timer started day=%d order=%d leave_in=%d days", today, mod_order(), config.timer_days))
    core.show_banner("Unrest is growing", string.format("Villagers will leave in %d days unless order rises", config.timer_days))
end

local function stop_timer(today)
    state:set("bandits_timer_start", -1)
    state:set("bandits_warned", 0)
    core.log.info(TAG, string.format("BANDITS timer reset day=%d order=%d", today, mod_order()))
end

-- The villagers leave. When no bandit pawn exists, they leave the map and the mod logs that no bandits spawned.
local function leave(today, count)
    local region = world.region()
    local families = region and world.families(region) or 0
    local wanted = count or rules.leavers_for(families, config)
    local result = { removed = 0, squads = 0, bandit_units = 0, spawned = false }
    if region ~= nil and wanted > 0 then
        local answer, problem = world.leave(region, wanted, config.families_per_squad)
        if answer == nil then core.log.error(TAG, "BANDITS leave failed: " .. tostring(problem)) else result = answer end
    end
    last_leave = { day = today, wanted = wanted, removed = result.removed, spawned = result.spawned, bandit_units = result.bandit_units }
    state:set("bandits_leaves", state:get("bandits_leaves") + 1)
    state:set("bandits_converted_families", state:get("bandits_converted_families") + result.removed)
    state:set("bandits_outstanding_families", state:get("bandits_outstanding_families") + result.removed)
    core.log.info(TAG, string.format("BANDITS leave day=%d wanted=%d families_left=%d bandits_spawned=%s squads=%d bandit_units=%d",
        today, wanted, result.removed, tostring(result.spawned), result.squads, result.bandit_units))
    if not result.spawned then core.log.info(TAG, "BANDITS no bandit pawn or spawn failed: no bandits spawned") end
    set_mod_order(rules.order_after_leave(mod_order(), config))
    core.show_banner("Families have turned to banditry", string.format("%d families left their homes", result.removed))
    return result
end

local function check_timer(today)
    local step = rules.timer_step(mod_order(), state:get("bandits_timer_start"), today, config)
    if step.action == "start" then return start_timer(today) end
    if step.action == "reset" then return stop_timer(today) end
    if step.action == "wait" and step.warn and state:get("bandits_warned") == 0 then
        state:set("bandits_warned", 1)
        core.log.info(TAG, string.format("BANDITS warning day=%d days_left=%d", today, step.days_left))
        return core.show_banner("Villagers are about to leave", string.format("They leave in %d days unless order rises", step.days_left))
    end
    if step.action == "leave" then
        state:set("bandits_timer_start", -1)
        leave(today)
        if rules.timer_step(mod_order(), -1, today, config).action == "start" then start_timer(today) end
    end
end

local function check_tick(today)
    local last = state:get("bandits_last_tick_day")
    if last < 0 then return state:set("bandits_last_tick_day", today) end -- a new game: the first tick is tick_days later
    if rules.tick_due(today, last, config.tick_days) then run_tick(today) end
end

---------------------------------------------------------------------------------------------
-- Buy-back (iteration 03): the player pays silver and the families come back through the native negotiation letter
---------------------------------------------------------------------------------------------

-- The price config with the tech tree factor (Iron Hand 1.25, Amnesty 0.5).
local function price_config()
    local cfg = {}
    for key, value in pairs(config.buy_back) do cfg[key] = value end
    cfg.price_multiplier = config.buy_back.price_multiplier * modifiers.buy_back_multiplier
    return cfg
end

local function buy_back_facts(region)
    return {
        outstanding = state:get("bandits_outstanding_families"), bandit_units = world.bandit_units() or 0,
        free_slots = world.free_slots(region) or 0, silver = world.silver() or 0,
    }
end

local function refuse(reason, facts)
    core.log.info(TAG, "BANDITS buy-back refused: " .. reason)
    return { accepted = false, reason = reason, facts = facts }
end

-- The game does not check the price, so every rule is checked here before the letter goes out.
local function buy_back()
    if pending ~= nil then return refuse("a buy-back is still running") end
    local region, problem = world.region()
    if region == nil then return refuse("no region: " .. tostring(problem)) end
    local facts = buy_back_facts(region)
    local reason = rules.buy_back_refusal(facts, price_config())
    if reason ~= nil then return refuse(reason, facts) end
    local returned = rules.families_to_return(facts.outstanding, facts.free_slots)
    local price = rules.buy_back_price(returned, price_config())
    local sent, why = world.send_settle_letter(price)
    if not sent then return refuse(why, facts) end
    state:set("bandits_outstanding_families", facts.outstanding - returned)
    pending = { families_before = world.families(region) or 0, silver_before = facts.silver, price = price, expected = returned, polls = 0,
        started = world.game_seconds() or 0 }
    core.log.info(TAG, string.format("BANDITS buy-back sent price=%d expected_families=%d silver=%d free_slots=%d bandit_units=%d",
        price, returned, facts.silver, facts.free_slots, facts.bandit_units))
    return { accepted = true, price = price, expected_families = returned, facts = facts }
end

-- No family came back: the deal failed. Give back the silver and keep the families in the pool for a later buy-back.
local function undo_failed_buy_back(result)
    local refund = rules.refund_amount(pending.silver_before, world.silver() or pending.silver_before, pending.price)
    local ok, why = true, nil
    if refund > 0 then ok, why = world.add_silver(refund) end
    if not ok then core.log.error(TAG, "BANDITS refund failed: " .. tostring(why)) end
    result.refunded = ok and refund or 0
    state:set("bandits_outstanding_families", state:get("bandits_outstanding_families") + pending.expected)
end

local function finish_buy_back(region, timed_out)
    local families = world.families(region) or pending.families_before
    local result = {
        price = pending.price, expected = pending.expected, family_gain = families - pending.families_before,
        silver_paid = pending.silver_before - (world.silver() or pending.silver_before),
        bandit_units_left = world.bandit_units(), timed_out = timed_out, refunded = 0,
    }
    if result.family_gain < 1 then undo_failed_buy_back(result) end
    buy_backs[#buy_backs + 1] = result
    state:set("bandits_returned_families", state:get("bandits_returned_families") + math.max(0, result.family_gain))
    core.log.info(TAG, string.format("BANDITS buy-back done price=%d paid=%d expected=%d gain=%d refunded=%d bandit_units_left=%s timed_out=%s",
        result.price, result.silver_paid, result.expected, result.family_gain, result.refunded, tostring(result.bandit_units_left), tostring(timed_out)))
    pending = nil
end

-- Done when the bandit units are gone and families came back, or after the poll limit.
local function check_buy_back()
    if pending == nil then return end
    pending.polls = pending.polls + 1
    if pending.polls % config.buy_back.check_every ~= 0 then return end
    local region = world.region()
    if region == nil then return end
    local gained = (world.families(region) or 0) > pending.families_before
    local waited = (world.game_seconds() or pending.started) - pending.started
    if (world.bandit_units() == 0 and gained) or waited >= config.buy_back.give_up_game_seconds then
        finish_buy_back(region, not gained)
    end
end

local function poll()
    if not state.loaded then return end
    check_buy_back()
    write_order()
    local today = world.current_day()
    if today == nil then return end
    check_tick(today)
    check_timer(today)
end

require("scheduler").every(TAG, config.poll_ms, poll)

-- Telemetry: the last tick (day, order before, manor term, homeless count, homeless term, order after), the timer and the last leave.
local has_telemetry, telemetry = pcall(require, "HarnessTelemetry")
if has_telemetry then
    telemetry.register("bandits_order", function()
        return {
            mod_order = state.loaded and mod_order() or nil, last_tick = last_tick,
            timer_start = state.loaded and state:get("bandits_timer_start") or nil, last_leave = last_leave,
        }
    end)
end

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local has_commands, commands = pcall(require, "HarnessCommands")

local function command_state()
    local region = world.region()
    local values = region and world.read_values(region)
    local today = world.current_day()
    local timer_start = state:get("bandits_timer_start")
    local timer = { start_day = timer_start, active = timer_start >= 0 }
    if timer.active and today then timer.days_left = config.timer_days - (today - timer_start) end
    return {
        day = today, mod_order = mod_order(), game_order = values and values.order, approval = values and values.approval,
        homeless = region and world.homeless(region), overwrites = overwrites,
        last_tick_day = state:get("bandits_last_tick_day"), last_tick = last_tick, ticks = state:get("bandits_ticks"),
        timer = timer, warned = state:get("bandits_warned") == 1, last_leave = last_leave, leaves = state:get("bandits_leaves"),
        families = region and world.families(region), converted_families = state:get("bandits_converted_families"),
        outstanding_families = state:get("bandits_outstanding_families"), returned_families = state:get("bandits_returned_families"),
        buy_back_pending = pending ~= nil, buy_backs = buy_backs, modifiers = modifiers, buy_back_multiplier = modifiers.buy_back_multiplier,
        free_slots = region and world.free_slots(region), silver = world.silver(), bandit_pawn = world.bandit_pawn_exists(),
    }
end

local function command_set_order(args)
    set_mod_order(args.value)
    local today = world.current_day()
    if today ~= nil then check_timer(today) end
    return command_state()
end

local function command_tick_now()
    local today = world.current_day()
    if today == nil then return nil, "the game day is not available" end
    run_tick(today)
    check_timer(today)
    return command_state()
end

-- A test command: the villagers leave at once, as if the timer had expired.
local function command_leave_now(args)
    local today = world.current_day()
    if today == nil then return nil, "the game day is not available" end
    leave(today, args.count)
    return command_state()
end

-- A test command: move the timer start back, so the timer expires after `days` more game days.
local function command_set_timer_days_left(args)
    local today = world.current_day()
    if today == nil then return nil, "the game day is not available" end
    state:set("bandits_timer_start", today - (config.timer_days - args.days))
    return command_state()
end

local function command_buy_back()
    return buy_back()
end

if has_commands then
    commands.register("InvasionMod.bandits_buy_back", command_buy_back, {})
    commands.register("InvasionMod.bandits_state", command_state, {})
    commands.register("InvasionMod.bandits_set_order", command_set_order, { value = { type = "integer", required = true, min = 0, max = 100 } })
    commands.register("InvasionMod.bandits_tick_now", command_tick_now, {})
    commands.register("InvasionMod.bandits_leave_now", command_leave_now, { count = { type = "integer", required = false, min = 1, max = 60 } })
    commands.register("InvasionMod.bandits_set_timer_days_left", command_set_timer_days_left, { days = { type = "integer", required = true, min = 1, max = 90 } })
end

-- Called by the tech tree. Takes effect at once. approval_bonus has no use now and is ignored.
local function set_modifiers(values)
    modifiers = { order_bonus = values.order_bonus or 0, buy_back_multiplier = values.buy_back_multiplier or 1 }
    core.log.info(TAG, string.format("BANDITS modifiers order_bonus=%s buy_back_multiplier=%s",
        tostring(modifiers.order_bonus), tostring(modifiers.buy_back_multiplier)))
end

core.log.info(TAG, "feature bandits loaded")
return { state = state, set_modifiers = set_modifiers }
