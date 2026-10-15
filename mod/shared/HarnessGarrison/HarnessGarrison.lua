-- HarnessGarrison: opt-in bonus for the manor garrison limit (issue 90, round 8).
-- Why: the garrison limit is native (12, +12 with a keep) and ignores buildingStats.garrisonLimit. A data pak cannot make a Lv3 keep give 36.
-- This post-hook adds a fixed bonus to the answer of SMBuildingMaster:getModularGarrisonLimit while a built manor module of a chosen type exists.
--
-- Detection (round 10): a built module is a type that HarnessWalls committed (manor_blueprint_add + commit) while the manor reads IsConstructed.
-- Opt-in by game environment (run.py --env):
--   HARNESS_GARRISON_BONUS        number to add. Unset or 0: no hook is installed.
--   HARNESS_GARRISON_MODULE_TYPE  module type that must be built (default 83; the mouse-free Lv3 tower uses 57).
-- The hook only runs when the game calls the function through the script VM (UI and bridge calls). Native C++ callers are not changed.

local log = require("HarnessLog")
local manor = require("HarnessManor")
local walls = require("HarnessWalls")

local M = {}

M.TAG = "HarnessGarrison"
M.FUNCTION_PATH = "/Script/ManorLords.SMBuildingMaster:getModularGarrisonLimit"
M.DEFAULT_MODULE_TYPE = 83

local function envNumber(name, default)
    local text = os.getenv and os.getenv(name)
    local number = text and tonumber(text)
    if number == nil then return default end
    return number
end

-- Round 10: a module part cannot be read after a commit, so the hook trusts the commit record of HarnessWalls
-- and asks the manor (self of the hooked call) whether it is finished again.
local function moduleIsBuilt(moduleType, self)
    local state = manor.manor_state()
    if state.ok then
        for _, row in ipairs(state.modules) do
            if row.type == moduleType and row.built then return true end
        end
    end
    if not walls.committed_types[moduleType] then return false end
    local ok, built = pcall(function() return self:get():IsConstructed() end)
    return ok and built == true
end

local function addBonus(bonus, moduleType, self, returnValue)
    if not moduleIsBuilt(moduleType, self) then return end
    local before = returnValue:get()
    returnValue:set(before + bonus)
    log.info(M.TAG, "limit " .. tostring(before) .. " -> " .. tostring(before + bonus))
end

-- Install the hook when HARNESS_GARRISON_BONUS is set. Returns true when it is installed.
function M.install()
    local bonus = envNumber("HARNESS_GARRISON_BONUS", 0)
    if bonus == 0 then return false end
    local moduleType = envNumber("HARNESS_GARRISON_MODULE_TYPE", M.DEFAULT_MODULE_TYPE)
    local ok, err = pcall(RegisterHook, M.FUNCTION_PATH, function() end, function(self, returnValue)
        log.try(M.TAG, addBonus, bonus, moduleType, self, returnValue)
    end)
    if not ok then error("RegisterHook failed for " .. M.FUNCTION_PATH .. ": " .. tostring(err)) end
    log.say(M.TAG, "installed: bonus " .. bonus .. " while a built module of type " .. moduleType .. " exists")
    return true
end

return M
