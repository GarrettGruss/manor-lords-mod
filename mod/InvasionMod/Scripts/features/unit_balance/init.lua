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
    armored_att_factor = config.armored_att_factor,
    armored_pierce_add = config.armored_pierce_add,
    militia_attack_factor = 1, -- set by the tech tree (M12): Militia Rights 1.1
    militia_defence_factor = 1, -- set by the tech tree (M12): Veteran Levies 1.1
}
-- unit address -> record { def_before, block_before, def_after, object } for a unit the rule changed, or false for a unit it skips.
local known = {}
local totals = { passes = 0, seen = 0, changed = 0, armored = 0, weapon = 0, failed = 0, militia = 0 }
-- unit address -> record of a unit of the player militia (the M12 factors apply) or false for another unit.
local militia_known = {}
-- Why the role and not the template: a unit has no readable template (unitTemp reads None). Militia are villagers with the role Husband (0) or Son (2) (measured in run 20261018-071923-11f8).
local militia_roles = {}
for _, role in ipairs(config.militia_roles) do militia_roles[role] = true end
local last_error = nil

local function address_of(unit)
    return read(function() return unit:GetAddress() end)
end

-- Write named stats (name -> value) and read each back.
local function write_stats(unit, values)
    local ok = pcall(function()
        for name, value in pairs(values) do unit[name] = value end
    end)
    if not ok then return false end
    for name, value in pairs(values) do
        local back = read(function() return unit[name] end)
        if type(back) ~= "number" or math.abs(back - value) >= TOLERANCE then return false end
    end
    return true
end

local function write_pair(unit, def, block)
    return write_stats(unit, { def = def, block = block })
end

-- An armored unit (not heavy) gets weapon values. Returns a record, or false when the unit has no att or armorPierce.
local function classify_armored(unit, def)
    local att, pierce = read(function() return unit.att end), read(function() return unit.armorPierce end)
    if type(att) ~= "number" or type(pierce) ~= "number" then return false end
    local new_att, new_pierce = rules.weapon(att, pierce, settings)
    if not write_stats(unit, { att = new_att, armorPierce = new_pierce }) then
        totals.failed = totals.failed + 1
        core.log.error(TAG, string.format("weapon write failed att %s pierce %s", tostring(att), tostring(pierce)))
        return false
    end
    totals.weapon = totals.weapon + 1
    return { def_before = def, block_before = read(function() return unit.block end), def_after = def,
             att_before = att, pierce_before = pierce, object = unit }
end

-- Look at a unit that has no record. Returns a record, false (the rule skips the unit) or nil (look again later).
local function classify(unit)
    if read(function() return unit.dead end) == true then return nil end
    local def, block = read(function() return unit.def end), read(function() return unit.block end)
    if def == nil or block == nil then return nil end
    totals.seen = totals.seen + 1
    if def >= config.armored_def_min then totals.armored = totals.armored + 1 end
    if rules.is_armored(def, config.armored_def_min, config.heavy_def_min) then return classify_armored(unit, def) end
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
local function record_still_holds(unit, record, key)
    if not record or type(militia_known[key]) == "table" then return true end
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

---------------------------------------------------------------------------------------------
-- Militia factors (M12 tech tree): att, def and block of a unit of the player militia are scaled by a factor
---------------------------------------------------------------------------------------------

local STATS = { "att", "def", "block" }

local function militia_factors_active()
    return settings.militia_attack_factor ~= 1 or settings.militia_defence_factor ~= 1
end

local function factor_of(stat)
    if stat == "att" then return settings.militia_attack_factor end
    return settings.militia_defence_factor
end

-- Why the squad map: a unit has no owner. The side comes from the squad of the unit (HarnessUnits).
local function squad_sides()
    local ok, units = pcall(require, "HarnessUnits")
    if not ok then return nil, "HarnessUnits is not available" end
    return units.squadMap()
end

local function is_player_militia(unit, sides)
    local squad_id = read(function() return unit.assignedSquadID.Value end)
    local squad = squad_id and sides[squad_id]
    if not squad or squad.side ~= "player" then return false end
    local role = read(function() return unit.currentUnitRole end)
    return role ~= nil and militia_roles[role] == true
end

-- Put the base values back on a militia unit. Returns true when the write worked.
local function reset_militia(record)
    if not isValid(record.object) then return false end
    return write_stats(record.object, record.base)
end

local function apply_militia(unit, record)
    local wanted = {}
    for _, stat in ipairs(STATS) do wanted[stat] = record.base[stat] * factor_of(stat) end
    local ok = write_stats(unit, wanted)
    if not ok then totals.failed = totals.failed + 1 end
    record.att_factor, record.def_factor = settings.militia_attack_factor, settings.militia_defence_factor
