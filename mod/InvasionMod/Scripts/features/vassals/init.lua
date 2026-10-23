-- Feature vassals (M07). Iteration 01: the game goal is Endless, so a claim never ends the game (spec 26).
-- The mod keeps a registry of vassal slots in ModState (pawn Tags). Each slot has a region, a lord name and a start day.
local core = require("ManorCore")
local ModState = require("ModState")
local rules = require("features.vassals.rules")
local world = require("features.vassals.world")
local config = require("config").vassals
local silver_world = require("features.bandits.world")

local TAG = "InvasionMod.vassals"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("vassals_goal_writes", 0, "integer")
state:register("vassals_home_region", rules.NO_REGION, "string")
state:register("vassals_lost", 0, "integer")
for slot = 1, config.max_vassals do
    state:register("vassal" .. slot .. "_region", rules.NO_REGION, "string")
    state:register("vassal" .. slot .. "_lord", rules.NO_REGION, "string")
    state:register("vassal" .. slot .. "_since_day", 0, "integer")
    state:register("vassal" .. slot .. "_handed_day", 0, "integer")      -- game day of the handover, 0 when not handed over
    state:register("vassal" .. slot .. "_handed_buildings", 0, "integer") -- buildings of the region at the handover
    state:register("vassal" .. slot .. "_stalled", false, "boolean")    -- the lord built nothing in growth_check_days
    state:register("vassal" .. slot .. "_rebuilding", false, "boolean") -- restored after a wipe; the tribute waits until the village is rebuilt
    state:register("vassal" .. slot .. "_rebuilt_target", 0, "integer") -- standing buildings that end the rebuilding
    state:register("vassal" .. slot .. "_policy", "fair", "string")      -- tribute policy: light, fair or heavy (iteration 03)
end

-- Wiped regions (outside the slots, owner question 5): a sacked vassal keeps no slot, but the player may restore its village.
for index = 1, config.sack_wipe.max_wiped do
    state:register("wiped" .. index .. "_region", rules.NO_REGION, "string")
    state:register("wiped" .. index .. "_lord", rules.NO_REGION, "string")
    state:register("wiped" .. index .. "_day", 0, "integer")
    state:register("wiped" .. index .. "_buildings", 0, "integer") -- buildings of the region at the start of the sack
end

local last_goal = nil        -- the goal as read at the last poll
local polls = 0
local attempts = {}      -- slot -> failed handover attempts of this session
local handover_errors = {} -- slot -> last error text
local war_logged = {}    -- slot -> true once a war was logged
local war_status = {}    -- slot -> last lord status
local goal_error = nil

local function set_if_changed(key, value)
    if state:get(key) ~= value then state:set(key, value) end
end

local function slot_key(slot, name) return "vassal" .. slot .. "_" .. name end

local function slot_regions()
    local regions = {}
    for slot = 1, config.max_vassals do regions[slot] = state:get(slot_key(slot, "region")) end
    return regions
end

---------------------------------------------------------------------------------------------
-- Goal = Endless
---------------------------------------------------------------------------------------------

-- Runs on every poll: a start, a load and a game reset all end with the goal written again.
local function ensure_goal()
    local setup, problem = world.setup_state()
    if setup == nil then goal_error = problem; return end
    goal_error = nil
    last_goal = setup.goals
    if not rules.goal_needs_write(setup.goals, config.goal) then return end
    local answer, why = world.set_goal(config.goal)
    if answer == nil then goal_error = why; return core.log.error(TAG, "VASSALS goal write failed: " .. tostring(why)) end
    state:set("vassals_goal_writes", state:get("vassals_goal_writes") + 1)
    last_goal = answer.after and answer.after.goals
    core.log.info(TAG, string.format("VASSALS goal written %s -> %s", tostring(setup.goals), tostring(last_goal)))
end


---------------------------------------------------------------------------------------------
-- Registry
---------------------------------------------------------------------------------------------

