-- Fallback capital (M06 iteration 03, simplest form, TBD). Before or during a battle the player pays to make a fortified vassal
-- the fallback capital. The mod takes the region back from its lord, moves grain from the home stores, and sends settlers there.
-- Not done in this form: moving the best units (no move order for a squad exists, spike S11) and removing the families from home
-- (removing a family kills it, spike S8). Both are TBD for a later iteration.
local core = require("ManorCore")
local ModState = require("ModState")
local invasion = require("features.invasion.init")
local vassals = require("features.vassals.init")
local raid_world = require("features.raid_behavior.world")
local silver_world = require("features.bandits.world")
local rules = require("features.sack_and_terms.fallback_rules")
local config = require("config").sack_and_terms.fallback

local TAG = "InvasionMod.fallback"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("fallback_slot", 0, "integer")       -- the vassal slot that became the capital, 0 when none
state:register("fallback_day", 0, "integer")        -- day + 1 of the move
state:register("fallback_silver_paid", 0, "integer")
state:register("fallback_grain_moved", 0, "integer")

local last = nil -- the result of the last move, for the state command

local function step(label, answer)
    if type(answer) ~= "table" or not answer.ok then
        return nil, label .. ": " .. tostring(type(answer) == "table" and answer.error or answer)
    end
    return answer
end

-- Take grain out of the home stores, one unit at a time (consumeGoodNoCheck, the proven removal). Returns the amount taken.
-- The first good of the list that the home stores hold.
local function pick_good(goods)
    for _, good in ipairs(goods) do
        for _, store in ipairs(raid_world.stores() or {}) do
            if (store.by_good[good] or 0) > 0 then return good end
        end
    end
    return nil
end

local function take_grain(good, wanted)
    local taken = 0
    if good == nil then return 0 end
    for _, store in ipairs(raid_world.stores() or {}) do
        local held = store.by_good[good] or 0
        for _ = 1, math.min(held, wanted - taken) do
            if pcall(function() store.building:consumeGoodNoCheck(good) end) then taken = taken + 1 end
        end
        if taken >= wanted then break end
    end
    return taken
end

-- Put goods into the first building of a region that takes them. Returns true or false and a message.
local function deposit_into_region(region_name, good, amount)
    local e = FindFirstOf("RTSMultiEngineCPP")
    local count = core.read(function() return e.regions:GetArrayNum() end) or 0
    for i = 1, count do
        local region = core.read(function() return e.regions[i] end)
        if core.shortName(region) == region_name then
            local list = core.read(function() return region:GetBuildings() end)
            for tries, building in ipairs(core.listOf(list)) do
                if tries > config.deposit_tries then break end
                if core.isValid(building) and core.read(function() return building:IsRubble() end) ~= true then
                    local ok = pcall(function() building:addToInventory({ Type = good, amt = amount }) end)
                    if ok then return true end
                end
            end
            return false, "no building of " .. region_name .. " took the goods"
        end
    end
    return false, "region " .. tostring(region_name) .. " not found"
end

-- Give the region back to the player: clear the owner, then the player claims it (the reverse of the M07 handover).
-- Variant "write": only change Region.ownerPawn to the player pawn (the change a won challenge made in spike S11).
local function write_owner(region_name)
    local e = FindFirstOf("RTSMultiEngineCPP")
    local player = core.read(function() return e.playerRef end)
    local count = core.read(function() return e.regions:GetArrayNum() end) or 0
    for i = 1, count do
        local region = core.read(function() return e.regions[i] end)
        if core.shortName(region) == region_name then
            local ok, problem = pcall(function() region.ownerPawn = player end)
            if not ok then return nil, "write ownerPawn: " .. tostring(problem) end
            return { ok = true }
        end
    end
    return nil, "region not found"
end

