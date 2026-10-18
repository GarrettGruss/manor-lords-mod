-- Feature unit_balance (M05): armor, weapon, reach and veterancy values of units.
-- Iteration 01: a new unit whose def is below config.armored_def_min gets def and block cut by a factor (first values: 0 and 0).
-- Iteration 03: an armored unit (def 10 to 40) gets a weapon bonus. Iteration 04: long reach adds att, experience adds att and def.
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
    reach_att_add = config.reach_att_add,
    vet_enabled = config.veterancy.enabled,
    vet_att_per_tier = config.veterancy.att_per_tier,
    vet_def_per_tier = config.veterancy.def_per_tier,
    militia_attack_factor = 1, -- set by the tech tree (M12): Militia Rights 1.1
    militia_defence_factor = 1, -- set by the tech tree (M12): Veteran Levies 1.1
}
-- unit address -> record { before = { stat = value }, def_after, object } for a unit the rule changed, or false for a unit it skips.
local known = {}
-- unit address -> { tier, object } for a unit whose experience tier is above 0.
local vets = {}
local totals = { passes = 0, seen = 0, changed = 0, armored = 0, weapon = 0, reach = 0, vet_changes = 0, failed = 0, militia = 0 }
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

local function read_stats(unit, names)
    local values = {}
    for _, name in ipairs(names) do values[name] = read(function() return unit[name] end) end
    return values
end

-- The stats the plan may change: reads only what the unit class needs (reach and armor decide which).
local function read_unit_values(unit, def, block)
    local values = { def = def, block = block, range = read(function() return unit.range end) }
    local wants_weapon = rules.is_armored(def, config.armored_def_min, config.heavy_def_min)
        or rules.is_pike(values.range, config)
    if wants_weapon then
        values.att = read(function() return unit.att end)
        values.armorPierce = read(function() return unit.armorPierce end)
    end
    return values
end

local function count_plan(plan)
    if plan.unarmored then totals.changed = totals.changed + 1 end
    if plan.armored then totals.weapon = totals.weapon + 1 end
    if plan.reach then totals.reach = totals.reach + 1 end
end

