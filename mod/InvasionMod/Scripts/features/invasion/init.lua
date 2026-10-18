-- Feature invasion (M02, iteration 01): the mod owns the raid timer.
-- It plans one minor raid, shows a daily banner with a size estimate, and spawns the raid on the planned day.
-- The plan lives in ModState (M01), so it survives a load. The mod never saves by itself.
local core = require("ManorCore")
local ModState = require("ModState")
local plan_rules = require("features.invasion.plan")
local great_raid = require("features.invasion.great_raid")
local difficulty_rules = require("features.invasion.difficulty")
local target_rules = require("features.invasion.target")
local lord_raid = require("features.invasion.lord_raid")
local all_config = require("config")
local config = all_config.invasion
local clock_config = config.great_raid
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
state:register("sub_day", 0, "integer")         -- subjugation raid: planned day (0: not planned)
state:register("sub_warning_day", 0, "integer")
state:register("sub_squads", 0, "integer")
state:register("sub_seed", 0, "integer")
state:register("sub_spawned", 0, "integer")
state:register("difficulty_chosen", 0, "integer") -- 1 after the player picked the difficulty
state:register("last_prompt_day", 0, "integer")
state:register("great_raid_day", 0, "integer") -- absolute game day when the great raid starts (0: the clock has not started)
state:register("last_clock_banner_day", 0, "integer")

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
-- A raid kind ("plunder" or "subjugation") keeps its own squads and seed in ModState.
local KEYS = {
    plunder = { squads = "squads", seed = "composition_seed" },
    subjugation = { squads = "sub_squads", seed = "sub_seed" },
}

local function ensure_seed(kind)
    local key = KEYS[kind or "plunder"].seed
    if state:get(key) == 0 then state:set(key, math.random(1, plan_rules.MAX_SEED)) end
end

local function composition_list(kind)
    kind = kind or "plunder"
    ensure_seed(kind)
    return plan_rules.composition(state:get(KEYS[kind].squads), state:get("difficulty"), roles, plan_rules.lcg(state:get(KEYS[kind].seed)))
end

local function planned_units(kind)
    local squads = state:get(KEYS[kind or "plunder"].squads)
    if not use_roles or squads < 1 then return squads * config.squad_units end
    return plan_rules.expected_units(composition_list(kind), roles.template_units)
end

local function make_plan(today)
    local plan = plan_rules.first_raid(today, state:get("difficulty"), config, math.random)
    for key, value in pairs(plan) do state:set(key, value) end
    ensure_seed()
    core.log.info(TAG, string.format("INVASION plan day=%d raid_day=%d warning_day=%d size_class=%d squads=%d difficulty=%d composition=%s",
        today, plan.raid_day, plan.warning_day, plan.size_class, plan.squads, state:get("difficulty"), plan_rules.join(composition_list())))
end

local function spawn_raid(today, kind)
    kind = kind or "plunder"
    local squads = state:get(KEYS[kind].squads)
    local centre = spawn_centre()
    if centre == nil then return core.log.error(TAG, "no player pawn: the raid is not spawned") end
    local tokens = {}
    for index, watcher in ipairs(spawn_watchers) do tokens[index] = watcher.before() end
    local ok, problem
    local lord_info = nil
    if use_roles then
        local list = composition_list(kind)
        raid_squads = {}
        if roles.lord_army.enabled then
            ok, problem = lord_raid.start(list, roles.lord_army)
            if ok then
                raid_squads, lord_info = problem.squads, problem
                lord_info.kind = kind
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
    if kind == "subjugation" then state:set("sub_spawned", 1) end
    local home = core.player_region()
    local target = target_rules.pick(kind, home and core.region_row(home).region or "home", {}, math.random) -- vassal targets: TBD for M07
    for index, watcher in ipairs(spawn_watchers) do
        core.log.try(TAG, watcher.after, tokens[index], { day = today, squads = squads, roles = use_roles, lord_raid = lord_info, kind = kind, target = target })
    end
    local planned_day = kind == "subjugation" and state:get("sub_day") or state:get("raid_day")
    core.log.info(TAG, string.format("INVASION spawn day=%d planned_day=%d squads=%d raiders=%d composition=%s roles=%s kind=%s target=%s stand_in=%s",
        today, planned_day, squads, planned_units(kind), plan_rules.join(composition_list(kind)), tostring(use_roles), kind, tostring(target.region), tostring(target.stand_in)))
    core.show_banner(kind == "subjugation" and "The subjugation raid is here" or "Raiders are here", string.format("About %d raiders", planned_units(kind)))
