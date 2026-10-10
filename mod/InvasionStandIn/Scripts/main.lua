-- InvasionStandIn: a TEST FIXTURE, not a real mod and not part of normal play.
-- It is a toy model of outposts, captives, tribute and evacuation. The rules are simple and deterministic.
-- Why: the real Invasion Mode mod adds systems that the base game does not have. This stand-in proves that the
-- harness can drive and observe mod-defined state (spec 10, U10) before that mod exists. The real mod replaces it.
--
-- What it does: it registers commands in HarnessCommands (as InvasionStandIn.<name>) and metrics in HarnessTelemetry.
-- What it does not do: it changes no game object, adds no hook and no loop. The state lives in plain Lua tables.
-- The only game read is the day counter (TemporalComponent.daysTotal). It moves the toy rules forward.
-- Use it on a developer machine only. Do not ship it. Deploy it only for the stand-in scenarios.
--
-- Toy rules (all numbers are fixed, so a test can predict them):
--   Regions 1 to 8. Region 1 is home. Each region starts with 20 families and 200 grain.
--   An outpost has a level 1 to 3. trade_value = 10 + 10 * level. scouting_range = 5 + 5 * level.
--   A lost outpost has trade_value 0 and scouting_range 0.
--   An alive outpost that is not protected, for 3 game days, pays tribute to the invader and leaks intel.
--   A raid is revealed when the outpost is alive and the distance of the raid is not more than scouting_range.
--   Raiders hit the alive outpost with the lowest region number first. With no outpost they hit the town.
--   A captive is worth 15 silver of ransom. Tribute kinds: payment (once), hostages (people), vassal (yearly).

local log = require("HarnessLog")
local commands = require("HarnessCommands")
local telemetry = require("HarnessTelemetry")

local VERSION = "1"
local TAG = "InvasionStandIn"

local REGION_COUNT = 8
local HOME_REGION = 1
local START_FAMILIES = 20
local START_GRAIN = 200
local START_TREASURY = 1000
local MAX_LEVEL = 3
local UNPROTECTED_DAYS = 3
local RANSOM_PER_CAPTIVE = 15
local DEFAULT_YEAR_DAYS = 365
local MAX_CATCH_UP_DAYS = 4000
local TRIBUTE_KINDS = { "payment", "hostages", "vassal" }

local state

---------------------------------------------------------------------------------------------
-- State and game days
---------------------------------------------------------------------------------------------

local function newState()
    local regions = {}
    for id = 1, REGION_COUNT do regions[id] = { families = START_FAMILIES, grain = START_GRAIN } end
    return {
        regions = regions,
        outposts = {},
        captives = { held = 0, freed = 0 },
        tribute = { pending = nil, treasury = START_TREASURY, paid_total = 0, hostages_given = 0, vassal = false,
                    yearly_amount = 0, years_paid = 0, year_days = DEFAULT_YEAR_DAYS, next_due_day = nil },
        last_day = nil,
    }
end

-- Returns the game day counter, or nil when no game map is loaded. A failed read is not an error here.
local function readDaysTotal()
    local okFind, engine = pcall(FindFirstOf, "RTSMultiEngineCPP")
    if not okFind or engine == nil then return nil end
    local okRead, days = pcall(function() return engine.TemporalComponent.daysTotal end)
    if okRead and type(days) == "number" then return days end
    return nil
end

local function payYearlyTribute(tribute)
    local payment = math.min(tribute.treasury, tribute.yearly_amount)
    tribute.treasury = tribute.treasury - payment
    tribute.paid_total = tribute.paid_total + payment
    tribute.years_paid = tribute.years_paid + 1
end

local function runTributeDay(day)
    local tribute = state.tribute
    if tribute.vassal and tribute.next_due_day and day >= tribute.next_due_day then
        payYearlyTribute(tribute)
        tribute.next_due_day = tribute.next_due_day + tribute.year_days
    end
end

local function runOutpostDay(outpost)
    if not outpost.alive or outpost.protected then return end
    outpost.unprotected_days = outpost.unprotected_days + 1
    if outpost.unprotected_days >= UNPROTECTED_DAYS then
        outpost.tribute_to_invader = true
        outpost.leaks_intel = true
    end
end

local function runDay(day)
    for _, outpost in pairs(state.outposts) do runOutpostDay(outpost) end
    runTributeDay(day)
end

-- Apply the rules for each game day that passed since the last call. Why here: the stand-in has no loop of its own.
local function syncTime()
    local today = readDaysTotal()
    if today == nil then return end
    if state.last_day == nil or today - state.last_day > MAX_CATCH_UP_DAYS then
        state.last_day = today
        return
    end
    while state.last_day < today do
        state.last_day = state.last_day + 1
        runDay(state.last_day)
    end
end

---------------------------------------------------------------------------------------------
-- Outposts
---------------------------------------------------------------------------------------------

