-- Feature invasion (M02, iteration 01): the mod owns the raid timer.
-- It plans one minor raid, shows a daily banner with a size estimate, and spawns the raid on the planned day.
-- The plan lives in ModState (M01), so it survives a load. The mod never saves by itself.
local core = require("ManorCore")
local ModState = require("ModState")
local plan_rules = require("features.invasion.plan")
local lord_raid = require("features.invasion.lord_raid")
local all_config = require("config")
local config = all_config.invasion
local roles = config.roles

local TAG = "InvasionMod.invasion"
local MOD = "invasion"
local STATE_VERSION = 1

local state = ModState.open(MOD, "pawn", STATE_VERSION)
state:register("difficulty", config.difficulty, "integer")
state:register("plan_day", 0, "integer")
state:register("raid_day", 0, "integer")
state:register("warning_day", 0, "integer")
state:register("size_class", 0, "integer")
state:register("squads", 0, "integer")
state:register("composition_seed", 0, "integer") -- seed of the template picks; the composition is computed from it (0: none yet)
state:register("raids_spawned", 0, "integer")
state:register("last_banner_day", 0, "integer")

if config.seed then math.randomseed(config.seed) else math.randomseed(os.time()) end

local last_handled_day = nil -- the day of the last daily step in this Lua state
local raid_squads = {} -- { id, template } of the squads of the last raid made by spawnArmy
local use_roles = roles.enabled -- the command invasion_set_roles changes it for one session
local spawn_watchers = {} -- { before, after } pairs from other features (M03 tracks the raid)

---------------------------------------------------------------------------------------------
-- Game reads
---------------------------------------------------------------------------------------------

local function calendar()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if engine == nil or not engine:IsValid() then return nil end
    local ok, value = pcall(function() return engine.TemporalComponent end)
    if ok and value ~= nil and value:IsValid() then return value end
    return nil
end

local function current_day()
    local time = calendar()
    if time == nil then return nil end
    local ok, value = pcall(function() return time.daysTotal end)
    if not ok or type(value) ~= "number" then return nil end
    return math.floor(value)
end

-- The base game timer must never reach 0, or the game starts its own raid. The mod owns the schedule.
local function keep_base_timer_high()
    local time = calendar()
    if time == nil then return end
    local ok, value = pcall(function() return time.daysUntilNextRaid end)
    if ok and type(value) == "number" and value < config.base_timer_floor then
        time.daysUntilNextRaid = config.base_timer_refill
        core.log.info(TAG, string.format("base raid timer was %d, set to %d", value, config.base_timer_refill))
    end
end

local function spawn_centre()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local pawn = engine and engine.playerRef
    if pawn == nil or not pawn:IsValid() then return nil end
    local at = pawn:K2_GetActorLocation()
    return { x = at.X, y = at.Y, z = at.Z }
end

---------------------------------------------------------------------------------------------
-- Plan and daily step
---------------------------------------------------------------------------------------------

-- Only the seed is saved: it is one integer (a string tag crashed the game, see the notes). The list follows from the seed,
-- the squads and the difficulty, so a size or difficulty change gives a new list with the same random picks.
local function ensure_seed()
    if state:get("composition_seed") == 0 then state:set("composition_seed", math.random(1, plan_rules.MAX_SEED)) end
end

local function composition_list()
    ensure_seed()
    return plan_rules.composition(state:get("squads"), state:get("difficulty"), roles, plan_rules.lcg(state:get("composition_seed")))
end

local function planned_units()
    local squads = state:get("squads")
    if not use_roles or squads < 1 then return squads * config.squad_units end
    return plan_rules.expected_units(composition_list(), roles.template_units)
end

local function make_plan(today)
    local plan = plan_rules.first_raid(today, state:get("difficulty"), config, math.random)
    for key, value in pairs(plan) do state:set(key, value) end
    ensure_seed()
    core.log.info(TAG, string.format("INVASION plan day=%d raid_day=%d warning_day=%d size_class=%d squads=%d difficulty=%d composition=%s",
        today, plan.raid_day, plan.warning_day, plan.size_class, plan.squads, state:get("difficulty"), plan_rules.join(composition_list())))
end

local function spawn_raid(today)
    local squads = state:get("squads")
    local centre = spawn_centre()
    if centre == nil then return core.log.error(TAG, "no player pawn: the raid is not spawned") end
    local tokens = {}
    for index, watcher in ipairs(spawn_watchers) do tokens[index] = watcher.before() end
    local ok, problem
    local lord_info = nil
    if use_roles then
        local list = composition_list()
        raid_squads = {}
        if roles.lord_army.enabled then
            local partial
            ok, problem, partial = lord_raid.start(list, roles.lord_army)
            if ok then
                raid_squads, lord_info = problem.squads, problem
            elseif partial then
                -- Armies exist already. Bandit squads on top would make a double raid. The next daily step tries again.
                return core.log.error(TAG, "lord raid failed after a partial spawn, no fallback squads: " .. tostring(problem))
            else
                core.log.error(TAG, "lord raid failed, the squads are bandit squads: " .. tostring(problem))
            end
        end
        if not ok then
            local ids
            ok, ids = core.spawn_squads(list, { x = centre.x, y = roles.raid_spawn_y, z = centre.z })
            problem = ids
            if ok then
                for index, name in ipairs(list) do raid_squads[index] = { id = ids[index] or false, template = name } end
            end
        end
    else
        ok, problem = core.spawn_raiders(squads, centre)
    end
    if not ok then return core.log.error(TAG, "raid spawn failed: " .. tostring(problem)) end
    state:set("raids_spawned", state:get("raids_spawned") + 1)
    for index, watcher in ipairs(spawn_watchers) do
        core.log.try(TAG, watcher.after, tokens[index], { day = today, squads = squads, roles = use_roles, lord_raid = lord_info })
    end
    core.log.info(TAG, string.format("INVASION spawn day=%d planned_day=%d squads=%d raiders=%d composition=%s roles=%s",
        today, state:get("raid_day"), squads, planned_units(), plan_rules.join(composition_list()), tostring(use_roles)))
    core.show_banner("Raiders are here", string.format("About %d raiders", planned_units()))
