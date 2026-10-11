-- HarnessLords: read and steer the AI lords (the baron and the other lords) for spike S11 of spec 10.
-- Why: the base game has AI lords (PawnCPP_AI). The baron is one of them (traits "off_map_lord", "villain").
-- The AI runs on timers in C++ and writes its decisions to three debug logs on RTSMultiEngineCPP
-- (debugLog_AI_general, debugLog_AI_tactics, debugLog_AI_construction). The steering calls need object
-- references (a pawn, a region), which the bridge cannot pass, so they live here as named commands.
-- A lord is named by its number: 1.. in the order FindAllOf("PawnCPP_AI") gives (the same order as send_letter).
-- A target is 0 for the player, or the number of a lord.
--
-- Rules: call only on the game thread. No save function. Every input is checked before it is used.

local datatable = require("HarnessDataTable")

local M = {}

M.MAX_GROUPS = 6
M.MAX_OFFSET = 60000
M.MAX_INFLUENCE = 10000
M.MAX_LOG_LINES = 40
M.MAX_NAME_CHARS = 40

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function read(fn)
    local ok, value = pcall(fn)
    if ok then return value end
    return nil
end

local function textOf(value)
    if type(value) == "string" then return value end
    if value == nil then return nil end
    return read(function() return value:ToString() end) or tostring(value)
end

-- Only a function return value may need :get(). Calling :get() on a struct element of a property array
-- crashed the game inside UE4SS (access violation, no Lua error), so property arrays are read directly.
local function unwrap(element)
    local ok, inner = pcall(function() return element:get() end)
    if ok and inner ~= nil then return inner end
    return element
end

local function shortName(object)
    if not isValid(object) then return nil end
    return read(function() return object:GetFName():ToString() end)
end

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if isValid(found) then return found end
    return nil
end

