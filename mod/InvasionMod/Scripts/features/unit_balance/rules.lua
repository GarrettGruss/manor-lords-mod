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

-- The values to write for an unarmored unit.
function M.reduced(def, block, factors)
    return def * factors.unarmored_def_factor, block * factors.unarmored_block_factor
end

return M
