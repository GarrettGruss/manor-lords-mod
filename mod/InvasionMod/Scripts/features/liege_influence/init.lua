-- Feature liege_influence: the player sends silver from the lord's treasury to the liege and gains influence.
-- The influence is a saved ModState value. It has no decay and no cap (owner decision 2026-10-19).
local core = require("ManorCore")
local ModState = require("ModState")
local rules = require("features.liege_influence.rules")
local config = require("config").liege_influence

local TAG = "InvasionMod.liege_influence"
local STATE_VERSION = 1

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

-- The menu and the command call this function. Returns a result table, or nil and a reason.
local function send_tribute(amount)
    local before = silver()
    local reason = rules.refusal(amount, before)
    if reason then
        core.log.warn(TAG, "LIEGE tribute refused: " .. reason)
        return nil, reason
    end
    local ok, problem = pcall(function() engine().playerRef.silver = before - amount end)
    if not ok then return nil, "silver write failed: " .. tostring(problem) end
    local influence_before = state:get("liege_influence")
    state:set("liege_influence", influence_before + rules.gain(amount, config.influence_per_unit))
    local result = { amount = amount, silver_before = before, silver = silver(), influence_before = influence_before,
        influence = state:get("liege_influence") }
    core.log.info(TAG, string.format("LIEGE tribute %d silver: influence %s -> %s", amount, tostring(influence_before), tostring(result.influence)))
    return result
end

local function command_state()
    return { influence = state:get("liege_influence"), silver = silver(), influence_per_unit = config.influence_per_unit,
        tribute_button_amount = config.tribute_button_amount }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.liege_state", command_state, {})
    commands.register("InvasionMod.liege_send_tribute", function(args)
        local result, reason = send_tribute(args.amount)
        if not result then return nil, reason end
        return result
    end, { amount = { type = "integer", required = true, min = 1, max = 1000000 } })
end

core.log.info(TAG, "feature liege_influence loaded")
return { state = state, send_tribute = send_tribute, command_state = command_state }
