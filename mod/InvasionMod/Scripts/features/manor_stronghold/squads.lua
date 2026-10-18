-- Extra retinue squads above the native limit of 12 men (M13 iteration 03).
-- Why: the native hire refuses above 12 and hooks cannot change it (iteration 02). spawnArmy with the player pawn as owner
-- makes player-owned squads of the template retinue_tier1 (spike S7: 36 men). The mod pays the silver and keeps the squad ids.
-- Game access: call only on the game thread.
local core = require("ManorCore")
local rules = require("features.manor_stronghold.rules")
local silver_world = require("features.bandits.world")

local TAG = "InvasionMod.manor_stronghold"

local M = {}

local squad_ids = {} -- ids of the squads that this feature made

local function engine()
    local object = FindFirstOf("RTSMultiEngineCPP")
    if object ~= nil and object:IsValid() then return object end
    return nil
end

local function squad_id_of(unit)
    local ok, value = pcall(function() return unit.assignedSquadID.Value end)
    if ok then return value end
    return nil
end

-- Living men of the squads that this feature made. One property read for each unit, on demand only.
function M.living_men()
    local wanted = {}
    for _, id in ipairs(squad_ids) do wanted[id] = true end
    local count = 0
    for _, unit in ipairs(FindAllOf("SMUnit") or {}) do
        local ok, valid = pcall(function() return unit:IsValid() end)
        local id = ok and valid and squad_id_of(unit) or nil
        if id ~= nil and wanted[id] then
            local read_ok, dead = pcall(function() return unit.dead end)
            if read_ok and dead ~= true then count = count + 1 end
        end
    end
    return count
end

function M.silver()
    local e = engine()
    local ok, value = pcall(function() return e.playerRef.silver end)
    if ok and type(value) == "number" then return value end
    return 0
end

function M.squad_count() return #squad_ids end

-- The returned TArray holds squad handles; each has the field Value (the same read as HarnessBattle).
local function squad_ids_of(returned)
    local ids = {}
    for index = 1, #returned do
        local ok, id = pcall(function()
            local element = returned[index]
            local good, inner = pcall(function() return element:get() end)
            if good and inner ~= nil then element = inner end
            return element.Value
        end)
        if not ok or id == nil then return nil end
        ids[#ids + 1] = id
    end
    if #ids == 0 then return nil end
    return ids
end

local function spot_beside(building)
    local ok, at = pcall(function() return building:K2_GetActorLocation() end)
    if not ok or at == nil then return nil end
    return { X = at.X + 1500, Y = at.Y, Z = at.Z }
end

-- Hires one squad. `state` is the answer of retinue.read(), `building` is the manor module.
-- Returns the answer table, or nil and a message.
function M.hire(state, building, config)
    local refusal = rules.squad_refusal(state.bonus, #squad_ids, config.bonus_per_squad, M.silver(), config.squad_men * state.hire_cost)
    if refusal then return nil, refusal end
    local e = engine()
    if e == nil then return nil, "no RTSMultiEngineCPP" end
    local owner = e.playerRef
    local spot = spot_beside(building)
    if spot == nil then return nil, "no manor position" end
    local ok, returned = pcall(function() return e:spawnArmy(spot, { FName(config.squad_template) }, owner, 0, 0) end)
    if not ok then return nil, "spawnArmy: " .. tostring(returned) end
    local ids = squad_ids_of(returned)
    if ids == nil then return nil, "spawnArmy returned no squad id" end
    local cost = config.squad_men * state.hire_cost
    local paid, why = silver_world.add_silver(-cost)
    if not paid then return nil, "squad made but the payment failed: " .. tostring(why) end
    for _, id in ipairs(ids) do squad_ids[#squad_ids + 1] = id end
    core.log.info(TAG, string.format("RETINUE_SQUAD hired ids=%s cost=%d", table.concat(ids, ","), cost))
    return { squad_ids = ids, cost = cost, x = spot.X, y = spot.Y }
end

return M
