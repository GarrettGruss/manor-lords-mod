-- Feature raid_behavior (M03, iteration 01): track a raid that runs under the native plunder AI.
-- The mod adds no steering and no rout. It counts living raiders and carried loot, and it gives the loot of a dead raider
-- back to the nearest store. The numbers live in ModState (M01) and in the log line "RAID_BEHAVIOR".
local core = require("ManorCore")
local ModState = require("ModState")
local invasion = require("features.invasion.init")
local rules = require("features.raid_behavior.rules")
local world = require("features.raid_behavior.world")
local config = require("config").raid_behavior
local leave = config.leave
local plunder = config.plunder
local lord_raid = require("features.invasion.lord_raid")

local TAG = "InvasionMod.raid_behavior"
local STATE_VERSION = 1
local LEAVE_TEXT = "Leaving map"

-- Raid states in ModState: 0 none, 1 active, 2 left, 3 destroyed.
local STATE_CODES = { active = 1, left = 2, destroyed = 3, empty = 3 }

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("raid_count", 0, "integer")
state:register("raid_start_day", 0, "integer")
state:register("raid_state", 0, "integer")
state:register("raid_returned", 0, "integer")
state:register("raid_lost", 0, "integer")
state:register("raid_burned", 0, "integer")

local leave_watchers = {}  -- functions called with the raid summary when a role raid begins to leave (M06 sack)
local raids = {}            -- raid id -> { raid, burned_base, leave_base }
local order = {}            -- raid ids in start order
local last_logged_day = nil

---------------------------------------------------------------------------------------------
-- Spawn hook (called by the invasion feature)
---------------------------------------------------------------------------------------------

local function before_spawn()
    return world.read_units()
end

