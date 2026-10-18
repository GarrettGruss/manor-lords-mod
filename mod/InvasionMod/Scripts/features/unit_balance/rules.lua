-- Pure rules of the unit_balance feature. No game calls here, so the fake game and plain Lua can test them.
local M = {}

-- A unit is unarmored when its own def is below the limit. A unit with def 0 and block 0 has nothing to reduce.
function M.is_unarmored(def, block, armored_def_min)
    if type(def) ~= "number" or type(block) ~= "number" then return false end
    if def >= armored_def_min then return false end
    return def > 0 or block > 0
end

-- A unit is armored (but not heavy) when its def is in [armored_def_min, heavy_def_min). Heavy units (retinue) are left alone.
function M.is_armored(def, armored_def_min, heavy_def_min)
    return type(def) == "number" and def >= armored_def_min and def < heavy_def_min
end

-- The weapon values to write for an armored unit: att times a factor, armorPierce plus an amount.
function M.weapon(att, pierce, settings)
    return att * settings.armored_att_factor, pierce + settings.armored_pierce_add
end

-- The stat writes for a unit first seen. `v` has def, block, range and (when read) att and armorPierce.
-- Returns { writes = { stat = value }, unarmored, armored, reach }.
function M.plan(v, settings, config)
    local plan = { writes = {} }
    if M.is_unarmored(v.def, v.block, config.armored_def_min) then
        plan.unarmored = true
        plan.writes.def, plan.writes.block = M.reduced(v.def, v.block, settings)
    elseif M.is_armored(v.def, config.armored_def_min, config.heavy_def_min) and type(v.att) == "number" and type(v.armorPierce) == "number" then
        plan.armored = true
        plan.writes.att, plan.writes.armorPierce = M.weapon(v.att, v.armorPierce, settings)
    end
    if settings.reach_att_add > 0 and type(v.range) == "number" and v.range >= config.reach_min and type(v.att) == "number" then
        plan.reach = true
        plan.writes.att = (plan.writes.att or v.att) + settings.reach_att_add
    end
    return plan
end

-- Experience tier: one tier for each `step` points, at most `max_tier`.
function M.vet_tier(experience, step, max_tier)
    if type(experience) ~= "number" or experience <= 0 then return 0 end
    return math.min(max_tier, math.floor(experience / step))
end

-- Stat factor of a tier.
function M.vet_factor(tier, per_tier)
    return 1 + tier * per_tier
end

-- The values to write for an unarmored unit.
function M.reduced(def, block, factors)
    return def * factors.unarmored_def_factor, block * factors.unarmored_block_factor
end

return M
