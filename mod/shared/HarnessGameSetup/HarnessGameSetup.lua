-- HarnessGameSetup: read and write the goal of the game (spec 26).
-- Why: the goal (EGameGoals) may decide if a region claim shows the victory cinematic.
-- The bridge cannot write a nested struct field by name, so this module writes it from Lua.
-- Values of EGameGoals: 0 Conquest, 1 Dominance, 2 Endless, 3 Growth (order of the jmap, checked by reading a fixture).

local M = {}

M.MAX_GOAL = 3

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

local function gameInstance()
    local found = FindFirstOf("MLGameInstance")
    if isValid(found) then return found end
    return nil
end

local function snapshot(instance)
    return {
        goals = read(function() return instance.gameSetup.currentGameSetup.goals end),
        victory_status = read(function() return instance.currentGameVictoryStatus end),
        difficulty = read(function() return instance.gameSetupDifficulty end),
        scenario = read(function() return instance.scenario:ToString() end),
        ai_lords = read(function() return instance.gameSetup.currentGameSetup.numGenericAILords end),
        starting_supplies = read(function() return instance.gameSetup.currentGameSetup.startingSuppliesMultiplier end),
        starting_day = read(function() return instance.gameSetup.currentGameSetup.startingDay end),
    }
end

-- Read only.
function M.game_setup_state()
    local instance = gameInstance()
    if not instance then return { ok = false, error = "no MLGameInstance" } end
    local state = snapshot(instance)
    state.ok = true
    return state
end

-- Write gameSetup.currentGameSetup.goals on the game instance. Reads the value back.
function M.game_setup_set_goal(request)
    local goal = request.goal
    if type(goal) ~= "number" or goal < 0 or goal > M.MAX_GOAL or goal ~= math.floor(goal) then
        return { ok = false, error = "goal must be a whole number from 0 to " .. M.MAX_GOAL .. " (got " .. type(goal) .. " " .. tostring(goal) .. ")" }
    end
    local instance = gameInstance()
    if not instance then return { ok = false, error = "no MLGameInstance" } end
    local before = snapshot(instance)
    local ok, err = pcall(function() instance.gameSetup.currentGameSetup.goals = goal end)
    if not ok then return { ok = false, error = "write goals: " .. tostring(err), before = before } end
    return { ok = true, before = before, after = snapshot(instance) }
end

return M
