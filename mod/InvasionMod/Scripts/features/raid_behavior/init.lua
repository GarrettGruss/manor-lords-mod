-- Feature raid_behavior (M03): steer the Hussite raids and track every raid that the invasion feature spawns.
-- A native raid is only counted, never steered. The numbers live in ModState (M01) and in the log line "RAID_BEHAVIOR".
local core = require("ManorCore")
local ModState = require("ModState")
local invasion = require("features.invasion.init")
local rules = require("features.raid_behavior.rules")
local world = require("features.raid_behavior.world")
local config = require("config").raid_behavior
local leave = config.leave
local plunder = config.plunder
local steal = config.steal
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
state:register("raid_plunder_record", "none", "string")

-- Loot override (change update-banditry-rebellion-raid): saved in ModState slots, read at the corpse pit.
local loot_override = require("features.raid_behavior.loot_override")
local override_paid = { bodies = 0, goods = 0 }  -- paid at a pit in this session, for the state command
local overrides = loot_override.new(loot_override.state_store(state, require("config").bandits.loot_override_slots), core.log)

local end_watchers = {}    -- functions called with the raid summary when a raid is no longer active (M08 protection)
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

-- Why a delay: a scan of all units in the tick of a spawn touches objects that are just made. Crashes were seen there
-- (spike-lua-crash-after-spawn). The scan of the new units runs in a later game-thread tick.
local SCAN_DELAY_S = 0.25
local pending_scans = {}

