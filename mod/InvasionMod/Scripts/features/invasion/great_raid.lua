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

-- Phases of the great raid in ModState (iteration 06).
M.PHASE = { clock = 0, waves = 1, final = 2, won = 3 }

-- What the daily step does next. `at` = { phase, wave, waves, last_day, today, due }, `cfg` = { wave_gap_days, relief_delay_days }.
-- Returns "wave" (spawn the next wave), "relief" (spawn the relief army and the final battle), or nil.
function M.next_action(at, cfg)
    if at.phase == M.PHASE.clock then
        if at.due then return "wave" end
        return nil
    end
    if at.phase ~= M.PHASE.waves then return nil end
    local waited = at.today - at.last_day
    if at.wave < at.waves then
        if waited >= cfg.wave_gap_days then return "wave" end
        return nil
    end
    if waited >= cfg.relief_delay_days then return "relief" end
    return nil
end

-- The relief army templates: the list is cycled over the squads.
function M.relief_templates(count, templates)
    local list = {}
    for index = 1, count do list[index] = templates[(index - 1) % #templates + 1] end
    return list
end

return M
