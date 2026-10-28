-- Feature invasion (M02, iteration 01): the mod owns the raid timer.
-- It plans one minor raid, shows a daily banner with a size estimate, and spawns the raid on the planned day.
-- The plan lives in ModState (M01), so it survives a load. The mod never saves by itself.
local core = require("ManorCore")
local ModState = require("ModState")
local plan_rules = require("features.invasion.plan")
local great_raid = require("features.invasion.great_raid")
local difficulty_rules = require("features.invasion.difficulty")
local target_rules = require("features.invasion.target")
local relief = require("features.invasion.relief")
local lord_raid = require("features.invasion.lord_raid")
local all_config = require("config")
local config = all_config.invasion
local clock_config = config.great_raid
local roles = config.roles

local TAG = "InvasionMod.invasion"
local MOD = "invasion"
local STATE_VERSION = 1

local state = ModState.open(MOD, "pawn", STATE_VERSION)
-- update-raid-difficulty-levels (#404): one level for each raid type, 0 (off) to 3 (hard). An old save has no levels and gets the defaults.
state:register("level_yearly", config.levels.yearly, "integer")
state:register("level_great", config.levels.great, "integer")
state:register("level_vassal", config.levels.vassal, "integer")
state:register("plan_day", 0, "integer")
state:register("raid_day", 0, "integer")
state:register("size_class", 0, "integer")
state:register("squads", 0, "integer")
state:register("composition_seed", 0, "integer") -- seed of the template picks; the composition is computed from it (0: none yet)
state:register("raids_spawned", 0, "integer")
state:register("sub_day", 0, "integer")         -- subjugation raid: planned day (0: not planned)
state:register("sub_squads", 0, "integer")
state:register("sub_seed", 0, "integer")
state:register("sub_spawned", 0, "integer")
state:register("gr_phase", 0, "integer")       -- great raid phase, see great_raid.PHASE
state:register("gr_wave", 0, "integer")
state:register("gr_last_day", 0, "integer")
state:register("gr_seed", 0, "integer")
state:register("difficulty_chosen", 0, "integer") -- 1 after the player picked the difficulty
state:register("great_raid_day", 0, "integer") -- absolute game day when the great raid starts (0: the clock has not started)
state:register("last_clock_banner_year", 0, "integer") -- the game year of the last great raid clock banner (a load does not repeat it)
state:register("plunder_banner", 0, "integer")  -- 1 after the 30 day banner of the current plunder plan showed
state:register("sub_banner", 0, "integer")      -- 1 after the 30 day banner of the subjugation plan showed
state:register("plunder_spawned", 0, "integer")   -- 1 after the current plunder plan spawned
state:register("yearly_season_no", -1, "integer") -- season changes since the mod started (-1: no season seen yet)
state:register("yearly_last_season", -1, "integer")
state:register("yearly_done_year", 0, "integer")  -- the last game year in which a raid was planned
-- add-scenario-settings-menu: the player settings. The registered values keep the old behaviour; the settings menu (or an old save) writes the config defaults.
state:register("first_raid_years", 1, "integer")  -- years before the season roll may bring the first raid (the roll starts in year N+1)
state:register("size_class_fixed", 0, "integer")  -- 0: random size class, 1 to 3: fixed
state:register("settings_applied", 0, "integer")  -- 1 after the settings menu closed (or an old save got the defaults)

if config.seed then math.randomseed(config.seed) else math.randomseed(os.time()) end

local last_handled_day = nil -- the day of the last daily step in this Lua state
local raid_direction = nil -- the border point of the last great army (for its banner)
local raid_squads = {} -- { id, template } of the squads of the last raid made by spawnArmy
local use_roles = roles.enabled -- the command invasion_set_roles changes it for one session
local vassal_provider = function() return {} end -- returns the target regions of the vassals (M08 registers it)
local spawn_watchers = {} -- { before, after } pairs from other features (M03 tracks the raid)
local hold_gate = function() return false end -- the scenario settings feature sets it (a new game waits for the settings menu)

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

local function current_season()
    local time = calendar()
    if time == nil then return nil end
    local ok, value = pcall(function() return time.Season end)
    if not ok or type(value) ~= "number" then return nil end
    return math.floor(value)
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

-- The level of a raid type: "yearly", "great" or "vassal".
local function level(kind)
    return state:get("level_" .. kind)
end

-- The plunder raid follows the yearly level, the subjugation raid the vassal level.
local LEVEL_OF_KIND = { plunder = "yearly", subjugation = "vassal" }

local function kind_level(kind)
    return level(LEVEL_OF_KIND[kind or "plunder"])
end

-- The number for the features that are not tied to one raid type (bandits, sack, terms, fallback).
local function general_difficulty()
    return difficulty_rules.general({ yearly = level("yearly"), great = level("great"), vassal = level("vassal") })
end

local function ensure_seed(kind)
    local key = KEYS[kind or "plunder"].seed
    if state:get(key) == 0 then state:set(key, math.random(1, plan_rules.MAX_SEED)) end
end

local function composition_list(kind)
    kind = kind or "plunder"
    ensure_seed(kind)
    return plan_rules.composition(state:get(KEYS[kind].squads), math.max(kind_level(kind), difficulty_rules.MIN), roles, plan_rules.lcg(state:get(KEYS[kind].seed)))
end

local function planned_units(kind)
    local squads = state:get(KEYS[kind or "plunder"].squads)
    if not use_roles or squads < 1 then return squads * config.squad_units end
    return plan_rules.expected_units(composition_list(kind), roles.template_units)
end

-- The player may fix the size class of the plunder raid (scenario settings). 0: random, as before.
local function size_class_for_plan()
    local fixed = state:get("size_class_fixed")
    if fixed >= 1 then return fixed end
    return plan_rules.pick(math.random, 1, #plan_rules.SIZE_NAMES)
end

local function make_plan(today)
    if level("yearly") == 0 then return core.log.info(TAG, "INVASION yearly level is 0: no raid planned") end
    local plan = plan_rules.yearly_raid(today, size_class_for_plan(), level("yearly"), config, math.random)
    for key, value in pairs(plan) do state:set(key, value) end
    state:set("plunder_spawned", 0)
    state:set("plunder_banner", 0)
    state:set("composition_seed", 0) -- a new plan gets a new composition
    ensure_seed()
    core.log.info(TAG, string.format("INVASION plan day=%d raid_day=%d size_class=%d squads=%d level=%d composition=%s",
        today, plan.raid_day, plan.size_class, plan.squads, level("yearly"), plan_rules.join(composition_list())))
end

local function make_subjugation_plan(today)
    if level("vassal") == 0 then return core.log.info(TAG, "INVASION vassal level is 0: no subjugation raid planned") end
    local plan = plan_rules.yearly_raid(today, config.subjugation.size_class, level("vassal"), config, math.random)
    state:set("sub_day", plan.raid_day)
    state:set("sub_squads", plan.squads)
    state:set("sub_banner", 0)
    ensure_seed("subjugation")
    core.log.info(TAG, string.format("INVASION subjugation plan day=%d sub_day=%d squads=%d composition=%s", today,
        plan.raid_day, plan.squads, plan_rules.join(composition_list("subjugation"))))
end

-- The kind rules: the first raid is a plunder raid, the second a subjugation raid (once), later raids are plunder raids.
local function next_kind()
    if config.subjugation.enabled and level("vassal") > 0 and state:get("plunder_spawned") == 1 and state:get("sub_spawned") == 0 then return "subjugation" end
    return "plunder"
end

-- The target of a raid. A subjugation raid picks its vassal from the saved seed, so the banner and the spawn name the same one.
local function raid_target(kind)
    local home = core.player_region()
    local random = kind == "subjugation" and plan_rules.lcg(state:get("sub_seed") + 777) or math.random
    return target_rules.pick(kind, home and core.region_row(home).region or "home", vassal_provider(), random)
end

-- The border point of a new army (change update-spawn-from-map-border), or nil when the map edge cannot be read:
-- then the army starts near the manor as before and the log says so.
local function border_point(label)
    local point, why = lord_raid.plan_border(config.border)
    if point == nil then
        core.log.error(TAG, string.format("INVASION %s has no border point (%s): the army starts near the manor", label, tostring(why)))
        return nil
    end
    core.log.info(TAG, string.format("INVASION %s border side=%s at=%d,%d distance=%d direction=%s", label, point.side, math.floor(point.x + 0.5), math.floor(point.y + 0.5), math.floor(point.distance + 0.5), point.direction))
    return point
end

-- The notice of a coming army: the direction of the border point seen from the manor.
local function approach_text(point)
    return point and (" from the " .. point.direction) or ""
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
    local point = nil
    if use_roles then
        local list = composition_list(kind)
        raid_squads = {}
        if roles.lord_army.enabled then
            local partial
            point = border_point(kind)
            ok, problem, partial = lord_raid.start(list, roles.lord_army, point)
            if ok then
                raid_squads, lord_info = problem.squads, problem
                lord_info.kind = kind
                lord_info.marching = point ~= nil
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
    if kind == "subjugation" then state:set("sub_spawned", 1) else state:set("plunder_spawned", 1) end
    local target = raid_target(kind)
    for index, watcher in ipairs(spawn_watchers) do
        core.log.try(TAG, watcher.after, tokens[index], { day = today, squads = squads, roles = use_roles, lord_raid = lord_info, kind = kind, target = target })
    end
    local planned_day = kind == "subjugation" and state:get("sub_day") or state:get("raid_day")
    core.log.info(TAG, string.format("INVASION spawn day=%d planned_day=%d squads=%d raiders=%d composition=%s roles=%s kind=%s target=%s stand_in=%s",
        today, planned_day, squads, planned_units(kind), plan_rules.join(composition_list(kind)), tostring(use_roles), kind, tostring(target.region), tostring(target.stand_in)))
    if point ~= nil and lord_info ~= nil then
        local title = (kind == "subjugation" and "The subjugation raid approaches" or "Raiders approach") .. approach_text(point)
        core.log.info(TAG, "INVASION approach banner: " .. title)
        core.show_banner(title, string.format("About %d raiders. They arrive in a few days", planned_units(kind)))
    else
        core.show_banner(kind == "subjugation" and "The subjugation raid is here" or "Raiders are here", string.format("About %d raiders", planned_units(kind)))
    end
end

-- One army group of the great raid (a wave or the final army): a lord army of the template list, watched like a raid.
-- Returns true, or false and a message. No fallback squads: a retry on the next daily step is better than a double raid.
local function spawn_great_army(today, list, label, final)
    local tokens = {}
    for index, watcher in ipairs(spawn_watchers) do tokens[index] = watcher.before() end
    local point = border_point("great " .. label)
    local ok, problem, partial = lord_raid.start(list, roles.lord_army, point)
    if not ok then
        -- Armies exist already (a partial spawn): bandit squads on top would make a double army. The caller must not retry.
        if partial then return false, tostring(problem), true end
        core.log.error(TAG, "great raid lord army failed, the squads are bandit squads: " .. tostring(problem))
        local centre = spawn_centre()
        local spawned, ids = core.spawn_squads(list, { x = centre.x, y = roles.raid_spawn_y, z = centre.z })
        if not spawned then return false, tostring(ids) end
        local squads = {}
        for index, name in ipairs(list) do squads[index] = { id = ids[index] or false, template = name } end
        problem = { squads = squads, anchor = { x = centre.x, y = centre.y }, fallback = true }
    end
    problem.kind = "great"
    problem.final = final == true
    problem.marching = point ~= nil and not problem.fallback
    problem.direction = point and point.direction or nil
    raid_squads = problem.squads
    raid_direction = point
    state:set("raids_spawned", state:get("raids_spawned") + 1)
    for index, watcher in ipairs(spawn_watchers) do
        core.log.try(TAG, watcher.after, tokens[index], { day = today, squads = #list, roles = true, lord_raid = problem, kind = "great" })
    end
    core.log.info(TAG, string.format("INVASION great %s day=%d squads=%d raiders=%d composition=%s", label, today, #list,
        plan_rules.expected_units(list, roles.template_units), plan_rules.join(list)))
    return true
end

local function great_wave_list()
    if state:get("gr_seed") == 0 then state:set("gr_seed", math.random(1, plan_rules.MAX_SEED)) end
    local seed = state:get("gr_seed") + state:get("gr_wave") + 1
    return plan_rules.composition(clock_config.wave_squads, math.max(level("great"), difficulty_rules.MIN), roles, plan_rules.lcg(seed))
end

local function spawn_great_wave(today)
    local wave = state:get("gr_wave") + 1
    local ok, problem, partial = spawn_great_army(today, great_wave_list(), "wave " .. wave, false)
    if not ok and not partial then return core.log.error(TAG, "great raid wave failed, the next daily step tries again: " .. problem) end
    if not ok then core.log.error(TAG, "great raid wave failed after a partial spawn, the wave counts as spawned: " .. problem) end
    state:set("gr_wave", wave)
    state:set("gr_last_day", today)
    state:set("gr_phase", great_raid.PHASE.waves)
    core.show_banner(string.format("Great raid: wave %d of %d%s", wave, difficulty_rules.wave_count(level("great")), approach_text(raid_direction)),
        "Hold the village until the relief army comes")
end

local function spawn_relief_and_final(today)
    local count = difficulty_rules.relief_squads(level("great"), clock_config.relief_full_squads)
    local centre = spawn_centre()
    if centre == nil then return core.log.error(TAG, "no player pawn: the relief army is not spawned") end
    local final_list = plan_rules.composition(clock_config.final_squads, clock_config.final_tier_difficulty, roles,
        plan_rules.lcg(state:get("gr_seed") + 1000))
    local ok, problem, partial = spawn_great_army(today, final_list, "final", true)
    if not ok and not partial then return core.log.error(TAG, "great raid final army failed, the next daily step tries again: " .. problem) end
    if not ok then core.log.error(TAG, "great raid final army failed after a partial spawn, no retry: " .. problem) end
    state:set("gr_phase", great_raid.PHASE.final)
    local spot = { x = centre.x + clock_config.relief_offset.x, y = centre.y + clock_config.relief_offset.y, z = centre.z }
    local sent, why = relief.spawn(great_raid.relief_templates(count, clock_config.relief_templates), spot)
    core.log.info(TAG, string.format("INVASION great relief day=%d squads=%d spawned=%s%s", today, count, tostring(sent), sent and "" or (" problem=" .. tostring(why))))
    core.show_banner("The relief army has come", string.format("%d squads of the liege. The final army approaches%s", count, approach_text(raid_direction)))
end

local function check_great_win(today)
    local ok, behavior = pcall(require, "features.raid_behavior.init")
    if not ok or behavior.final_raid_ended == nil then return end
    if behavior.final_raid_ended() ~= true then return end
    state:set("gr_phase", great_raid.PHASE.won)
    core.log.info(TAG, string.format("INVASION great won day=%d", today))
    core.show_banner("The great raid is beaten", "The village stands")
end

local function great_step(today)
    local phase = state:get("gr_phase")
    if phase == great_raid.PHASE.won then return end
    if phase == great_raid.PHASE.final then return check_great_win(today) end
    local action = great_raid.next_action({ phase = phase, wave = state:get("gr_wave"), waves = difficulty_rules.wave_count(level("great")),
        last_day = state:get("gr_last_day"), today = today, due = great_raid.is_due(state:get("great_raid_day"), today) }, clock_config)
    if action == "wave" then spawn_great_wave(today) elseif action == "relief" then spawn_relief_and_final(today) end
end

local function clock_days_left(today)
    return great_raid.days_left(state:get("great_raid_day"), today)
end

-- The game year of the yearly rule: 4 season changes make one year (year 1 is the first year the mod saw).
local function current_year()
    return (plan_rules.season_year(math.max(state:get("yearly_season_no"), 0)))
end

-- The clock ends at the first day of game year `great_raid.start_year`. The day is an estimate until that year begins.
local function start_clock(today)
    local seasons_done = math.max(state:get("yearly_season_no"), 0)
    local end_day = great_raid.estimated_end_day(today, seasons_done, clock_config)
    state:set("great_raid_day", end_day)
    core.log.info(TAG, string.format("INVASION clock start day=%d end_day=%d start_year=%d year=%d", today, end_day, clock_config.start_year, current_year()))
end

local last_seen_year = nil -- the game year at the last daily step in this Lua state (nil after a load: a missed warning is skipped)

-- One banner at the start of each of the last `warning_years` years before the start year. None in other years.
local function clock_banner_step(year)
    local years_left = clock_config.start_year - year
    if last_seen_year == nil or year == last_seen_year then return end
    if years_left < 1 or years_left > clock_config.warning_years or state:get("last_clock_banner_year") >= year then return end
    local ok, problem = core.show_banner(great_raid.years_text(years_left), "")
    state:set("last_clock_banner_year", year)
    core.log.info(TAG, string.format("INVASION clock banner year=%d years_left=%d shown=%s%s", year, years_left, tostring(ok), ok and "" or (" problem=" .. tostring(problem))))
end

local function clock_step(today)
    local year = current_year()
    local previous_year = last_seen_year
    if level("great") == 0 then
        last_seen_year = year
        return -- Great raid level 0: no clock, no banner, no waves
    end
    if state:get("great_raid_day") == 0 then start_clock(today) end
    if state:get("gr_phase") == great_raid.PHASE.clock then
        if year >= clock_config.start_year and state:get("great_raid_day") > today then
            state:set("great_raid_day", today) -- the start year began: the estimate was later than the real day
            core.log.info(TAG, string.format("INVASION clock end day=%d year=%d", today, year))
        end
        clock_banner_step(year)
    end
    last_seen_year = year
    great_step(today)
end

local function target_text(kind)
    local target = target_rules.pick(kind, "home", vassal_provider(), plan_rules.lcg(state:get("sub_seed") + 777)) -- the home name does not matter here
    if kind ~= "subjugation" or target.stand_in then return "you" end
    return "your vassal " .. tostring(target.region)
end

-- Only a subjugation raid and a large plunder raid (the player raid) have a banner. A small or medium yearly raid has none.
local function has_banner(kind)
    return kind == "subjugation" or state:get("size_class") == plan_rules.SIZE_CLASSES.large
end

-- One banner, `raid_banner_days` before the raid day (on the plan day when the plan is shorter). The flag keeps it from repeating after a load.
local function raid_banner_step(kind, today, days_left)
    local flag = kind == "subjugation" and "sub_banner" or "plunder_banner"
    if state:get(flag) == 1 or not has_banner(kind) or days_left > config.raid_banner_days then return end
    state:set(flag, 1)
    local text = plan_rules.banner_text(days_left, target_text(kind), planned_units(kind))
    local ok, problem = core.show_banner(text, "")
    core.log.info(TAG, string.format("INVASION raid banner kind=%s day=%d days_left=%d target=%s raiders=%d shown=%s%s", kind, today, days_left, target_text(kind),
        planned_units(kind), tostring(ok), ok and "" or (" problem=" .. tostring(problem))))
end

-- A lord army marches about `march_lead_days` from the edge, so it spawns that many days before the planned raid day and
-- arrives on the planned day (requirement "The raid spawns on the planned day"). Bandit squads spawn at the manor: no lead.
local function spawn_lead()
    if use_roles and roles.lord_army.enabled then return config.border.march_lead_days end
    return 0
end

local function minor_raid_step(today)
    if level("yearly") == 0 or state:get("raid_day") == 0 or state:get("plunder_spawned") == 1 then return end
    local days_left = state:get("raid_day") - today
    if days_left <= spawn_lead() then return spawn_raid(today) end
    raid_banner_step("plunder", today, days_left)
end

-- The yearly roll plans the subjugation raid after the first (plunder) raid. It is a major raid on a vassal region (stand-in: the home region).
local function subjugation_step(today)
    if not config.subjugation.enabled or level("vassal") == 0 or state:get("sub_day") == 0 or state:get("sub_spawned") == 1 then return end
    local days_left = state:get("sub_day") - today
    if days_left <= spawn_lead() then return spawn_raid(today, "subjugation") end
    raid_banner_step("subjugation", today, days_left)
end

-- One roll for the season that just began. Returns true when a raid was planned.
local function roll_season(today, roll)
    local year, position = plan_rules.season_year(state:get("yearly_season_no"))
    local chances = config.yearly.chance_by_season
    local raid = plan_rules.should_raid(year, position, state:get("yearly_done_year"), chances, roll, state:get("first_raid_years") + 1)
    local kind = raid and next_kind() or "none"
    if kind == "plunder" and level("yearly") == 0 then raid, kind = false, "none" end -- level 0: no yearly raid
    core.log.info(TAG, string.format("INVASION yearly roll day=%d year=%d season=%d chance=%s roll=%.2f raid=%s kind=%s", today, year, position,
        tostring(chances[math.min(position, #chances)]), roll, tostring(raid), kind))
    if not raid then return false end
    state:set("yearly_done_year", year)
    if kind == "subjugation" then make_subjugation_plan(today) else make_plan(today) end
    return true
end

-- The saved season is set before the roll, so an error in the roll cannot make it run twice (like mod/bandits).
local function yearly_step(today)
    local season = current_season()
    if season == nil then return end
    local last = state:get("yearly_last_season")
    if last < 0 then
        state:set("yearly_last_season", season)
        state:set("yearly_season_no", 0)
        return
    end
    if season == last then return end
    state:set("yearly_last_season", season)
    state:set("yearly_season_no", state:get("yearly_season_no") + 1)
    roll_season(today, math.random())
end

local function daily_step(today)
    yearly_step(today)
    minor_raid_step(today)
    subjugation_step(today)
    clock_step(today)
end

local function tick()
    if not state.loaded then return end
    local today = current_day()
    if today == nil then return end
    keep_base_timer_high()
    if hold_gate() then return end -- the settings menu of a new game is open or about to open: no banner, no plan yet
    if today == last_handled_day then return end
    last_handled_day = today
    daily_step(today)
end

require("scheduler").every(TAG, config.poll_ms, tick)

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local has_commands, commands = pcall(require, "HarnessCommands")

-- A level change re-plans the squads of an unspawned raid of that type.
local function replan_size()
    if state:get("raid_day") ~= 0 and state:get("plunder_spawned") ~= 1 and level("yearly") > 0 then
        state:set("squads", plan_rules.squads(state:get("size_class"), level("yearly"), config.size_multipliers))
    end
    if state:get("sub_day") ~= 0 and state:get("sub_spawned") ~= 1 and level("vassal") > 0 then
        state:set("sub_squads", plan_rules.squads(config.subjugation.size_class, level("vassal"), config.size_multipliers))
    end
end

local function command_state()
    local today = current_day()
    local raid_day = state:get("raid_day")
    local squads = state:get("squads")
    return {
        day = today, level_yearly = level("yearly"), level_great = level("great"), level_vassal = level("vassal"), plan_day = state:get("plan_day"), raid_day = raid_day,
        size_class = state:get("size_class"), squads = squads,
        raiders = planned_units(), composition = (use_roles and state:get("squads") > 0) and plan_rules.join(composition_list()) or "none", roles = use_roles, days_left = (today and raid_day > 0) and (raid_day - today) or nil,
        raids_spawned = state:get("raids_spawned"), plunder_banner = state:get("plunder_banner"), sub_banner = state:get("sub_banner"),
    }
end

-- For tests: plan a raid now, whatever the year and the season are. Without kind, the kind rules pick it.
local function command_plan_now(args)
    local today = current_day()
    if today == nil then return nil, "the game day is not available" end
    local kind = args.kind or next_kind()
    if kind_level(kind) == 0 then return nil, "the level of this raid type is 0" end
    if kind == "subjugation" then
        if state:get("sub_spawned") == 1 then return nil, "the subjugation raid was spawned already" end
        if state:get("sub_day") == 0 then make_subjugation_plan(today) end
    elseif state:get("raid_day") == 0 or state:get("plunder_spawned") == 1 then
        make_plan(today)
    end
    last_handled_day = nil
    return command_state()
end

local function command_yearly_state()
    local no = state:get("yearly_season_no")
    local year, position = plan_rules.season_year(math.max(no, 0))
    return { day = current_day(), season = current_season(), last_season = state:get("yearly_last_season"), season_no = no,
        year = year, position = position, done_year = state:get("yearly_done_year"), raid_day = state:get("raid_day"),
        plunder_spawned = state:get("plunder_spawned") == 1, sub_day = state:get("sub_day"), sub_spawned = state:get("sub_spawned") == 1,
        raids_spawned = state:get("raids_spawned") }
end

-- For tests: count one season change now and roll (without a real calendar change). `roll` fixes the random number.
local function command_yearly_advance_season(args)
    local today = current_day()
    if today == nil then return nil, "the game day is not available" end
    if state:get("yearly_season_no") < 0 then return nil, "no season was seen yet" end
    state:set("yearly_season_no", state:get("yearly_season_no") + 1)
    local planned = roll_season(today, args.roll or math.random())
    last_handled_day = nil
    local answer = command_yearly_state()
    answer.planned = planned
    return answer
end

-- For tests: move the raid day of a planned raid so that `days` game days remain. The banner flag is reset.
local function command_set_raid_days(args)
    local today = current_day()
    if today == nil then return nil, "the game day is not available" end
    if args.kind == "subjugation" then
        if state:get("sub_day") == 0 or state:get("sub_spawned") == 1 then return nil, "no subjugation raid is planned" end
        state:set("sub_day", today + args.days)
        state:set("sub_banner", 0)
    else
        if state:get("raid_day") == 0 or state:get("plunder_spawned") == 1 then return nil, "no plunder raid is planned" end
        state:set("raid_day", today + args.days)
        state:set("plunder_banner", 0)
    end
    last_handled_day = nil
    return command_state()
end

local function command_force_next()
    local today = current_day()
    if today == nil then return nil, "the game day is not available" end
    if state:get("plunder_spawned") == 1 then return nil, "the raid was spawned already" end
    if level("yearly") == 0 then return nil, "the yearly level is 0" end
    if state:get("raid_day") == 0 then make_plan(today) end -- a test may force a raid in year 1
    state:set("raid_day", today)
    last_handled_day = nil
    return command_state()
end

local function command_clock_state()
    local today = current_day()
    local end_day = state:get("great_raid_day")
    return { day = today, great_raid_day = end_day, days_left = (today and end_day > 0) and clock_days_left(today) or nil,
        last_clock_banner_year = state:get("last_clock_banner_year"), year = current_year() }
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
    return { day = today, sub_day = sub_day, squads = state:get("sub_squads"), banner = state:get("sub_banner"),
        raiders = planned_units("subjugation"), spawned = state:get("sub_spawned") == 1, days_left = (today and sub_day > 0) and (sub_day - today) or nil,
        composition = state:get("sub_squads") > 0 and plan_rules.join(composition_list("subjugation")) or "none" }
end

-- For tests: the subjugation raid spawns on the next check (it must be planned already).
local function command_subjugation_force_next()
    local today = current_day()
    if today == nil then return nil, "the game day is not available" end
    if state:get("sub_spawned") == 1 then return nil, "the subjugation raid was spawned already" end
    if state:get("sub_day") == 0 then return nil, "the subjugation raid is not planned yet" end
    if level("vassal") == 0 then return nil, "the vassal level is 0" end
    state:set("sub_day", today)
    last_handled_day = nil
    return command_subjugation_state()
end

local function command_great_state()
    local today = current_day()
    return { day = today, level = level("great"), phase = state:get("gr_phase"), wave = state:get("gr_wave"), waves = difficulty_rules.wave_count(level("great")),
        last_day = state:get("gr_last_day"), great_raid_day = state:get("great_raid_day"),
        relief_squads = difficulty_rules.relief_squads(level("great"), clock_config.relief_full_squads),
        wave_squads = clock_config.wave_squads, final_squads = clock_config.final_squads, raids_spawned = state:get("raids_spawned") }
end

-- For tests: the clock ends today.
local function command_great_force_start()
    local today = current_day()
    if today == nil then return nil, "the game day is not available" end
    if level("great") == 0 then return nil, "the great raid level is 0" end
    if state:get("gr_phase") ~= great_raid.PHASE.clock then return nil, "the great raid has started already" end
    state:set("great_raid_day", today)
    last_handled_day = nil
    return command_great_state()
end

-- For tests: the wait for the next wave or the relief army is over now.
local function command_great_skip_wait()
    local today = current_day()
    if today == nil then return nil, "the game day is not available" end
    state:set("gr_last_day", today - 1000)
    last_handled_day = nil
    return command_great_state()
end

local function command_difficulty_state()
    local great = level("great")
    return { yearly = level("yearly"), great = great, vassal = level("vassal"), chosen = state:get("difficulty_chosen") == 1,
        relief_squads = difficulty_rules.relief_squads(great, clock_config.relief_full_squads),
        waves = difficulty_rules.wave_count(great), wave_squads = clock_config.wave_squads }
end

-- A level change clears the plan of a raid type that is now off, and re-plans the squads of the others.
local function settings_changed()
    if level("yearly") == 0 and state:get("plunder_spawned") ~= 1 then
        state:set("raid_day", 0)
        state:set("squads", 0)
    end
    if level("vassal") == 0 and state:get("sub_spawned") ~= 1 then
        state:set("sub_day", 0)
        state:set("sub_squads", 0)
    end
    if level("great") == 0 and state:get("gr_phase") == great_raid.PHASE.clock then state:set("great_raid_day", 0) end
    replan_size()
    last_handled_day = nil
end

-- Set the levels of some raid types (a table kind -> level). Returns true, or nil and a message (and changes nothing).
-- `keep_pick_open` (an old save got the defaults) does not count as a choice of the player.
local function set_levels(levels, keep_pick_open)
    for kind, value in pairs(levels) do
        if not difficulty_rules.valid_kind(kind) then return nil, "unknown raid type " .. tostring(kind) end
        if not difficulty_rules.valid_level(value) then return nil, string.format("the %s level must be 0 to 3", kind) end
    end
    for kind, value in pairs(levels) do state:set("level_" .. kind, value) end
    if not keep_pick_open then state:set("difficulty_chosen", 1) end
    settings_changed()
    return true
end

-- Shared by the named command and the raid widget. Returns the difficulty state, or nil and a message.
local function pick_difficulty(value)
    if state:get("difficulty_chosen") == 1 then return nil, "the difficulty was picked already" end
    if state:get("raids_spawned") > 0 then return nil, "the first raid was spawned already" end
    local ok, problem = set_levels({ yearly = value, great = value, vassal = value })
    if not ok then return nil, problem end
    core.log.info(TAG, "INVASION levels picked " .. value)
    return command_difficulty_state()
end

local function command_pick_difficulty(args)
    return pick_difficulty(args.value)
end

-- Everything the raid widget shows about raids, in one table (M02 iteration 05). Days are nil when not known.
-- The upcoming raids for the raid menu. A switched-off raid type is not listed (plunder: nil when not planned; subjugation: nil when it is off).
local function upcoming_raids(today)
    local list = {}
    if level("yearly") > 0 and today and state:get("raid_day") > 0 and state:get("plunder_spawned") == 0 then
        list.plunder = { days_left = state:get("raid_day") - today, target = "you", raiders = planned_units(), squads = state:get("squads"),
            size = plan_rules.SIZE_NAMES[state:get("size_class")] }
    end
    if config.subjugation.enabled then
        list.subjugation = { planned = false }
        if today and state:get("sub_day") > 0 and state:get("sub_spawned") == 0 then
            list.subjugation = { planned = true, days_left = state:get("sub_day") - today, target = target_text("subjugation"),
                raiders = planned_units("subjugation"), squads = state:get("sub_squads") }
        end
    end
    return list
end

local function raid_info()
    local today = current_day()
    local raid_day, great_day = state:get("raid_day"), state:get("great_raid_day")
    return {
        day = today, levels = { yearly = level("yearly"), great = level("great"), vassal = level("vassal") },
        difficulty_chosen = state:get("difficulty_chosen") == 1,
        raid_days_left = (today and raid_day > 0) and (raid_day - today) or nil,
        raiders = state:get("squads") > 0 and planned_units() or nil, squads = state:get("squads"),
        great_days_left = (today and great_day > 0) and clock_days_left(today) or nil,
        great_phase = state:get("gr_phase"), great_wave = state:get("gr_wave"), great_waves = difficulty_rules.wave_count(level("great")),
        picks_allowed = state:get("difficulty_chosen") ~= 1 and state:get("raids_spawned") == 0,
        upcoming = upcoming_raids(today),
    }
end

-- The harness sets all three levels to one value, at any time (a test command).
local function command_set_difficulty(args)
    local ok, problem = set_levels({ yearly = args.value, great = args.value, vassal = args.value })
    if not ok then return nil, problem end
    return command_state()
end

-- The harness sets the level of one raid type.
local function command_set_level(args)
    local ok, problem = set_levels({ [args.kind] = args.value })
    if not ok then return nil, problem end
    return command_state()
end

local function command_set_size(args)
    local class = plan_rules.SIZE_CLASSES[args.size]
    if state:get("raid_day") == 0 then return nil, "no raid is planned yet" end
    if state:get("plunder_spawned") == 1 then return nil, "the raid was spawned already" end
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
    commands.register("InvasionMod.invasion_great_state", command_great_state, {})
    commands.register("InvasionMod.invasion_great_force_start", command_great_force_start, {})
    commands.register("InvasionMod.invasion_great_skip_wait", command_great_skip_wait, {})
    commands.register("InvasionMod.invasion_subjugation_state", command_subjugation_state, {})
    commands.register("InvasionMod.invasion_subjugation_force_next", command_subjugation_force_next, {})
    commands.register("InvasionMod.invasion_difficulty_state", command_difficulty_state, {})
    commands.register("InvasionMod.invasion_pick_difficulty", command_pick_difficulty, { value = { type = "integer", required = true, min = 0, max = 3 } })
    commands.register("InvasionMod.invasion_clock_state", command_clock_state, {})
    commands.register("InvasionMod.invasion_clock_set_days_left", command_clock_set_days_left, { days = { type = "integer", required = true, min = 1, max = 2000 } })
    commands.register("InvasionMod.invasion_force_next", command_force_next, {})
    commands.register("InvasionMod.invasion_set_raid_days", command_set_raid_days, { days = { type = "integer", required = true, min = 1, max = 400 }, kind = { type = "string", oneOf = { "plunder", "subjugation" } } })
    commands.register("InvasionMod.invasion_plan_now", command_plan_now, { kind = { type = "string", oneOf = { "plunder", "subjugation" } } })
    commands.register("InvasionMod.invasion_yearly_state", command_yearly_state, {})
    commands.register("InvasionMod.invasion_yearly_advance_season", command_yearly_advance_season, { roll = { type = "number", min = 0, max = 0.999 } })
    commands.register("InvasionMod.invasion_set_difficulty", command_set_difficulty, { value = { type = "integer", required = true, min = 0, max = 3 } })
    commands.register("InvasionMod.invasion_set_level", command_set_level, {
        kind = { type = "string", required = true, oneOf = difficulty_rules.KINDS }, value = { type = "integer", required = true, min = 0, max = 3 } })
    commands.register("InvasionMod.invasion_set_size", command_set_size, { size = { type = "string", required = true, oneOf = { "small", "medium", "large" } } })
end

core.log.info(TAG, "feature invasion loaded")
-- Another feature registers two functions: before() runs just before the spawn call and returns a token,
-- after(token, { day, squads }) runs just after it.
local function watch_spawn(before, after)
    spawn_watchers[#spawn_watchers + 1] = { before = before, after = after }
end

-- raid_behavior calls this when a marching lord army has arrived at the manor (`summary` is the raid summary).
-- The wave gap and the relief delay count from here. A yearly or subjugation raid shows its "is here" banner.
local function on_arrival(summary)
    local today = current_day()
    if summary.kind == "great" then
        if today ~= nil and state:get("gr_phase") == great_raid.PHASE.waves then state:set("gr_last_day", today) end
        core.log.info(TAG, string.format("INVASION great army arrived day=%s final=%s", tostring(today), tostring(summary.final == true)))
        return
    end
    core.show_banner(summary.kind == "subjugation" and "The subjugation raid is here" or "Raiders are here", "")
end

-- Another feature registers fn(). It returns a list of vassal region names that a subjugation raid may target.
local function set_vassal_provider(fn)
    vassal_provider = fn
end

return { state = state, on_arrival = on_arrival, set_vassal_provider = set_vassal_provider, watch_spawn = watch_spawn, raid_info = raid_info, pick_difficulty = pick_difficulty,
         level = level, difficulty = general_difficulty, set_levels = set_levels, settings_changed = settings_changed, command_state = command_state,
         set_hold_gate = function(gate) hold_gate = gate end }
