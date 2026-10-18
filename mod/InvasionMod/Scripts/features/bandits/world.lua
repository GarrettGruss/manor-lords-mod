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

function M.free_slots(region)
    local ok, value = pcall(function() return region:getAvailableLivingSpace().constructed end)
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

return M
