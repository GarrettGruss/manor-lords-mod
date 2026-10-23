-- Pure text rules of the raid widget (M02 iteration 05). No game calls, so a test can run them.
-- update-raid-banners: the menu lists the upcoming raids all the time (type, target, size, days left). A switched-off raid type has an empty line.
local M = {}

local PHASE_TEXT = { [2] = "final battle", [3] = "won" }
local TERMS_TEXT = { [0] = "none", [1] = "offered", [2] = "payment made", [3] = "vassal" }

local function days_text(days)
    if days <= 0 then return "today" end
    return string.format("in %d %s", days, days == 1 and "day" or "days")
end

-- `raid` is { days_left, target, raiders, squads, size }: one planned raid.
local function raid_text(raid)
    local size = raid.size and (raid.size .. " ") or ""
    return string.format("%s, %sabout %d raiders (%d squads), %s", raid.target, size, raid.raiders, raid.squads, days_text(raid.days_left))
end

function M.next_raid(info)
    local plunder = info.upcoming and info.upcoming.plunder
    if plunder == nil then return "Yearly raid: not planned yet" end
    return "Yearly raid: " .. raid_text(plunder)
end

-- Empty when the subjugation raid is switched off.
function M.subjugation_raid(info)
    local sub = info.upcoming and info.upcoming.subjugation
    if sub == nil then return "" end
    if not sub.planned then return "Subjugation raid: not planned yet" end
    return "Subjugation raid: " .. raid_text(sub)
end

-- Empty when great raids are off.
function M.great_raid(info)
    if info.great_raids == false then return "" end
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
    return { M.next_raid(info), M.subjugation_raid(info), M.great_raid(info), M.difficulty(info), M.terms(terms) }
end

return M