-- Look at a unit that has no record. Returns a record, false (the rule skips the unit) or nil (look again later).
local function classify(unit)
    if read(function() return unit.dead end) == true then return nil end
    local def, block = read(function() return unit.def end), read(function() return unit.block end)
    if def == nil or block == nil then return nil end
    totals.seen = totals.seen + 1
    if def >= config.armored_def_min then totals.armored = totals.armored + 1 end
    local values = read_unit_values(unit, def, block)
    local plan = rules.plan(values, settings, config)
    if next(plan.writes) == nil then return false end
    local names = {}
    for name in pairs(plan.writes) do names[#names + 1] = name end
    local before = read_stats(unit, names)
    if not write_stats(unit, plan.writes) then
        totals.failed = totals.failed + 1
        core.log.error(TAG, string.format("write failed def %s block %s", tostring(def), tostring(block)))
        return false
    end
    count_plan(plan)
    return { before = before, def_after = plan.writes.def or def, object = unit }
end

local function forget_missing(present, map)
    for key in pairs(map) do
        if not present[key] then map[key] = nil end
    end
end

-- A record whose unit def is not the written value belongs to a new unit on a reused address.
-- A veteran has its def scaled by the tier factor on top of the written value.
local function record_still_holds(unit, record, key)
    if not record or type(militia_known[key]) == "table" then return true end
    local entry = vets[key]
    local expected = record.def_after * (entry and rules.vet_factor(entry.tier, settings.vet_def_per_tier) or 1)
    local now = read(function() return unit.def end)
    return type(now) == "number" and math.abs(now - expected) < 0.01
end

---------------------------------------------------------------------------------------------
-- Veterancy: the experience tier scales att and def. A tier change multiplies the current values by the ratio of the factors.
---------------------------------------------------------------------------------------------

local function scale_by_tier(unit, from_tier, to_tier)
    local current = read_stats(unit, { "att", "def" })
    if type(current.att) ~= "number" or type(current.def) ~= "number" then return false end
    local att_ratio = rules.vet_factor(to_tier, settings.vet_att_per_tier) / rules.vet_factor(from_tier, settings.vet_att_per_tier)
    local def_ratio = rules.vet_factor(to_tier, settings.vet_def_per_tier) / rules.vet_factor(from_tier, settings.vet_def_per_tier)
    return write_stats(unit, { att = current.att * att_ratio, def = current.def * def_ratio })
end

local function update_veteran(unit, key)
    local experience = read(function() return unit.combatExperience end)
    if type(experience) ~= "number" then return end
    local tier = rules.vet_tier(experience, config.veterancy.step, config.veterancy.max_tier)
    local entry = vets[key]
    local old = entry and entry.tier or 0
    if tier < old then -- experience never falls, so this is a new unit on a reused address
        vets[key], old = nil, 0
    end
    if tier == old then return end
    if not scale_by_tier(unit, old, tier) then
        totals.failed = totals.failed + 1
        return core.log.error(TAG, "veterancy write failed at tier " .. tier)
    end
    vets[key] = tier > 0 and { tier = tier, object = unit } or nil
    totals.vet_changes = totals.vet_changes + 1
end

---------------------------------------------------------------------------------------------
-- Poll
---------------------------------------------------------------------------------------------

-- Why a lazy recheck: every property read makes a Lua userdata, and long runs crashed in the Lua state (issue 163).
-- A known unit costs no read of def, unless the unit count changed or every Nth pass.
local last_count = -1

local function needs_recheck(count)
    local changed = count ~= last_count
    last_count = count
    return changed or totals.passes % config.recheck_every == 0
end

local function check_known(unit, key, recheck)
    local record = known[key]
    if record == nil then
        known[key] = classify(unit)
    elseif recheck and not record_still_holds(unit, record, key) then
        known[key] = classify(unit)
    end
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

-- A veteran keeps its tier scaling on top of the militia factors (record.base has no tier scaling).
local function vet_scale_of(key, stat)
    local entry = vets[key]
    if not entry then return 1 end
    if stat == "att" then return rules.vet_factor(entry.tier, settings.vet_att_per_tier) end
    if stat == "def" then return rules.vet_factor(entry.tier, settings.vet_def_per_tier) end
    return 1
end

local function apply_militia(unit, record, key)
    local wanted = {}
    for _, stat in ipairs(STATS) do wanted[stat] = record.base[stat] * factor_of(stat) * vet_scale_of(key, stat) end
    local ok = write_stats(unit, wanted)
    if not ok then totals.failed = totals.failed + 1 end
    record.att_factor, record.def_factor = settings.militia_attack_factor, settings.militia_defence_factor
end

local function new_militia_record(unit, key)
    local base = {}
    for _, stat in ipairs(STATS) do
        base[stat] = read(function() return unit[stat] end)
        if type(base[stat]) ~= "number" then return nil end
        base[stat] = base[stat] / vet_scale_of(key, stat)
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
                record = is_player_militia(unit, sides) and new_militia_record(unit, key) or false
                militia_known[key] = record
            end
            local stale = record and (record.att_factor ~= settings.militia_attack_factor or record.def_factor ~= settings.militia_defence_factor)
            if stale then apply_militia(unit, record, key) end
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

local function pass(force_experience)
    totals.passes = totals.passes + 1
    local present = {}
    local units = FindAllOf("SMUnit") or {}
    local recheck = needs_recheck(#units)
    local look_at_experience = settings.vet_enabled and (force_experience or totals.passes % config.veterancy.every == 0)
    for _, unit in ipairs(units) do
        local key = address_of(unit)
        if key ~= nil then
            present[key] = true
            check_known(unit, key, recheck)
            if look_at_experience and read(function() return unit.dead end) ~= true then update_veteran(unit, key) end
        end
    end
    forget_missing(present, known)
    forget_missing(present, vets)
    if militia_factors_active() or next(militia_known) ~= nil then militia_pass(units, recheck) end
end

local function safe_pass()
    local ok, problem = pcall(pass)
    if not ok then
        last_error = tostring(problem)
        core.log.error(TAG, "pass failed: " .. last_error)
    end
end

-- Put the original values back on the units that the rules changed. Returns the number of restored units.
local function restore_all()
    local restored = 0
    for key, entry in pairs(vets) do
        if isValid(entry.object) then scale_by_tier(entry.object, entry.tier, 0) end
        vets[key] = nil
    end
    for key, record in pairs(militia_known) do
        if record and reset_militia(record) then restored = restored + 1 end
        militia_known[key] = nil
    end
    for key, record in pairs(known) do
        if record and isValid(record.object) and write_stats(record.object, record.before) then restored = restored + 1 end
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
        if record and record.before.def ~= nil and isValid(record.object) then
            count = count + 1
            def_sum = def_sum + (read(function() return record.object.def end) or 0)
            block_sum = block_sum + (read(function() return record.object.block end) or 0)
        end
    end
    if count == 0 then return { units = 0 } end
    return { units = count, def = def_sum / count, block = block_sum / count }
end

local function command_state()
    local veterans = 0
    for _ in pairs(vets) do veterans = veterans + 1 end
    return { enabled = settings.enabled, def_factor = settings.unarmored_def_factor, block_factor = settings.unarmored_block_factor,
             armored_def_min = config.armored_def_min, poll_ms = config.poll_ms, passes = totals.passes, seen = totals.seen,
             changed = totals.changed, armored = totals.armored, weapon = totals.weapon, reach = totals.reach,
             att_factor = settings.armored_att_factor, pierce_add = settings.armored_pierce_add, reach_att_add = settings.reach_att_add,
             vet_enabled = settings.vet_enabled, vet_att_per_tier = settings.vet_att_per_tier, vet_def_per_tier = settings.vet_def_per_tier,
             veterans = veterans, vet_changes = totals.vet_changes,
             failed = totals.failed, tracked = mean_changed(), last_error = last_error, militia = militia_summary() }
end

local SETTING_ARGS = {
    def_factor = "unarmored_def_factor", block_factor = "unarmored_block_factor", att_factor = "armored_att_factor",
    pierce_add = "armored_pierce_add", reach_att_add = "reach_att_add", vet_att_per_tier = "vet_att_per_tier",
    vet_def_per_tier = "vet_def_per_tier",
}

-- Turning the rule off puts the original values back. Turning only veterancy off scales the veterans back.
local function command_set(args)
    for arg_name, setting in pairs(SETTING_ARGS) do
        if args[arg_name] ~= nil then settings[setting] = args[arg_name] end
    end
    local restored = 0
    if args.enabled == false and settings.enabled then restored = restore_all() end
    if args.enabled ~= nil then settings.enabled = args.enabled end
    if args.vet_enabled ~= nil then
        if args.vet_enabled == false and settings.vet_enabled then
            for key, entry in pairs(vets) do
                if isValid(entry.object) then scale_by_tier(entry.object, entry.tier, 0) end
                vets[key] = nil
            end
        end
        settings.vet_enabled = args.vet_enabled
    end
    core.log.info(TAG, string.format("UNIT_BALANCE set enabled=%s def_factor=%s block_factor=%s vet=%s restored=%d", tostring(settings.enabled),
        tostring(settings.unarmored_def_factor), tostring(settings.unarmored_block_factor), tostring(settings.vet_enabled), restored))
    local state = command_state()
    state.restored = restored
    return state
end

-- One pass now. With the rule off it does nothing. The pass also looks at the experience of every unit.
local function command_apply()
    if settings.enabled then pass(true) end
    return command_state()
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    local factor = { type = "number", min = 0, max = 1 }
    local per_tier = { type = "number", min = 0, max = 1 }
    commands.register("InvasionMod.unit_balance_state", command_state, {})
    commands.register("InvasionMod.unit_balance_set", command_set, {
        enabled = { type = "boolean" }, def_factor = factor, block_factor = factor,
        att_factor = { type = "number", min = 0, max = 10 }, pierce_add = { type = "number", min = 0, max = 50 },
        reach_att_add = { type = "number", min = 0, max = 10 }, vet_enabled = { type = "boolean" },
        vet_att_per_tier = per_tier, vet_def_per_tier = per_tier })
    commands.register("InvasionMod.unit_balance_apply", command_apply, {})
end

core.log.info(TAG, "feature unit_balance loaded")
return { restore_all = restore_all, set_militia = set_militia, militia_summary = militia_summary }
