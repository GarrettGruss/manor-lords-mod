-- Feature unit_balance (M05, iteration 01): unarmored units take more damage.
-- Rule: a new unit whose def is below config.armored_def_min gets def and block cut by a factor (first values: 0 and 0).
-- Why a poll: no spawn hook exists for units, and a live write is lost for units that spawn later (spec 25, spec 28).
-- The poll reads as little as it can (M03 crashed the game with many reads each second): a known unit costs one read of def.
local core = require("ManorCore")
local rules = require("features.unit_balance.rules")
local config = require("config").unit_balance

local TAG = "InvasionMod.unit_balance"
local isValid, read = core.isValid, core.read
local TOLERANCE = 0.001

local settings = {
    enabled = config.enabled,
    unarmored_def_factor = config.unarmored_def_factor,
    unarmored_block_factor = config.unarmored_block_factor,
}
-- unit address -> record { def_before, block_before, def_after, object } for a unit the rule changed, or false for a unit it skips.
local known = {}
local totals = { passes = 0, seen = 0, changed = 0, armored = 0, failed = 0 }
local last_error = nil

local function address_of(unit)
    return read(function() return unit:GetAddress() end)
end

local function write_pair(unit, def, block)
    local ok = pcall(function()
        unit.def = def
        unit.block = block
    end)
    local def_back, block_back = read(function() return unit.def end), read(function() return unit.block end)
    return ok and type(def_back) == "number" and type(block_back) == "number"
        and math.abs(def_back - def) < TOLERANCE and math.abs(block_back - block) < TOLERANCE
end

-- Look at a unit that has no record. Returns a record, false (the rule skips the unit) or nil (look again later).
local function classify(unit)
    if read(function() return unit.dead end) == true then return nil end
    local def, block = read(function() return unit.def end), read(function() return unit.block end)
    if def == nil or block == nil then return nil end
    totals.seen = totals.seen + 1
    if def >= config.armored_def_min then totals.armored = totals.armored + 1 end
    if not rules.is_unarmored(def, block, config.armored_def_min) then return false end
    local new_def, new_block = rules.reduced(def, block, settings)
    if not write_pair(unit, new_def, new_block) then
        totals.failed = totals.failed + 1
        core.log.error(TAG, string.format("write failed def %s block %s", tostring(def), tostring(block)))
        return false
    end
    totals.changed = totals.changed + 1
    return { def_before = def, block_before = block, def_after = new_def, object = unit }
end

local function forget_missing(present)
    for key in pairs(known) do
        if not present[key] then known[key] = nil end
    end
end

-- A record whose unit def is not the written value belongs to a new unit on a reused address.
local function record_still_holds(unit, record)
    if not record then return true end
    return read(function() return unit.def end) == record.def_after
end

-- Why a lazy recheck: every property read makes a Lua userdata, and long runs crashed in the Lua state (issue 163).
-- A known unit costs no read of def, unless the unit count changed or every Nth pass.
local last_count = -1

local function needs_recheck(count)
    local changed = count ~= last_count
    last_count = count
    return changed or totals.passes % config.recheck_every == 0
end

local function pass()
    totals.passes = totals.passes + 1
    local present = {}
    local units = FindAllOf("SMUnit") or {}
    local recheck = needs_recheck(#units)
    for _, unit in ipairs(units) do
        local key = address_of(unit)
        if key ~= nil then
            present[key] = true
            local record = known[key]
            if record == nil or (recheck and not record_still_holds(unit, record)) then known[key] = classify(unit) end
        end
    end
    forget_missing(present)
end

local function safe_pass()
    local ok, problem = pcall(pass)
    if not ok then
        last_error = tostring(problem)
        core.log.error(TAG, "pass failed: " .. last_error)
    end
end

-- Put the original values back on the units that the rule changed. Returns the number of restored units.
local function restore_all()
    local restored = 0
    for key, record in pairs(known) do
        if record and isValid(record.object) and write_pair(record.object, record.def_before, record.block_before) then
            restored = restored + 1
        end
        known[key] = nil
    end
    return restored
end

require("scheduler").every(TAG, config.poll_ms, function()
    if settings.enabled then safe_pass() end
end)

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local function mean_changed()
    local count, def_sum, block_sum = 0, 0, 0
    for _, record in pairs(known) do
        if record and isValid(record.object) then
            count = count + 1
            def_sum = def_sum + (read(function() return record.object.def end) or 0)
            block_sum = block_sum + (read(function() return record.object.block end) or 0)
        end
    end
    if count == 0 then return { units = 0 } end
    return { units = count, def = def_sum / count, block = block_sum / count }
end

local function command_state()
    return { enabled = settings.enabled, def_factor = settings.unarmored_def_factor, block_factor = settings.unarmored_block_factor,
             armored_def_min = config.armored_def_min, poll_ms = config.poll_ms, passes = totals.passes, seen = totals.seen,
             changed = totals.changed, armored = totals.armored, failed = totals.failed, tracked = mean_changed(), last_error = last_error }
end

-- args: enabled, def_factor, block_factor. Turning the rule off puts the original values back.
local function command_set(args)
    if args.def_factor ~= nil then settings.unarmored_def_factor = args.def_factor end
    if args.block_factor ~= nil then settings.unarmored_block_factor = args.block_factor end
    local restored = 0
    if args.enabled == false and settings.enabled then restored = restore_all() end
    if args.enabled ~= nil then settings.enabled = args.enabled end
    core.log.info(TAG, string.format("UNIT_BALANCE set enabled=%s def_factor=%s block_factor=%s restored=%d", tostring(settings.enabled),
        tostring(settings.unarmored_def_factor), tostring(settings.unarmored_block_factor), restored))
    local state = command_state()
    state.restored = restored
    return state
end

-- One pass now. With the rule off it does nothing.
local function command_apply()
    if settings.enabled then pass() end
    return command_state()
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    local factor = { type = "number", min = 0, max = 1 }
    commands.register("InvasionMod.unit_balance_state", command_state, {})
    commands.register("InvasionMod.unit_balance_set", command_set, { enabled = { type = "boolean" }, def_factor = factor, block_factor = factor })
    commands.register("InvasionMod.unit_balance_apply", command_apply, {})
end

core.log.info(TAG, "feature unit_balance loaded")
return { restore_all = restore_all }
