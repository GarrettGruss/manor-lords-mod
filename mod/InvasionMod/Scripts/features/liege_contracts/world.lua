-- Game access of the feature liege_contracts. Every call runs on the game thread (the scheduler tick or a command).
-- Reads return nil when the game does not answer; a write returns true, or nil and a message.
local core = require("ManorCore")

local M = {}
local isValid, read, listOf = core.isValid, core.read, core.listOf

local STOREHOUSE_TYPE = 72                   -- EBuildingType of the storehouse (wiki engine-limits.md)
local TIER1_STORES = { 6, 72 }               -- the stores that raid_behavior plunders first; a good is added to the first one
local TAKE_FROM_TYPES = { 6, 72, 50, 57, 58, 81, 82, 83, 95, 98 } -- stores in the order of taking (tier 1, then tier 2: config store_tiers of raid_behavior)
local HOME_TYPE = 3

function M.current_day()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil end
    local day = read(function() return engine.TemporalComponent.daysTotal end)
    return type(day) == "number" and math.floor(day) or nil
end

-- The day of the calendar year (TemporalComponent.day), used for the days to the next season start.
function M.day_of_year()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil end
    local day = read(function() return engine.TemporalComponent.day end)
    return type(day) == "number" and math.floor(day) or nil
end

-- Is a manor built? Returns true, or nil and a reason. The first built module of HarnessManor.manor_state() counts
-- (the same rule as the old arms shipment had).
function M.manor_built()
    local manor = require("HarnessManor")
    local listed = manor.manor_state()
    if not listed.ok then return nil, tostring(listed.error) end
    for _, module in ipairs(listed.modules) do
        if module.built then return true end
    end
    return nil, "no manor is built"
end

-- Raise King's Favour of the player (change update-liege-contracts-tier-goods, spike notes/kings-favour.md: changeKingsFavour on the
-- player pawn raised kingsFavour from 0 to 10 and the value held). Returns true, or nil and a message. The value is read back.
function M.add_kings_favour(amount)
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil, "no RTSMultiEngineCPP" end
    local player = read(function() return engine.playerRef end)
    if not isValid(player) then return nil, "no player pawn" end
    local before = read(function() return player.kingsFavour end)
    local ok, why = pcall(function() player:changeKingsFavour(amount) end)
    if not ok then return nil, "changeKingsFavour: " .. tostring(why) end
    local after = read(function() return player.kingsFavour end)
    if type(before) == "number" and type(after) == "number" and after < before + amount then
        return nil, string.format("King's Favour went from %s to %s, not up by %d", tostring(before), tostring(after), amount)
    end
    return true
end

-- The King's Favour of the player, or nil.
function M.kings_favour()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil end
    local value = read(function() return engine.playerRef.kingsFavour end)
    return type(value) == "number" and value or nil
end

---------------------------------------------------------------------------------------------
-- Large costs
---------------------------------------------------------------------------------------------

-- The number of families of the player region, or nil.
function M.family_count()
    local region = core.player_region()
    if region == nil then return nil end
    local count = read(function() return region.workerFamilies:GetArrayNum() end)
    return type(count) == "number" and math.floor(count) or nil
end

