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
state:register("bandits_outstanding_families", 0, "integer") -- families that turned to bandits and have not come back
state:register("bandits_returned_families", 0, "integer")
state:register("bandits_natural_order", -1, "integer")
state:register("bandits_written_order", -1, "integer")

math.randomseed(os.time() + 7)

local natural_order = nil -- the game's own value, as far as the mod knows
local written_order = nil -- the last value the mod wrote
local debuff = 0
local last_ticks = {}     -- the tick results, for the state command
local overwrites = 0      -- how often the game replaced the mod's value
local pending = nil       -- a sent buy-back that is not finished: { families_before, silver_before, price, expected, polls }
local buy_backs = {}      -- the results, for the state command
-- Set by the tech tree (M12): a Public Order bonus, an approval bonus (used for the debuff only) and a buy-back price factor.
local modifiers = { order_bonus = 0, approval_bonus = 0, buy_back_multiplier = 1 }

local function difficulty()
    return invasion.difficulty()
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
    debuff = rules.debuff(rules.effective_approval(values.approval, modifiers.approval_bonus), difficulty())
    local target = rules.debuffed_order(natural, values.approval, difficulty(), modifiers)
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
    state:set("bandits_outstanding_families", state:get("bandits_outstanding_families") + record.converted)
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
        outstanding_families = state:get("bandits_outstanding_families"), returned_families = state:get("bandits_returned_families"),
        buy_back_pending = pending ~= nil, buy_backs = buy_backs, modifiers = modifiers, buy_back_multiplier = modifiers.buy_back_multiplier,
        free_slots = region and world.free_slots(region), silver = world.silver(),
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

local function command_buy_back()
    return buy_back()
end

if has_commands then
    commands.register("InvasionMod.bandits_buy_back", command_buy_back, {})
    commands.register("InvasionMod.bandits_state", command_state, {})
    commands.register("InvasionMod.bandits_set_approval", command_set_approval, { value = { type = "integer", required = true, min = 0, max = 100 } })
    commands.register("InvasionMod.bandits_tick_now", command_tick_now, { roll = { type = "number", required = false, min = 0, max = 1 } })
end

-- Called by the tech tree. Takes effect at once.
local function set_modifiers(values)
    modifiers = {
        order_bonus = values.order_bonus or 0, approval_bonus = values.approval_bonus or 0,
        buy_back_multiplier = values.buy_back_multiplier or 1,
    }
    if state.loaded then apply_debuff() end
    core.log.info(TAG, string.format("BANDITS modifiers order_bonus=%s approval_bonus=%s buy_back_multiplier=%s",
        tostring(modifiers.order_bonus), tostring(modifiers.approval_bonus), tostring(modifiers.buy_back_multiplier)))
end

core.log.info(TAG, "feature bandits loaded")
return { state = state, set_modifiers = set_modifiers }
