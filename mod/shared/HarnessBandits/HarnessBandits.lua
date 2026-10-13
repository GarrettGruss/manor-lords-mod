-- HarnessBandits: negotiate with the bandit faction (the "Outlaws" lord) so raiders settle (spec 15).
-- Why: the game offers the letter paragraph `raider_suggestSettle` (DT_Para, category Negotiation) to the player.
-- The paragraph needs the relation tag "attacking" between the player and the bandit lord, and the player sends it with
-- PawnCPP:sendLetter(banditPawn, paragraphs). The bridge cannot pass a pawn, so these named commands do it.
-- The letter names a paragraph with an amount as "<id>+<silver>".
-- Commands: bandit_state (read only), bandit_tag, bandit_letter, settle_raiders (the developer cheat).
-- Reverse direction (families become bandits, see implementation-notes/homeless-rebellion.md):
--   bandit_spawn_at (bandit squads at a chosen point), bandit_turn (SMUnit:turnToBandit on harness-made player units),
--   bandit_kill_squads (SMUnit:just_die on the units of chosen bandit squads, for example a raid),
--   homeless_rebel (remove families, then bandit squads appear at their homes),
--   rebel_raid_rally (remove families, then a real raid aimed at a forest spot; it rallies at the AI waypoint).
--
-- Rules: call only on the game thread. No save function. Every input is checked before it is used.

local units = require("HarnessUnits")
local battle = require("HarnessBattle")
local sack = require("HarnessSack")
local datatable = require("HarnessDataTable")
local raids = require("HarnessRaids")
local housing = require("HarnessHousing")
local core = require("ManorCore")

local M = {}

M.TAGS = { attacking = true, acquainted = true, at_war = true }
M.PARAGRAPHS = { raider_greeting = true, raider_suggestSettle = true, raider_acceptSettle = true, raider_refuseSettle = true }
M.MAX_PARAGRAPHS = 4

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

local function shortName(object)
    if not isValid(object) then return nil end
    return read(function() return object:GetFName():ToString() end)
end