local function take_region_back(region_name)
    if config.take_back == "write" then return write_owner(region_name) end
    local lords = require("HarnessLords")
    local cleared, why = step("clear owner", lords.region_clear_owner({ region = region_name }))
    if not cleared then return nil, why end
    return step("claim", lords.claim_region({ target = 0, region = region_name, finalize = 1 }))
end

local function check(slot)
    local row
    for _, candidate in ipairs(vassals.slot_rows(true)) do
        if candidate.slot == slot then row = candidate end
    end
    local difficulty = invasion.difficulty()
    local facts = {
        has_vassal = row ~= nil and row.lord ~= "none", is_capital = row ~= nil and row.capital == true,
        buildings = row and row.buildings or 0, silver = silver_world.silver() or 0, already = state:get("fallback_slot") ~= 0,
    }
    return row, rules.refusal(facts, rules.cost(difficulty, config), config), rules.cost(difficulty, config)
end

local function send_settlers(region_name)
    local rows = core.regions_state().regions or {}
    local region_row
    for _, row in ipairs(rows) do
        if row.region == region_name then region_row = row end
    end
    local added = 0
    for _ = 1, config.family_calls do
        local answer = core.settle_region({ target = 0, region = region_name, type = region_row and region_row.settlement_type or 1, supply = 0 })
        if not answer.ok then
            core.log.error(TAG, "FALLBACK settleRegion failed: " .. tostring(answer.error))
            break
        end
        added = added + 1
    end
    return added
end

local function move(slot)
    local row, refusal, cost = check(slot)
    if refusal then return nil, refusal end
    local region = row.region
    local taken_back, why = take_region_back(region)
    if not taken_back then return nil, "the region could not be taken back: " .. tostring(why) end
    vassals.set_capital(slot)
    local paid, pay_why = silver_world.add_silver(-cost)
    if not paid then core.log.error(TAG, "FALLBACK payment failed: " .. tostring(pay_why)) end
    local grain_good = pick_good(config.grain_goods)
    local grain = take_grain(grain_good, config.grain_amount)
    local grain_in = grain > 0 and deposit_into_region(region, grain_good, grain)
    local calls = send_settlers(region)
    state:set("fallback_slot", slot)
    state:set("fallback_day", (raid_world.current_day() or 0) + 1)
    state:set("fallback_silver_paid", state:get("fallback_silver_paid") + (paid and cost or 0))
    state:set("fallback_grain_moved", state:get("fallback_grain_moved") + (grain_in and grain or 0))
    last = { slot = slot, region = region, cost = cost, grain_taken = grain, grain_deposited = grain_in and grain or 0, settle_calls = calls }
    core.log.info(TAG, string.format("FALLBACK capital slot=%d region=%s cost=%d grain=%d/%d settle_calls=%d",
        slot, region, cost, last.grain_deposited, grain, calls))
    core.show_banner("A fallback capital is ready", string.format("%s is your second seat", region))
    return last
end

local function command_state()
    return { slot = state:get("fallback_slot"), day = state:get("fallback_day"), silver_paid = state:get("fallback_silver_paid"),
        grain_moved = state:get("fallback_grain_moved"), last = last, silver = silver_world.silver(),
        cost = rules.cost(invasion.difficulty(), config) }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.fallback_state", command_state, {})
    commands.register("InvasionMod.fallback_set_take_back", function(args)
        config.take_back = args.mode
        return command_state()
    end, { mode = { type = "string", required = true, oneOf = { "clear", "write" } } })
    commands.register("InvasionMod.fallback_set_min_buildings", function(args)
        config.min_buildings = args.value
        return command_state()
    end, { value = { type = "integer", required = true, min = 1, max = 100 } })
    commands.register("InvasionMod.fallback_move", function(args)
        local result, problem = move(args.slot)
        if result == nil then return nil, problem end
        return command_state()
    end, { slot = { type = "integer", required = true, min = 1, max = 3 } })
end

core.log.info(TAG, "fallback loaded")
return { state = state, move = move }
