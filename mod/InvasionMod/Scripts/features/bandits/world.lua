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

local function bandit_pawn()
    for _, pawn in ipairs(FindAllOf("PawnCPP") or {}) do
        local ok, bandit = pcall(function() return pawn:IsValid() and not pawn:GetFullName():find("Default__", 1, true) and pawn.isBandit == true end)
        if ok and bandit then return pawn end
    end
    return nil
end

function M.bandit_pawn_exists()
    return bandit_pawn() ~= nil
end

local function camp_place()
    local ok, encampment = pcall(require, "HarnessEncampment")
    if not ok then return nil end
    local read_ok, answer = pcall(encampment.encampment_sites, nil, '{"type":100}')
    if not read_ok or type(answer) ~= "table" or not answer.sites then return nil end
    local last = answer.sites[#answer.sites]
    return last and last.at or nil
end

local function distance_to_village(at)
    local e = engine()
    if at == nil or e == nil then return nil end
    local ok, village = pcall(function() return e.playerRef:K2_GetActorLocation() end)
    if not ok or village == nil then return nil end
    return math.floor(math.sqrt((at.x - village.X) ^ 2 + (at.y - village.Y) ^ 2))
end

-- One bandit camp (18 Brigands). The same call makes the bandit pawn when the game has none (bandit camps 0).
-- The game picks the place: spawnBanditCamp has no argument. A new pawn has no relation row, so addPawnRelations follows.
-- Returns { pawn_created, bandit_units, at, distance } or nil and a message.
function M.spawn_camp()
    local e = engine()
    if e == nil then return nil, "no RTSMultiEngineCPP" end
    local units_before = M.bandit_units() or 0
    local had_pawn = bandit_pawn() ~= nil
    local called, problem = pcall(function() e:spawnBanditCamp() end)
    if not called then return nil, "spawnBanditCamp: " .. tostring(problem) end
    local pawn = bandit_pawn()
    if not had_pawn then
        if pawn == nil then return nil, "spawnBanditCamp made no bandit pawn" end
        local related, why = pcall(function() e:addPawnRelations(pawn) end)
        if not related then core.log.warn("Bandits", "addPawnRelations failed: " .. tostring(why)) end
    end
    local at = camp_place()
    return { pawn_created = not had_pawn, bandit_units = (M.bandit_units() or 0) - units_before, at = at, distance = distance_to_village(at) }
end

-- Villagers leave and one bandit camp appears for the leave event (the number of families does not change the number of camps).
-- Returns { removed, camps, squads, bandit_units, spawned, pawn_created, at, distance } or nil and a message.
function M.leave(region, count)
    local result = { removed = 0, camps = 0, squads = 0, bandit_units = 0, spawned = false, pawn_created = false }
    while result.removed < count do
        local removed = core.remove_families(region, math.min(core.MAX_REBEL_FAMILIES, count - result.removed))
        if removed < 1 then break end
        result.removed = result.removed + removed
    end
    if result.removed < 1 then return result end
    local camp, problem = M.spawn_camp()
    if camp == nil then
        core.log.error("Bandits", "camp failed: " .. tostring(problem))
        return result
    end
    result.camps, result.squads, result.spawned = 1, 1, true
    result.bandit_units, result.pawn_created, result.at, result.distance = camp.bandit_units, camp.pawn_created, camp.at, camp.distance
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
