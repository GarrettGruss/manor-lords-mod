-- Feature raid_behavior (M03, iteration 01): track a raid that runs under the native plunder AI.
-- The mod adds no steering and no rout. It counts living raiders and carried loot, and it gives the loot of a dead raider
-- back to the nearest store. The numbers live in ModState (M01) and in the log line "RAID_BEHAVIOR".
local core = require("ManorCore")
local ModState = require("ModState")
local invasion = require("features.invasion.init")
local rules = require("features.raid_behavior.rules")
local world = require("features.raid_behavior.world")
local config = require("config").raid_behavior

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
    local raid = rules.new_raid(id, info.day, info.squads, keys)
    raids[id] = { raid = raid, burned_base = world.burned_count() or 0, leave_base = world.ai_log_tail_count(LEAVE_TEXT) or 0 }
    order[#order + 1] = id
    if state.loaded then
        state:set("raid_count", id)
        state:set("raid_start_day", info.day)
        state:set("raid_state", STATE_CODES.active)
    end
    core.log.info(TAG, string.format("RAID_BEHAVIOR start id=%d day=%d squads=%d raiders=%d", id, info.day, info.squads, #keys))
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

local function step_raid(entry, seen, today)
    local raid = entry.raid
    local was_active = raid.state == "active"
    for _, death in ipairs(rules.update(raid, seen, config, today)) do return_loot(entry, death) end
    write_caps(seen)
    refresh_burned(entry)
    check_leave_line(entry, today)
    if state.loaded then save_summary(entry) end
    if was_active and raid.state ~= "active" then
        core.log.info(TAG, string.format("RAID_BEHAVIOR end id=%d day=%s state=%s", raid.id, tostring(today), raid.state))
    end
end

local function has_active_raid()
    for _, id in ipairs(order) do
        if raids[id].raid.state == "active" then return true end
    end
    return false
end

local function tick()
    if not has_active_raid() then return end
    local today = world.current_day()
    local seen = world.read_units()
    for _, id in ipairs(order) do
        if raids[id].raid.state == "active" then step_raid(raids[id], seen, today) end
    end
    if today ~= nil and today ~= last_logged_day then
        last_logged_day = today
        log_day(today)
    end
end

LoopAsync(config.poll_ms, function()
    ExecuteInGameThread(function() core.log.try(TAG, tick) end)
    return false
end)

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
end

core.log.info(TAG, "feature raid_behavior loaded")
return { state = state }