local function register_raid(before, info)
    local keys = world.new_keys(before, world.read_units())
    local id = #order + 1
    local raid = rules.new_raid(id, info.day, info.squads, keys, info.roles, info.lord_raid)
    raid.target = info.target and info.target.region or nil
    raids[id] = { raid = raid, burned_base = world.burned_count() or 0, leave_base = world.ai_log_tail_count(LEAVE_TEXT) or 0 }
    order[#order + 1] = id
    if state.loaded then
        state:set("raid_count", id)
        state:set("raid_start_day", info.day)
        state:set("raid_state", STATE_CODES.active)
    end
    core.log.info(TAG, string.format("RAID_BEHAVIOR start id=%d day=%d squads=%d raiders=%d roles=%s", id, info.day, info.squads, #keys, tostring(info.roles == true)))
end

local function after_spawn(before, info)
    pending_scans[#pending_scans + 1] = { before = before, info = info, at = os.clock() }
end

-- Runs from the scheduler. An entry waits until a later tick than its spawn.
local function resolve_pending_scans()
    if #pending_scans == 0 or os.clock() - pending_scans[1].at < SCAN_DELAY_S then return end
    local entries = pending_scans
    pending_scans = {}
    for _, entry in ipairs(entries) do core.log.try(TAG, register_raid, entry.before, entry.info) end
end

require("scheduler").every(TAG .. ".scan", 200, resolve_pending_scans)

invasion.watch_spawn(before_spawn, after_spawn)

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

-- The goods record of the latest Hussite raid, as text "<good>-<amount>_...", so a load can show it (ModState has no table kind).
local function save_record(raid)
    if raid.lord == nil or not state.loaded then return end
    local parts = {}
    for good, count in pairs(raid.plunder_goods) do parts[#parts + 1] = string.format("%d-%d", good, count) end
    table.sort(parts)
    set_if_changed("raid_plunder_record", #parts > 0 and table.concat(parts, "_") or "none")
end

-- The plunder tick: while the lord army stands at the manor, goods leave the village stores (once a day).
local function check_plunder(entry, seen, today)
    local raid = entry.raid
    local want = rules.plunder_amount(raid, seen, plunder, leave, today, config.carry_cap)
    if want <= 0 then return end
    local taken, by_good = world.plunder(want, config.store_tiers)
    rules.record_plunder(raid, taken, by_good)
    save_record(raid)
    core.log.info(TAG, string.format("RAID_BEHAVIOR plunder id=%d day=%s wanted=%d taken=%d plundered=%d", raid.id, tostring(today), want, taken, raid.plundered))
end

-- The baron steal: a raider far from the battle marker takes goods from tier 1 stores (once a day, up to the steal goal).
local function check_steal(entry, seen, today)
    local raid = entry.raid
    local want = rules.steal_amount(raid, seen, steal, today)
    if want <= 0 then return end
    local taken = world.plunder(want, config.store_tiers)
    rules.record_steal(raid, taken)
    core.log.info(TAG, string.format("RAID_BEHAVIOR steal id=%d day=%s wanted=%d taken=%d stolen=%d goal=%s", raid.id, tostring(today), want, taken, raid.stolen, tostring(rules.steal_goal(raid, steal))))
end

-- A won challenge writes the lord as region owner (run 20261018-015009-371a). The region goes back to the player at once.
local function check_region(entry, slow_look)
    local lord = entry.raid.lord
    if lord == nil or lord.home_region == nil or not slow_look then return end
    if world.region_is_players(lord.home_region) ~= false then return end
    local ok, problem = world.give_region_to_player(lord.home_region)
    core.log.warn(TAG, string.format("RAID_BEHAVIOR region %s was taken by the lord, given back=%s%s", lord.home_region, tostring(ok), ok and "" or (" problem=" .. tostring(problem))))
end

-- A role raid that has taken enough, lost enough or stayed long enough must leave (user decision 2026-10-18). A lord raid
-- leaves by peace with its lord. A bandit squad raid is only marked (watchers and the terms feature hear of it): the mod
-- does not make peace, send it home or remove its units (owner decision 2026-10-21).
local function start_leave(raid, reason, today)
    rules.begin_leave(raid, reason, today)
    local ok, problem = true, nil
    if raid.lord ~= nil then ok, problem = lord_raid.peace() end
    core.log.info(TAG, string.format("RAID_BEHAVIOR role raid must leave id=%d day=%s reason=%s peace=%s%s", raid.id, tostring(today),
        reason, tostring(raid.lord ~= nil and ok), ok and "" or (" problem=" .. tostring(problem))))
    for _, watcher in ipairs(leave_watchers) do core.log.try(TAG, watcher, rules.summary(raid)) end
end

local function check_leave(entry, today)
    local raid = entry.raid
    if not leave.enabled or raid.leave_reason ~= nil then return end
    local reason = rules.leave_reason(raid, today, leave, config.carry_cap)
    if reason ~= nil then start_leave(raid, reason, today) end
end

-- Raiders that died in this session, all raids (read by the contract objective kill_raiders; a count only, not saved).
local raiders_died = 0

local function step_raid(entry, seen, today, slow_look)
    local raid = entry.raid
    local was_active = raid.state == "active"
    local deaths = rules.update(raid, seen, config, today)
    raiders_died = raiders_died + #deaths
    rules.note_deaths(raid, deaths)
    write_caps(seen)
    check_plunder(entry, seen, today)
    check_steal(entry, seen, today)
    check_region(entry, slow_look)
    check_leave(entry, today)
    if slow_look then
        refresh_burned(entry)
        check_leave_line(entry, today)
    end
    if state.loaded then save_summary(entry) end
    if was_active and raid.state ~= "active" then
        core.log.info(TAG, string.format("RAID_BEHAVIOR end id=%d day=%s state=%s", raid.id, tostring(today), raid.state))
        for _, watcher in ipairs(end_watchers) do core.log.try(TAG, watcher, rules.summary(raid)) end
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

-- The pit poll (change add-corpse-pit-loot). A delivered body has no hook: it shows only as the pit corpse count rising.
-- It runs once a game second, only after a Hussite raid exists. A rise pays one share for each unpaid dead Hussite raider;
-- other bodies (villagers, native raiders) are ignored. No pit means no give-back.
local pit_baseline = {}   -- pit key -> corpse count at the last look

local function raid_records()
    local list = {}
    for _, id in ipairs(order) do list[#list + 1] = raids[id].raid end
    return list
end

-- Strip the Dead (tech tree) turns the pay-out on. Without the law a body is still counted as received but pays nothing.
local corpse_loot_on = false
local bodies_consumed, bodies_looted = 0, 0 -- tracked bodies that reached a pit, and those that were looted (law on); for the test state
local looted_watchers = {}  -- functions called with the number of bodies looted in one pit look (tech tree: order loss)

local function merge_goods(into, from)
    for good, amount in pairs(from) do into[good] = (into[good] or 0) + amount end
end

-- Bodies with a loot override are paid first: their goods replace the config loot. The other bodies follow the raid rules.
local function pit_poll()
    if #order == 0 and not (state.loaded and overrides.count() > 0) then return end
    local pits = world.pits()
    if pits == nil then return end
    for _, pit in ipairs(pits) do
        local before = pit_baseline[pit.key]
        pit_baseline[pit.key] = pit.corpses
        if before ~= nil and pit.corpses > before then
            local bodies = pit.corpses - before
            -- Loot order: the loot override of a dead brigand first (the law "Strip the Dead" does not gate it: it is how the player
            -- recovers the goods that the rebels took), then the Hussite share of the raid record, then body_loot for other tracked dead.
            local goods, paid_override = {}, 0
            if state.loaded then goods, paid_override = overrides.pay(bodies) end
            for _, amount in pairs(goods) do override_paid.goods = override_paid.goods + amount end
            override_paid.bodies = override_paid.bodies + paid_override
            local raid_goods, paid = rules.pay_bodies(raid_records(), bodies - paid_override)
            local other_goods, other_paid = rules.pay_other_bodies(raid_records(), bodies - paid_override - paid, config.body_loot, "bandit", math.random)
            merge_goods(raid_goods, other_goods)
            paid = paid + other_paid
            bodies_consumed = bodies_consumed + paid
            if paid > 0 and corpse_loot_on then
                bodies_looted = bodies_looted + paid
                merge_goods(goods, raid_goods)
                for _, watcher in ipairs(looted_watchers) do core.log.try(TAG, watcher, paid) end
            elseif paid > 0 then
                core.log.info(TAG, string.format("RAID_BEHAVIOR pit bodies=%d not looted (no law)", paid))
            end
            if paid_override > 0 or (paid > 0 and corpse_loot_on) then
                if next(goods) ~= nil then
                    local ok, problem = world.pit_add(pit, goods)
                    if not ok then core.log.error(TAG, "pit give-back failed: " .. tostring(problem)) end
                end
                core.log.info(TAG, string.format("RAID_BEHAVIOR pit bodies=%d paid=%d override_paid=%d other=%d unpaid=%d", bodies, paid_override + paid, paid_override, other_paid, rules.unpaid_total(raid_records())))
            end
        end
    end
end

require("scheduler").every(TAG .. ".pit", config.pit_poll_ms, pit_poll)

-- The loot override poll. After a load it reads the saved slots and links them to the new units; later it ends the entries of units
-- that left the map or whose body expired.
local known_pawn = nil        -- the player pawn address of the game the entries belong to
local relink = nil            -- { until_s, polls } while a load waits for its units

local function relink_step()
    local seconds = world.game_seconds() or 0
    relink.polls = relink.polls + 1
    local wanted = {}
    for _, row in ipairs(overrides.list()) do wanted[row.squad] = true end
    local _, unlinked = overrides.relink(world.units_by_squad(wanted))
    if unlinked > 0 and seconds < relink.until_s and relink.polls < config.relink_max_polls then return end
    local lost = overrides.drop_unlinked()
    core.log.info(TAG, string.format("LOOT_OVERRIDE relink done entries=%d lost=%d polls=%d", overrides.count(), lost, relink.polls))
    relink = nil
end

local function override_poll()
    if not state.loaded then return end
    local pawn = world.player_address()
    if pawn == nil then return end
    if pawn ~= known_pawn then
        known_pawn = pawn
        local saved = overrides.load_saved()
        core.log.info(TAG, string.format("LOOT_OVERRIDE load saved=%d", saved))
        relink = saved > 0 and { until_s = (world.game_seconds() or 0) + config.relink_window_s, polls = 0 } or nil
    end
    if relink ~= nil then return relink_step() end
    if overrides.count() > 0 then overrides.poll(world.override_units(overrides.addresses()), world.current_day()) end
end

require("scheduler").every(TAG .. ".override", config.override_poll_ms, override_poll)

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
             carry_cap = config.carry_cap, steal = steal, store_tiers = config.store_tiers }
end

if has_commands then
    commands.register("InvasionMod.raid_behavior_state", command_state, {})
    -- Test: the loot override entries (slot, squad, unit index, goods, linked) and the pit goods.
    commands.register("InvasionMod.raid_behavior_override_state", function()
        local alive, dead, missing = 0, 0, 0
        if state.loaded and overrides.count() > 0 then
            local seen = world.override_units(overrides.addresses())
            for address in pairs(overrides.addresses()) do
                if seen[address] == nil then missing = missing + 1 elseif seen[address].dead then dead = dead + 1 else alive = alive + 1 end
            end
        end
        return { entries = state.loaded and overrides.list() or {}, count = state.loaded and overrides.count() or 0, relinking = relink ~= nil,
                 slots = require("config").bandits.loot_override_slots, units_alive = alive, units_dead = dead, units_missing = missing,
                 paid_bodies = override_paid.bodies, paid_goods = override_paid.goods }
    end, {})
    -- Test: kill the units of the first `count` override entries (just_die, no hiding). Returns the number killed.
    commands.register("InvasionMod.raid_behavior_test_kill_override_units", function(args)
        local wanted, slots = {}, {}
        for _, row in ipairs(overrides.list()) do
            if #slots < args.count then slots[#slots + 1] = row.slot end
        end
        for address, entry in pairs(overrides.addresses()) do
            for _, slot in ipairs(slots) do if entry.slot == slot then wanted[address] = true end end
        end
        local killed = 0
        for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
            local address = core.isValid(unit) and core.read(function() return unit:GetAddress() end) or nil
            if address ~= nil and wanted[address] and world.remove_unit(unit) then killed = killed + 1 end
        end
        return { killed = killed, slots = slots }
    end, { count = { type = "integer", required = true, min = 1, max = 100 } })
    -- Test: the corpse pits (corpse count and goods) and the dead raiders that no pit delivery has paid yet.
    commands.register("InvasionMod.raid_behavior_pit_state", function()
        local pits = {}
        for _, pit in ipairs(world.pits() or {}) do
            local goods = {}
            for good, amount in pairs(pit.goods) do goods[#goods + 1] = { good = good, amount = amount } end
            table.sort(goods, function(a, b) return a.good < b.good end)
            pits[#pits + 1] = { corpses = pit.corpses, goods = goods, limit = world.pit_limit(pit) }
        end
        local record = {}
        for _, id in ipairs(order) do
            local goods = {}
            for good, amount in pairs(raids[id].raid.plunder_goods) do goods[#goods + 1] = { good = good, amount = amount } end
            table.sort(goods, function(a, b) return a.good < b.good end)
            record[#record + 1] = { id = id, goods = goods, unpaid = raids[id].raid.unpaid, unpaid_other = raids[id].raid.unpaid_other }
        end
        return { pits = pits, raids = record, consumed = bodies_consumed, looted = bodies_looted }
    end, {})
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

-- Another feature registers fn(summary). It runs once when a raid is no longer active.
local function watch_end(fn)
    end_watchers[#end_watchers + 1] = fn
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

-- Summaries of the raids that are still active.
local function active_raids()
    local list = {}
    for _, id in ipairs(order) do
        if raids[id].raid.state == "active" then list[#list + 1] = rules.summary(raids[id].raid) end
    end
    return list
end

local function active_role_raid()
    for _, id in ipairs(order) do
        local raid = raids[id].raid
        if raid.roles and raid.state == "active" and raid.leave_reason == nil then return rules.summary(raid) end
    end
    return nil
end

local function raiders_killed() return raiders_died end

-- Called by the tech tree (Strip the Dead): `on` turns the pit pay-out on or off.
local function set_corpse_loot(on)
    local value = on == true
    if value ~= corpse_loot_on then core.log.info(TAG, "RAID_BEHAVIOR corpse loot " .. (value and "on" or "off")) end
    corpse_loot_on = value
end

local function watch_looted(fn) looted_watchers[#looted_watchers + 1] = fn end

return { state = state, raiders_killed = raiders_killed, loot_override = overrides, set_corpse_loot = set_corpse_loot, watch_looted = watch_looted, watch_leave = watch_leave, watch_end = watch_end, active_raids = active_raids, force_leave = force_leave, active_role_raid = active_role_raid, final_raid_ended = final_raid_ended }