local function lords()
    local out = {}
    for _, pawn in ipairs(FindAllOf("PawnCPP_AI") or {}) do
        if isValid(pawn) and not pawn:GetFullName():find("Default__", 1, true) then out[#out + 1] = pawn end
    end
    return out
end

local function player(engineObject)
    local found = read(function() return engineObject.playerRef end)
    if isValid(found) then return found end
    return nil
end

-- 0 is the player; 1.. is a lord.
local function pawnByNumber(number, engineObject)
    if number == 0 then return player(engineObject) end
    return lords()[number]
end

local function checkedLord(request)
    local number = request.lord
    if type(number) ~= "number" or number < 1 then return nil, "lord must be a number from 1" end
    local pawn = lords()[number]
    if not pawn then return nil, "no AI lord number " .. tostring(number) .. " (found " .. #lords() .. ")" end
    return pawn
end

local function arrayTexts(array)
    local out = {}
    local count = read(function() return array:GetArrayNum() end) or 0
    for i = 1, count do out[#out + 1] = textOf(read(function() return array[i] end)) end
    return out
end

local function arrayNames(array)
    local out = {}
    local count = read(function() return array:GetArrayNum() end) or 0
    for i = 1, count do out[#out + 1] = shortName(read(function() return array[i] end)) end
    return out
end

local function squadHandles(array)
    local out = {}
    local count = read(function() return array:GetArrayNum() end) or 0
    for i = 1, count do out[#out + 1] = read(function() return array[i].Value end) end
    return out
end

local function distance2d(a, b)
    if not a or not b then return nil end
    return math.floor(math.sqrt((a.X - b.X) ^ 2 + (a.Y - b.Y) ^ 2) + 0.5)
end

local function location(actor)
    local at = read(function() return actor:K2_GetActorLocation() end)
    if not at then return nil end
    return { X = at.X, Y = at.Y, Z = at.Z }
end

---------------------------------------------------------------------------------------------
-- State (read only)
---------------------------------------------------------------------------------------------

-- Living units of each squad id: count and center. One pass over all units.
local function squadPositions()
    local per = {}
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) and read(function() return unit.dead end) ~= true then
            local id = read(function() return unit.assignedSquadID.Value end)
            -- realPos is the simulated position. The actor location of a unit did not move in the real game.
            local at = id and id > 0 and read(function() return unit.realPos end)
            if at then
                local row = per[id] or { alive = 0, x = 0, y = 0 }
                if row.alive == 0 then
                    local target = read(function() return unit:getTargetPos() end)
                    if target then row.target_x, row.target_y = math.floor(target.X + 0.5), math.floor(target.Y + 0.5) end
                    row.region = shortName(read(function() return unit.currentRegion end))
                end
                per[id] = row
                row.alive = row.alive + 1
                row.x = row.x + at.X
                row.y = row.y + at.Y
            end
        end
    end
    for _, row in pairs(per) do
        row.x = math.floor(row.x / row.alive + 0.5)
        row.y = math.floor(row.y / row.alive + 0.5)
    end
    return per
end

local function squadRows(pawn, positions, home)
    local rows = {}
    for _, id in ipairs(squadHandles(read(function() return pawn.commandedSquads end))) do
        local seen = positions[id] or { alive = 0 }
        local row = { id = id, alive = seen.alive, x = seen.x, y = seen.y, target_x = seen.target_x, target_y = seen.target_y,
                      region = seen.region }
        if seen.x and home then row.distance_to_player = distance2d({ X = seen.x, Y = seen.y }, home) end
        rows[#rows + 1] = row
    end
    return rows
end

local function relationTags(engineObject, pawnA, pawnB)
    local out = {}
    local list = read(function() return engineObject.relations end)
    local count = read(function() return list:GetArrayNum() end) or 0
    local a, b = shortName(pawnA), shortName(pawnB)
    for i = 1, count do
        local relation = read(function() return list[i] end)
        local ra, rb = shortName(read(function() return relation.pawnA end)), shortName(read(function() return relation.pawnB end))
        if (ra == a and rb == b) or (ra == b and rb == a) then
            return { tags = arrayTexts(read(function() return relation.Tags end)), friendship = read(function() return relation.friendship end),
                     status = read(function() return relation.status end) }
        end
    end
    return out
end

local function lordRow(number, pawn, engineObject, positions, home)
    return {
        lord = number, object = shortName(pawn), name = textOf(read(function() return pawn.lordsName end)),
        bandit = read(function() return pawn.isBandit end), traits = arrayTexts(read(function() return pawn.traits end)),
        influence = read(function() return pawn.influence end), silver = read(function() return pawn.silver end),
        enemies = arrayNames(read(function() return pawn.enemies end)),
        claims = read(function() return pawn.claims:GetArrayNum() end),
        with_player = relationTags(engineObject, pawn, player(engineObject)),
        squads = squadRows(pawn, positions, home),
    }
end

local function challengeRows(engineObject)
    local out = {}
    local list = read(function() return engineObject.challenges end)
    local count = read(function() return list:GetArrayNum() end) or 0
    for i = 1, count do
        local challenge = read(function() return list[i] end)
        out[#out + 1] = {
            id = read(function() return challenge.ID end), challenged = shortName(read(function() return challenge.challengedPawn end)),
            by = shortName(read(function() return challenge.challengedBy end)), days_left = read(function() return challenge.DaysLeft end),
            status = read(function() return challenge.status end), contested = read(function() return challenge.contested end),
            regions = arrayNames(read(function() return challenge.inRegardsTo end)),
        }
    end
    return out
end

local function lastLines(array, limit)
    local lines = arrayTexts(array)
    local first = math.max(1, #lines - limit + 1)
    local out = {}
    for i = first, #lines do out[#out + 1] = lines[i] end
    return out
end

-- Every AI lord: name, traits, influence, enemies, relation with the player, squads with position and orders.
-- Also the challenges and the last lines of the AI debug logs. request.log = N sets the number of log lines (0 = none).
function M.lords_state(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local home = player(engineObject) and location(player(engineObject))
    local positions = squadPositions()
    local rows = {}
    for number, pawn in ipairs(lords()) do rows[#rows + 1] = lordRow(number, pawn, engineObject, positions, home) end
    local lines = math.min(request and request.log or 12, M.MAX_LOG_LINES)
    local logs = {}
    if lines > 0 then
        for _, name in ipairs({ "debugLog_AI_general", "debugLog_AI_tactics", "debugLog_AI_construction" }) do
            logs[name] = lastLines(read(function() return engineObject[name] end), lines)
        end
    end
    local open = read(function() return engineObject.openClaims:GetArrayNum() end)
    return { ok = true, lords = rows, challenges = challengeRows(engineObject), open_claims = open, logs = logs,
             player_region = shortName(read(function() return player(engineObject).currentRegion end)),
             player_at = home and { x = math.floor(home.X), y = math.floor(home.Y) },
             settings = { spawn_ai_players = read(function() return engineObject.spawnAIPlayers end),
                          declare_war_instant = read(function() return engineObject.declareWarInstant end),
                          ai_can_build = read(function() return engineObject.AI_canBuild end) } }
end

---------------------------------------------------------------------------------------------
-- Steering
---------------------------------------------------------------------------------------------

local function checkedTarget(request, engineObject)
    local number = request.target
    if type(number) ~= "number" or number < 0 then return nil, "target must be 0 (the player) or a lord number" end
    local pawn = pawnByNumber(number, engineObject)
    if not isValid(pawn) then return nil, "no pawn for target " .. tostring(number) end
    return pawn
end

-- PawnCPP:declareWar(targetPawn) on the lord. Reports the relation tags before and after.
function M.lord_declare_war(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local lord, problem = checkedLord(request)
    if not lord then return { ok = false, error = problem } end
    local target, why = checkedTarget(request, engineObject)
    if not target then return { ok = false, error = why } end
    local before = relationTags(engineObject, lord, target)
    local ok, err = pcall(function() lord:declareWar(target) end)
    if not ok then return { ok = false, error = "declareWar: " .. tostring(err) } end
    return { ok = true, before = before, after = relationTags(engineObject, lord, target),
             enemies = arrayNames(read(function() return lord.enemies end)) }
end

-- PawnCPP:declarePeace(targetPawn) on the lord.
function M.lord_declare_peace(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local lord, problem = checkedLord(request)
    if not lord then return { ok = false, error = problem } end
    local target, why = checkedTarget(request, engineObject)
    if not target then return { ok = false, error = why } end
    local before = relationTags(engineObject, lord, target)
    local ok, err = pcall(function() lord:declarePeace(target) end)
    if not ok then return { ok = false, error = "declarePeace: " .. tostring(err) } end
    return { ok = true, before = before, after = relationTags(engineObject, lord, target),
             enemies = arrayNames(read(function() return lord.enemies end)) }
end

-- Write the influence of the lord (the AI logged "claimRegions: not enough influence").
function M.lord_set_influence(request)
    local lord, problem = checkedLord(request)
    if not lord then return { ok = false, error = problem } end
    local value = request.value
    if type(value) ~= "number" or value < 0 or value > M.MAX_INFLUENCE then
        return { ok = false, error = "value must be a number from 0 to " .. M.MAX_INFLUENCE }
    end
    local before = read(function() return lord.influence end)
    local ok, err = pcall(function() lord.influence = math.floor(value) end)
    if not ok then return { ok = false, error = "write influence: " .. tostring(err) } end
    return { ok = true, before = before, after = read(function() return lord.influence end) }
end

-- RTSMultiEngineCPP:initChallenge(challengedPawn, challengedBy, region): the lord challenges the target over the
-- target's current region (the player: the region the camera is in).
function M.lord_challenge(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local lord, problem = checkedLord(request)
    if not lord then return { ok = false, error = problem } end
    local target, why = checkedTarget(request, engineObject)
    if not target then return { ok = false, error = why } end
    local region = read(function() return target.currentRegion end)
    if not isValid(region) then return { ok = false, error = "the target has no current region" } end
    local before = #challengeRows(engineObject)
    local ok, err = pcall(function() engineObject:initChallenge(target, lord, region) end)
    if not ok then return { ok = false, error = "initChallenge: " .. tostring(err) } end
    return { ok = true, region = shortName(region), challenges_before = before, challenges = challengeRows(engineObject) }
end

-- PawnCPP:layClaim(region, useFavour false, consumeInfluence false) on the target's current region.
function M.lord_claim(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local lord, problem = checkedLord(request)
    if not lord then return { ok = false, error = problem } end
    local target, why = checkedTarget(request, engineObject)
    if not target then return { ok = false, error = why } end
    local region = read(function() return target.currentRegion end)
    if not isValid(region) then return { ok = false, error = "the target has no current region" } end
    local before = read(function() return lord.claims:GetArrayNum() end)
    local ok, err = pcall(function() lord:layClaim(region, false, false) end)
    if not ok then return { ok = false, error = "layClaim: " .. tostring(err) } end
    return { ok = true, region = shortName(region), claims_before = before, claims_after = read(function() return lord.claims:GetArrayNum() end),
             open_claims = read(function() return engineObject.openClaims:GetArrayNum() end) }
end

-- spawnArmy with the lord as owner, dx, dy from the player pawn. One squad for each count.
function M.lord_spawn_army(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local lord, problem = checkedLord(request)
    if not lord then return { ok = false, error = problem } end
    local template = request.template
    if not template or not datatable.has_row(template, "units") then
        return { ok = false, error = "no unit template named " .. tostring(template) .. " (rows of DT_UnitTemplates)" }
    end
    local count = request.count or 1
    if count < 1 or count > M.MAX_GROUPS then return { ok = false, error = "count must be 1 to " .. M.MAX_GROUPS } end
    local dx, dy = request.dx or 0, request.dy or 0
    if math.abs(dx) > M.MAX_OFFSET or math.abs(dy) > M.MAX_OFFSET then return { ok = false, error = "dx and dy must be within " .. M.MAX_OFFSET } end
    local home = player(engineObject) and location(player(engineObject))
    if not home then return { ok = false, error = "no player position" } end
    local names = {}
    for i = 1, count do names[i] = FName(template) end
    local ok, returned = pcall(function()
        return engineObject:spawnArmy({ X = home.X + dx, Y = home.Y + dy, Z = home.Z }, names, lord, 0, 0)
    end)
    if not ok then return { ok = false, error = "spawnArmy: " .. tostring(returned) } end
    local ids = {}
    for i = 1, #returned do ids[#ids + 1] = read(function() return unwrap(returned[i]).Value end) end
    return { ok = true, squads = ids, at = { x = math.floor(home.X + dx), y = math.floor(home.Y + dy) },
             commanded = squadHandles(read(function() return lord.commandedSquads end)) }
end

-- RTSMultiEngineCPP:spawnNewAILord(name, isFemale false, no portrait, canBuild = request.build == 1). Returns the new lord number.
function M.spawn_ai_lord(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local name = request.name
    if type(name) ~= "string" or name == "" or #name > M.MAX_NAME_CHARS then
        return { ok = false, error = "name must be 1 to " .. M.MAX_NAME_CHARS .. " characters" }
    end
    local before = #lords()
    local canBuild = request.build == 1
    local ok, pawn = pcall(function() return engineObject:spawnNewAILord(name, false, nil, canBuild) end)
    if not ok then return { ok = false, error = "spawnNewAILord: " .. tostring(pawn) } end
    local after = lords()
    local number
    for i, found in ipairs(after) do
        if isValid(pawn) and shortName(found) == shortName(pawn) then number = i end
    end
    return { ok = true, lords_before = before, lords_after = #after, lord = number, object = shortName(pawn), can_build = canBuild }
end

-- PawnCPP_AI:startAI(speed, canBuild) on the lord. A new lord may need it to run its timers.
function M.lord_start_ai(request)
    local lord, problem = checkedLord(request)
    if not lord then return { ok = false, error = problem } end
    local speed = request.value or 1
    if speed <= 0 or speed > 100 then return { ok = false, error = "value (speed) must be above 0 and at most 100" } end
    local canBuild = request.build == 1
    local ok, err = pcall(function() lord:startAI(speed, canBuild) end)
    if not ok then return { ok = false, error = "startAI: " .. tostring(err) } end
    return { ok = true, speed = speed, can_build = canBuild }
end

---------------------------------------------------------------------------------------------
-- Regions (spike S13: dynamic lords)
---------------------------------------------------------------------------------------------


local function regions(engineObject)
    local out = {}
    local list = read(function() return engineObject.regions end)
    local count = read(function() return list:GetArrayNum() end) or 0
    for i = 1, count do
        local region = read(function() return list[i] end)
        if isValid(region) then out[#out + 1] = region end
    end
    return out
end

-- A region named by its object name (for example "Goldhof"), the same name lords_state prints.
local function checkedRegion(request, engineObject)
    if type(request.region) ~= "string" or request.region == "" then return nil, "region (an object name) is required" end
    for _, region in ipairs(regions(engineObject)) do
        if shortName(region) == request.region then return region end
    end
    return nil, "no region named " .. request.region
end

local function buildingCount(region)
    local list = read(function() return region:GetBuildings() end)
    if list == nil then return nil end
    return read(function() return list:GetArrayNum() end) or read(function() return #list end)
end

local function regionRow(region)
    return {
        region = shortName(region), name = textOf(read(function() return region.regionName end)),
        owner = shortName(read(function() return region.ownerPawn end)),
        settled = read(function() return region.isSettled end), settlement_type = read(function() return region.settlementType end),
        level = read(function() return region.settlementLevel end), town_center = shortName(read(function() return region.townCenter end)),
        manor = shortName(read(function() return region.manor end)), buildings = buildingCount(region),
        families = read(function() return region:getTotalNumFamilies() end),
    }
end

-- Every region: owner, settled, settlement type and level, town center, manor, buildings, families. Read only.
function M.regions_state()
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local rows = {}
    for _, region in ipairs(regions(engineObject)) do rows[#rows + 1] = regionRow(region) end
    return { ok = true, regions = rows }
end

-- RTSMultiEngineCPP:addPawnRelations(lord): a lord made by spawnNewAILord had no relation row with anyone.
function M.lord_relations(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local lord, problem = checkedLord(request)
    if not lord then return { ok = false, error = problem } end
    local before = read(function() return engineObject.relations:GetArrayNum() end)
    local ok, err = pcall(function() engineObject:addPawnRelations(lord) end)
    if not ok then return { ok = false, error = "addPawnRelations: " .. tostring(err) } end
    return { ok = true, relations_before = before, relations_after = read(function() return engineObject.relations:GetArrayNum() end),
             with_player = relationTags(engineObject, lord, player(engineObject)) }
end

-- PawnCPP:settleRegion is NOT offered: called from Lua it crashed the game 3 of 3 times (access violation at 0x34c, with a new
-- lord, with the player pawn, and with an outpost region). See docs/specs/10-invasion-testability/implementation-notes/dynamic-lords.md.

-- Write Region.ownerPawn = lord (the change a won challenge made in spike S11).
function M.lord_take_region(request)
    local engineObject = engine()
    if not engineObject then return { ok = false, error = "no RTSMultiEngineCPP" } end
    local lord, problem = checkedLord(request)
    if not lord then return { ok = false, error = problem } end
    local region, why = checkedRegion(request, engineObject)
    if not region then return { ok = false, error = why } end
    local before = regionRow(region)
    local ok, err = pcall(function() region.ownerPawn = lord end)
    if not ok then return { ok = false, error = "write ownerPawn: " .. tostring(err) } end
    return { ok = true, before = before, after = regionRow(region) }
end

return M
