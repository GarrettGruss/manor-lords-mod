-- Game access of the bandits feature (M04). Every call runs on the game thread.
local core = require("ManorCore")
local rules = require("features.bandits.rules")

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

local isValid, read, listOf = core.isValid, core.read, core.listOf
local CAMP_BUILDING = 100  -- DT_Buildings bType of the bandit camp (encampment)

-- Living bandit units now: address -> unit.
local function bandit_unit_set()
    local ok, units = pcall(require, "HarnessUnits")
    if not ok then return {} end
    local set = {}
    for _, unit in ipairs(units.unitsOfSide("bandit", 2000)) do
        local address = read(function() return unit:GetAddress() end)
        if address ~= nil then set[address] = unit end
    end
    return set
end

-- The standing bandit camps (SMBuildingMaster, bType 100): address -> building.
local function camp_set()
    local set = {}
    for _, master in ipairs(FindAllOf("SMBuildingMaster") or {}) do
        local default = read(function() return master:GetFullName():find("Default__", 1, true) end)
        if isValid(master) and not default and read(function() return master.Data.bType end) == CAMP_BUILDING then
            local address = read(function() return master:GetAddress() end)
            if address ~= nil then set[address] = master end
        end
    end
    return set
end

-- One bandit camp (18 Brigands). The same call makes the bandit pawn when the game has none (bandit camps 0).
-- The game picks the place: spawnBanditCamp has no argument. A new pawn has no relation row, so addPawnRelations follows.
-- Returns { pawn_created, units (the new bandit units), camps (the new camp buildings), at } or nil and a message.
function M.spawn_camp()
    local e = engine()
    if e == nil then return nil, "no RTSMultiEngineCPP" end
    local units_before, camps_before = bandit_unit_set(), camp_set()
    local had_pawn = bandit_pawn() ~= nil
    local called, problem = pcall(function() e:spawnBanditCamp() end)
    if not called then return nil, "spawnBanditCamp: " .. tostring(problem) end
    local pawn = bandit_pawn()
    if not had_pawn then
        if pawn == nil then return nil, "spawnBanditCamp made no bandit pawn" end
        local related, why = pcall(function() e:addPawnRelations(pawn) end)
        if not related then core.log.warn("Bandits", "addPawnRelations failed: " .. tostring(why)) end
    end
    local units, camps = {}, {}
    for address, unit in pairs(bandit_unit_set()) do
        if units_before[address] == nil then units[#units + 1] = unit end
    end
    for address, camp in pairs(camp_set()) do
        if camps_before[address] == nil then camps[#camps + 1] = camp end
    end
    return { pawn_created = not had_pawn, units = units, camps = camps, at = camp_place() }
end

-- Kill units with just_die and hide the bodies at once (SetActorHiddenInGame is safe, K2_DestroyActor on an SMUnit crashes).
-- No reference is kept after the call. Returns the number killed.
function M.kill_and_hide(units)
    local killed = 0
    for _, unit in ipairs(units) do
        if isValid(unit) and read(function() return unit.dead end) ~= true then
            if pcall(function() unit:just_die() end) then
                killed = killed + 1
                pcall(function() unit:SetActorHiddenInGame(true) end)
            end
        end
    end
    return killed
end

-- Demolish camp buildings. demolish() without the argument is refused; demolish(true) works (spike militia-corpses-and-camp-removal).
-- Returns the number demolished, or nil and a message.
function M.demolish_camps(camps)
    local done = 0
    for _, camp in ipairs(camps) do
        if isValid(camp) then
            local ok, problem = pcall(function() camp:demolish(true) end)
            if not ok then return nil, "demolish: " .. tostring(problem) end
            done = done + 1
        end
    end
    return done
end

---------------------------------------------------------------------------------------------
-- Rebellion: families, goods, bodies, squads
---------------------------------------------------------------------------------------------

local function inventory_of(building)
    local rows = {}
    for _, good in ipairs(listOf(building.Inventory)) do
        local id, amount = read(function() return good.Type end), read(function() return good.amt end)
        if type(id) == "number" and type(amount) == "number" and amount > 0 then rows[#rows + 1] = { id = id, amount = amount } end
    end
    return rows
end

-- The families whose home holds at least one item of `id_set`. Each row: { home, goods (a list of ids, one per item), members, at }.
-- The members are read here, in the same pass, so no family struct is read after a death (#357).
function M.armed_families(region, id_set)
    local rows = {}
    for _, family in ipairs(listOf(region.workerFamilies)) do
        local home = read(function() return family.familyHome end)
        if isValid(home) then
            local goods = rules.armed_goods(inventory_of(home), id_set)
            local at = read(function() return home:K2_GetActorLocation() end)
            local x, y, z = at and read(function() return at.X end), at and read(function() return at.Y end), at and read(function() return at.Z end)
            if #goods > 0 and x ~= nil then
                local members = {}
                for _, member in ipairs(listOf(family.familyMembers)) do members[#members + 1] = member end
                rows[#rows + 1] = { home = home, goods = goods, members = members, at = { x = x, y = y, z = z } }
            end
        end
    end
    return rows
end

-- Take the goods (a list of ids) from a home: one consumeGoodNoCheck for each item. Returns the list of ids really taken.
function M.take_goods(home, goods)
    local taken = {}
    for _, id in ipairs(goods) do
        if pcall(function() home:consumeGoodNoCheck(id) end) then taken[#taken + 1] = id end
    end
    return taken
end

-- Put goods back into the home they came from. `rows` is a list of { home, id }. Returns the number returned.
function M.return_goods(rows)
    local counts, order = {}, {}
    for _, row in ipairs(rows) do
        local per_home = counts[row.home]
        if per_home == nil then per_home = {}; counts[row.home] = per_home; order[#order + 1] = row.home end
        per_home[row.id] = (per_home[row.id] or 0) + 1
    end
    local returned = 0
    for _, home in ipairs(order) do
        for id, amount in pairs(counts[home]) do
            if isValid(home) and pcall(function() home:addToInventory({ Type = id, amt = amount }) end) then returned = returned + amount end
        end
    end
    return returned
end

-- `count` squads of the template Brigands for the pawn Outlaws at `point` ({ x, y, z }): the proven spawn of homeless_rebel mode home.
-- Returns { squads (ids), units (a list of { address, squad, index }) } or nil and a message.
function M.spawn_squads(count, point)
    local ok, battle = pcall(require, "HarnessBattle")
    if not ok then return nil, "HarnessBattle is not available: " .. tostring(battle) end
    local spawned, problem = battle.spawn_at("bandit", "Brigands", count, point)
    if not spawned then return nil, tostring(problem) end
    local wanted, ids = {}, {}
    for _, squad in ipairs(spawned.squads) do wanted[squad.id] = true; ids[#ids + 1] = squad.id end
    local by_squad = require("features.raid_behavior.world").units_by_squad(wanted)
    local units = {}
    for _, id in ipairs(ids) do
        for index, row in ipairs(by_squad[id] or {}) do
            if not row.dead then units[#units + 1] = { address = row.address, squad = id, index = index } end
        end
    end
    return { squads = ids, units = units }
end

-- A rebellion: see features/bandits/rebellion.lua. Returns its result record.
function M.leave(region, wanted)
    local rebellion = require("features.bandits.rebellion")
    return rebellion.run(region, wanted, rebellion.default_deps())
end

function M.distance(at)
    return distance_to_village(at)
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


-- The address of the player pawn: it changes with each game load.
function M.player_address()
    local e = engine()
    local pawn = e and core.read(function() return e.playerRef end)
    if not core.isValid(pawn) then return nil end
    return core.read(function() return pawn:GetAddress() end)
end

return M
