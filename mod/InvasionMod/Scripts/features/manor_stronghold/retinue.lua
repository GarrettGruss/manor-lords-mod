-- Retinue capacity hooks (M13.02). Game access: runs on the game thread.
-- Spike result (docs/mod/M13-manor_stronghold/implementation-notes/iteration-02-retinue-capacity.md): a post-hook on
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

function M.hire()
    local state, building = M.read()
    if not state then return nil, building end
    building:hireExtraRetinue()
    return (M.read())
end

return M
