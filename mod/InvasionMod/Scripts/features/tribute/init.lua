-- Feature tribute (M08). At each game month change each handed-over vassal pays goods into the player stores:
-- the rich resources of its region (change update-vassal-tribute-rich-resources). No goods move between regions (M00 decision 21).
local core = require("ManorCore")
local ModState = require("ModState")
local vassals = require("features.vassals.init")
local raid_world = require("features.raid_behavior.world")
local raid_behavior = require("features.raid_behavior.init")
local vassal_rules = require("features.vassals.rules")
local rules = require("features.tribute.rules")
local world = require("features.tribute.world")
local config = require("config").tribute

local TAG = "InvasionMod.tribute"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("tribute_last_month", -1, "integer") -- TemporalComponent.month of the last poll
state:register("tribute_ticks", 0, "integer")
state:register("tribute_paid_total", 0, "integer")
state:register("tribute_skip_months", 0, "integer") -- months with no tribute (a liege contract of the cost tribute_season; change update-liege-contracts-tier-goods)

local share_factor = 1     -- set by the tech tree laws (M12.04)
local history = {}          -- results of the ticks of this session
local failed_deposits = 0

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if core.isValid(found) then return found end
    return nil
end

local function read_number(path_fn)
    local ok, value = pcall(path_fn)
    if ok and type(value) == "number" then return math.floor(value) end
    return nil
end

local function current_month()
    local e = engine()
    return e and read_number(function() return e.TemporalComponent.month end)
end

local function current_season()
    local e = engine()
    return e and read_number(function() return e.TemporalComponent.Season end)
end

local function current_day()
    local e = engine()
    return e and read_number(function() return e.TemporalComponent.daysTotal end)
end

local function stored_total(building)
    local total = 0
    for _, held in ipairs(core.listOf(building.Inventory)) do
        local amount = core.read(function() return held.amt end)
        if type(amount) == "number" and amount > 0 then total = total + amount end
    end
    return total
end

-- Put goods into one store. The deposit is read back from the building inventory (addToInventory is proven on a storehouse).
local function deposit(store, good, amount)
    local before = stored_total(store.building)
    local ok, problem = pcall(function() store.building:addToInventory({ Type = good, amt = amount }) end)
    if not ok then return false, "addToInventory: " .. tostring(problem) end
    local rise = stored_total(store.building) - before
    if rise ~= amount then return false, string.format("store rose by %d, wanted %d", rise, amount) end
    return true
end

-- Put `amount` of one good into the first store that takes all of it.
local function pay_good(good, amount)
    if amount <= 0 then return true end
    for _, store in ipairs(raid_world.stores() or {}) do
        local ok, why = deposit(store, good, amount)
        if ok then return true end
        core.log.warn(TAG, string.format("TRIBUTE deposit of %d of good %d refused: %s", amount, good, tostring(why)))
    end
    failed_deposits = failed_deposits + 1
    return false
end

