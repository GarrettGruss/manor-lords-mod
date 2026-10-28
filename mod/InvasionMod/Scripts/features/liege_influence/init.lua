-- Feature liege_influence: the influence with the liege is a saved ModState value, and the arms shipment (silver for goods).
-- Only contracts change the influence (feature liege_contracts, change update-liege-tribute-to-contracts, #505). It has no decay and no cap.
-- The liege window itself is built by liege_contracts; this feature offers the silver, influence and arms shipment functions to it.
local core = require("ManorCore")
local ModState = require("ModState")
local rules = require("features.liege_influence.rules")
local config = require("config").liege_influence

local TAG = "InvasionMod.liege_influence"
local STATE_VERSION = 2

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("liege_influence", 0, "number")
state:register("arms_last_day", -1, "integer") -- game day of the last arms shipment (-1: none yet), saved with the game

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if core.isValid(found) then return found end
    return nil
end

local function silver()
    local e = engine()
    if e == nil then return nil end
    local ok, value = pcall(function() return e.playerRef.silver end)
    if ok and type(value) == "number" then return value end
    return nil
end

-- A direct write to silver does not raise the HUD update event, so the lord panel keeps the old number (spike 2026-10-19).
-- The panel's own updatePlayerStats function reads playerRef.silver again.
local function refresh_hud()
    local ok, problem = pcall(function()
        local panel = FindFirstOf("W_HUD_LordPanel_V2_C")
        if core.isValid(panel) then panel:updatePlayerStats() end
    end)
    if not ok then core.log.warn(TAG, "HUD refresh failed: " .. tostring(problem)) end
end

local function current_day()
    local e = engine()
    if e == nil then return nil end
    local day = core.read(function() return e.TemporalComponent.daysTotal end)
    return type(day) == "number" and math.floor(day) or nil
end

---------------------------------------------------------------------------------------------
-- The arms shipment (change add-scenario-start-kit, #425): silver for goods in the manor store, with a cooldown.
---------------------------------------------------------------------------------------------
local manor = require("HarnessManor")
local NO_MANOR_REASON = "Build a manor first"

-- The first built manor module and its units of goods. Returns the module and the total, or nil and a reason.
local function manor_module()
    local listed = manor.manor_state()
    if not listed.ok then return nil, tostring(listed.error) end
    for _, module in ipairs(listed.modules) do
        if module.built then return module end
    end
    return nil, NO_MANOR_REASON
end

-- A manor is needed first (change fix-arms-button-manor, #455). The other reasons come from the pure rule.
-- The menu refresh asks for a cached manor answer: a built manor stays built while the menu is open, and a missing manor is
-- looked for again after MANOR_RECHECK_S. Without this the building list was read twice a second (two real runs crashed the
-- game after such reads). A click and the commands read the manor fresh.
local MANOR_RECHECK_S = 2
local manor_cache = { built = false, problem = nil, checked = nil }

local function reset_manor_cache() manor_cache = { built = false, problem = nil, checked = nil } end

local function manor_module_cached()
    if manor_cache.built then return true end
    local now = os.clock()
    if manor_cache.checked == nil or now - manor_cache.checked >= MANOR_RECHECK_S then
        local module, problem = manor_module()
        manor_cache = { built = module ~= nil, problem = problem, checked = now }
    end
    if manor_cache.built then return true end
    return nil, manor_cache.problem
end

local function shipment_status(cached)
    local module, problem
    if cached then module, problem = manor_module_cached() else module, problem = manor_module() end
    if not module then return { enabled = false, reason = problem, days_left = 0 } end
    return rules.shipment_status(config.arms_shipment, silver(), current_day(), state:get("arms_last_day"))
end

-- Puts every good of the shipment into the manor. On a failure the goods already put are taken out again.
-- Returns true, or false and a reason. No silver moves here.
local function deliver_goods(goods)
    local module, problem = manor_module()
    if not module then return false, problem end
    local total = rules.goods_total(goods)
    if module.total + total > manor.CAPACITY then
        return false, string.format("manor store full: %d of %d units held, %d more do not fit", module.total, manor.CAPACITY, total)
    end
    local put = {}
    for _, good in ipairs(goods) do
        local answer = manor.manor_put({ good = good.id, amount = good.amount, manor = module.id })
        if not answer.ok then
            for _, done in ipairs(put) do manor.manor_take({ good = done.id, amount = done.amount, manor = module.id }) end
            return false, tostring(answer.error)
        end
        put[#put + 1] = good
    end
    return true
end

-- The menu button and the command call this function. Returns a result table, or nil and a reason.
-- The silver and the cooldown day change only after a successful delivery.
local function request_arms_shipment()
    local cfg = config.arms_shipment
    local status = shipment_status()
    if not status.enabled then
        core.log.warn(TAG, "LIEGE arms shipment refused: " .. status.reason)
        return nil, status.reason
    end
    local delivered, why = deliver_goods(cfg.goods)
    if not delivered then
        core.log.warn(TAG, "LIEGE arms shipment failed, nothing was paid: " .. tostring(why))
        return nil, why
    end
    local before = silver()
    local ok, problem = pcall(function() engine().playerRef.silver = before - cfg.cost end)
    if not ok then
        -- The goods are in the store. Say so, and keep the cooldown so the shipment is not free twice.
        core.log.error(TAG, "LIEGE arms shipment delivered but the silver write failed: " .. tostring(problem))
    end
    state:set("arms_last_day", current_day())
    refresh_hud()
    core.log.info(TAG, string.format("LIEGE arms shipment: silver %s -> %s", tostring(before), tostring(silver())))
    return { cost = cfg.cost, silver_before = before, silver = silver(), day = current_day(), goods = cfg.goods }
end

local function command_state()
    local status = shipment_status()
    return { influence = state:get("liege_influence"), silver = silver(), arms_last_day = state:get("arms_last_day"), day = current_day(),
        arms_enabled = status.enabled, arms_reason = status.reason, arms_days_left = status.days_left }
end

---------------------------------------------------------------------------------------------
-- Influence and silver changes for the contracts (feature liege_contracts)
---------------------------------------------------------------------------------------------

-- Influence changes only by a contract reward or a contract penalty. It never falls below 0. Returns the new value.
local function change_influence(delta)
    local before = state:get("liege_influence") or 0
    local after = math.max(0, before + delta)
    state:set("liege_influence", after)
    return after
end

-- Add silver to the lord's treasury (a contract reward). Returns true, or nil and a message.
local function add_silver(amount)
    local before = silver()
    if before == nil then return nil, "the silver of the lord's treasury is not known" end
    local ok, problem = pcall(function() engine().playerRef.silver = before + amount end)
    if not ok then return nil, "silver write failed: " .. tostring(problem) end
    refresh_hud()
    return true
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.liege_state", command_state, {})
    -- Test helper: set the day of the last shipment (a cooldown of N days left needs no 180 day wait).
    commands.register("InvasionMod.liege_test_set_arms_day", function(args)
        state:set("arms_last_day", args.day)
        return command_state()
    end, { day = { type = "integer", required = true, min = -1, max = 1000000 } })
    commands.register("InvasionMod.liege_request_arms", function()
        local result, reason = request_arms_shipment()
        if not result then return nil, reason end
        return result
    end, {})
end

core.log.info(TAG, "feature liege_influence loaded")
return { state = state, request_arms_shipment = request_arms_shipment, command_state = command_state, shipment_status = shipment_status,
         reset_manor_cache = reset_manor_cache, silver = silver, refresh_hud = refresh_hud, change_influence = change_influence,
         add_silver = add_silver, current_day = current_day, arms_config = config.arms_shipment }