end

local function clock_days_left(today)
    return great_raid.days_left(state:get("great_raid_day"), today)
end

local function start_clock(today)
    local length = great_raid.length(clock_config, math.random)
    state:set("great_raid_day", today + length)
    core.log.info(TAG, string.format("INVASION clock start day=%d end_day=%d length=%d", today, today + length, length))
end

local function show_clock_banner(today)
    local days_left = clock_days_left(today)
    local ok, problem = core.show_banner(great_raid.text(days_left), "")
    state:set("last_clock_banner_day", today)
    core.log.info(TAG, string.format("INVASION clock banner day=%d days_left=%d shown=%s%s", today, days_left, tostring(ok), ok and "" or (" problem=" .. tostring(problem))))
end

local function show_countdown(today, days_left)
    local text = plan_rules.banner_text(days_left, planned_units())
    local ok, problem = core.show_banner(text, great_raid.text(clock_days_left(today)))
    state:set("last_clock_banner_day", today)
    state:set("last_banner_day", today)
    core.log.info(TAG, string.format("INVASION banner day=%d days_left=%d raiders=%d shown=%s%s", today, days_left,
        planned_units(), tostring(ok), ok and "" or (" problem=" .. tostring(problem))))
end

local function minor_raid_step(today)
    if state:get("raids_spawned") > 0 then return end
    if state:get("raid_day") == 0 then make_plan(today) end
    local days_left = state:get("raid_day") - today
    if days_left <= 0 then return spawn_raid(today) end
    if today >= state:get("warning_day") and state:get("last_banner_day") ~= today then show_countdown(today, days_left) end
end

local function make_subjugation_plan(today)
    local sub = config.subjugation
    local wait = plan_rules.pick(math.random, sub.wait_days_min, sub.wait_days_max)
    local warning = math.min(plan_rules.pick(math.random, config.warning_days_min, config.warning_days_max), wait)
    state:set("sub_day", today + wait)
    state:set("sub_warning_day", today + wait - warning)
    state:set("sub_squads", plan_rules.squads(sub.size_class, state:get("difficulty"), config.size_multipliers))
    ensure_seed("subjugation")
    core.log.info(TAG, string.format("INVASION subjugation plan day=%d sub_day=%d warning_day=%d squads=%d composition=%s", today,
        today + wait, today + wait - warning, state:get("sub_squads"), plan_rules.join(composition_list("subjugation"))))
end

local function show_subjugation_countdown(today, days_left)
    local text = "Subjugation " .. plan_rules.banner_text(days_left, planned_units("subjugation")):lower()
    local ok = core.show_banner(text, great_raid.text(clock_days_left(today)))
    state:set("last_clock_banner_day", today)
    state:set("last_banner_day", today)
    core.log.info(TAG, string.format("INVASION subjugation banner day=%d days_left=%d raiders=%d shown=%s", today, days_left, planned_units("subjugation"), tostring(ok)))
end

-- The subjugation raid comes after the first (plunder) raid. It is a major raid on a vassal region (stand-in: the home region).
local function subjugation_step(today)
    if not config.subjugation.enabled or state:get("raids_spawned") < 1 or state:get("sub_spawned") == 1 then return end
    if state:get("sub_day") == 0 then make_subjugation_plan(today) end
    local days_left = state:get("sub_day") - today
    if days_left <= 0 then return spawn_raid(today, "subjugation") end
    if today >= state:get("sub_warning_day") and state:get("last_banner_day") ~= today then show_subjugation_countdown(today, days_left) end
end

