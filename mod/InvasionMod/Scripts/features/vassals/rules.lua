-- Pure rules of the vassals feature (M07). No game access, so a fake-game test can run them.
local M = {}

M.NO_REGION = "none"

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

-- Ruins that complete a sack: a share of the buildings at the start of the sack, rounded up (decision 28).
function M.ruins_needed(total, share)
    return math.ceil(total * share - 1e-9)
end

function M.sack_complete(total, ruins, share)
    return ruins >= M.ruins_needed(total, share)
end

-- Standing buildings still to collapse so that `needed` ruins exist.
function M.houses_to_collapse(needed, ruins)
    return math.max(0, needed - ruins)
end

-- A restored village counts as rebuilt when this many buildings stand again (a share of the buildings before the wipe, at least 1).
function M.rebuilt_target(buildings_at_wipe, share)
    return math.max(1, math.ceil(buildings_at_wipe * share - 1e-9))
end

-- The first used wiped record whose region is `region` (or the first used one when `region` is nil). Returns the index or nil.
function M.find_wiped(regions, max_wiped, region)
    for index = 1, max_wiped do
        local name = regions[index]
        if name ~= nil and name ~= M.NO_REGION and (region == nil or region == name) then return index end
    end
    return nil
end

-- Refusal text for a restore, or nil when it may go on. The gold is checked first; nothing is taken before all checks pass.
function M.restore_refusal(wiped_index, free_slot, silver, cost)
    if wiped_index == nil then return "no wiped region to restore" end
    if free_slot == nil then return "all vassal slots are used" end
    if type(silver) ~= "number" or silver < cost then return string.format("silver %s is below the restore cost %d", tostring(silver), cost) end
    return nil
end

return M