local function slot_row(slot)
    local region = state:get(slot_key(slot, "region"))
    if region == rules.NO_REGION then return nil end
    return { slot = slot, region = region, lord = state:get(slot_key(slot, "lord")),
        since_day = state:get(slot_key(slot, "since_day")),
        handed_day = state:get(slot_key(slot, "handed_day")), stalled = state:get(slot_key(slot, "stalled")), rebuilding = state:get(slot_key(slot, "rebuilding")), policy = state:get(slot_key(slot, "policy")) }
end

local function slot_rows(with_region)
    local rows = {}
    for slot = 1, config.max_vassals do
        local row = slot_row(slot)
        if row and with_region then
            local region = world.region_row(row.region)
            row.owner, row.settled, row.buildings, row.families = region and region.owner, region and region.settled, region and region.buildings, region and region.families
        end
        rows[#rows + 1] = row
    end
    return rows
end

local function register_vassal(region_name)
    local slot = rules.free_slot(slot_regions(), config.max_vassals)
    if slot == nil then return nil, "all " .. config.max_vassals .. " vassal slots are used" end
    state:set(slot_key(slot, "region"), region_name)
    state:set(slot_key(slot, "since_day"), world.current_day() or 0)
    core.log.info(TAG, string.format("VASSALS slot %d registered region=%s", slot, region_name))
    return slot
end

---------------------------------------------------------------------------------------------
-- Claim, settle, handover (iteration 02)
---------------------------------------------------------------------------------------------

local function choose_home(rows)
    local home, most = nil, -1
    for _, row in ipairs(rows) do
        if row.buildings > most then home, most = row.region, row.buildings end
    end
    return home
end

local function lord_name_for(slot)
    return config.lord_names[slot] or ("Vassal" .. slot)
end

local function log_lord_status(name, when)
    local status = world.lord_status(name)
    if status == nil then return core.log.info(TAG, "VASSALS lord " .. name .. " status " .. when .. ": not found") end
    core.log.info(TAG, string.format("VASSALS lord %s status %s: enemy_of_player=%s tags=%s", name, when, tostring(status.enemy_of_player), table.concat(status.tags, ",")))
end

-- Spawn the lord of a slot (when it does not exist) and give it the region.
local function hand_over(slot, region)
    local name = lord_name_for(slot)
    local number = world.lord_number(name)
    if number == nil then
        local spawned, why = world.spawn_lord(name)
        if spawned == nil then return nil, why end
        number = spawned
    end
    log_lord_status(name, "after spawn")
    local answer, why = world.hand_over(number, region)
    if answer == nil then return nil, why end
    log_lord_status(name, "after handover")
    state:set(slot_key(slot, "lord"), name)
    state:set(slot_key(slot, "handed_day"), (world.current_day() or 0) + 1) -- stored as day + 1: 0 means not handed over
    state:set(slot_key(slot, "handed_buildings"), world.region_buildings(region) or 0)
    core.log.info(TAG, string.format("VASSALS handover slot=%d region=%s lord=%s number=%d", slot, region, name, number))
    return number
end

local function try_hand_over(slot, region)
    if (attempts[slot] or 0) >= config.handover_attempts then return end
    local number, why = hand_over(slot, region)
    if number ~= nil then return end
    attempts[slot] = (attempts[slot] or 0) + 1
    handover_errors[tostring(slot)] = why
    core.log.error(TAG, string.format("VASSALS handover failed slot=%d attempt=%d: %s", slot, attempts[slot], tostring(why)))
end

local function scan_regions()
    local rows, problem = world.player_regions()
    if rows == nil then return core.log.warn(TAG, "VASSALS scan skipped: " .. tostring(problem)) end
    if state:get("vassals_home_region") == rules.NO_REGION then
        local home = choose_home(rows)
        if home == nil then return end
        state:set("vassals_home_region", home)
        core.log.info(TAG, "VASSALS home region " .. home)
    end
    local home = state:get("vassals_home_region")
    for _, row in ipairs(rows) do
        if row.region ~= home then
            local slot = rules.slot_of_region(slot_regions(), config.max_vassals, row.region) or register_vassal(row.region)
            if slot ~= nil and row.settled and state:get(slot_key(slot, "lord")) == rules.NO_REGION then try_hand_over(slot, row.region) end
        end
    end
end

local peace_calls = {}      -- slot -> how often the mod declared peace

local function make_peace(slot, number)
    local answer = require("HarnessLords").lord_declare_peace({ lord = number, target = 0 })
    peace_calls[tostring(slot)] = (peace_calls[tostring(slot)] or 0) + 1
    core.log.info(TAG, string.format("VASSALS declarePeace slot=%d ok=%s error=%s", slot, tostring(answer.ok), tostring(answer.error)))
end

-- A vassal lord that declares war on the player is logged once. The state shows the latest status.
local function watch_wars()
    for slot = 1, config.max_vassals do
        local lord = state:get(slot_key(slot, "lord"))
        if lord ~= rules.NO_REGION then
            local status = world.lord_status(lord)
            war_status[tostring(slot)] = status
            if status and (status.enemy_of_player or rules.has_war_tag(status.tags)) and not war_logged[slot] then
                war_logged[slot] = true
                core.log.warn(TAG, string.format("VASSALS lord %s is at war with the player (tags: %s)", lord, table.concat(status.tags, ",")))
            end
            if status and (status.enemy_of_player or rules.has_war_tag(status.tags)) and config.keep_peace then make_peace(slot, status.number) end
        end
    end
end

local growth_checked = {} -- slot -> true once the growth check ran in this session
local detect_losses -- defined in the loss section below
local advance_sacks, check_rebuilt -- defined in the sack section below

-- A handed-over lord can fail to build (3 of 6 real runs: AI_build failed to find place). The mod flags it, so that later features do not count on growth.
local function check_growth()
    local today = world.current_day()
    if today == nil then return end
    for slot = 1, config.max_vassals do
        local handed = state:get(slot_key(slot, "handed_day"))
        if handed > 0 and not state:get(slot_key(slot, "stalled")) and not growth_checked[slot]
            and rules.growth_check_due(handed, today, config.growth_check_days) then
            local now = world.region_buildings(state:get(slot_key(slot, "region")))
            if now ~= nil then
                local before = state:get(slot_key(slot, "handed_buildings"))
                growth_checked[slot] = true
                if rules.is_stalled(before, now, config.growth_min_buildings) then
                    state:set(slot_key(slot, "stalled"), true)
                    core.log.warn(TAG, string.format("VASSALS slot %d stalled: buildings %d -> %d in %d days", slot, before, now, today + 1 - handed))
                else
                    core.log.info(TAG, string.format("VASSALS slot %d grows: buildings %d -> %d", slot, before, now))
                end
            end
        end
    end
end

local function poll()
    if not state.loaded then return end
    ensure_goal()
    polls = polls + 1
    if polls % config.scan_every ~= 0 then return end
    scan_regions()
    watch_wars()
    check_growth()
    detect_losses()
    advance_sacks()
    check_rebuilt()
end

require("scheduler").every(TAG, config.poll_ms, poll)


---------------------------------------------------------------------------------------------
-- Policies (iteration 03). Mod-owned: the game policy system is not used (enactPolicy returned false in 95 tries).
---------------------------------------------------------------------------------------------

local function policy_of(slot)
    return state:get(slot_key(slot, "policy"))
end

local function set_policy(slot, name)
    if config.policies[name] == nil then return nil, "unknown policy " .. tostring(name) end
    if slot_row(slot) == nil then return nil, "slot " .. slot .. " is empty" end
    state:set(slot_key(slot, "policy"), name)
    core.log.info(TAG, string.format("VASSALS policy slot=%d %s", slot, name))
    return true
end


---------------------------------------------------------------------------------------------
-- Loss (iteration 04)
---------------------------------------------------------------------------------------------

local lost_listeners = {}  -- functions called with { slot, region, families, reason } when a vassal is lost
local lost_events = {}     -- the events of this session, for the state command

-- Another feature asks to hear about lost vassals (refugees send a wave).
local function on_lost(listener)
    lost_listeners[#lost_listeners + 1] = listener
end

-- Free the slot and tell the listeners. The families are read first (or passed in), because the wave size depends on them.
local function lose_vassal(slot, reason, families)
    local region = state:get(slot_key(slot, "region"))
    if region == rules.NO_REGION then return nil, "slot " .. slot .. " is empty" end
    local event = { slot = slot, region = region, families = families or world.region_families(region) or 0, reason = reason,
        lord = state:get(slot_key(slot, "lord")), day = world.current_day() }
    state:set(slot_key(slot, "region"), rules.NO_REGION)
    state:set(slot_key(slot, "lord"), rules.NO_REGION)
    state:set(slot_key(slot, "handed_day"), 0)
    state:set(slot_key(slot, "stalled"), false)
    state:set(slot_key(slot, "rebuilding"), false)
    state:set("vassals_lost", state:get("vassals_lost") + 1)
    lost_events[#lost_events + 1] = event
    core.log.info(TAG, string.format("VASSALS lost slot=%d region=%s families=%d reason=%s", slot, region, event.families, reason))
    core.show_banner("A vassal is lost", string.format("%s has fallen", region))
    for _, listener in ipairs(lost_listeners) do core.log.try(TAG, function() listener(event) end) end
    return event
end

-- A handed-over vassal whose region is owned by another pawn than its lord was taken.
detect_losses = function()
    for slot = 1, config.max_vassals do
        local lord = state:get(slot_key(slot, "lord"))
        if lord ~= rules.NO_REGION then
            local status = world.lord_status(lord)
            local owner = world.region_owner(state:get(slot_key(slot, "region")))
            if status and owner and owner ~= status.object then lose_vassal(slot, "taken") end
        end
    end
end

---------------------------------------------------------------------------------------------
-- Sack and wipe (change add-vassal-sack-wipe)
-- A Hussite sack of a vassal collapses its buildings until sack_wipe.ruin_share of the buildings at the start are ruins.
-- Then the mod deletes all villagers, frees the slot (reason `wiped`) and the refugee wave starts. The land stays a village of rubble.
---------------------------------------------------------------------------------------------

local sack_config = config.sack_wipe
local end_sack_without_wipe  -- forward declaration, defined below

local function json_text(map)
    local parts = {}
    for key, value in pairs(map) do parts[#parts + 1] = key .. "=" .. tostring(value) end
    table.sort(parts)
    return "{" .. table.concat(parts, ",") .. "}"
end
local sacks = {}   -- slot -> { region, total, needed, steps, reason }: the sacks of this session (a load ends a running sack)
local sack_errors = {}

local function wiped_regions()
    local regions = {}
    for index = 1, sack_config.max_wiped do regions[index] = state:get("wiped" .. index .. "_region") end
    return regions
end

local function wiped_rows()
    local rows = {}
    for index = 1, sack_config.max_wiped do
        local region = state:get("wiped" .. index .. "_region")
        if region ~= rules.NO_REGION then
            rows[#rows + 1] = { index = index, region = region, lord = state:get("wiped" .. index .. "_lord"),
                day = state:get("wiped" .. index .. "_day"), buildings = state:get("wiped" .. index .. "_buildings") }
        end
    end
    return rows
end

-- The wiped record lives outside the slots (owner question 5, design default): the slot is free for a new vassal.
local function record_wiped(region, lord, buildings)
    local index = rules.free_slot(wiped_regions(), sack_config.max_wiped)
    if index == nil then
        core.log.warn(TAG, "VASSALS no free wiped record for " .. region .. "; it cannot be restored")
        return nil
    end
    state:set("wiped" .. index .. "_region", region)
    state:set("wiped" .. index .. "_lord", lord)
    state:set("wiped" .. index .. "_day", world.current_day() or 0)
    state:set("wiped" .. index .. "_buildings", buildings)
    return index
end

local function wipe_vassal(slot, run)
    local region = state:get(slot_key(slot, "region"))
    local families_before = world.region_families(region) or 0
    local deleted, why = world.delete_villagers(region)
    if deleted == nil then return nil, why end
    record_wiped(region, state:get(slot_key(slot, "lord")), run.total)
    local event = lose_vassal(slot, "wiped", families_before)
    event.people_deleted = deleted.people
    core.log.info(TAG, string.format("VASSALS wiped region=%s ruins needed=%d of %d buildings, villagers deleted families=%d people=%d", region, run.needed, run.total, deleted.families, deleted.people))
    return event
end

-- Wipe the vassal when enough buildings are ruins. Returns done (true when the sack ended), then the event or the error text.
local function wipe_if_complete(slot, run, census)
    if not rules.sack_complete(run.total, census.rubble, sack_config.ruin_share) then return false end
    sacks[slot] = nil
    local event, why = wipe_vassal(slot, run)
    if event == nil then
        sack_errors[tostring(slot)] = why
        core.log.error(TAG, "VASSALS wipe failed: " .. tostring(why))
    end
    return true, event, why
end

-- A sack that ends and does not wipe the village (owner, 2026-10-22): give wood and order the rebuild of every ruin at once.
-- A pcall keeps an error here from stopping the poll.
end_sack_without_wipe = function(run)
    local deposited = world.deposit_goods(run.region, sack_config.give, sack_config.deposit_tries, true) or {}
    local ordered, why = world.rebuild_ruins(run.region)
    core.log.info(TAG, string.format("VASSALS sack ends without wipe region=%s gave=%s ordered=%s", run.region, json_text(deposited), ordered and tostring(ordered.ordered) or tostring(why)))
    return { given = deposited, rebuild = ordered }
end

-- One step of a sack: wipe when enough buildings are ruins, else collapse the missing ones. The wipe waits for the next poll: a wipe in the same tick as the collapses crashed the game in 1 of 2 real runs (20261022-042514-3045).
local function advance_sack(slot)
    local run = sacks[slot]
    local census = world.census(run.region)
    if census == nil then sacks[slot] = nil; return nil, "region " .. run.region .. " not found" end
    local done, event, why = wipe_if_complete(slot, run, census)
    if done then return event, why end
    if run.steps >= sack_config.max_steps then
        sacks[slot] = nil
        sack_errors[tostring(slot)] = string.format("sack gave up after %d steps: %d of %d ruins", run.steps, census.rubble, run.needed)
        core.log.error(TAG, "VASSALS " .. sack_errors[tostring(slot)])
        end_sack_without_wipe(run)
        return nil, sack_errors[tostring(slot)]
    end
    run.steps = run.steps + 1
    local hit = world.collapse_buildings(run.region, rules.houses_to_collapse(run.needed, census.rubble)) or 0
    core.log.info(TAG, string.format("VASSALS sack slot=%d region=%s step=%d collapsed=%d ruins=%d/%d", slot, run.region, run.steps, hit, census.rubble, run.needed))
    return nil
end

local function start_sack(slot, reason)
    local region = state:get(slot_key(slot, "region"))
    if region == rules.NO_REGION then return nil, "slot " .. slot .. " is empty" end
    if sacks[slot] then return nil, "slot " .. slot .. " is already sacked" end
    local census = world.census(region)
    if census == nil then return nil, "region " .. region .. " not found" end
    local wood = world.remove_goods(region, sack_config.wood) or {}
    core.log.info(TAG, "VASSALS sack removes wood region=" .. region .. " " .. json_text(wood))
    sacks[slot] = { region = region, total = census.total, needed = rules.ruins_needed(census.total, sack_config.ruin_share), steps = 0, reason = reason }
    core.log.info(TAG, string.format("VASSALS sack starts slot=%d region=%s buildings=%d ruins needed=%d reason=%s", slot, region, census.total, sacks[slot].needed, reason))
    local event, why = advance_sack(slot)
    return event or { slot = slot, region = region, started = true }, why
end

advance_sacks = function()
    for slot = 1, config.max_vassals do
        if sacks[slot] then core.log.try(TAG, function() advance_sack(slot) end) end
    end
end

---------------------------------------------------------------------------------------------
-- Restore (owner answers 2026-10-21: flat cost; goods for the rebuild)
---------------------------------------------------------------------------------------------

-- A restored village counts as rebuilt when enough buildings stand again. Until then the tribute waits.
check_rebuilt = function()
    for slot = 1, config.max_vassals do
        if state:get(slot_key(slot, "rebuilding")) then
            local census = world.census(state:get(slot_key(slot, "region")))
            if census and (census.built or census.standing) >= state:get(slot_key(slot, "rebuilt_target")) then
                state:set(slot_key(slot, "rebuilding"), false)
                core.log.info(TAG, string.format("VASSALS slot %d rebuilt: %d buildings stand", slot, census.standing))
            end
        end
    end
end

-- Pay the cost, raise the villager count to 5 and spawn the rebuild goods. A refusal takes nothing.
local function restore_vassal(region)
    local index = rules.find_wiped(wiped_regions(), sack_config.max_wiped, region)
    local refusal = rules.restore_refusal(index, rules.free_slot(slot_regions(), config.max_vassals), silver_world.silver(), config.restore.silver)
    if refusal then return nil, refusal end
    local name = state:get("wiped" .. index .. "_region")
    local lord = state:get("wiped" .. index .. "_lord")
    local buildings_before = state:get("wiped" .. index .. "_buildings")
    local handed, hand_why = world.hand_over_to_lord(lord, name)
    if handed == nil then return nil, "the region could not be given to a lord: " .. tostring(hand_why) end
    local settled, why = world.restore_villagers(name)
    if settled == nil then return nil, "the villagers could not be raised: " .. tostring(why) end
    local paid, pay_why = silver_world.add_silver(-config.restore.silver)
    if not paid then error("restore payment failed: " .. tostring(pay_why), 0) end
    local goods = world.deposit_goods(name, config.restore.goods, config.restore.deposit_tries, true) or {}
    for good, amount in pairs(goods) do
        if amount == 0 then core.log.warn(TAG, "VASSALS restore: no building took the goods " .. good) end
    end
    local slot = register_vassal(name)
    state:set(slot_key(slot, "lord"), lord)
    state:set(slot_key(slot, "handed_day"), (world.current_day() or 0) + 1)
    state:set(slot_key(slot, "handed_buildings"), world.region_buildings(name) or 0)
    state:set(slot_key(slot, "rebuilding"), true)
    -- The rebuild is ordered, so the AI builds in the old spots. The tribute waits until rebuilt_share of the old buildings are built.
    local rebuild, rebuild_why = world.rebuild_ruins(name)
    if rebuild == nil then core.log.error(TAG, "VASSALS restore rebuild order failed: " .. tostring(rebuild_why)) end
    state:set(slot_key(slot, "rebuilt_target"), rules.rebuilt_target(buildings_before, config.restore.rebuilt_share))
    state:set("wiped" .. index .. "_region", rules.NO_REGION)
    core.log.info(TAG, string.format("VASSALS restored region=%s slot=%d lord=%s silver paid=%d families=%s", name, slot, lord, config.restore.silver, tostring(settled.families)))
    core.show_banner("A village is restored", string.format("%s has villagers again", name))
    return { region = name, slot = slot, cost = config.restore.silver, goods = goods, families = settled.families, lord = lord, rebuild = rebuild }
end

-- Regions that a subjugation raid may attack: handed-over vassals.
local function target_regions()
    local regions = {}
    for _, row in ipairs(slot_rows()) do
        if row.lord ~= rules.NO_REGION then regions[#regions + 1] = row.region end
    end
    return regions
end

local function command_state()
    local setup = world.setup_state()
    local running = {}
    for slot, run in pairs(sacks) do running[tostring(slot)] = run end
    return {
        day = world.current_day(), goal = last_goal, goal_error = goal_error, goal_writes = state:get("vassals_goal_writes"),
        victory_status = setup and setup.victory_status, count = rules.count_used(slot_regions(), config.max_vassals),
        lost = state:get("vassals_lost"), lost_events = lost_events, vassals = slot_rows(true), home_region = state:get("vassals_home_region"), handover_errors = handover_errors, wars = war_status, peace_calls = peace_calls, keep_peace = config.keep_peace,
        sacks = running, sack_errors = sack_errors, wiped = wiped_rows(), restore_cost = config.restore.silver, silver = silver_world.silver(),
    }
end

local function command_claim(args)
    if rules.slot_of_region(slot_regions(), config.max_vassals, args.region) then return nil, args.region .. " is already a vassal" end
    local row, problem = world.region_row(args.region)
    if row == nil then return nil, problem end
    if row.owner ~= nil then return nil, args.region .. " already has an owner: " .. tostring(row.owner) end
    local claimed, why = world.claim_for_player(args.region)
    if claimed == nil then return nil, why end
    local slot, reason = register_vassal(args.region)
    if slot == nil then return nil, reason end
    local result = command_state()
    result.claimed_slot = slot
    return result
end

local function command_set_keep_peace(args)
    config.keep_peace = args.value
    return command_state()
end

local function command_set_goal(args)
    local answer, why = world.set_goal(args.goal)
    if answer == nil then return nil, why end
    return command_state()
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.vassals_state", command_state, {})
    commands.register("InvasionMod.vassals_claim", command_claim, { region = { type = "string", required = true } })
    commands.register("InvasionMod.vassals_set_keep_peace", command_set_keep_peace, { value = { type = "boolean", required = true } })
    commands.register("InvasionMod.vassals_set_policy", function(args)
        local ok, why = set_policy(args.slot, args.policy)
        if not ok then return nil, why end
        return command_state()
    end, { slot = { type = "integer", required = true, min = 1, max = config.max_vassals }, policy = { type = "string", required = true } })
    commands.register("InvasionMod.vassals_lose", function(args)
        local event, why = lose_vassal(args.slot, "command")
        if not event then return nil, why end
        local result = command_state()
        result.event = event
        return result
    end, { slot = { type = "integer", required = true, min = 1, max = config.max_vassals } })
    commands.register("InvasionMod.vassals_sack", function(args)
        local started, why = start_sack(args.slot, "command")
        if not started then return nil, why end
        local result = command_state()
        result.sack = started
        return result
    end, { slot = { type = "integer", required = true, min = 1, max = config.max_vassals } })
    commands.register("InvasionMod.vassals_end_sack", function(args)
        local run = sacks[args.slot]
        if run == nil then return nil, "slot " .. args.slot .. " has no running sack" end
        sacks[args.slot] = nil
        local ended = end_sack_without_wipe(run)
        local result = command_state()
        result.ended = ended
        return result
    end, { slot = { type = "integer", required = true, min = 1, max = config.max_vassals } })
    commands.register("InvasionMod.vassals_rebuild_ruins", function(args)
        local ordered, why = world.rebuild_ruins(args.region)
        if ordered == nil then return nil, why end
        return ordered
    end, { region = { type = "string", required = true } })
    commands.register("InvasionMod.vassals_restore", function(args)
        local restored, why = restore_vassal(args.region)
        if not restored then return nil, why end
        local result = command_state()
        result.restored = restored
        return result
    end, { region = { type = "string", required = false } })
    commands.register("InvasionMod.vassals_region_census", function(args)
        local census, why = world.census(args.region)
        if census == nil then return nil, why or ("no region " .. args.region) end
        return census
    end, { region = { type = "string", required = true } })
    commands.register("InvasionMod.vassals_set_goal", command_set_goal, { goal = { type = "integer", required = true, min = 0, max = 3 } })
end

core.log.info(TAG, "feature vassals loaded")
return { state = state, on_lost = on_lost, lose_vassal = lose_vassal, start_sack = start_sack, restore_vassal = restore_vassal, policy_of = policy_of, set_policy = set_policy, region_families = world.region_families, target_regions = target_regions, register_vassal = register_vassal, slot_rows = slot_rows, slot_regions = slot_regions }