local function sorted_names(set)
    local names = {}
    for name in pairs(set) do names[#names + 1] = name end
    table.sort(names)
    return names
end

-- The vassal pays `base x policy factor x tech factor` units of each of the goods that rules.choose_goods picks for its region.
local function pay_vassal(row)
    local detected = world.rich_goods(row.region, config.rich)
    if detected == nil then
        core.log.error(TAG, string.format("TRIBUTE no resource nodes read for region %s: nothing paid", tostring(row.region)))
        return { slot = row.slot, region = row.region, policy = row.policy, amount = 0, paid = 0, goods = {}, rich = {}, dropped = {} }
    end
    local chosen, dropped = rules.choose_goods(detected, config.rich)
    local factor = (require("config").vassals.policies[row.policy] or { tribute = 1.0 }).tribute -- vassal policy (M07.03)
    local amount = rules.amount(config.base, factor * share_factor)
    local paid, goods = 0, {}
    for _, name in ipairs(chosen) do
        local id = config.rich.goods[name]
        local ok = pay_good(id, amount)
        goods[#goods + 1] = { name = name, id = id, paid = ok and amount or 0 }
        if ok then paid = paid + amount end
    end
    if #dropped > 0 then
        core.log.info(TAG, string.format("TRIBUTE region %s has more rich goods than it pays: dropped %s", tostring(row.region), table.concat(dropped, ",")))
    end
    return { slot = row.slot, region = row.region, policy = row.policy, amount = amount, paid = paid,
        goods = goods, rich = sorted_names(detected), dropped = dropped }
end

local function run_tick()
    local day = current_day()
    local result = { day = day, payments = {} }
    local skip = state:get("tribute_skip_months")
    if skip > 0 then
        -- Saved before the log: the tribute of this month goes to the liege.
        state:set("tribute_skip_months", skip - 1)
        result.total, result.skipped = 0, true
        history[#history + 1] = result
        core.log.info(TAG, string.format("TRIBUTE tick day=%s skipped for the liege, %d months left", tostring(day), skip - 1))
        return result
    end
    for _, row in ipairs(vassals.slot_rows()) do
        if row and row.lord ~= "none" and not row.rebuilding then result.payments[#result.payments + 1] = pay_vassal(row) end
    end
    local total = 0
    for _, payment in ipairs(result.payments) do total = total + payment.paid end
    result.total = total
    state:set("tribute_ticks", state:get("tribute_ticks") + 1)
    state:set("tribute_paid_total", state:get("tribute_paid_total") + total)
    history[#history + 1] = result
    core.log.info(TAG, string.format("TRIBUTE tick day=%s vassals=%d total=%d", tostring(day), #result.payments, total))
    if total > 0 then core.show_banner("Tribute has arrived", string.format("Your vassals sent %d goods", total)) end
    return result
end

---------------------------------------------------------------------------------------------
-- Vassal targets and siege (M02 iteration 07)
---------------------------------------------------------------------------------------------

require("features.invasion.init").set_vassal_provider(vassals.target_regions)

local siege_resolved = {}   -- raid id -> "taken" or "failed"

local function vassal_slot(region)
    return vassal_rules.slot_of_region(vassals.slot_regions(), require("config").vassals.max_vassals, region)
end

local function resolve_siege(summary)
    local slot = summary.target and vassal_slot(summary.target)
    if slot == nil or siege_resolved[tostring(summary.id)] then return end
    local result = rules.siege_result(summary, raid_world.current_day(), config.siege)
    if result == nil then return end
    siege_resolved[tostring(summary.id)] = result
    core.log.info(TAG, string.format("TRIBUTE siege raid=%d region=%s slot=%d result=%s", summary.id, summary.target, slot, result))
    if result == "taken" then
        local started, why = vassals.start_sack(slot, "siege")
        if started == nil then core.log.error(TAG, "TRIBUTE sack did not start: " .. tostring(why)) end
    end
end

-- The raid that sacks a vassal region ended (all raiders dead or gone): a sack that is not in its wipe ends without a wipe (owner, 2026-10-22).
local function on_raid_end(summary)
    local slot = summary.target and vassal_slot(summary.target)
    if slot == nil or not vassals.sack_slot_of_region(summary.target) then return end
    local ended, why = vassals.end_sack(slot)
    core.log.info(TAG, string.format("TRIBUTE raid %d ended: sack of %s ended without wipe=%s %s", summary.id, summary.target, tostring(ended ~= nil), why or ""))
end
raid_behavior.watch_end(on_raid_end)

local function siege_poll()
    for _, summary in ipairs(raid_behavior.active_raids()) do resolve_siege(summary) end
end

require("scheduler").every(TAG .. ".siege", config.siege.poll_ms, siege_poll)

-- The saved month is set before the tick, so an error in the tick cannot make it run twice.
local function poll()
    if not state.loaded then return end
    local month = current_month()
    if month == nil then return end
    local last = state:get("tribute_last_month")
    if last < 0 then return state:set("tribute_last_month", month) end
    if not rules.month_changed(month, last) then return end
    state:set("tribute_last_month", month)
    core.log.info(TAG, string.format("TRIBUTE month change %d to %d", last, month))
    run_tick()
end

require("scheduler").every(TAG, config.poll_ms, poll)

local function stock()
    local by_good = {}
    for _, store in ipairs(raid_world.stores() or {}) do
        for good, amount in pairs(store.by_good) do by_good[tostring(good)] = (by_good[tostring(good)] or 0) + amount end
    end
    return by_good
end

local function command_state()
    return { day = current_day(), season = current_season(), month = current_month(), last_month = state:get("tribute_last_month"),
        ticks = state:get("tribute_ticks"), paid_total = state:get("tribute_paid_total"), skip_months = state:get("tribute_skip_months"), failed_deposits = failed_deposits,
        history = history, stock = stock(),
        siege = siege_resolved }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.tribute_state", command_state, {})
    commands.register("InvasionMod.tribute_tick_now", function()
        run_tick()
        return command_state()
    end, {})
end

-- Read access for the Vassals menu (change add-vassals-menu, #564): the goods that a region pays and the units of each good,
-- computed with the same rules as the tick. They pay nothing and change nothing.
local function paid_goods(region)
    local detected = world.rich_goods(region, config.rich)
    if detected == nil then return nil end
    return (rules.choose_goods(detected, config.rich))
end

local function amount_for(policy_factor)
    return rules.amount(config.base, policy_factor * share_factor)
end

-- A liege contract gives the tribute of the next `months` months to the liege (they add up). Returns the months that are skipped now.
local function skip_months(months)
    local total = state:get("tribute_skip_months") + months
    state:set("tribute_skip_months", total)
    core.log.info(TAG, string.format("TRIBUTE the next %d months go to the liege", total))
    return total
end

-- The number of vassals that pay tribute now (handed over, not rebuilding), as the tick counts them.
local function paying_vassals()
    local count = 0
    for _, row in ipairs(vassals.slot_rows()) do
        if row and row.lord ~= "none" and not row.rebuilding then count = count + 1 end
    end
    return count
end

core.log.info(TAG, "feature tribute loaded")
return { state = state, run_tick = run_tick, skip_months = skip_months, paying_vassals = paying_vassals, on_raid_end = on_raid_end, set_share_factor = function(value) share_factor = value end,
         paid_goods = paid_goods, amount_for = amount_for }
