-- Pure rules of the refugees feature (M09). No game access.
local M = {}

-- Families that leave a lost vassal: a share of its families, rounded up, at least 1.
function M.wave_families(vassal_families, share)
    return math.max(1, math.ceil(vassal_families * share))
end

-- settleRegion adds families_per_call families each call. The wave comes in whole calls.
function M.calls_for(wave_families, families_per_call, max_calls)
    local calls = math.floor(wave_families / families_per_call + 0.5)
    return math.max(1, math.min(max_calls, calls))
end

-- A share between min and max for one wave. `roll` is a random number from 0 to 1.
function M.share_from_roll(roll, share_min, share_max)
    return share_min + (share_max - share_min) * roll
end

-- The timer ran out: start_day is stored as day + 1.
function M.timed_out(start_day, today, timeout_days)
    return start_day > 0 and today + 1 - start_day >= timeout_days
end

return M