local function applyLevel(outpost)
    outpost.trade_value = 10 + 10 * outpost.level
    outpost.scouting_range = 5 + 5 * outpost.level
end

local function outpostView(regionId, outpost)
    return {
        region_id = regionId, alive = outpost.alive, level = outpost.level, protected = outpost.protected,
        trade_value = outpost.trade_value, scouting_range = outpost.scouting_range,
        tribute_to_invader = outpost.tribute_to_invader, leaks_intel = outpost.leaks_intel,
        unprotected_days = outpost.unprotected_days,
    }
end

local function aliveOutpost(regionId)
    local outpost = state.outposts[regionId]
    if outpost and outpost.alive then return outpost end
    return nil
end

local function foundOutpost(args)
    if args.region_id == HOME_REGION then return nil, "region " .. HOME_REGION .. " is the home region" end
    if aliveOutpost(args.region_id) then return nil, "an outpost is alive in region " .. args.region_id end
    local outpost = { alive = true, level = 1, protected = args.protected ~= false, unprotected_days = 0,
                      tribute_to_invader = false, leaks_intel = false }
    applyLevel(outpost)
    state.outposts[args.region_id] = outpost
    return outpostView(args.region_id, outpost)
end

local function loseOutpost(args)
    local outpost = aliveOutpost(args.region_id)
    if not outpost then return nil, "no alive outpost in region " .. args.region_id end
    outpost.alive = false
    outpost.trade_value = 0
    outpost.scouting_range = 0
    outpost.tribute_to_invader = false
    outpost.leaks_intel = false
    return outpostView(args.region_id, outpost)
end

local function upgradeOutpost(args)
    local outpost = aliveOutpost(args.region_id)
    if not outpost then return nil, "no alive outpost in region " .. args.region_id end
    if outpost.level >= MAX_LEVEL then return nil, "the outpost has the highest level " .. MAX_LEVEL end
    outpost.level = outpost.level + 1
    applyLevel(outpost)
    return outpostView(args.region_id, outpost)
end

local function showOutpost(args)
    local outpost = state.outposts[args.region_id]
    if not outpost then return nil, "no outpost was ever founded in region " .. args.region_id end
    return outpostView(args.region_id, outpost)
end

-- A raid at `distance` from the outpost is seen only inside the scouting range of an alive outpost.
local function revealRaid(args)
    local outpost = aliveOutpost(args.region_id)
    local range = outpost and outpost.scouting_range or 0
    return { sees = outpost ~= nil and args.distance <= range, scouting_range = range }
end

local function raidTarget()
    local lowest = nil
    for regionId, outpost in pairs(state.outposts) do
        if outpost.alive and (lowest == nil or regionId < lowest) then lowest = regionId end
    end
    if lowest then return { target = "outpost", region_id = lowest } end
    return { target = "town", region_id = HOME_REGION }
end

---------------------------------------------------------------------------------------------
-- Evacuation
---------------------------------------------------------------------------------------------

local function stockView(regionId)
    local stock = state.regions[regionId]
    return { families = stock.families, grain = stock.grain }
end

local function checkEvacuation(args)
    if args.from_region == args.to_region then return "from_region and to_region must differ" end
    if not aliveOutpost(args.to_region) then return "the fallback region " .. args.to_region .. " has no alive outpost" end
    local source = state.regions[args.from_region]
    if args.families > source.families then return "region " .. args.from_region .. " has only " .. source.families .. " families" end
    if args.grain > source.grain then return "region " .. args.from_region .. " has only " .. source.grain .. " grain" end
end

local function evacuate(args)
    local problem = checkEvacuation(args)
    if problem then return nil, problem end
    local source, target = state.regions[args.from_region], state.regions[args.to_region]
    source.families, target.families = source.families - args.families, target.families + args.families
    source.grain, target.grain = source.grain - args.grain, target.grain + args.grain
    return { from = stockView(args.from_region), to = stockView(args.to_region),
             moved = { families = args.families, grain = args.grain } }
end

---------------------------------------------------------------------------------------------
-- Captives
---------------------------------------------------------------------------------------------

local function captiveView()
    local captives = state.captives
    return { held = captives.held, freed = captives.freed, ransom_value = captives.held * RANSOM_PER_CAPTIVE }
end

local function captureCaptives(args)
    state.captives.held = state.captives.held + args.count
    return captiveView()
end

local function freeCaptives(args)
    local captives = state.captives
    if args.count > captives.held then return nil, "only " .. captives.held .. " captives are held" end
    captives.held = captives.held - args.count
    captives.freed = captives.freed + args.count
    return captiveView()
end

---------------------------------------------------------------------------------------------
-- Tribute
---------------------------------------------------------------------------------------------

local function tributeView()
    local tribute = state.tribute
    return {
        treasury = tribute.treasury, paid_total = tribute.paid_total, hostages_given = tribute.hostages_given,
        vassal = tribute.vassal, yearly_amount = tribute.yearly_amount, years_paid = tribute.years_paid,
        year_days = tribute.year_days, pending = tribute.pending and tribute.pending.kind or "none",
    }
