-- RaidStandIn: a TEST FIXTURE, not a real mod and not part of normal play.
-- It is a toy model of the mod-defined raid logic of the Invasion Mode brief (spec 10, follow-up of U10): the raid director,
-- raid behavior, tiers, the warlord, the sack rule and the pressure systems (laws, morale, war economy, seasons).
-- Why: the real Invasion Mode mod will define this state. This stand-in proves that the harness can observe and drive it,
-- also over many runs (A/B), before the real mod exists. The real mod will later pass the same scenarios.
--
-- It registers commands and metrics in HarnessCommands (as RaidStandIn.<name>). It changes no game object, adds no hook
-- and no loop. The state lives in plain Lua tables. The only game read is the day counter (TemporalComponent.daysTotal):
-- the toy day moves forward by the game days that passed, lazily, on each command or metric read.
-- Commands can also move the toy day by hand (set_day, advance_days), so a test can simulate years in a moment.
-- Use it on a developer machine only. Do not ship it.
--
-- Toy rules (the numbers are fixed, so a test can predict them; random choices use a seeded generator):
--   Calendar: a year has 360 days, a season 90 days: spring 0-89, summer 90-179, autumn 180-269, winter 270-359.
--   Factions: cuman raid in summer only. norse raid in spring and autumn. No raid is scheduled to arrive in winter.
--   Director: automatic raids never repeat one faction a third time in a row. A raid is scheduled (set_timer, or automatically when auto is on), announced `announce_days` before it arrives,
--     then it arrives. The announced kind is the dominant unit type of the composition.
--   Tiers 1 to 4 set size, gap between raids, number of unit types, targeting and the breaking point (see TIERS).
--   Target: tier 1 picks a random stockpile. Other tiers pick the nearest stockpile with at least 100 stock (HIGH_VALUE).
--   An active raid loots 1 per unit and day, carries 4 per unit, loses 5 morale a day (and 1 more for each 10 defense).
--   Retreat: leader dead, morale at or under the breaking point, full loot, timer end (6 days). At the top tier only a dead leader counts.
--   Warlord: a raid that retreats with a living leader raises the warlord level. The next raid is 25% bigger for each level.
--   Sack: a second sack inside the window (360 days) is fatal (game_over). The first one is not.
--   Winter: active raids pause, farms give no food, the town eats 5 more a day.

local log = require("HarnessLog")
local commands = require("HarnessCommands")

local VERSION = "1"
local TAG = "RaidStandIn"
local PREFIX = "RaidStandIn."

local YEAR_DAYS = 360
local SEASON_DAYS = 90
local SEASONS = { "spring", "summer", "autumn", "winter" }
local MAX_ADVANCE_DAYS = 4000
local MAX_CATCH_UP_DAYS = 4000
local LOG_LIMIT = 200
local MAX_ACTIVE_DAYS = 6
local CARRY_PER_UNIT = 4
local LOOT_PER_UNIT_DAY = 1
local RAID_MORALE_LOSS = 5
local RAID_MORALE_START = 100
local KILL_MORALE_LOSS = 4
local HIGH_VALUE = 100
local GAP_JITTER = 15
local SIZE_JITTER_PERCENT = 10
local STOCK_REGROW_PER_DAY = 3
local MAX_WARLORD_LEVEL = 5
local WARLORD_BONUS_PERCENT = 25
local SACK_FOOD_KEPT_PERCENT = 70
local SACK_MORALE_LOSS = 30
local REPEL_MORALE_GAIN = 10
local DEFAULT_SIZE_PERCENT = 100
local RNG_MODULUS = 2147483648
local MAX_FACTION_STREAK = 2

