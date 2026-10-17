-- Pure rules of the unit_balance feature. No game calls here, so the fake game and plain Lua can test them.
local M = {}

-- A unit is unarmored when its own def is below the limit. A unit with def 0 and block 0 has nothing to reduce.
function M.is_unarmored(def, block, armored_def_min)
    if type(def) ~= "number" or type(block) ~= "number" then return false end
    if def >= armored_def_min then return false end
    return def > 0 or block > 0
end

-- The values to write for an unarmored unit.
function M.reduced(def, block, factors)
    return def * factors.unarmored_def_factor, block * factors.unarmored_block_factor
end

return M