end

local function new_militia_record(unit)
    local base = {}
    for _, stat in ipairs(STATS) do
        base[stat] = read(function() return unit[stat] end)
        if type(base[stat]) ~= "number" then return nil end
    end
    totals.militia = totals.militia + 1
    return { object = unit, base = base }
end

local last_militia_count = -1

local function militia_summary_count()
    local count = 0
    for _, record in pairs(militia_known) do
        if record then count = count + 1 end
    end
    return count
end

local function militia_pass(units, recheck)
    local sides, problem = squad_sides()
    if sides == nil then
        last_error = tostring(problem)
        return core.log.error(TAG, "militia pass: " .. last_error)
    end
    local present = {}
    for _, unit in ipairs(units) do
        local key = address_of(unit)
        if key ~= nil then
            present[key] = true
            local record = militia_known[key]
            if record == nil or (recheck and record == false) then
                record = is_player_militia(unit, sides) and new_militia_record(unit) or false
                militia_known[key] = record
            end
            local stale = record and (record.att_factor ~= settings.militia_attack_factor or record.def_factor ~= settings.militia_defence_factor)
            if stale then apply_militia(unit, record) end
        end
    end
    for key in pairs(militia_known) do
        if not present[key] then militia_known[key] = nil end
    end
    local count = militia_summary_count()
    if count ~= last_militia_count then
        last_militia_count = count
        core.log.info(TAG, string.format("UNIT_BALANCE militia units=%d of %d", count, #units))
    end
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
            if record == nil or (recheck and not record_still_holds(unit, record, key)) then known[key] = classify(unit) end
        end
    end
    forget_missing(present)
    if militia_factors_active() or next(militia_known) ~= nil then militia_pass(units, recheck) end
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
    for key, record in pairs(militia_known) do
        if record and reset_militia(record) then restored = restored + 1 end
        militia_known[key] = nil
    end
    for key, record in pairs(known) do
        if record and isValid(record.object) then
            local ok
            if record.att_before ~= nil then
                ok = write_stats(record.object, { att = record.att_before, armorPierce = record.pierce_before })
            else
                ok = write_pair(record.object, record.def_before, record.block_before)
            end
            if ok then restored = restored + 1 end
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

-- Called by the tech tree. A factor of 1 puts the base values back at the next pass.
local function set_militia(attack_factor, defence_factor)
    settings.militia_attack_factor = attack_factor
    settings.militia_defence_factor = defence_factor
    core.log.info(TAG, string.format("UNIT_BALANCE militia factors attack=%s defence=%s", tostring(attack_factor), tostring(defence_factor)))
end

local function militia_summary()
    local units, sample = 0, nil
    for _, record in pairs(militia_known) do
        if record then
            units = units + 1
            if sample == nil and isValid(record.object) then
                sample = { base_att = record.base.att, att = read(function() return record.object.att end) }
            end
        end
    end
    return { attack_factor = settings.militia_attack_factor, defence_factor = settings.militia_defence_factor, units = units, sample = sample }
end

local function mean_changed()
    local count, def_sum, block_sum = 0, 0, 0
    for _, record in pairs(known) do
        if record and record.att_before == nil and isValid(record.object) then
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
             changed = totals.changed, armored = totals.armored, weapon = totals.weapon,
             att_factor = settings.armored_att_factor, pierce_add = settings.armored_pierce_add, failed = totals.failed, tracked = mean_changed(), last_error = last_error,
             militia = militia_summary() }
end

-- args: enabled, def_factor, block_factor. Turning the rule off puts the original values back.
local function command_set(args)
    if args.def_factor ~= nil then settings.unarmored_def_factor = args.def_factor end
    if args.block_factor ~= nil then settings.unarmored_block_factor = args.block_factor end
    if args.att_factor ~= nil then settings.armored_att_factor = args.att_factor end
    if args.pierce_add ~= nil then settings.armored_pierce_add = args.pierce_add end
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
    commands.register("InvasionMod.unit_balance_set", command_set, { enabled = { type = "boolean" }, def_factor = factor, block_factor = factor,
        att_factor = { type = "number", min = 0, max = 10 }, pierce_add = { type = "number", min = 0, max = 50 } })
    commands.register("InvasionMod.unit_balance_apply", command_apply, {})
end

core.log.info(TAG, "feature unit_balance loaded")
return { restore_all = restore_all, set_militia = set_militia, militia_summary = militia_summary }
