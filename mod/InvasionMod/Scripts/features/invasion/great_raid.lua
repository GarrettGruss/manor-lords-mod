-- Pure rules of the great raid clock (no game calls), so a test can run them without a game.
local M = {}

-- The estimated end day of the clock: the clock ends at the first day of game year `start_year`.
-- `seasons_done` is the number of season changes since game year 1 began. The estimate uses a fixed season length.
function M.estimated_end_day(today, seasons_done, config)
    if config.start_year < 1 then error("great_raid: bad start year", 0) end
    local seasons_left = math.max(0, (config.start_year - 1) * 4 - seasons_done)
    return today + seasons_left * config.season_estimate_days
end

function M.days_left(end_day, today)
    return end_day - today
end

function M.is_due(end_day, today)
    return end_day > 0 and today >= end_day
end

-- Text of the clock banner: the game years left to the start year.
function M.years_text(years_left)
    return string.format("Great raid in %d %s", years_left, years_left == 1 and "year" or "years")
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
