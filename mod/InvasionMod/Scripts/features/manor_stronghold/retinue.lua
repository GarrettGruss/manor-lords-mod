-- Retinue capacity hooks (M13.02). Game access: runs on the game thread.
-- Spike result (openspec/changes/archive/2026-10-16-legacy-m13-manor-stronghold/implementation-notes/iteration-02-retinue-capacity.md): a post-hook on
-- getModularGarrisonLimit changes the number that script callers read, but the native hire stops at the native limit.
-- So the feature also hooks canHireRetinue, which the retinue editor (Blueprint) calls to enable its hire button.
local core = require("ManorCore")
local manor = require("HarnessManor")

local TAG = "InvasionMod.manor_stronghold"
local LIMIT_FUNCTION = "/Script/ManorLords.SMBuildingMaster:getModularGarrisonLimit"
local CAN_HIRE_FUNCTION = "/Script/ManorLords.SMBuildingMaster:canHireRetinue"

local M = {}

local bonus = 0

local function count_of(array)
    local ok, count = pcall(function() return array:GetArrayNum() end)
    if ok then return count end
    return #array
end

function M.set_bonus(value) bonus = value end
function M.bonus() return bonus end

local function is_manor(building)
    local ok, kind = pcall(function() return building.Data.bType end)
    return ok and manor.MANOR_TYPES[kind] == true
end

local function add_to_limit(self, return_value)
    if bonus == 0 then return end
    local ok, err = pcall(function()
        local building = self:get()
        if not is_manor(building) then return end
        return_value:set(return_value:get() + bonus)
    end)
    if not ok then core.log.warn(TAG, "limit hook failed: " .. tostring(err)) end
end

-- The limit read inside this hook already holds the bonus, because it goes through the limit hook.
local function allow_hire_below_limit(self, return_value)
    if bonus == 0 or return_value:get() == true then return end
    local ok, err = pcall(function()
        local building = self:get()
        if not is_manor(building) then return end
        if count_of(building:getBoundRetinue()) < building:getModularGarrisonLimit() then return_value:set(true) end
    end)
    if not ok then core.log.warn(TAG, "can-hire hook failed: " .. tostring(err)) end
end

-- Fails loudly when a hook cannot be registered.
function M.install()
    for path, post in pairs({ [LIMIT_FUNCTION] = add_to_limit, [CAN_HIRE_FUNCTION] = allow_hire_below_limit }) do
        local ok, err = pcall(RegisterHook, path, function() end, post)
        if not ok then error("manor_stronghold: RegisterHook failed for " .. path .. ": " .. tostring(err), 0) end
    end
end

-- The numbers for the commands. The first manor module is used.
function M.read()
    local state = manor.manor_state()
    if not state.ok then return nil, state.error end
    local building
    for _, object in ipairs(FindAllOf("SMBuildingMaster") or {}) do
        local ok, built = pcall(function() return object:IsConstructed() end)
        if ok and built and is_manor(object) then building = object; break end
    end
    if building == nil then return nil, "no built manor module" end
    return {
        limit = building:getModularGarrisonLimit(), can_hire = building:canHireRetinue(), bound = count_of(building:getBoundRetinue()),
        hire_cost = building:GetRetinueHireTreasuryCost(), bonus = bonus,
    }, building
end

local function commanded_ids(player)
    local ids = {}
    local ok = pcall(function()
        for index = 1, count_of(player.commandedSquads) do
            local element = player.commandedSquads[index]
            local good, inner = pcall(function() return element:get() end)
            if good and inner ~= nil then element = inner end
            ids[element.Value] = true
        end
    end)
    return ok and ids or nil
end

-- The id of the squad that the manor recruits into now (the newest squad: the native hire fills the last squad), or nil.
function M.bound_squad_id()
    local _, building = M.read()
    if building == nil then return nil end
    local ok, id = pcall(function()
        local member = building:getBoundRetinue()[1]
        local good, inner = pcall(function() return member:get() end)
        if good and inner ~= nil then member = inner end
        return member.assignedSquadID.Value
    end)
    if ok and type(id) == "number" and id > 0 then return id end
    return nil
end

-- Adds one native retinue squad with `men` men (change add-contract-retinue-reward, spike: InitializeEmptyRetinueSquad with the region object,
-- then the native hire fills the new squad). The silver of the hires is added first, so the squad costs the player nothing. The game saves the squad.
-- Returns the squad id, or nil and a reason.
function M.add_native_squad(men)
    local state, building = M.read()
    if not state then return nil, building end
    local region, why = core.player_region()
    if region == nil then return nil, why end
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local player = engine and engine.playerRef
    if player == nil then return nil, "no player pawn" end
    local before = commanded_ids(player)
    if before == nil then return nil, "the commanded squads cannot be read" end
    local cost = men * state.hire_cost
    local silver_world = require("features.bandits.world")
    local credited, problem = silver_world.add_silver(cost)
    if not credited then return nil, "silver: " .. tostring(problem) end
    local ok, err = pcall(function() player:InitializeEmptyRetinueSquad(region) end)
    if not ok then
        silver_world.add_silver(-cost)
        return nil, "InitializeEmptyRetinueSquad: " .. tostring(err)
    end
    local id
    for found in pairs(commanded_ids(player) or {}) do
        if not before[found] then id = found end
    end
    local hired = 0
    for _ = 1, men do
        if pcall(function() building:hireExtraRetinue() end) then hired = hired + 1 end
    end
    local bound = count_of(building:getBoundRetinue())
    if bound < men then
        silver_world.add_silver(-(men - bound) * state.hire_cost)
        return nil, string.format("only %d of %d men were recruited (calls %d)", bound, men, hired)
    end
    if id == nil then return nil, "the new squad id is not known" end
    core.log.info(TAG, string.format("RETINUE_SQUAD native squad %d with %d men", id, men))
    return id
end

function M.hire()
    local state, building = M.read()
    if not state then return nil, building end
    building:hireExtraRetinue()
    return (M.read())
end

return M