end

local function show_countdown(today, days_left)
    local text = plan_rules.banner_text(days_left, planned_units())
    local ok, problem = core.show_banner(text, "")
    state:set("last_banner_day", today)
    core.log.info(TAG, string.format("INVASION banner day=%d days_left=%d raiders=%d shown=%s%s", today, days_left,
        planned_units(), tostring(ok), ok and "" or (" problem=" .. tostring(problem))))
end

local function daily_step(today)
    if state:get("raids_spawned") > 0 then return end
    if state:get("raid_day") == 0 then make_plan(today) end
    local days_left = state:get("raid_day") - today
    if days_left <= 0 then return spawn_raid(today) end
    if today >= state:get("warning_day") and state:get("last_banner_day") ~= today then show_countdown(today, days_left) end
end

local function tick()
    if not state.loaded then return end
    local today = current_day()
    if today == nil then return end
    keep_base_timer_high()
    if today == last_handled_day then return end
    last_handled_day = today
    daily_step(today)
end

require("scheduler").every(TAG, config.poll_ms, tick)

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local has_commands, commands = pcall(require, "HarnessCommands")

local function replan_size()
    if state:get("raid_day") == 0 or state:get("raids_spawned") > 0 then return end
    state:set("squads", plan_rules.squads(state:get("size_class"), state:get("difficulty"), config.size_multipliers))
end

local function command_state()
    local today = current_day()
    local raid_day = state:get("raid_day")
    local squads = state:get("squads")
    return {
        day = today, difficulty = state:get("difficulty"), plan_day = state:get("plan_day"), raid_day = raid_day,
        warning_day = state:get("warning_day"), size_class = state:get("size_class"), squads = squads,
        raiders = planned_units(), composition = (use_roles and state:get("squads") > 0) and plan_rules.join(composition_list()) or "none", roles = use_roles, days_left = (today and raid_day > 0) and (raid_day - today) or nil,
        raids_spawned = state:get("raids_spawned"), last_banner_day = state:get("last_banner_day"),
    }
end

local function command_force_next()
    local today = current_day()
    if today == nil then return nil, "the game day is not available" end
    if state:get("raids_spawned") > 0 then return nil, "the raid was spawned already" end
    if state:get("raid_day") == 0 then make_plan(today) end
    state:set("raid_day", today)
    last_handled_day = nil
    return command_state()
end

local function command_set_difficulty(args)
    state:set("difficulty", args.value)
    replan_size()
    return command_state()
end

local function command_set_size(args)
    local class = plan_rules.SIZE_CLASSES[args.size]
    if state:get("raid_day") == 0 then return nil, "no raid is planned yet" end
    if state:get("raids_spawned") > 0 then return nil, "the raid was spawned already" end
    state:set("size_class", class)
    replan_size()
    return command_state()
end

-- The squads of the last raid with the units now alive and their mean stats. The scenario compares them with the plan.
-- Few reads on purpose (M03 crashed the game with many reads): stats are read only for units of the raid squads.
local STAT_NAMES = { "att", "def", "armorPierce" }

local function command_raid_squads()
    local wanted = {}
    for _, squad in ipairs(raid_squads) do
        if squad.id then wanted[squad.id] = true end
    end
    local by_id = {}
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if core.isValid(unit) then
            local id = core.read(function() return unit.assignedSquadID.Value end)
            if id ~= nil and wanted[id] and core.read(function() return unit.dead end) ~= true then
                local row = by_id[id] or { alive = 0, sum = {} }
                by_id[id] = row
                row.alive = row.alive + 1
                for _, name in ipairs(STAT_NAMES) do
                    row.sum[name] = (row.sum[name] or 0) + (core.read(function() return unit[name] end) or 0)
                end
            end
        end
    end
    local rows = {}
    for _, squad in ipairs(raid_squads) do
        local seen = squad.id and by_id[squad.id]
        local mean = {}
        for _, name in ipairs(STAT_NAMES) do mean[name] = seen and seen.sum[name] / seen.alive or 0 end
        rows[#rows + 1] = { id = squad.id, template = squad.template, alive = seen and seen.alive or 0, mean = mean }
    end
    return { squads = rows }
end

-- Switch the Hussite roles for this session (not saved). Off: the raid uses spawnRaiders.
local function command_set_roles(args)
    use_roles = args.enabled
    return command_state()
end

if has_commands then
    commands.register("InvasionMod.invasion_raid_squads", command_raid_squads, {})
    commands.register("InvasionMod.invasion_set_roles", command_set_roles, { enabled = { type = "boolean", required = true } })
    commands.register("InvasionMod.invasion_state", command_state, {})
    commands.register("InvasionMod.invasion_force_next", command_force_next, {})
    commands.register("InvasionMod.invasion_set_difficulty", command_set_difficulty, { value = { type = "integer", required = true, min = 1, max = 3 } })
    commands.register("InvasionMod.invasion_set_size", command_set_size, { size = { type = "string", required = true, oneOf = { "small", "medium", "large" } } })
end

core.log.info(TAG, "feature invasion loaded")
-- Another feature registers two functions: before() runs just before the spawn call and returns a token,
-- after(token, { day, squads }) runs just after it.
local function watch_spawn(before, after)
    spawn_watchers[#spawn_watchers + 1] = { before = before, after = after }
end

return { state = state, watch_spawn = watch_spawn }
