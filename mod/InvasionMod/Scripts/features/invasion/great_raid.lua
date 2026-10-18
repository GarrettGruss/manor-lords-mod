-- Pure rules of the great raid clock (no game calls), so a test can run them without a game.
local M = {}

-- The clock length in game days: a random whole number between min_days and max_days.
function M.length(config, random)
    if config.max_days < config.min_days then error("great_raid: bad range", 0) end
    return random(config.min_days, config.max_days)
end

function M.days_left(end_day, today)
    return end_day - today
end

function M.is_due(end_day, today)
    return end_day > 0 and today >= end_day
end

-- Text for the banner. The years are shown as a hint for long times.
function M.text(days_left)
    if days_left <= 0 then return "The great raid is here" end
    local unit = days_left == 1 and "day" or "days"
    return string.format("Great raid in %d %s", days_left, unit)
end

return M
