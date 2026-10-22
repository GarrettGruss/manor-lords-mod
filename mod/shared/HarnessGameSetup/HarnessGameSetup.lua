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
        raiding_frequency = read(function() return instance.gameSetup.currentGameSetup.raidingFrequency end),
        years_until_first_raid = read(function() return instance.gameSetup.currentGameSetup.yearsUntilFirstRaid end),
        max_bandit_camps = read(function() return instance.gameSetup.currentGameSetup.maxBanditCamps end),
        initial_bandit_camps = read(function() return instance.gameSetup.currentGameSetup.initialBanditCamps end),
        ai_aggressiveness = read(function() return instance.gameSetup.currentGameSetup.AI_aggressiveness end),
        adversary_baron = read(function() return instance.gameSetup.currentGameSetup.adversary_baron end),
    }
end

-- Spike #358: fields of GameSetupParameters that a spike may write (byte values only).
local BYTE_FIELDS = { raidingFrequency = true, yearsUntilFirstRaid = true, maxBanditCamps = true, initialBanditCamps = true, AI_aggressiveness = true }

function M.game_setup_set_byte(request)
    if not BYTE_FIELDS[request.field] then return { ok = false, error = "field not allowed: " .. tostring(request.field) } end
    if type(request.value) ~= "number" or request.value < 0 or request.value > 255 then return { ok = false, error = "value must be 0 to 255" } end
    local instance = gameInstance()
    if not instance then return { ok = false, error = "no MLGameInstance" } end
    local before = snapshot(instance)
    local ok, err = pcall(function() instance.gameSetup.currentGameSetup[request.field] = request.value end)
    if not ok then return { ok = false, error = "write " .. request.field .. ": " .. tostring(err), before = before } end
    return { ok = true, before = before, after = snapshot(instance) }
end

-- Spike #358 (new game menu): list the children of the settings scroll box of the Game Setup screen, and optionally add
-- a clone of one setting entry widget. Run it while the main menu shows the Game Setup screen. It reads no struct.
function M.game_setup_menu_probe(request)
    local steps = {}
    local function step(name, fn)
        local ok, value = pcall(fn)
        steps[#steps + 1] = name .. ": " .. (ok and "ok" or ("ERR " .. tostring(value)))
        if ok then return value end
        return nil
    end
    local screen = FindFirstOf("mainMenu_GameSetup_C")
    if not isValid(screen) then return { ok = false, error = "no mainMenu_GameSetup_C (open the Game Setup screen)" } end
    local box = step("parent of entry_untilFirstRaid", function() return screen.entry_untilFirstRaid:GetParent() end)
    if not isValid(box) then return { ok = false, error = "no SettingsScrollBox", steps = steps } end
    local function children()
        local names = {}
        local count = step("GetChildrenCount", function() return box:GetChildrenCount() end) or 0
        for i = 0, count - 1 do
            names[#names + 1] = step("child" .. i, function() return box:GetChildAt(i):GetFName():ToString() end) or "?"
        end
        return names
    end
    local result = { ok = true, before = children() }
    if request.count == 1 then -- count 1 adds the clone (HarnessActions parses a fixed list of fields)
        local class = StaticFindObject("/Game/UI/Game_Setup/W_Menu_GameSetupSettingEntry.W_Menu_GameSetupSettingEntry_C")
        local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
        local controller = FindFirstOf("PlayerController")
        local widget = step("Create clone", function() return library:Create(controller, class, controller) end)
        if isValid(widget) then
            step("AddChild", function() return box:AddChild(widget) end)
            result.clone_name = step("clone name", function() return widget:GetFName():ToString() end)
            result.clone_spinner_valid = step("clone Spinner", function() return isValid(widget.Spinner) end)
        end
        result.after = children()
    end
    result.steps = steps
    return result
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
