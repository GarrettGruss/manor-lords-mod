-- Pure rules of the vassals feature (M07). No game access, so a fake-game test can run them.
local M = {}

M.LOYALTY_MIN = 0
M.LOYALTY_MAX = 100
M.NO_REGION = "none"

function M.clamp_loyalty(value)
    return math.max(M.LOYALTY_MIN, math.min(M.LOYALTY_MAX, math.floor(value + 0.5)))
end

-- The goal is written only when it differs, because a write is a game call.
function M.goal_needs_write(current, wanted)
    return current ~= wanted
end

-- The first slot number (1 to max) whose region is empty, or nil when all slots are used.
function M.free_slot(regions, max_vassals)
    for slot = 1, max_vassals do
        if regions[slot] == nil or regions[slot] == M.NO_REGION then return slot end
    end
    return nil
end

-- The slot number that holds this region, or nil.
function M.slot_of_region(regions, max_vassals, region)
    for slot = 1, max_vassals do
        if regions[slot] == region then return slot end
    end
    return nil
end

function M.count_used(regions, max_vassals)
    local count = 0
    for slot = 1, max_vassals do
        if regions[slot] ~= nil and regions[slot] ~= M.NO_REGION then count = count + 1 end
    end
    return count
end

-- The growth check is due when enough game days have passed since the handover.
function M.growth_check_due(handed_day, today, days)
    return handed_day > 0 and today + 1 - handed_day >= days -- handed_day is stored as day + 1
end

-- A lord that added fewer than min_new buildings stalled.
function M.is_stalled(before, now, min_new)
    return now - before < min_new
end

-- A relation tag that means war.
function M.has_war_tag(tags)
    for _, tag in ipairs(tags or {}) do
        if tag == "at_war" then return true end
    end
    return false
end

return M