-- Remove `count` families for good (ManorCore.remove_families: the members die, their bodies are hidden and leave the game's body count; change fix-removed-families-bodies).
-- Returns the number of families removed, or nil and a message.
function M.remove_families(count)
    local region, problem = core.player_region()
    if region == nil then return nil, problem end
    local families = core.remove_families(region, count)
    return families
end

local function player_pawn()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil, nil end
    local player = read(function() return engine.playerRef end)
    if not isValid(player) then return nil, engine end
    return player, engine
end

-- The squads of the player with their living men and the mean experience: a list of { id, men, experience }. One pass over all units.
function M.player_squads()
    local player = player_pawn()
    if player == nil then return nil, "no player pawn" end
    local wanted = {}
    for _, handle in ipairs(listOf(read(function() return player.commandedSquads end))) do
        local id = read(function() return handle.Value end)
        if type(id) == "number" then wanted[id] = { id = id, men = 0, xp_sum = 0 } end
    end
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        if isValid(unit) then
            local id = read(function() return unit.assignedSquadID.Value end)
            local row = id ~= nil and wanted[id] or nil
            if row ~= nil and read(function() return unit.dead end) ~= true then
                row.men = row.men + 1
                row.xp_sum = row.xp_sum + (read(function() return unit.combatExperience end) or 0)
            end
        end
    end
    local list = {}
    for _, row in pairs(wanted) do
        list[#list + 1] = { id = row.id, men = row.men, experience = row.men > 0 and math.floor(row.xp_sum / row.men + 0.5) or 0 }
    end
    table.sort(list, function(a, b) return a.id < b.id end)
    return list
end

-- The template that the game helper registry knows for a squad (a squad that a script spawned), or nil. The units do not tell it.
function M.known_template(id)
    local ok, battle = pcall(require, "HarnessBattle")
    if not ok or type(battle.template_of) ~= "function" then return nil end
    return battle.template_of(id)
end

-- Remove a squad of the player (spike spike-loan-units: no bodies, no crash). Returns true, or nil and a message.
function M.remove_squad(id)
    local player = player_pawn()
    if player == nil then return nil, "no player pawn" end
    local ok, why = pcall(function() player:addRemoveSquadRequest({ Value = id }) end)
    if not ok then return nil, "addRemoveSquadRequest: " .. tostring(why) end
    return true
end

-- A squad of `template` beside the player pawn, with the given mean experience. Returns the squad id, or nil and a message.
function M.spawn_squad(template, experience)
    local player = player_pawn()
    if player == nil then return nil, "no player pawn" end
    local ok, battle = pcall(require, "HarnessBattle")
    if not ok then return nil, "HarnessBattle is not available: " .. tostring(battle) end
    local at = read(function() return player:K2_GetActorLocation() end)
    if at == nil then return nil, "no player position" end
    local spawned, why = battle.spawn_at("player", template, 1, { x = at.X, y = at.Y, z = at.Z })
    if not spawned then return nil, tostring(why) end
    local id = spawned.squads[1] and spawned.squads[1].id
    if id ~= nil and (experience or 0) > 0 then pcall(battle.set_squad_experience, { squad = id, value = experience }) end
    return id
end

local function built_buildings(region)
    local list = {}
    for _, building in ipairs(listOf(region:GetBuildings())) do
        if isValid(building) and read(function() return building:IsRubble() end) ~= true then list[#list + 1] = building end
    end
    return list
end

local function building_type(building)
    local kind = read(function() return building.Data.bType end)
    return type(kind) == "number" and math.floor(kind) or nil
end

local function amount_of(building, good)
    local total = 0
    for _, row in ipairs(listOf(building.Inventory)) do
        if read(function() return row.Type end) == good then total = total + (read(function() return row.amt end) or 0) end
    end
    return total
end

function M.stock(good)
    local region = core.player_region()
    if region == nil then return nil end
    local value = read(function() return region:getStockOfGood(good, false, false) end)
    return type(value) == "number" and math.floor(value) or nil
end

-- Where a good lies: a text such as "type 72: 40, type 50: 30" (for the message of a refused take).
function M.holders(good)
    local region = core.player_region()
    if region == nil then return "no region" end
    local parts = {}
    for _, building in ipairs(built_buildings(region)) do
        local held = amount_of(building, good)
        if held > 0 then parts[#parts + 1] = string.format("type %s: %d", tostring(building_type(building)), held) end
    end
    return #parts > 0 and table.concat(parts, ", ") or "in no building"
end

-- Take `amount` units of a good from the buildings of the player region that hold it. The known stores come first (tier 1, then tier 2);
-- then any other building that holds the good (food lies in a building of type 80, real run 20261030-183206-25f3), never a home.
-- Returns the number of units taken (it can be less than `amount`), or nil and a message.
function M.take_goods(good, amount)
    local region, problem = core.player_region()
    if region == nil then return nil, problem end
    local rank = {}
    for position, kind in ipairs(TAKE_FROM_TYPES) do rank[kind] = position end
    local stores = {}
    for _, building in ipairs(built_buildings(region)) do
        local kind = building_type(building)
        if kind ~= HOME_TYPE and amount_of(building, good) > 0 then stores[#stores + 1] = { building = building, rank = rank[kind] or 1000 } end
    end
    table.sort(stores, function(a, b) return a.rank < b.rank end)
    local taken = 0
    for _, store in ipairs(stores) do
        local held = amount_of(store.building, good)
        for _ = 1, math.min(held, amount - taken) do
            if not pcall(function() store.building:consumeGoodNoCheck(good) end) then break end
            taken = taken + 1
        end
        if taken >= amount then break end
    end
    return taken
end

-- Add goods to the first storehouse of the player region. Returns true, or nil and a message.
function M.add_goods(good, amount)
    local region, problem = core.player_region()
    if region == nil then return nil, problem end
    local by_type = {}
    for _, building in ipairs(built_buildings(region)) do
        local kind = building_type(building)
        if kind ~= nil then by_type[kind] = by_type[kind] or building end
    end
    for _, kind in ipairs(TIER1_STORES) do
        local store = by_type[kind]
        if store ~= nil then
            local before = amount_of(store, good)
            local ok, why = pcall(function() store:addToInventory({ Type = good, amt = amount }) end)
            if not ok then return nil, "addToInventory: " .. tostring(why) end
            if amount_of(store, good) - before < amount then return nil, "the storehouse kept less than " .. amount end
            return true
        end
    end
    return nil, "no storehouse"
end

-- The data folder lies next to the Scripts folder of the mod. UE4SS puts that Scripts folder on package.path.
function M.data_path(relative)
    for entry in string.gmatch(package.path, "[^;]+") do
        local scripts = entry:gsub("\\", "/"):match("^(.*)/Scripts/%?%.lua$")
        if scripts and scripts:find("InvasionMod", 1, true) then return scripts .. "/" .. relative end
    end
    error("liege contracts: the Scripts folder of the mod is not on package.path", 0)
end

M.STOREHOUSE_TYPE = STOREHOUSE_TYPE

return M