end

local function offerTribute(args)
    if state.tribute.pending then return nil, "an offer is already pending" end
    state.tribute.pending = { kind = args.kind, amount = args.amount }
    return tributeView()
end

local function acceptPayment(tribute, offer)
    if offer.amount > tribute.treasury then return "the treasury has only " .. tribute.treasury end
    tribute.treasury = tribute.treasury - offer.amount
    tribute.paid_total = tribute.paid_total + offer.amount
end

local function acceptVassal(tribute, offer)
    if tribute.vassal then return "the town is already a vassal" end
    tribute.vassal = true
    tribute.yearly_amount = offer.amount
    tribute.next_due_day = state.last_day and (state.last_day + tribute.year_days) or nil
end

local ACCEPT_RULES = {
    payment = acceptPayment,
    hostages = function(tribute, offer) tribute.hostages_given = tribute.hostages_given + offer.amount end,
    vassal = acceptVassal,
}

local function acceptTribute()
    local tribute = state.tribute
    local offer = tribute.pending
    if not offer then return nil, "no offer is pending" end
    local problem = ACCEPT_RULES[offer.kind](tribute, offer)
    if problem then return nil, problem end
    tribute.pending = nil
    return tributeView()
end

local function rejectTribute()
    if not state.tribute.pending then return nil, "no offer is pending" end
    state.tribute.pending = nil
    return tributeView()
end

local function setYearDays(args)
    state.tribute.year_days = args.days
    return tributeView()
end

---------------------------------------------------------------------------------------------
-- Commands and metrics
---------------------------------------------------------------------------------------------

local REGION = { type = "integer", required = true, min = 1, max = REGION_COUNT }

local COMMAND_TABLE = {
    found_outpost = { run = foundOutpost,
                      schema = { region_id = REGION, protected = { type = "boolean" } } },
    lose_outpost = { run = loseOutpost, schema = { region_id = REGION } },
    upgrade_outpost = { run = upgradeOutpost, schema = { region_id = REGION } },
    outpost = { run = showOutpost, schema = { region_id = REGION } },
    reveal = { run = revealRaid, schema = { region_id = REGION, distance = { type = "number", required = true, min = 0, max = 1000 } } },
    raid_target = { run = raidTarget, schema = {} },
    region_stock = { run = function(args) return stockView(args.region_id) end, schema = { region_id = REGION } },
    evacuate = { run = evacuate, schema = {
        from_region = REGION, to_region = REGION,
        families = { type = "integer", required = true, min = 0, max = 1000 },
        grain = { type = "integer", required = true, min = 0, max = 100000 } } },
    capture = { run = captureCaptives, schema = { count = { type = "integer", required = true, min = 1, max = 50 } } },
    free_captives = { run = freeCaptives, schema = { count = { type = "integer", required = true, min = 1, max = 50 } } },
    captives = { run = captiveView, schema = {} },
    offer_tribute = { run = offerTribute, schema = {
        kind = { type = "string", required = true, oneOf = TRIBUTE_KINDS },
        amount = { type = "integer", required = true, min = 1, max = 100000 } } },
    accept_tribute = { run = acceptTribute, schema = {} },
    reject_tribute = { run = rejectTribute, schema = {} },
    tribute = { run = tributeView, schema = {} },
    set_year_days = { run = setYearDays, schema = { days = { type = "integer", required = true, min = 1, max = 365 } } },
    reset = { run = function() state = newState(); syncTime(); return tributeView() end, schema = {} },
}

-- Every command first moves the toy rules to the current game day, so its answer is up to date.
local function defineCommand(name, definition)
    local full = "InvasionStandIn." .. name
    commands.unregister(full)  -- a hot reload runs this file again
    commands.register(full, function(args)
        syncTime()
        return definition.run(args)
    end, definition.schema)
end

local function countOutposts(isCounted, valueOf)
    local total = 0
    for _, outpost in pairs(state.outposts) do
        if isCounted(outpost) then total = total + valueOf(outpost) end
    end
    return total
end

local function one() return 1 end

local METRICS = {
    outposts_alive = function() return countOutposts(function(o) return o.alive end, one) end,
    trade_value = function() return countOutposts(function(o) return o.alive end, function(o) return o.trade_value end) end,
    captives = function() return state.captives.held end,
    tribute_paid = function() return state.tribute.paid_total end,
    leaked = function() return countOutposts(function(o) return o.alive and o.leaks_intel end, one) end,
}

local function defineMetric(name, read)
    telemetry.register("InvasionStandIn." .. name, function()
        syncTime()
        return read()
    end)
end

state = newState()
for name, definition in pairs(COMMAND_TABLE) do defineCommand(name, definition) end
for name, read in pairs(METRICS) do defineMetric(name, read) end

log.say(TAG, "loaded version " .. VERSION .. " (test fixture: a toy model, not the real mod)")
