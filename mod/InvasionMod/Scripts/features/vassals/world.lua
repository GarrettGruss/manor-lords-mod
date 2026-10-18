-- Game access of the vassals feature (M07). Every call runs on the game thread.
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

-- The goal setting and the victory status of the game instance. Nil when the instance is not there yet.
function M.setup_state()
    local ok, module = pcall(require, "HarnessGameSetup")
    if not ok then return nil, "HarnessGameSetup is not available: " .. tostring(module) end
    local state = module.game_setup_state()
    if not state.ok then return nil, tostring(state.error) end
    return state
end

function M.set_goal(goal)
    local module = require("HarnessGameSetup")
    local answer = module.game_setup_set_goal({ goal = goal })
    if not answer.ok then return nil, tostring(answer.error) end
    return answer
end

-- The rows of all regions (object name, owner, settled flag, families).
function M.regions()
    local answer = core.regions_state()
    if not answer.ok then return nil, tostring(answer.error) end
    return answer.regions
end

function M.region_row(name)
    local rows, problem = M.regions()
    if rows == nil then return nil, problem end
    for _, row in ipairs(rows) do
        if row.region == name then return row end
    end
    return nil, "no region named " .. tostring(name)
end

-- The player claims a free region: layClaim, then finalizeClaim.
function M.claim_for_player(name)
    local lords = require("HarnessLords")
    local answer = lords.claim_region({ target = 0, region = name, finalize = 1 })
    if not answer.ok then return nil, tostring(answer.error) end
    return answer
end

---------------------------------------------------------------------------------------------
-- Regions of the player
---------------------------------------------------------------------------------------------

local function player_pawn()
    local e = engine()
    if e == nil then return nil end
    local pawn = core.read(function() return e.playerRef end)
    if core.isValid(pawn) then return pawn end
    return nil
end

local function building_count(region)
    local list = core.read(function() return region:GetBuildings() end)
    if list == nil then return 0 end
    return core.read(function() return list:GetArrayNum() end) or core.read(function() return #list end) or 0
end

-- A light scan: only the regions that the player owns. Rows: { region, settled, buildings }.
function M.player_regions()
    local e, player = engine(), player_pawn()
    if e == nil or player == nil then return nil, "no engine or player pawn" end
    local address = core.read(function() return player:GetAddress() end)
    local rows = {}
    for _, region in ipairs(core.listOf(e.regions)) do
        local owner = core.read(function() return region.ownerPawn end)
        if core.isValid(region) and core.isValid(owner) and core.read(function() return owner:GetAddress() end) == address then
            rows[#rows + 1] = { region = core.shortName(region), settled = core.read(function() return region.isSettled end) == true,
                buildings = building_count(region) }
        end
    end
    return rows
end

---------------------------------------------------------------------------------------------
-- Lords
---------------------------------------------------------------------------------------------

local function lords()
    local out = {}
    for _, pawn in ipairs(FindAllOf("PawnCPP_AI") or {}) do
        if core.isValid(pawn) and not pawn:GetFullName():find("Default__", 1, true) then out[#out + 1] = pawn end
    end
    return out
end

local function lord_name(pawn)
    return core.textOf(core.read(function() return pawn.lordsName end))
end

-- The number of a lord for the Harness lord commands (1.. in FindAllOf order), or nil.
function M.lord_number(name)
    for number, pawn in ipairs(lords()) do
        if lord_name(pawn) == name then return number end
    end
    return nil
end

-- Does the lord count the player as an enemy, and which relation tags exist between them? Read only.
function M.lord_status(name)
    local number = M.lord_number(name)
    if number == nil then return nil end
    local pawn, e, player = lords()[number], engine(), player_pawn()
    local player_name = core.shortName(player)
    local at_war = false
    for _, enemy in ipairs(core.listOf(pawn.enemies)) do
        if core.shortName(enemy) == player_name then at_war = true end
    end
    local tags = {}
    local count = core.read(function() return e.relations:GetArrayNum() end) or 0
    for i = 1, count do
        local relation = e.relations[i] -- direct index: :get() on a struct element crashed the game (S11)
        local a, b = core.shortName(core.read(function() return relation.pawnA end)), core.shortName(core.read(function() return relation.pawnB end))
        local mine = core.shortName(pawn)
        if (a == mine and b == player_name) or (b == mine and a == player_name) then
            local tag_count = core.read(function() return relation.Tags:GetArrayNum() end) or 0
            for t = 1, tag_count do tags[#tags + 1] = core.textOf(relation.Tags[t]) end
        end
    end
    return { number = number, object = core.shortName(pawn), enemy_of_player = at_war, tags = tags }
end

local function step(label, answer)
    if type(answer) ~= "table" or not answer.ok then
        return nil, label .. ": " .. tostring(type(answer) == "table" and answer.error or answer)
    end
    return answer
end

-- Make a lord that builds, neutral to the player. Returns the lord number.
function M.spawn_lord(name)
    local lords_module = require("HarnessLords")
    local spawned, why = step("spawn", lords_module.spawn_ai_lord({ name = name, build = 1 }))
    if not spawned then return nil, why end
    local number = spawned.lord
    if number == nil then return nil, "spawn: the new lord has no number" end
    local ok, problem = step("relations", lords_module.lord_relations({ lord = number }))
    if not ok then return nil, problem end
    ok, problem = step("start ai", lords_module.lord_start_ai({ lord = number, value = 1, build = 1 }))
    if not ok then return nil, problem end
    return number
end

-- Clear the owner, then the lord claims and finalizes (the route that makes the construction AI run, spike S13).
function M.hand_over(number, region)
    local answer, why = step("receive", require("HarnessLords").lord_receive_region({ lord = number, region = region }))
    if not answer then return nil, why end
    return answer
end

-- The building count of one region by object name. Nil when the region is not found.
function M.region_buildings(name)
    local e = engine()
    if e == nil then return nil end
    for _, region in ipairs(core.listOf(e.regions)) do
        if core.shortName(region) == name then return building_count(region) end
    end
    return nil
end

return M