local FACTION_ORDER = { "cuman", "norse" }
local FACTIONS = {
    cuman = { seasons = { summer = true }, objective = "loot",
              units = { "horse_archers", "spearmen", "archers", "scouts" } },
    norse = { seasons = { spring = true, autumn = true }, objective = "burn",
              units = { "shock_infantry", "archers", "spearmen", "scouts" } },
}
local TIERS = {
    { size = 12, gap_days = 120, variety = 1, targeting = "random", breaking_point = 50, leader_only = false },
    { size = 20, gap_days = 60, variety = 2, targeting = "nearest_high_value", breaking_point = 40, leader_only = false },
    { size = 32, gap_days = 30, variety = 3, targeting = "nearest_high_value", breaking_point = 30, leader_only = false },
    { size = 48, gap_days = 15, variety = 4, targeting = "nearest_high_value", breaking_point = 0, leader_only = true },
}
local LAWS = {
    conscription = { cost = 100, upkeep = 3, defense = 20 },
    tithe = { income = 5, morale_cost = 10 },
    cuman_pact = { cost = 200, cuman_size_percent = 50 },
}
local LAW_NAMES = { "conscription", "cuman_pact", "tithe" }
local START_STOCKPILES = {
    { id = 1, distance = 10, stock = 50 }, { id = 2, distance = 20, stock = 300 },
    { id = 3, distance = 35, stock = 400 }, { id = 4, distance = 5, stock = 20 },
}

local S  -- the whole toy state

---------------------------------------------------------------------------------------------
-- State
---------------------------------------------------------------------------------------------

local function sizePercentFromEnv()
    local text = os.getenv("RAID_STANDIN_SIZE_PERCENT")
    if text == nil or text == "" then return DEFAULT_SIZE_PERCENT end
    local value = tonumber(text)
    if value == nil or value < 10 or value > 1000 then
        error("RAID_STANDIN_SIZE_PERCENT must be a number from 10 to 1000, got " .. text)
    end
    return math.floor(value)
end

local function newConfig()
    return { tier = 2, announce_days = 5, leader_death_percent = 10, size_percent = sizePercentFromEnv(),
             sack_window_days = YEAR_DAYS, sack_limit = 2, auto = false }
end

local function newStockpiles()
    local piles = {}
    for _, pile in ipairs(START_STOCKPILES) do
        piles[pile.id] = { distance = pile.distance, stock = pile.stock, max = pile.stock }
    end
    return piles
end

local function newState()
    return {
        day = 0, last_game_day = nil, rng = 1, config = newConfig(),
        next = nil, active = nil, log = {}, raid_counter = 0, arrivals = 0, spawned_units = 0, bait_hits = 0,
        warlord = { level = 0, escapes = 0 }, repelled = 0, last_faction = nil, faction_streak = 0, stockpiles = newStockpiles(),
        settlement = { food = 1000, silver = 500, workers = { farming = 40, crafting = 20, military = 0 }, war_economy = false,
                       laws = {}, town_morale = 70, sacks = {}, game_over = false },
    }
end

local function readDaysTotal()
    local okFind, engine = pcall(FindFirstOf, "RTSMultiEngineCPP")
    if not okFind or engine == nil then return nil end
    local okRead, days = pcall(function() return engine.TemporalComponent.daysTotal end)
    if okRead and type(days) == "number" then return math.floor(days) end
    return nil
end

---------------------------------------------------------------------------------------------
-- Random numbers (seeded, so a run can be repeated)
---------------------------------------------------------------------------------------------

local function rand(n)
    S.rng = (S.rng * 1103515245 + 12345) % RNG_MODULUS
    return (S.rng >> 16) % n + 1
end

---------------------------------------------------------------------------------------------
-- Calendar and settlement
---------------------------------------------------------------------------------------------

