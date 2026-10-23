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

function M.current_season()
    local e = engine()
    if e == nil then return nil end
    local ok, value = pcall(function() return e.TemporalComponent.Season end)
    if ok and type(value) == "number" then return math.floor(value) end
    return nil
end

-- The object name of the pawn that owns a region ("nil" when it has none), or nil when the region is not found.
function M.region_owner(name)
    local e = engine()
    if e == nil then return nil end
    local count = core.read(function() return e.regions:GetArrayNum() end) or 0
    for i = 1, count do
        local region = core.read(function() return e.regions[i] end)
        if core.shortName(region) == name then
            return core.shortName(core.read(function() return region.ownerPawn end)) or "nil"
        end
    end
    return nil
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

-- Families of one region by object name. Nil when the region is not found.
function M.region_families(name)
    local e = engine()
    if e == nil then return nil end
    for _, region in ipairs(core.listOf(e.regions)) do
        if core.shortName(region) == name then return core.read(function() return region:getTotalNumFamilies() end) end
    end
    return nil
end

---------------------------------------------------------------------------------------------
-- Sack, wipe and restore of a vassal region (change add-vassal-sack-wipe)
-- The mod controls only the sacking of houses in an AI village (owner, 2026-10-20). It never writes the owner or the lord.
---------------------------------------------------------------------------------------------

local function region_object(name)
    local e = engine()
    if e == nil then return nil end
    for _, region in ipairs(core.listOf(e.regions)) do
        if core.shortName(region) == name then return region end
    end
    return nil
end

-- Buildings of a region: { total, standing, rubble }. Nil when the region is not found.
function M.census(name)
    local region = region_object(name)
    if region == nil then return nil end
    local rubble, standing, built, first_location = 0, 0, 0, nil
    for _, building in ipairs(core.listOf(core.read(function() return region:GetBuildings() end))) do
        if core.isValid(building) then
            first_location = first_location or core.read(function() return building:K2_GetActorLocation() end)
            if core.read(function() return building:IsRubble() end) == true then
                rubble = rubble + 1
            else
                standing = standing + 1
                -- A construction site made by the rebuild order is not rubble but is not built yet (Data.constructed false).
                if core.read(function() return building.Data.constructed end) ~= false then built = built + 1 end
            end
        end
    end
    local at = first_location
    local centre = at and core.read(function() return { x = math.floor(at.X), y = math.floor(at.Y) } end) or nil
    return { total = rubble + standing, standing = standing, built = built, rubble = rubble, centre = centre }
end

-- Remove every unit of the given goods from all buildings of a region (HarnessSack.remove_goods: consumeGoodNoCheck).
-- `goods` is a list of { id, name }. Returns a map name -> units removed.
function M.remove_goods(name, goods)
    local region = region_object(name)
    if region == nil then return nil, "no region " .. tostring(name) end
    local sack = require("HarnessSack")
    local removed = {}
    for _, good in ipairs(goods) do removed[good.name] = sack.remove_goods(region, good.id, sack.MAX_GOODS_REMOVED) end
    return removed
end

-- The lord name of the AI pawn that owns a region, or nil (no owner, or the owner is not an AI lord).
function M.region_lord_name(name)
    local region = region_object(name)
    if region == nil then return nil end
    local owner = core.read(function() return region.ownerPawn end)
    if not core.isValid(owner) then return nil end
    local text = core.textOf(core.read(function() return owner.lordsName end))
    if text == nil or text == "" then return nil end
    return text
end

-- Give a wiped region back to an AI lord (the handover of a new vassal: lord_receive_region). The lord is spawned when it is gone.
function M.hand_over_to_lord(lord_name, region)
    local number = M.lord_number(lord_name)
    if number == nil then
        local spawned, why = M.spawn_lord(lord_name)
        if spawned == nil then return nil, why end
        number = spawned
    end
    local answer, why = M.hand_over(number, region)
    if answer == nil then return nil, why end
    return number
end

local RUBBLE_TYPE = 75    -- EBuildingType::Rubble
local NO_TYPE = 0          -- typeBeforeChange of a building that never collapsed