local function after_spawn(before, info)
    local keys = world.new_keys(before, world.read_units())
    local id = #order + 1
    local raid = rules.new_raid(id, info.day, info.squads, keys, info.roles, info.lord_raid)
    raids[id] = { raid = raid, burned_base = world.burned_count() or 0, leave_base = world.ai_log_tail_count(LEAVE_TEXT) or 0 }
    order[#order + 1] = id
    if state.loaded then
        state:set("raid_count", id)
        state:set("raid_start_day", info.day)
        state:set("raid_state", STATE_CODES.active)
    end
    core.log.info(TAG, string.format("RAID_BEHAVIOR start id=%d day=%d squads=%d raiders=%d roles=%s", id, info.day, info.squads, #keys, tostring(info.roles == true)))
end

invasion.watch_spawn(before_spawn, after_spawn)

---------------------------------------------------------------------------------------------
-- Loot of a dead raider goes back to the nearest store
---------------------------------------------------------------------------------------------

local function return_loot(entry, death)
    if death.loot <= 0 then return end
    local stores, problem = world.stores()
    local store = stores and death.x and rules.nearest_store(stores, death.x, death.y)
    if store == nil then
        rules.record_loss(entry.raid, death.loot)
        return core.log.warn(TAG, string.format("RAID_BEHAVIOR loot %d lost: no store (%s)", death.loot, tostring(problem)))
    end
    local good = rules.pick_good(store.by_good, config.fallback_good)
    local ok, why = world.deposit(store, good, death.loot)
    if not ok then
        rules.record_loss(entry.raid, death.loot)
        return core.log.error(TAG, string.format("RAID_BEHAVIOR loot %d lost: %s", death.loot, tostring(why)))
    end
    rules.record_return(entry.raid, death.loot)
    core.log.info(TAG, string.format("RAID_BEHAVIOR loot returned amount=%d good=%d store=%s", death.loot, good, tostring(store.id)))
end

---------------------------------------------------------------------------------------------
-- Poll
---------------------------------------------------------------------------------------------

local function write_caps(seen)
    for _, now in pairs(seen) do
        if now.new_loot ~= nil and now.new_loot ~= now.loot and now.object ~= nil then
            local ok, why = world.write_loot(now.object, now.new_loot)
            if not ok then core.log.error(TAG, "carry cap write failed: " .. why) end
        end
    end
end

local function refresh_burned(entry)
    local burned = world.burned_count()
    if burned ~= nil then entry.raid.burned = math.max(entry.raid.burned, burned - entry.burned_base) end
end

local function check_leave_line(entry, today)
    if entry.raid.leaving then return end
    local count = world.ai_log_tail_count(LEAVE_TEXT)
    if count ~= nil and count > entry.leave_base then
        rules.mark_leaving(entry.raid, today)
        core.log.info(TAG, string.format("RAID_BEHAVIOR native leave line seen id=%d", entry.raid.id))
    end
end

-- Every set writes the Tags of the player pawn. A write each second may have crashed the game in real runs, so write only a change.
local function set_if_changed(key, value)
    if state:get(key) ~= value then state:set(key, value) end
end

local function save_summary(entry)
    local raid = entry.raid
    set_if_changed("raid_state", STATE_CODES[raid.state])
    set_if_changed("raid_returned", raid.returned)
    set_if_changed("raid_lost", raid.lost)
    set_if_changed("raid_burned", raid.burned)
end

local function log_day(today)
    for _, id in ipairs(order) do
        local s = rules.summary(raids[id].raid)
        core.log.info(TAG, string.format(
            "RAID_BEHAVIOR day=%d id=%d state=%s living=%d loot=%d looted_total=%d returned=%d burned=%d leaving=%s",
            today, id, s.state, s.living, s.loot, s.looted_total, s.returned, s.burned, tostring(s.leaving)))
    end
end

-- The plunder tick: while the lord army stands at the manor, goods leave the village stores (once a day).
local function check_plunder(entry, seen, today)
    local raid = entry.raid
    local want = rules.plunder_amount(raid, seen, plunder, leave, today)
    if want <= 0 then return end
    local taken = world.plunder(want)
    rules.record_plunder(raid, taken)
    core.log.info(TAG, string.format("RAID_BEHAVIOR plunder id=%d day=%s wanted=%d taken=%d plundered=%d", raid.id, tostring(today), want, taken, raid.plundered))
end

-- A won challenge writes the lord as region owner (run 20261018-015009-371a). The region goes back to the player at once.
local function check_region(entry, slow_look)
    local lord = entry.raid.lord
    if lord == nil or lord.home_region == nil or not slow_look then return end
    if world.region_is_players(lord.home_region) ~= false then return end
    local ok, problem = world.give_region_to_player(lord.home_region)
    core.log.warn(TAG, string.format("RAID_BEHAVIOR region %s was taken by the lord, given back=%s%s", lord.home_region, tostring(ok), ok and "" or (" problem=" .. tostring(problem))))
end

-- A role raid that has taken enough, lost enough or stayed long enough must leave (user decision 2026-10-18): it first goes away
-- (peace with the bandit lord), and the mod removes a unit only in a quiet spot, far from the village (config leave.quiet_distance).
local function start_leave(raid, reason, today)
    rules.begin_leave(raid, reason, today)
    local ok, problem
    if raid.lord ~= nil then ok, problem = lord_raid.peace() else ok, problem = world.make_peace() end
    core.log.info(TAG, string.format("RAID_BEHAVIOR role raid must leave id=%d day=%s reason=%s peace=%s%s", raid.id, tostring(today),
        reason, tostring(ok), ok and "" or (" problem=" .. tostring(problem))))
    for _, watcher in ipairs(leave_watchers) do core.log.try(TAG, watcher, rules.summary(raid)) end
end

local function check_leave(entry, seen, today)
    local raid = entry.raid
    if not leave.enabled then return end
    if raid.leave_reason == nil then
        local reason = rules.leave_reason(raid, today, leave)
        if reason == nil then return end
        start_leave(raid, reason, today)
    end
    local keys = rules.exit_quiet(raid, seen, world.home(), { distance = leave.quiet_distance, exit_y = config.exit_y })
    if #keys == 0 then return end
    local removed = 0
    for _, key in ipairs(keys) do
        if seen[key].object ~= nil and world.remove_unit(seen[key].object) then removed = removed + 1 end
    end
    core.log.info(TAG, string.format("RAID_BEHAVIOR role raid units removed in a quiet spot id=%d day=%s units=%d removed=%d living=%d carried_out=%d",
        raid.id, tostring(today), #keys, removed, raid.living - #keys, raid.carried_out))
end

local function step_raid(entry, seen, today, slow_look)
    local raid = entry.raid
    local was_active = raid.state == "active"
    for _, death in ipairs(rules.update(raid, seen, config, today)) do return_loot(entry, death) end
    write_caps(seen)
    check_plunder(entry, seen, today)
    check_region(entry, slow_look)
    check_leave(entry, seen, today)
    if slow_look then
        refresh_burned(entry)
        check_leave_line(entry, today)
    end
    if state.loaded then save_summary(entry) end
    if was_active and raid.state ~= "active" then
        core.log.info(TAG, string.format("RAID_BEHAVIOR end id=%d day=%s state=%s", raid.id, tostring(today), raid.state))
        if raid.leave_reason ~= nil and raid.lord == nil then
            local ok, problem = world.restore_war()
            core.log.info(TAG, string.format("RAID_BEHAVIOR war restored=%s%s", tostring(ok), ok and "" or (" problem=" .. tostring(problem))))
        end
    end
end

local function has_active_raid()
    for _, id in ipairs(order) do
        if raids[id].raid.state == "active" then return true end
    end
    return false
end

-- Why only the raid units and a slow look: reads of every unit, building and log line each second crashed
-- the Lua state in 120 day runs (issue 163).
local function tracked_keys()
    local keys = {}
    for _, id in ipairs(order) do
        if raids[id].raid.state == "active" then
            for key in pairs(raids[id].raid.units) do keys[key] = true end
        end
    end
    return keys
end

local function any_leaving()
    for _, id in ipairs(order) do
        local raid = raids[id].raid
        if raid.state == "active" and (raid.leave_reason ~= nil or raid.lord ~= nil) then return true end
    end
    return false
end

local tick_count = 0

local function tick()
    if not has_active_raid() then return end
    tick_count = tick_count + 1
    local slow_look = tick_count % config.slow_every == 1
    local today = world.current_day()
    local seen = world.read_units(tracked_keys(), any_leaving())
    for _, id in ipairs(order) do
        if raids[id].raid.state == "active" then step_raid(raids[id], seen, today, slow_look) end
    end
    if today ~= nil and today ~= last_logged_day then
        last_logged_day = today
        log_day(today)
    end
end

require("scheduler").every(TAG, config.poll_ms, tick)

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local has_commands, commands = pcall(require, "HarnessCommands")

local function command_state()
    local summaries = {}
    for _, id in ipairs(order) do
        if raids[id].raid.state == "active" then refresh_burned(raids[id]) end
        summaries[#summaries + 1] = rules.summary(raids[id].raid)
    end
    return { day = world.current_day(), raids = summaries, active = has_active_raid(), population = world.population(),
             carry_cap = config.carry_cap }
end

if has_commands then
    commands.register("InvasionMod.raid_behavior_state", command_state, {})
    -- Test commands. They change the leave rules for this session only (not saved) and act on the raid of this session.
    commands.register("InvasionMod.raid_behavior_test_set_leave", function(args)
        for _, key in ipairs({ "loot_per_raider", "loss_share", "max_days" }) do
            if args[key] ~= nil then leave[key] = args[key] end
        end
        return { loot_per_raider = leave.loot_per_raider, loss_share = leave.loss_share, max_days = leave.max_days }
    end, { loot_per_raider = { type = "number", min = 0, max = 1000 }, loss_share = { type = "number", min = 0, max = 10 },
           max_days = { type = "integer", min = 0, max = 1000 } })
    -- Test: make the raid lord the owner of the home region, as a won challenge does. The guard must give it back.
    commands.register("InvasionMod.raid_behavior_test_take_region", function()
        local lord = raids[order[#order]] and raids[order[#order]].raid.lord
        local pawn = lord_raid.lord_pawn()
        if lord == nil or lord.home_region == nil or pawn == nil then return nil, "no lord raid" end
        local ok, problem = world.set_region_owner(lord.home_region, pawn)
        if not ok then return nil, problem end
        return { region = lord.home_region }
    end, {})
    -- Test: kill a share of the living raiders of the last raid (just_die) so the loss rule can fire.
    commands.register("InvasionMod.raid_behavior_test_kill_raiders", function(args)
        local entry = raids[order[#order]]
        if entry == nil then return nil, "no raid" end
        local seen = world.read_units(tracked_keys(), false)
        local living = {}
        for key, row in pairs(seen) do
            if not row.dead and row.object ~= nil then living[#living + 1] = row.object end
        end
        local want = math.ceil(#living * args.share)
        local killed = 0
        for index = 1, want do
            if world.remove_unit(living[index]) then killed = killed + 1 end
        end
        return { living = #living, killed = killed }
    end, { share = { type = "number", required = true, min = 0, max = 1 } })
    commands.register("InvasionMod.raid_behavior_claim_back", function(args)
        local ok, problem = world.give_region_to_player(args.region)
        return { ok = ok, problem = problem }
    end, { region = { type = "string", required = true, maxLength = 40 } })
end

core.log.info(TAG, "feature raid_behavior loaded")
-- Another feature registers fn(summary). It runs once when a role raid begins to leave.
local function watch_leave(fn)
    leave_watchers[#leave_watchers + 1] = fn
end

-- True when the last final-battle raid of the great raid has no living unit. nil when there is no such raid yet.
local function final_raid_ended()
    for index = #order, 1, -1 do
        local raid = raids[order[index]].raid
        if raid.lord ~= nil and raid.lord.final then return raid.initial > 0 and raid.state ~= "active" end
    end
    return nil
end

-- Make the active role raid leave now (for example after the player accepted terms). Returns true, or false and a message.
local function force_leave(reason)
    for _, id in ipairs(order) do
        local raid = raids[id].raid
        if raid.roles and raid.state == "active" and raid.leave_reason == nil then
            start_leave(raid, reason, world.current_day())
            return true
        end
    end
    return false, "no active role raid that can leave"
end

local function active_role_raid()
    for _, id in ipairs(order) do
        local raid = raids[id].raid
        if raid.roles and raid.state == "active" and raid.leave_reason == nil then return rules.summary(raid) end
    end
    return nil
end

return { state = state, watch_leave = watch_leave, force_leave = force_leave, active_role_raid = active_role_raid, final_raid_ended = final_raid_ended }
