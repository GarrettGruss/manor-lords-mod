-- Pure text rules of the raid widget (M02 iteration 05). No game calls, so a test can run them.
local M = {}

local PHASE_TEXT = { [2] = "final battle", [3] = "won" }
local TERMS_TEXT = { [0] = "none", [1] = "offered", [2] = "payment made", [3] = "vassal" }

local function days_text(days)
    if days <= 0 then return "today" end
    return string.format("in %d %s", days, days == 1 and "day" or "days")
end

function M.next_raid(info)
    if info.raid_days_left == nil then return "Next raid: not planned yet" end
    return "Next raid: " .. days_text(info.raid_days_left)
end

function M.size_estimate(info)
    if info.raiders == nil then return "Size estimate: not known yet" end
    return string.format("Size estimate: about %d raiders (%d squads)", info.raiders, info.squads)
end

function M.great_raid(info)
    local phase = info.great_phase or 0
    if phase == 1 then return string.format("Great raid: wave %d of %d", info.great_wave, info.great_waves) end
    if phase > 1 then return "Great raid: " .. PHASE_TEXT[phase] end
    if info.great_days_left == nil then return "Great raid: clock not started" end
    return "Great raid: " .. days_text(info.great_days_left)
end

function M.difficulty(info)
    if info.difficulty_chosen then return string.format("Difficulty: %d", info.difficulty) end
    return string.format("Difficulty: %d (not picked yet)", info.difficulty)
end

-- `terms` is the summary of the terms feature, or nil when that feature is off.
function M.terms(terms)
    if terms == nil then return "Terms: not in this game" end
    local text = TERMS_TEXT[terms.state] or "unknown"
    if terms.state == 1 and terms.offer then
        text = string.format("offered, %d silver or vassalage (%d a year)", terms.offer.payment, terms.offer.tribute)
    end
    return "Terms: " .. text
end

-- The lines of the widget, top to bottom.
function M.all(info, terms)
    return { M.next_raid(info), M.size_estimate(info), M.great_raid(info), M.difficulty(info), M.terms(terms) }
end

return M
