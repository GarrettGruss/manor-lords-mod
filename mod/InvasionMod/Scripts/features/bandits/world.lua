-- Game access of the bandits feature (M04). Every call runs on the game thread.
local core = require("ManorCore")

local M = {}

local function engine()
    local object = FindFirstOf("RTSMultiEngineCPP")
    if object ~= nil and object:IsValid() then return object end
    return nil
end

function M.current_day()
    local e = engine()
    if e == nil then return nil end
    local ok, value = pcall(function() return e.TemporalComponent.daysTotal end)
    if ok and type(value) == "number" then return math.floor(value) end
    return nil
end

function M.current_season()
    local e = engine()
    if e == nil then return nil end
    local ok, value = pcall(function() return e.TemporalComponent.Season end)
    if ok and type(value) == "number" then return math.floor(value) end
    return nil
end

function M.region()
    local region, problem = core.player_region()
    return region, problem
end

function M.read_values(region)
    local ok, order, approval = pcall(function() return region.publicOrder, region.Approval end)
    if not ok or type(order) ~= "number" or type(approval) ~= "number" then return nil end
    return { order = order, approval = approval }
end

function M.write_order(region, value)
    local ok, problem = pcall(function() region.publicOrder = value end)
    if not ok then return nil, tostring(problem) end
    return true
end

function M.write_approval(region, value)
    local ok, problem = pcall(function() region.Approval = value end)
    if not ok then return nil, tostring(problem) end
    return true
end

function M.families(region)
    local ok, value = pcall(function() return region:getTotalNumFamilies() end)
    if ok and type(value) == "number" then return value end
    return nil
end

-- Remove families and let a bandit squad appear at each home (the proven homeless_rebel route).
function M.rebel(count, families_per_squad)
    local ok, bandits = pcall(require, "HarnessBandits")
    if not ok then return nil, "HarnessBandits is not available: " .. tostring(bandits) end
    local answer = bandits.homeless_rebel({ count = count, families_per_squad = families_per_squad, mode = "home", template = "Brigands" })
    if not answer.ok then return nil, tostring(answer.error) end
    return answer
end

function M.homeless(region)
    local ok, value = pcall(function() return region:getNumHomelessFamilies() end)
    if ok and type(value) == "number" then return value end
    return nil
end

-- The game has a bandit pawn only when the game settings made bandit camps. Without it no bandit can spawn.
function M.bandit_pawn_exists()
    for _, pawn in ipairs(FindAllOf("PawnCPP") or {}) do
        local ok, bandit = pcall(function() return pawn:IsValid() and not pawn:GetFullName():find("Default__", 1, true) and pawn.isBandit == true end)
        if ok and bandit then return true end
    end
    return false
end

-- Villagers leave. Every `families_per_squad` families that leave form one brigand squad: squads = floor(count / families_per_squad).
-- The remaining families leave without a squad. A squad spawns only when the bandit pawn exists.
-- Returns { removed, squads, bandit_units, spawned } or nil and a message.
function M.leave(region, count, families_per_squad)
    local spawn = M.bandit_pawn_exists()
    local result = { removed = 0, squads = 0, bandit_units = 0, spawned = spawn }
    local full_squads = math.floor(count / families_per_squad)
    for _ = 1, spawn and full_squads or 0 do
        local answer, problem = M.rebel(families_per_squad, families_per_squad)
        if answer == nil then return nil, problem end
        result.removed = result.removed + (answer.families_removed or families_per_squad)
        result.squads = result.squads + #answer.squads
        result.bandit_units = result.bandit_units + (answer.bandit_units_spawned or 0)
    end
    while result.removed < count do
        local removed = core.remove_families(region, math.min(core.MAX_REBEL_FAMILIES, count - result.removed))
        if removed < 1 then break end
        result.removed = result.removed + removed
    end
    return result
end

function M.free_slots(region)
    local ok, value = pcall(function() return region:getAvailableLivingSpace().constructed end)
    if ok and type(value) == "number" then return value end
    return nil
end

function M.game_seconds()
    local e = engine()
    if e == nil then return nil end
    local ok, value = pcall(function() return e:getGameTimeAdjusted() end)
    if ok and type(value) == "number" then return value end
    return nil
end

function M.silver()
    local e = engine()
    if e == nil then return nil end
    local ok, value = pcall(function() return e.playerRef.silver end)
    if ok and type(value) == "number" then return value end
    return nil
end

function M.bandit_units()
    local ok, units = pcall(require, "HarnessUnits")
    if not ok then return nil end
    local counted, counts = pcall(units.counts)
    if not counted then return nil end
    return counts.by_side.bandit or 0
end

-- The native negotiation letter: tag "attacking", then raider_suggestSettle+<price>. The game takes the price and does not check it.
-- bandit_letter reads its paragraphs from the raw request text, so the text is built here.
function M.send_settle_letter(price)
    local ok, bandits = pcall(require, "HarnessBandits")
    if not ok then return nil, "HarnessBandits is not available: " .. tostring(bandits) end
    local tagged = bandits.bandit_tag({ tag = "attacking" })
    if not tagged.ok then return nil, "tag failed: " .. tostring(tagged.error) end
    local sent = bandits.bandit_letter({}, string.format('{"paragraphs":["raider_suggestSettle+%d"]}', price))
    if not sent.ok then return nil, "letter failed: " .. tostring(sent.error) end
    return true
end

function M.add_silver(amount)
    local e = engine()
    if e == nil then return nil, "no engine" end
    local ok, problem = pcall(function() e.playerRef.silver = e.playerRef.silver + amount end)
    if not ok then return nil, tostring(problem) end
    return true
end

return M