local function arrayTexts(array)
    local out = {}
    local count = read(function() return array:GetArrayNum() end) or 0
    for i = 1, count do out[#out + 1] = textOf(read(function() return array[i] end)) end
    return out
end

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if isValid(found) then return found end
    return nil
end

local function playerPawn(engineObject)
    local found = read(function() return engineObject.playerRef end)
    if isValid(found) then return found end
    return nil
end

local function banditPawn()
    for _, pawn in ipairs(FindAllOf("PawnCPP_AI") or {}) do
        if isValid(pawn) and not pawn:GetFullName():find("Default__", 1, true) and read(function() return pawn.isBandit end) == true then
            return pawn
        end
    end
    return nil
end

local function parties()
    local engineObject = engine()
    if not engineObject then return nil, "no RTSMultiEngineCPP" end
    local player = playerPawn(engineObject)
    if not player then return nil, "the player pawn is not loaded" end
    local bandit = banditPawn()
    if not bandit then return nil, "no bandit pawn (isBandit) found" end
    return { engine = engineObject, player = player, bandit = bandit }
end

local function relationRow(engineObject, pawnA, pawnB)
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
    return { tags = {}, missing = true }
end

-- Families in the regions the player owns.
local function playerFamilies(player)
    local total, homeless, regions = 0, 0, {}
    for _, region in ipairs(FindAllOf("Region") or {}) do
        if isValid(region) and read(function() return region.ownerPawn end) == player then
            local families = read(function() return region:getTotalNumFamilies() end) or 0
            local lost = read(function() return region:getNumHomelessFamilies() end) or 0
            total = total + families
            homeless = homeless + lost
            -- Vacant slots matter: a settle adds a family only if a home is free (spec 15).
            local space = read(function() return region:getAvailableLivingSpace() end) or {}
            regions[#regions + 1] = { name = textOf(read(function() return region.regionName end)), families = families, homeless = lost,
                                      vacant_slots = space.constructed or 0, vacant_slots_unbuilt = space.unconstructed or 0 }
        end
    end
    return total, regions, homeless
end

local function snapshot(who)
    local families, regions, homeless = playerFamilies(who.player)
    local counts = units.counts()
    return {
        families = families, homeless_families = homeless, regions = regions,
        bandit_units = counts.by_side.bandit or 0, player_units = counts.by_side.player or 0,
        silver = read(function() return who.player.silver end), influence = read(function() return who.player.influence end),
        bandit_silver = read(function() return who.bandit.silver end),
        relation = relationRow(who.engine, who.player, who.bandit),
        outbox = read(function() return who.player.outbox:GetArrayNum() end),
        bandit_inbox = read(function() return who.bandit.InBox:GetArrayNum() end),
        quests = read(function() return who.bandit.quests:GetArrayNum() end),
        player_quests = read(function() return who.player.quests:GetArrayNum() end),
    }
end

-- Read only: families, bandit units, silver, influence and the relation tags between the player and the bandit lord.
function M.bandit_state()
    local who, problem = parties()
    if not who then return { ok = false, error = problem } end
    local state = snapshot(who)
    state.ok = true
    state.bandit = shortName(who.bandit)
    return state
end

-- RTSMultiEngineCPP:addRelationTag(player, bandit, tag), or changeRelationTags to remove it (remove = 1).
function M.bandit_tag(request)
    if not M.TAGS[request.tag or ""] then return { ok = false, error = "tag must be one of: attacking, acquainted, at_war" } end
    local who, problem = parties()
    if not who then return { ok = false, error = problem } end
    local before = relationRow(who.engine, who.player, who.bandit)
    local ok, err
    if request.remove == 1 then
        ok, err = pcall(function() who.player:changeRelationTags(who.bandit, {}, { FName(request.tag) }) end)
    else
        ok, err = pcall(function() who.engine:addRelationTag(who.player, who.bandit, FName(request.tag)) end)
    end
    if not ok then return { ok = false, error = "tag change: " .. tostring(err) } end
    return { ok = true, before = before, after = relationRow(who.engine, who.player, who.bandit) }
end

local function paragraphNames(raw)
    local names = {}
    local inner = (raw or ""):match('"paragraphs"%s*:%s*%[(.-)%]') or ""
    for name in inner:gmatch('"([^"]*)"') do
        -- A paragraph with an amount is named "<id>+<amount>", for example "raider_suggestSettle+30" (hook on sendLetter, spec 15).
        local base, amount = name:match("^([%w_]+)%+(%d+)$")
        if not M.PARAGRAPHS[base or name] or (amount and #amount > 6) then return nil, "paragraph not allowed: " .. tostring(name) end
        names[#names + 1] = FName(name)
    end
    if #names == 0 or #names > M.MAX_PARAGRAPHS then return nil, "give 1 to " .. M.MAX_PARAGRAPHS .. " paragraphs" end
    return names
end

-- PawnCPP:sendLetter from the player to the bandit lord. Reports the state before and after.
function M.bandit_letter(_, raw)
    local names, why = paragraphNames(raw)
    if not names then return { ok = false, error = why } end
    local who, problem = parties()
    if not who then return { ok = false, error = problem } end
    local before = snapshot(who)
    local ok, err = pcall(function() who.player:sendLetter(who.bandit, names) end)
    if not ok then return { ok = false, error = "sendLetter: " .. tostring(err) } end
    return { ok = true, before = before, after = snapshot(who) }
end

-- MLCheatManager:SettleRaiders, the developer cheat. Reports the state before and after.
function M.settle_raiders()
    local who, problem = parties()
    if not who then return { ok = false, error = problem } end
    local cheat = FindFirstOf("MLCheatManager")
    if not isValid(cheat) then return { ok = false, error = "no MLCheatManager" } end
    local before = snapshot(who)
    local ok, err = pcall(function() cheat:SettleRaiders() end)
    if not ok then return { ok = false, error = "SettleRaiders: " .. tostring(err) } end
    return { ok = true, before = before, after = snapshot(who) }
end

-- Follow the units of the bandit side: bandit_mark remembers them, bandit_track tells what each one is now.
-- Why: after a settle call the bandit units leave the bandit side. This shows where they go (spec 15, Q2).
local ROLE_NAMES = { [0] = "Husband", "Wife", "Son", "Daughter", "Retainer", "Soldier", "FreeMerchant", "FreeLivestockMerchant",
    "Deer", "Chicken", "Sheep", "Lamb", "Ox", "Goat", "Hound", "Horse", "Mule", "BanditRecruit", "None", "Pig", "Hare", "Cow", "Calf" }
local marked = {}

function M.bandit_mark()
    marked = units.unitsOfSide("bandit", 200)
    return { ok = true, marked = #marked }
end

local function trackRow(unit)
    if not isValid(unit) then return { gone = true } end
    local role = read(function() return unit.currentUnitRole end)
    local pos = read(function() return unit.realPos end)
    return {
        gone = false, dead = read(function() return unit.dead end) == true, role = ROLE_NAMES[role] or tostring(role),
        squad = read(function() return unit.assignedSquadID.Value end),
        x = pos and read(function() return math.floor(pos.X) end), y = pos and read(function() return math.floor(pos.Y) end),
        region = textOf(read(function() return unit.currentRegion.regionName end)),
    }
end

-- `sample` rows are returned; the counts cover every marked unit.
function M.bandit_track(request)
    local counts, rows = { gone = 0, dead = 0, no_squad = 0, in_squad = 0 }, {}
    local roles = {}
    for index, unit in ipairs(marked) do
        local row = trackRow(unit)
        if row.gone then counts.gone = counts.gone + 1
        elseif row.dead then counts.dead = counts.dead + 1
        elseif row.squad == nil or row.squad == 0 or row.squad < 0 then counts.no_squad = counts.no_squad + 1
        else counts.in_squad = counts.in_squad + 1 end
        if row.role then roles[row.role] = (roles[row.role] or 0) + 1 end
        if #rows < (request.sample or 3) and index % 6 == 1 then rows[#rows + 1] = row end
    end
    return { ok = true, marked = #marked, counts = counts, roles = roles, sample = rows }
end

---------------------------------------------------------------------------------------------
-- Reverse direction: families become bandits (spec 15, homeless rebellion)
---------------------------------------------------------------------------------------------

M.MAX_COORDINATE = 500000
M.MAX_REBEL_FAMILIES = 6
M.MAX_TURN_UNITS = 20
M.DEFAULT_TEMPLATE = "Brigands"

local function checkedTemplate(request)
    local template = request.template or M.DEFAULT_TEMPLATE
    if type(template) ~= "string" or not datatable.has_row(template, "units") then
        return nil, "no unit template named " .. tostring(template) .. " (rows of DT_UnitTemplates)"
    end
    return template
end

local function banditCount()
    return units.counts().by_side.bandit or 0
end

-- Bandit squads at a chosen point (RTSMultiEngineCPP:spawnArmy with the bandit pawn as owner).
function M.bandit_spawn_at(request)
    local x, y, z = request.x, request.y, request.z or 0
    local limit = M.MAX_COORDINATE
    if type(x) ~= "number" or type(y) ~= "number" or type(z) ~= "number" or math.abs(x) > limit or math.abs(y) > limit or math.abs(z) > limit then
        return { ok = false, error = "x and y are required numbers within " .. limit }
    end
    local template, why = checkedTemplate(request)
    if not template then return { ok = false, error = why } end
    local count = request.count or 1
    if count < 1 or count > battle.MAX_GROUPS then return { ok = false, error = "count must be 1 to " .. battle.MAX_GROUPS } end
    local before = banditCount()
    local spawned, problem = battle.spawn_at("bandit", template, count, { x = x, y = y, z = z })
    if not spawned then return { ok = false, error = problem } end
    return { ok = true, squads = spawned.squads, units = spawned.units, bandit_units_before = before, bandit_units_after = banditCount() }
end

local function unitRow(unit)
    local pos = read(function() return unit.realPos end)
    return { squad = read(function() return unit.assignedSquadID.Value end), role = read(function() return unit.currentUnitRole end),
             dead = read(function() return unit.dead end), family = read(function() return unit:hasValidFamily() end),
             x = pos and read(function() return math.floor(pos.X) end), y = pos and read(function() return math.floor(pos.Y) end) }
end

-- SMUnit:turnToBandit on up to `count` living units. source "squad" (default): player squads that the harness spawned (spawn_units side=player).
-- source "family": members of the first families of the player village.
function M.bandit_turn(request)
    local count = request.count or 1
    if count < 1 or count > M.MAX_TURN_UNITS then return { ok = false, error = "count must be 1 to " .. M.MAX_TURN_UNITS } end
    local source = request.source or "squad"
    local chosen, seen
    if source == "family" then
        local region, problem = sack.playerRegion()
        if not region then return { ok = false, error = problem } end
        chosen, seen = sack.family_members(region, M.MAX_REBEL_FAMILIES, count)
    elseif source == "squad" then
        chosen = battle.registered_units("player", count)
    else
        return { ok = false, error = "source must be squad or family" }
    end
    if #chosen == 0 then return { ok = false, error = "no units to turn; for source squad run spawn_units side=player first (seen: " .. (seen and string.format("families %d, members %d, dead %d, invalid %d", seen.families, seen.members, seen.dead, seen.invalid) or "n/a") .. ")" } end
    local before = units.counts().by_side
    local rows = {}
    for _, unit in ipairs(chosen) do
        local row = { before = unitRow(unit) }
        local ok, err = pcall(function() unit:turnToBandit() end)
        if not ok then return { ok = false, error = "turnToBandit: " .. tostring(err), turned = rows } end
        row.after = unitRow(unit)
        rows[#rows + 1] = row
    end
    return { ok = true, turned = rows, side_before = before, side_after = units.counts().by_side }
end

M.MAX_KILL_SQUADS = 10

-- Kill (SMUnit:just_die) every living bandit unit of `count` squads (default 1) with the ids squad, squad + 1, ...
-- Why: to remove the units of a raid and keep the home squads (spec 15, test 4). The request holds numbers only, so the squads are a range.
function M.bandit_kill_squads(request)
    local first, span = request.squad, request.count or 1
    if type(first) ~= "number" or first < 1 or span < 1 or span > M.MAX_KILL_SQUADS then
        return { ok = false, error = "squad must be a squad id; count must be 1 to " .. M.MAX_KILL_SQUADS }
    end
    local last = first + span - 1
    local killed = 0
    for _, unit in ipairs(units.unitsOfSide("bandit", 1000)) do
        local squad = read(function() return unit.assignedSquadID.Value end)
        if squad and squad >= first and squad <= last then
            local ok, err = pcall(function() unit:just_die() end)
            if not ok then return { ok = false, error = "just_die: " .. tostring(err), killed = killed } end
            killed = killed + 1
        end
    end
    return { ok = true, killed = killed, bandit_units_after = banditCount() }
end

local function rebelState(region)
    return { families = read(function() return region:getTotalNumFamilies() end), homeless = read(function() return region:getNumHomelessFamilies() end),
             residents = read(function() return region:getNumHumanResidents() end),
             vacant = (read(function() return region:getAvailableLivingSpace() end) or {}).constructed }
end

-- Remove `count` families (sack_people), then spawn one bandit squad at the home of the first family of each group of
-- `families_per_squad` families. Reports the village numbers before and after, the homes and the squads.
-- mode "home" (default): spawnArmy at the home. The squads walk to a waypoint near (-31000,-22500), wait, and about 650 game
-- seconds after the spawn they march into the village and burn (runs s15-h1, h2, h3). The first watch (150 s) was too short to see it.
-- mode "raid": spawnRaiders with the home as target. The game makes a real raid that marches to the home and attacks (run s15-r1).
function M.homeless_rebel(request)
    local count = request.count or 1
    if count < 1 or count > M.MAX_REBEL_FAMILIES then return { ok = false, error = "count must be 1 to " .. M.MAX_REBEL_FAMILIES } end
    local perSquad = request.families_per_squad or 1
    if perSquad < 1 or perSquad > M.MAX_REBEL_FAMILIES then return { ok = false, error = "families_per_squad must be 1 to " .. M.MAX_REBEL_FAMILIES } end
    local mode = request.mode or "home"
    if mode ~= "home" and mode ~= "raid" then return { ok = false, error = "mode must be home or raid" } end
    local template, why = checkedTemplate(request)
    if not template then return { ok = false, error = why } end
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local before, banditsBefore = rebelState(region), banditCount()
    local homes = sack.family_homes(region, count)
    local families, people = sack.remove_families(region, count)
    local squads, spawnedUnits = {}, 0
    for first = 1, #homes, perSquad do
        local home = homes[first]
        if home.x and mode == "raid" then
            local before = banditCount()
            local raid = raids.spawn_raiders({ squads = 1, x = home.x, y = home.y, z = home.z })
            if not raid.ok then return { ok = false, error = raid.error, homes = homes, families_removed = families } end
            local added = banditCount() - before
            squads[#squads + 1] = { units = added, x = math.floor(home.x), y = math.floor(home.y) }
            spawnedUnits = spawnedUnits + added
        elseif home.x then
            local spawned, spawnProblem = battle.spawn_at("bandit", template, 1, home)
            if not spawned then return { ok = false, error = spawnProblem, homes = homes, families_removed = families } end
            squads[#squads + 1] = { id = spawned.squads[1].id, units = spawned.units, x = math.floor(home.x), y = math.floor(home.y) }
            spawnedUnits = spawnedUnits + spawned.units
        end
    end
    return { ok = true, families_removed = families, people_removed = people, homes = homes, squads = squads, bandit_units_spawned = spawnedUnits,
             before = before, after = rebelState(region), bandit_units_before = banditsBefore, bandit_units_after = banditCount() }
end

M.AI_WAYPOINT, M.RALLY_MIN_DIST, M.RALLY_MAX_DIST = core.AI_WAYPOINT, core.RALLY_MIN_DIST, core.RALLY_MAX_DIST

local function banditSquadIds()
    local ids = {}
    for _, unit in ipairs(units.unitsOfSide("bandit", 2000)) do
        local id = read(function() return unit.assignedSquadID.Value end)
        if id then ids[id] = true end
    end
    return ids
end

local function newIds(before, after)
    local added = {}
    for id in pairs(after) do if not before[id] then added[#added + 1] = id end end
    table.sort(added)
    return added
end

-- Remove `count` families (they leave), then send one real raid (spawnRaiders) with a forest spot as the target.
-- Measured (runs s15-p1 to p5): the raiders appear at the map edge, walk north and burn a few buildings on the way,
-- stand at the AI waypoint (-31000,-22500, inside the player region) for about 100 to 150 game seconds, then attack the village.
-- The target only sets where the raiders appear. The settle letter (bandit_tag attacking, bandit_letter raider_suggestSettle+20) while
-- they stand at the waypoint removes them and gave +2 families in 2 of 2 clean tries. See "Raid aimed at the woods" in homeless-rebellion.md.
function M.rebel_raid_rally(request)
    local region, problem = sack.playerRegion()
    if not region then return { ok = false, error = problem } end
    local before, squadsBefore, banditsBefore = rebelState(region), banditSquadIds(), banditCount()
    local answer = core.rebel_raid_rally(request)
    if not answer.ok then return answer end
    answer.squads = newIds(squadsBefore, banditSquadIds())
    answer.before, answer.after = before, rebelState(region)
    answer.bandit_units_before, answer.bandit_units_after = banditsBefore, banditCount()
    return answer
end

return M