local function seasonOf(day) return SEASONS[(day % YEAR_DAYS) // SEASON_DAYS + 1] end

local function isWinter() return seasonOf(S.day) == "winter" end

local function hasLaw(name) return S.settlement.laws[name] == true end

local function defense()
    local value = 10 + S.settlement.workers.military
    if hasLaw("conscription") then value = value + LAWS.conscription.defense end
    return value
end

local function lawUpkeep()
    return hasLaw("conscription") and LAWS.conscription.upkeep or 0
end

local function foodIncome()
    if isWinter() then return 0 end
    return S.settlement.workers.farming // 2
end

local function foodUse()
    return 10 + (isWinter() and 5 or 0) + lawUpkeep()
end

local function clamp(value, low, high) return math.max(low, math.min(high, value)) end

local function threatIsNear()
    return (S.next ~= nil and S.next.state == "announced") or S.active ~= nil
end

local function runSettlementDay()
    local town = S.settlement
    town.food = math.max(0, town.food + foodIncome() - foodUse())
    if hasLaw("tithe") then town.silver = town.silver + LAWS.tithe.income end
    town.town_morale = clamp(town.town_morale + (threatIsNear() and -2 or 1), 0, 100)
    for _, pile in pairs(S.stockpiles) do pile.stock = math.min(pile.max, pile.stock + STOCK_REGROW_PER_DAY) end
end

local function sacksInWindow()
    local count = 0
    for _, day in ipairs(S.settlement.sacks) do
        if S.day - day < S.config.sack_window_days then count = count + 1 end
    end
    return count
end

---------------------------------------------------------------------------------------------
-- Raids: views and planning
---------------------------------------------------------------------------------------------

local function copyTable(t)
    local copy = {}
    for key, value in pairs(t) do copy[key] = value end
    return copy
end

local function raidView(raid)
    local view = copyTable(raid)
    view.composition = copyTable(raid.composition)
    view.arrival_season = seasonOf(raid.arrival_day)
    return view
end

local function dominantUnit(composition)
    local best, bestCount = nil, -1
    for unit, count in pairs(composition) do
        if count > bestCount or (count == bestCount and unit < best) then best, bestCount = unit, count end
    end
    return best
end

-- The first unit type is the dominant one: 60% when there is more than one type. The rest is shared by the other types.
local function composeUnits(unitTypes, size, variety)
    local composition = { [unitTypes[1]] = size }
    if variety == 1 then return composition end
    local dominant = math.ceil(size * 0.6)
    composition[unitTypes[1]] = dominant
    local others, rest = variety - 1, size - dominant
    for index = 2, variety do composition[unitTypes[index]] = rest // others end
    composition[unitTypes[2]] = composition[unitTypes[2]] + rest % others
    return composition
end

local function raidSize(faction, tier)
    local jitter = 100 - SIZE_JITTER_PERCENT + rand(2 * SIZE_JITTER_PERCENT + 1) - 1
    local size = tier.size * S.config.size_percent * jitter / 10000
    size = size * (100 + WARLORD_BONUS_PERCENT * S.warlord.level) / 100
    if faction == "cuman" and hasLaw("cuman_pact") then size = size * LAWS.cuman_pact.cuman_size_percent / 100 end
    return math.max(1, math.floor(size + 0.5))
end

local function announceIfDue(raid)
    if raid.state == "scheduled" and S.day >= raid.announce_day then
        raid.state = "announced"
        raid.announced_day = S.day
    end
end

local function planRaid(faction, arrivalDay, forced)
    local tier = TIERS[S.config.tier]
    local info = FACTIONS[faction]
    local size = raidSize(faction, tier)
    local composition = composeUnits(info.units, size, tier.variety)
    S.raid_counter = S.raid_counter + 1
    local raid = {
        id = S.raid_counter, state = "scheduled", faction = faction, kind = dominantUnit(composition), objective = info.objective,
        tier = S.config.tier, forced = forced, size = size, units_left = size, composition = composition,
        breaking_point = tier.breaking_point, leader_only = tier.leader_only,
        announce_day = math.max(S.day, arrivalDay - S.config.announce_days), planned_day = arrivalDay, arrival_day = arrivalDay,
        announced_day = -1, end_day = -1, target = 0, bait_hit = false, loot = 0, capacity = CARRY_PER_UNIT * size,
        morale = RAID_MORALE_START, timer_left = MAX_ACTIVE_DAYS, leader_alive = true, retreat_reason = "",
        warlord_level = S.warlord.level, paused_days = 0, days_active = 0,
    }
    S.next = raid
    announceIfDue(raid)
    return raid
end

local function seasonAllows(faction, day)
    return FACTIONS[faction].seasons[seasonOf(day)] == true
end

-- Random, but never a third raid of one faction in a row. Why: a test that looks at both factions must not depend on luck.
local function pickFaction()
    local faction = FACTION_ORDER[rand(#FACTION_ORDER)]
    if faction == S.last_faction and S.faction_streak >= MAX_FACTION_STREAK then
        faction = FACTION_ORDER[faction == FACTION_ORDER[1] and 2 or 1]
    end
    S.faction_streak = (faction == S.last_faction) and (S.faction_streak + 1) or 1
    S.last_faction = faction
    return faction
end

local function scheduleAutomatic()
    local tier = TIERS[S.config.tier]
    local faction = pickFaction()
    local gap = tier.gap_days + rand(2 * GAP_JITTER + 1) - GAP_JITTER - 1
    local day = S.day + math.max(gap, S.config.announce_days + 1)
    while not seasonAllows(faction, day) do day = day + 1 end
    return planRaid(faction, day, false)
end

---------------------------------------------------------------------------------------------
-- Raids: targets, behavior and retreat
---------------------------------------------------------------------------------------------

local function sortedPileIds()
    local ids = {}
    for id in pairs(S.stockpiles) do ids[#ids + 1] = id end
    table.sort(ids)
    return ids
end

-- Returns the id of the nearest stockpile that passes `accept`, or nil. A tie goes to the lowest id.
local function nearestPile(accept)
    local best
    for _, id in ipairs(sortedPileIds()) do
        local pile = S.stockpiles[id]
        if accept(pile) and (best == nil or pile.distance < S.stockpiles[best].distance) then best = id end
    end
    return best
end

local function nearestHighValue()
    return nearestPile(function(pile) return pile.stock >= HIGH_VALUE end)
end

-- The choice of the rule: the nearest high value stockpile, or the nearest stockpile when none has high value.
local function ruleChoice()
    return nearestHighValue() or nearestPile(function() return true end)
end

local function chooseTarget(tier)
    local ids = sortedPileIds()
    if #ids == 0 then return 0 end
    if tier.targeting == "random" then return ids[rand(#ids)] end
    return ruleChoice()
end

local function retreatReason(raid)
    if not raid.leader_alive then return "leader_dead" end
    if raid.leader_only then return nil end
    if raid.morale <= raid.breaking_point then return "morale_break" end
    if raid.loot >= raid.capacity then return "full_loot" end
    if raid.timer_left <= 0 then return "timer_end" end
    return nil
end

local function updateWarlord(raid)
    if raid.leader_alive then
        S.warlord.level = math.min(MAX_WARLORD_LEVEL, S.warlord.level + 1)
        S.warlord.escapes = S.warlord.escapes + 1
        return
    end
    S.warlord.level = 0
    S.repelled = S.repelled + 1
    S.settlement.town_morale = clamp(S.settlement.town_morale + REPEL_MORALE_GAIN, 0, 100)
end

local function archiveRaid(raid)
    S.log[#S.log + 1] = raidView(raid)
    if #S.log > LOG_LIMIT then table.remove(S.log, 1) end
end

local function endRaid(raid, reason)
    raid.state = "ended"
    raid.end_day = S.day
    raid.retreat_reason = reason
    updateWarlord(raid)
    archiveRaid(raid)
    S.active = nil
end

local function evaluateRetreat(raid)
    local reason = retreatReason(raid)
    if reason then endRaid(raid, reason) end
end

local function arrive(raid)
    S.next = nil
    raid.state = "active"
    raid.arrival_day = S.day
    raid.target = chooseTarget(TIERS[raid.tier])
    raid.bait_hit = raid.target ~= 0 and raid.target == ruleChoice()
    S.active = raid
    S.arrivals = S.arrivals + 1
    S.spawned_units = S.spawned_units + raid.size
    if raid.bait_hit then S.bait_hits = S.bait_hits + 1 end
end

local function gainLoot(raid)
    local pile = S.stockpiles[raid.target]
    if not pile then return end
    local take = math.min(raid.units_left * LOOT_PER_UNIT_DAY, pile.stock, raid.capacity - raid.loot)
    pile.stock = pile.stock - take
    raid.loot = raid.loot + take
end

local function runActiveRaidDay()
    local raid = S.active
    if not raid then return end
    if isWinter() then
        raid.paused_days = raid.paused_days + 1
        return
    end
    raid.days_active = raid.days_active + 1
    raid.timer_left = raid.timer_left - 1
    gainLoot(raid)
    raid.morale = raid.morale - RAID_MORALE_LOSS - defense() // 10
    if rand(100) <= S.config.leader_death_percent then raid.leader_alive = false end
    evaluateRetreat(raid)
end

local function runScheduleDay()
    local raid = S.next
    if raid then
        announceIfDue(raid)
        if S.day >= raid.arrival_day and not S.active then arrive(raid) end
    end
    if S.config.auto and not S.next and not S.active then scheduleAutomatic() end
end

local function runDay()
    S.day = S.day + 1
    runSettlementDay()
    runActiveRaidDay()
    runScheduleDay()
end

-- Apply the rules for each game day that passed since the last call. Why here: the stand-in has no loop of its own.
local function syncTime()
    local today = readDaysTotal()
    if today == nil then return end
    local last = S.last_game_day
    if last == nil or today < last or today - last > MAX_CATCH_UP_DAYS then
        S.last_game_day = today
        return
    end
    while S.last_game_day < today do
        S.last_game_day = S.last_game_day + 1
        runDay()
    end
end

---------------------------------------------------------------------------------------------
-- Views of the other state
---------------------------------------------------------------------------------------------

local function clockView()
    return { day = S.day, season = seasonOf(S.day), year = S.day // YEAR_DAYS, game_day = S.last_game_day or -1 }
end

local function configView()
    local view = copyTable(S.config)
    view.targeting = TIERS[S.config.tier].targeting
    return view
end

local function lawList()
    local list = {}
    for _, name in ipairs(LAW_NAMES) do
        if hasLaw(name) then list[#list + 1] = name end
    end
    return list
end

local function settlementView()
    local town = S.settlement
    return {
        food = town.food, silver = town.silver, town_morale = town.town_morale, defense = defense(), food_income = foodIncome(),
        food_use = foodUse(), workers = copyTable(town.workers), war_economy = town.war_economy, laws = lawList(),
        sacks_in_window = sacksInWindow(), sacks_total = #town.sacks, game_over = town.game_over,
        warlord_level = S.warlord.level, season = seasonOf(S.day),
    }
end

local function pendingView()
    if not S.next then return { state = "none" } end
    return raidView(S.next)
end

local function activeView()
    if not S.active then return { state = "none" } end
    return raidView(S.active)
end

---------------------------------------------------------------------------------------------
-- Commands: clock, director and raids
---------------------------------------------------------------------------------------------

local function applyConfig(args)
    local config = S.config
    for _, key in ipairs({ "tier", "announce_days", "leader_death_percent", "size_percent", "sack_window_days", "sack_limit", "auto" }) do
        if args[key] ~= nil then config[key] = args[key] end
    end
    if args.seed ~= nil then S.rng = math.floor(args.seed) end
    return configView()
end

local function resetAll()
    S = newState()
    S.last_game_day = readDaysTotal()
    return configView()
end

local function setDay(args)
    S.day = args.day
    return clockView()
end

local function advanceDays(args)
    for _ = 1, args.days do runDay() end
    return clockView()
end

local function setTimer(args)
    if S.next then return nil, "a raid is already scheduled (raid " .. S.next.id .. "). Cancel it first" end
    return raidView(planRaid(args.faction or "cuman", S.day + args.days, true))
end

local function cancelRaid()
    if not S.next then return nil, "no raid is scheduled" end
    local cancelled = raidView(S.next)
    S.next = nil
    return cancelled
end

local function raidLog(args)
    local first = math.max(1, #S.log - (args.count or 20) + 1)
    local raids = {}
    for index = first, #S.log do raids[#raids + 1] = raidView(S.log[index]) end
    return { total = #S.log, arrivals = S.arrivals, raids = raids }
end

---------------------------------------------------------------------------------------------
-- Commands: force a condition of the active raid
---------------------------------------------------------------------------------------------

local function withActiveRaid(change)
    return function(args)
        local raid = S.active
        if not raid then return nil, "no raid is active" end
        change(raid, args)
        evaluateRetreat(raid)
        return raidView(raid)
    end
end

local function killRaiders(raid, args)
    local killed = math.min(args.count, raid.units_left - 1)
    raid.units_left = raid.units_left - killed
    raid.capacity = CARRY_PER_UNIT * raid.units_left
    raid.morale = raid.morale - KILL_MORALE_LOSS * killed
end

---------------------------------------------------------------------------------------------
-- Commands: stockpiles, sack, laws and war economy
---------------------------------------------------------------------------------------------

local function setStockpile(args)
    S.stockpiles[args.id] = { distance = args.distance, stock = args.stock, max = args.stock }
    return { id = args.id, distance = args.distance, stock = args.stock, nearest_high_value = nearestHighValue() or 0 }
end

local function stockpileList()
    local list = {}
    for _, id in ipairs(sortedPileIds()) do
        local pile = S.stockpiles[id]
        list[#list + 1] = { id = id, distance = pile.distance, stock = pile.stock, max = pile.max }
    end
    return { stockpiles = list, nearest_high_value = nearestHighValue() or 0, high_value = HIGH_VALUE }
end

local function sack()
    local town = S.settlement
    if town.game_over then return nil, "the game is over" end
    town.sacks[#town.sacks + 1] = S.day
    town.food = town.food * SACK_FOOD_KEPT_PERCENT // 100
    town.town_morale = clamp(town.town_morale - SACK_MORALE_LOSS, 0, 100)
    if sacksInWindow() >= S.config.sack_limit then town.game_over = true end
    return settlementView()
end

local function enactLaw(args)
    local town, law = S.settlement, LAWS[args.law]
    if hasLaw(args.law) then return nil, args.law .. " is already in force" end
    if (law.cost or 0) > town.silver then return nil, args.law .. " costs " .. law.cost .. " silver, the town has " .. town.silver end
    town.silver = town.silver - (law.cost or 0)
    town.town_morale = clamp(town.town_morale - (law.morale_cost or 0), 0, 100)
    town.laws[args.law] = true
    return settlementView()
end

local function repealLaw(args)
    if not hasLaw(args.law) then return nil, args.law .. " is not in force" end
    S.settlement.laws[args.law] = nil
    return settlementView()
end

local WAR_ECONOMY_SHIFT = 10

local function setWarEconomy(args)
    local town = S.settlement
    if town.war_economy == args.on then return nil, "the war economy is already " .. (args.on and "on" or "off") end
    local direction = args.on and 1 or -1
    town.workers.farming = town.workers.farming - direction * WAR_ECONOMY_SHIFT
    town.workers.military = town.workers.military + direction * WAR_ECONOMY_SHIFT
    town.war_economy = args.on
    return settlementView()
end

---------------------------------------------------------------------------------------------
-- Command table and metrics
---------------------------------------------------------------------------------------------

local function integer(min, max, required) return { type = "integer", required = required, min = min, max = max } end
local FACTION_RULE = { type = "string", oneOf = FACTION_ORDER }
local LAW_RULE = { type = "string", required = true, oneOf = LAW_NAMES }

local COMMAND_TABLE = {
    configure = { run = applyConfig, schema = {
        tier = integer(1, #TIERS), announce_days = integer(1, 30), leader_death_percent = integer(0, 100),
        size_percent = integer(10, 1000), sack_window_days = integer(1, 3600), sack_limit = integer(1, 10),
        seed = integer(0, RNG_MODULUS - 1), auto = { type = "boolean" } } },
    reset = { run = resetAll, schema = {} },
    clock = { run = clockView, schema = {} },
    set_day = { run = setDay, schema = { day = integer(0, 100000, true) } },
    advance_days = { run = advanceDays, schema = { days = integer(1, MAX_ADVANCE_DAYS, true) } },
    set_timer = { run = setTimer, schema = { days = integer(1, 400, true), faction = FACTION_RULE } },
    cancel_raid = { run = cancelRaid, schema = {} },
    next_raid = { run = pendingView, schema = {} },
    current_raid = { run = activeView, schema = {} },
    raid_log = { run = raidLog, schema = { count = integer(1, 100) } },
    kill_leader = { run = withActiveRaid(function(raid) raid.leader_alive = false end), schema = {} },
    kill_raiders = { run = withActiveRaid(killRaiders), schema = { count = integer(1, 50, true) } },
    damage_morale = { run = withActiveRaid(function(raid, args) raid.morale = raid.morale - args.amount end),
                      schema = { amount = integer(1, 1000, true) } },
    fill_loot = { run = withActiveRaid(function(raid) raid.loot = raid.capacity end), schema = {} },
    expire_timer = { run = withActiveRaid(function(raid) raid.timer_left = 0 end), schema = {} },
    set_stockpile = { run = setStockpile, schema = { id = integer(1, 8, true), distance = integer(0, 1000, true),
                                                     stock = integer(0, 100000, true) } },
    stockpiles = { run = stockpileList, schema = {} },
    sack = { run = sack, schema = {} },
    settlement = { run = settlementView, schema = {} },
    enact = { run = enactLaw, schema = { law = LAW_RULE } },
    repeal = { run = repealLaw, schema = { law = LAW_RULE } },
    set_war_economy = { run = setWarEconomy, schema = { on = { type = "boolean", required = true } } },
}

-- Every command first moves the toy rules to the current game day, so its answer is up to date.
local function defineCommand(name, definition)
    local full = PREFIX .. name
    commands.unregister(full)  -- a hot reload runs this file again
    commands.register(full, function(args)
        syncTime()
        return definition.run(args)
    end, definition.schema)
end

local METRICS = {
    day = function() return S.day end,
    season = function() return seasonOf(S.day) end,
    raids_arrived = function() return S.arrivals end,
    raid_announced = function() return S.next ~= nil and S.next.state == "announced" end,
    raid_active = function() return S.active ~= nil end,
    spawned_units = function() return S.spawned_units end,
    bait_hits = function() return S.bait_hits end,
    warlord_level = function() return S.warlord.level end,
    town_morale = function() return S.settlement.town_morale end,
    defense = defense,
    silver = function() return S.settlement.silver end,
    food = function() return S.settlement.food end,
    workers_farming = function() return S.settlement.workers.farming end,
    sacks_in_window = sacksInWindow,
    game_over = function() return S.settlement.game_over end,
}

local function defineMetric(name, read)
    commands.metric(PREFIX .. name, function()
        syncTime()
        return read()
    end)
end

S = newState()
S.last_game_day = readDaysTotal()
for name, definition in pairs(COMMAND_TABLE) do defineCommand(name, definition) end
for name, read in pairs(METRICS) do defineMetric(name, read) end

log.say(TAG, "loaded version " .. VERSION .. " (test fixture: a toy model, not the real mod)")
