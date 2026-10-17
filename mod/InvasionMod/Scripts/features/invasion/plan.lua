-- Pure rules of the raid plan (no game calls), so a test can run them without a game.
local M = {}

M.SIZE_CLASSES = { small = 1, medium = 2, large = 3 }
M.SIZE_NAMES = { "small", "medium", "large" }

-- A random whole number from low to high. The random function is a parameter so a test can fix it.
function M.pick(random, low, high)
    if high < low then error("plan: bad range " .. low .. ".." .. high, 0) end
    return random(low, high)
end

-- Raid size in squads: base size multiplier times difficulty (decisions 8 and 22).
function M.squads(size_class, difficulty, multipliers)
    local multiplier = multipliers[M.SIZE_NAMES[size_class]]
    if multiplier == nil then error("plan: unknown size class " .. tostring(size_class), 0) end
    return multiplier * difficulty
end

-- Plan the first raid. `today` is the game day when the plan is made.
-- The warning cannot start before the plan exists, so a short wait gives a shorter warning.
function M.first_raid(today, difficulty, config, random)
    local wait = M.pick(random, config.first_raid_days_min, config.first_raid_days_max)
    local warning = math.min(M.pick(random, config.warning_days_min, config.warning_days_max), wait)
    local size_class = M.pick(random, 1, #M.SIZE_NAMES)
    return {
        plan_day = today,
        raid_day = today + wait,
        warning_day = today + wait - warning,
        size_class = size_class,
        squads = M.squads(size_class, difficulty, config.size_multipliers),
    }
end

function M.banner_text(days_left, squads, squad_units)
    local raiders = squads * squad_units
    local unit = days_left == 1 and "day" or "days"
    return string.format("Raid in %d %s, about %d raiders", days_left, unit, raiders)
end

return M
