-- Feature manor_stronghold (M13). The manor is the safest store. Iteration 01: its storage capacity rises with the tech tree.
-- The store is owned by the mod (spec 12): the base game does not use the Keep as a store, so HarnessManor keeps goods in the
-- building inventory and refuses a put above CAPACITY. This feature sets that capacity from the tech tree bonus.
local core = require("ManorCore")
local manor = require("HarnessManor")
local rules = require("features.manor_stronghold.rules")
local config = require("config").manor_stronghold

local TAG = "InvasionMod.manor_stronghold"

local bonus = { storage = 0 }

local function apply_capacity()
    manor.CAPACITY = rules.storage_capacity(config.storage_base_capacity, bonus.storage)
end

apply_capacity()

-- Called by the tech tree. Takes effect at once.
local function set_modifiers(values)
    bonus.storage = values.storage_bonus or 0
    apply_capacity()
    core.log.info(TAG, string.format("MANOR_STRONGHOLD storage_capacity=%d", manor.CAPACITY))
end

local function command_state()
    local state = manor.manor_state()
    if not state.ok then return nil, state.error end
    state.capacity = manor.CAPACITY
    state.storage_bonus = bonus.storage
    return state
end

local function checked(result)
    if not result.ok then return nil, result.error end
    return result
end

local function command_put(args) return checked(manor.manor_put({ good = args.good, amount = args.amount })) end
local function command_take(args) return checked(manor.manor_take({ good = args.good, amount = args.amount })) end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    local goods_args = { good = { type = "integer", required = true }, amount = { type = "integer", required = true } }
    commands.register("InvasionMod.manor_state", command_state, {})
    commands.register("InvasionMod.manor_put", command_put, goods_args)
    commands.register("InvasionMod.manor_take", command_take, goods_args)
end

core.log.info(TAG, "feature manor_stronghold loaded: capacity " .. manor.CAPACITY)
return { set_modifiers = set_modifiers, capacity = function() return manor.CAPACITY end }