local function clock_step(today)
    if state:get("great_raid_day") == 0 then start_clock(today) end
    local due = state:get("last_clock_banner_day") + clock_config.banner_every_days <= today
    if due and not great_raid.is_due(state:get("great_raid_day"), today) then show_clock_banner(today) end
end

local function prompt_step(today)
    if state:get("difficulty_chosen") == 1 then return end
    if state:get("last_prompt_day") ~= 0 and today - state:get("last_prompt_day") < clock_config.prompt_every_days then return end
    state:set("last_prompt_day", today)
    local ok = core.show_banner("Pick the difficulty: 1, 2 or 3", string.format("Now %d. Use the command invasion_pick_difficulty", state:get("difficulty")))
    core.log.info(TAG, string.format("INVASION difficulty prompt day=%d current=%d shown=%s", today, state:get("difficulty"), tostring(ok)))
end

local function daily_step(today)
    prompt_step(today)
    minor_raid_step(today)
    subjugation_step(today)
    clock_step(today)
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

local function command_clock_state()
    local today = current_day()
    local end_day = state:get("great_raid_day")
    return { day = today, great_raid_day = end_day, days_left = (today and end_day > 0) and clock_days_left(today) or nil,
        last_clock_banner_day = state:get("last_clock_banner_day") }
end

-- For tests: move the end of the clock so that `days` game days remain.
local function command_clock_set_days_left(args)
    local today = current_day()
    if today == nil then return nil, "the game day is not available" end
    state:set("great_raid_day", today + args.days)
    return command_clock_state()
end

local function command_subjugation_state()
    local today = current_day()
    local sub_day = state:get("sub_day")
    return { day = today, sub_day = sub_day, warning_day = state:get("sub_warning_day"), squads = state:get("sub_squads"),
        raiders = planned_units("subjugation"), spawned = state:get("sub_spawned") == 1, days_left = (today and sub_day > 0) and (sub_day - today) or nil,
        composition = state:get("sub_squads") > 0 and plan_rules.join(composition_list("subjugation")) or "none" }
end

-- For tests: the subjugation raid spawns on the next check (it must be planned already).
local function command_subjugation_force_next()
    local today = current_day()
    if today == nil then return nil, "the game day is not available" end
    if state:get("sub_spawned") == 1 then return nil, "the subjugation raid was spawned already" end
    if state:get("sub_day") == 0 then return nil, "the subjugation raid is not planned yet" end
    state:set("sub_day", today)
    last_handled_day = nil
    return command_subjugation_state()
end

local function command_difficulty_state()
    local difficulty = state:get("difficulty")
    return { difficulty = difficulty, chosen = state:get("difficulty_chosen") == 1,
        relief_squads = difficulty_rules.relief_squads(difficulty, clock_config.relief_full_squads),
        waves = difficulty_rules.wave_count(difficulty), wave_squads = clock_config.wave_squads }
end

local function command_pick_difficulty(args)
    if state:get("difficulty_chosen") == 1 then return nil, "the difficulty was picked already" end
    if state:get("raids_spawned") > 0 then return nil, "the first raid was spawned already" end
    if not difficulty_rules.valid(args.value) then return nil, "difficulty must be 1 to 3" end
    state:set("difficulty", args.value)
    state:set("difficulty_chosen", 1)
    replan_size()
    core.log.info(TAG, "INVASION difficulty picked " .. args.value)
    return command_difficulty_state()
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
    commands.register("InvasionMod.invasion_subjugation_state", command_subjugation_state, {})
    commands.register("InvasionMod.invasion_subjugation_force_next", command_subjugation_force_next, {})
    commands.register("InvasionMod.invasion_difficulty_state", command_difficulty_state, {})
    commands.register("InvasionMod.invasion_pick_difficulty", command_pick_difficulty, { value = { type = "integer", required = true, min = 1, max = 3 } })
    commands.register("InvasionMod.invasion_clock_state", command_clock_state, {})
    commands.register("InvasionMod.invasion_clock_set_days_left", command_clock_set_days_left, { days = { type = "integer", required = true, min = 1, max = 2000 } })
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
