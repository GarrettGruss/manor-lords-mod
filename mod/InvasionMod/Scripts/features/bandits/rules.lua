-- Pure rules of the bandits feature (M04). No game access, so the fake game and plain Lua can test them.
local M = {}

-- debuff = (100 - approval) x difficulty, rounded up (M00 decisions 11 to 15, 30).
function M.debuff(approval, difficulty)
    local gap = math.max(0, 100 - approval)
    return math.ceil(gap * difficulty)
end

function M.clamp_order(value)
    return math.max(0, math.min(100, value))
end

function M.debuffed_order(natural, approval, difficulty)
    return M.clamp_order(natural - M.debuff(approval, difficulty))
end

-- The game rewrites Region.publicOrder from time to time. A value that differs from the last value
-- the mod wrote is the game's own value. A value equal to it is still the mod's write.
-- Returns the natural order the mod must use now.
function M.natural_order(current, last_written, known_natural)
    if last_written == nil or known_natural == nil then return current end
    if current == last_written then return known_natural end
    return current
end

-- First threshold that the order is under. thresholds: list of { below = 75, chance = 0.10 }, sorted from the highest.
-- The chance of the lowest matching band applies.
function M.chance_for(order, bands)
    local chance = 0
    for _, band in ipairs(bands) do
        if order < band.below then chance = band.chance end
    end
    return chance
end

-- One roll for the region. roll is a number in [0, 1). True when the roll is under the chance.
function M.should_convert(order, bands, roll)
    return roll < M.chance_for(order, bands)
end

-- A season tick is due when the season differs from the saved one.
-- last -1 means no season is saved yet: the caller only stores the season then and does not roll.
function M.season_changed(current, last)
    return last >= 0 and current ~= last
end

return M
