-- Feature liege_influence: the influence with the liege is a saved ModState value.
-- Only contracts change the influence (feature liege_contracts, changes update-liege-tribute-to-contracts, #505, and update-liege-contracts-tiers, #533).
-- It has no decay and no cap. The liege window itself is built by liege_contracts; this feature offers the silver and influence functions to it.
-- The arms shipment is gone (change update-liege-contracts-tiers): a Medium contract can pay weapons instead.
local core = require("ManorCore")
local ModState = require("ModState")

local TAG = "InvasionMod.liege_influence"
local STATE_VERSION = 2

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("liege_influence", 0, "number")

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

local function command_state()
    return { influence = state:get("liege_influence"), silver = silver(), day = current_day() }
end

---------------------------------------------------------------------------------------------
-- Influence and silver changes for the contracts (feature liege_contracts)
---------------------------------------------------------------------------------------------

-- Influence changes only by a contract reward. It never falls below 0. Returns the new value.
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
end

core.log.info(TAG, "feature liege_influence loaded")
return { state = state, command_state = command_state, silver = silver, refresh_hud = refresh_hud, change_influence = change_influence,
         add_silver = add_silver, current_day = current_day }
