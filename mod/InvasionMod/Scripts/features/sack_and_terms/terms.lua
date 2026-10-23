-- Tribute terms (M06 iteration 02). While a lord raid stands on the map the invader offers terms:
-- a one-time payment, or vassalage with a yearly tribute. Hostages are dropped (M00 decision 8).
-- Accepting ends the raid early through raid_behavior.force_leave (the M03.02 peace route). Banner and commands for now; UI later (TBD).
local core = require("ManorCore")
local ModState = require("ModState")
local invasion = require("features.invasion.init")
local raid_behavior = require("features.raid_behavior.init")
local raid_world = require("features.raid_behavior.world")
local silver_world = require("features.bandits.world")
local rules = require("features.sack_and_terms.terms_rules")
local config = require("config").sack_and_terms.terms

local TAG = "InvasionMod.terms"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("terms_state", rules.NONE, "integer")
state:register("terms_next_tribute_day", 0, "integer")
state:register("terms_paid_total", 0, "integer")      -- silver paid as one-time payment or tribute
state:register("terms_tribute_paid", 0, "integer")

local offer = nil -- { day, difficulty, payment, tribute } while an offer is open (not saved)
local sacked_raid = nil -- id of the raid whose sack of the player region ended the terms (not saved)

local function set_if_changed(key, value)
    if state:get(key) ~= value then state:set(key, value) end
end

local function open_offer(reason)
    local difficulty = invasion.state:get("difficulty")
    offer = { day = raid_world.current_day(), difficulty = difficulty, payment = rules.payment(difficulty, config), tribute = rules.tribute(difficulty, config) }
    set_if_changed("terms_state", rules.OFFERED)
    core.log.info(TAG, string.format("TERMS offer reason=%s payment=%d tribute=%d difficulty=%d", reason, offer.payment, offer.tribute, difficulty))
    core.show_banner("The invader offers terms", string.format("Pay %d silver, or become a vassal and pay %d silver a year", offer.payment, offer.tribute))
end

local function close_offer(new_state)
    offer = nil
    set_if_changed("terms_state", new_state)
end

-- After a sack of the player region the terms of that raid are over (owner, 2026-10-20, item 4; option a of question 4).
-- Open offers close. A raid of the same id gets no new offer. A later raid is a new raid and may offer terms again.
local function close_after_sack(raid_id)
    local active = raid_behavior.active_role_raid()
    sacked_raid = raid_id or (active and active.id) or nil
    if offer ~= nil then
        close_offer(rules.NONE)
        core.log.info(TAG, "TERMS offer closed by a sack, raid " .. tostring(sacked_raid))
    end
end

-- An offer opens when a lord raid spawns.
invasion.watch_spawn(function() return nil end, function(_, info)
    if info.lord_raid ~= nil and config.offer_on_spawn then open_offer("raid spawn") end
end)

local function accept(kind)
    local silver = silver_world.silver()
    local refusal = rules.refusal(kind, offer ~= nil, silver, offer and offer.payment or 0)
    if refusal then return nil, refusal end
    if raid_behavior.active_role_raid() == nil then return nil, "the raid is gone, the offer is void" end
    local today = raid_world.current_day()
    local ok, problem = raid_behavior.force_leave("terms")
    if not ok then return nil, problem end
    local result = { kind = kind, day = today, silver_before = silver }
    if kind == "payment" then
        local paid, why = silver_world.add_silver(-offer.payment)
        if not paid then error("payment failed: " .. tostring(why), 0) end
        state:set("terms_paid_total", state:get("terms_paid_total") + offer.payment)
        close_offer(rules.PAID)
    else
        state:set("terms_next_tribute_day", today + config.tribute_days)
        close_offer(rules.VASSAL)
    end
    result.silver_after = silver_world.silver()
    core.log.info(TAG, string.format("TERMS accepted kind=%s day=%s silver %s->%s", kind, tostring(today), tostring(result.silver_before), tostring(result.silver_after)))
    return result
end

-- The yearly tribute of a vassal, once the day is reached.
local function tribute_tick()
    if not state.loaded then return end
    local today = raid_world.current_day()
    if today == nil or not rules.tribute_due(state:get("terms_state"), state:get("terms_next_tribute_day"), today) then return end
    local silver = silver_world.silver()
    if silver == nil then return end
    local amount = rules.tribute_charge(silver, rules.tribute(invasion.state:get("difficulty"), config))
    if amount > 0 then silver_world.add_silver(-amount) end
    state:set("terms_tribute_paid", state:get("terms_tribute_paid") + amount)
    state:set("terms_paid_total", state:get("terms_paid_total") + amount)
    state:set("terms_next_tribute_day", today + config.tribute_days)
    core.log.info(TAG, string.format("TERMS tribute day=%d paid=%d silver=%d", today, amount, silver))
end

require("scheduler").every(TAG, config.poll_ms, tribute_tick)

local has_commands, commands = pcall(require, "HarnessCommands")

local function command_state()
    return {
        state = state:get("terms_state"), offer = offer, next_tribute_day = state:get("terms_next_tribute_day"),
        paid_total = state:get("terms_paid_total"), tribute_paid = state:get("terms_tribute_paid"), silver = silver_world.silver(),
        day = raid_world.current_day(),
    }
end

if has_commands then
    commands.register("InvasionMod.terms_state", command_state, {})
    commands.register("InvasionMod.terms_offer", function()
        local active = raid_behavior.active_role_raid()
        if active == nil then return nil, "no active role raid" end
        if sacked_raid ~= nil and active.id == sacked_raid then return nil, "raid " .. tostring(active.id) .. " sacked the town: no terms after a sack" end
        open_offer("command")
        return command_state()
    end, {})
    commands.register("InvasionMod.terms_accept", function(args)
        return accept(args.kind)
    end, { kind = { type = "string", required = true, oneOf = { "payment", "vassalage" } } })
    commands.register("InvasionMod.terms_decline", function()
        if offer == nil then return nil, "no offer is open" end
        close_offer(rules.NONE)
        return command_state()
    end, {})
end

core.log.info(TAG, "terms loaded")
return { state = state, summary = command_state, close_after_sack = close_after_sack }