-- Order the rebuild of one ruin (notes/rebuild-order.md, proven in the real game): write Data back with the old type, not constructed,
-- hp 0; then SetupBuilding. Never convertBlueprintsToBuildings: it removes the model. Returns "ordered" or "skipped", or nil and an error.
local function order_rebuild(building)
    local old = core.read(function() return building.typeBeforeChange end)
    if type(old) ~= "number" or old == NO_TYPE or old == RUBBLE_TYPE then return "skipped", old end
    local ok, problem = pcall(function()
        local data = building.Data
        data.bType = old
        data.constructed = false
        data.hp = 0
        building.Data = data
        building:SetupBuilding()
    end)
    if not ok then return nil, tostring(problem) end
    return "ordered", old
end

-- Give the rebuild order to every ruin of the region. Returns { ordered, skipped, failed }.
function M.rebuild_ruins(name)
    local region = region_object(name)
    if region == nil then return nil, "no region " .. tostring(name) end
    local result = { ordered = 0, skipped = 0, failed = 0 }
    for _, building in ipairs(core.listOf(core.read(function() return region:GetBuildings() end))) do
        if core.isValid(building) and core.read(function() return building:IsRubble() end) == true then
            local outcome, detail = order_rebuild(building)
            if outcome == "ordered" then
                result.ordered = result.ordered + 1
                core.log.info("InvasionMod.vassals", string.format("VASSALS rebuild order region=%s type=%s", name, tostring(detail)))
            elseif outcome == "skipped" then
                result.skipped = result.skipped + 1
            else
                result.failed = result.failed + 1
                core.log.error("InvasionMod.vassals", "VASSALS rebuild order failed: " .. tostring(detail))
            end
        end
    end
    return result
end

-- Collapse up to `count` standing buildings (collapseBuilding: ruin at once, spike empty-ai-village.md). Returns how many calls worked.
function M.collapse_buildings(name, count)
    local region = region_object(name)
    if region == nil then return nil, "no region " .. tostring(name) end
    local hit = 0
    for _, building in ipairs(core.listOf(core.read(function() return region:GetBuildings() end))) do
        if hit >= count then break end
        if core.isValid(building) and core.read(function() return building:IsRubble() end) ~= true then
            if pcall(function() building:collapseBuilding() end) then hit = hit + 1 end
        end
    end
    return hit
end

-- Delete every villager of a region. ManorCore.remove_families collects the members first (the fix of #357), then kills each.
function M.delete_villagers(name)
    local region = region_object(name)
    if region == nil then return nil, "no region " .. tostring(name) end
    local families, people = core.remove_families(region, 1000)
    return { families = families, people = people }
end

-- Raise the villager count of a wiped region: settleRegion with the owner (the lord pawn) as the settling pawn (spike restore-to-five.md).
function M.restore_villagers(name)
    local region = region_object(name)
    if region == nil then return nil, "no region " .. tostring(name) end
    local owner = core.read(function() return region.ownerPawn end)
    if not core.isValid(owner) then return nil, "the region has no owner" end
    local row = M.region_row(name)
    local answer = core.settle_region({ region = name, type = row and row.settlement_type or 1, supply = 0 }, owner)
    if not answer.ok then return nil, tostring(answer.error) end
    return { families = answer.after and answer.after.families }
end

-- Put goods into the first standing building (with include_rubble: any building, a ruin takes goods too) of the region that takes them. `goods` is a list of { id, amount, name }.
-- Returns a map name -> amount deposited. A refused deposit gives 0 (the caller logs it).
function M.deposit_goods(name, goods, tries, include_rubble)
    local region = region_object(name)
    if region == nil then return nil, "no region " .. tostring(name) end
    local buildings = {}
    for _, building in ipairs(core.listOf(core.read(function() return region:GetBuildings() end))) do
        if core.isValid(building) and (include_rubble or core.read(function() return building:IsRubble() end) ~= true) then buildings[#buildings + 1] = building end
    end
    local deposited = {}
    for _, good in ipairs(goods) do
        deposited[good.name] = 0
        for index, building in ipairs(buildings) do
            if index > tries then break end
            if pcall(function() building:addToInventory({ Type = good.id, amt = good.amount }) end) then
                deposited[good.name] = good.amount
                break
            end
        end
    end
    return deposited
end

return M
