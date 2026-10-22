-- Feature scenario_settings (change add-scenario-settings-menu, #375): the menu that opens when a new game starts.
-- The player sets the difficulty, the first Hussite raid year, the raid size and the great raids, then clicks "Begin the game".
-- The settings are stored in the mod state of the invasion feature (so they are saved with the game by the player's own save).
-- The mod never calls a save function. It does not use or change the game's own new game menus.
-- The menu is built on the base menu (core/menu.lua) without a bottom bar button. Its layout is a cooked Widget Blueprint in the
-- pak raidmenu_P.pak (ue/make_scenario_settings_widget.py). The click buttons are WBP_ClickButton (HarnessClickHooks).
-- Rules: game objects are touched on the game thread only (the scheduler runs jobs there). A click is a hook event.
local core = require("ManorCore")
local menu = require("core.menu")
local clickhooks = require("HarnessClickHooks")
local invasion = require("features.invasion.init")
local rules = require("features.scenario_settings.rules")
local config = require("config").scenario_settings

local TAG = "InvasionMod.scenario_settings"
local MENU_ID = "scenario_settings"
local isValid, read = core.isValid, core.read
local state = invasion.state

local MAX_CHOICES = 3
local S = {
    decided = false, kind = nil,           -- the decision runs once per game session
    holding = false,                       -- a new game waits for the menu: the invasion feature plans and shows nothing
    waiting_since = nil,                   -- os.clock() when the menu waited for the intro
    selection = rules.defaults(config),    -- what the menu shows
    session = false, paused = false,       -- the menu is open and we paused the game
    widget = nil, title = nil, background = nil, labels = {}, choices = {}, buttons = {},
    last_error = nil, clicks = 0, unknown_logged = false,
}

---------------------------------------------------------------------------------------------
-- Game reads
---------------------------------------------------------------------------------------------

local function engine() return FindFirstOf("RTSMultiEngineCPP") end

local function player()
    local e = engine()
    if not isValid(e) then return nil end
    local pawn = read(function() return e.playerRef end)
    if isValid(pawn) then return pawn end
    return nil
end

local function current_day()
    local e = engine()
    if not isValid(e) then return nil end
    local day = read(function() return e.TemporalComponent.daysTotal end)
    return type(day) == "number" and math.floor(day) or nil
end

-- The name of the save file that is loading. Empty on a new game. nil when it cannot be read.
local function save_file_name()
    local instance = FindFirstOf("MLGameInstance")
    if not isValid(instance) then return nil end
    local value = read(function() return instance.savefileToLoad end)
    if value == nil then return nil end
    if type(value) == "string" then return value end
    return read(function() return value:ToString() end)
end

-- true while the intro cinematic plays (PawnCPP.currentUIMode is not 0). A value that cannot be read counts as "not playing".
local function intro_playing()
    local pawn = player()
    if pawn == nil then return false end
    local mode = read(function() return pawn.currentUIMode end)
    return type(mode) == "number" and mode ~= 0
end

-- Pause: pauseGame. Un-pause: unPauseGame, then the begin speed. A new game starts at game speed 0 and unPauseGame alone leaves it
-- there (run 20261022-045052-489b), so the game would stay still after "Begin the game".
local function set_paused(paused)
    local pawn = player()
    if pawn == nil then return false, "no player pawn" end
    local name = paused and "pauseGame" or "unPauseGame"
    local ok, problem = pcall(function()
        pawn[name](pawn)
        if not paused then pawn:changeGameSpeed(config.begin_speed, false) end
    end)
    if not ok then
        core.log.warn(TAG, name .. " failed: " .. tostring(problem))
        return false, tostring(problem)
    end
    return true
end

-- The game undoes the first disable_autosave right after a new game from the menu (spike #358). It is sent again after the
-- intro and after "Begin the game". This is not a save function: it only restarts the autosave timer with a long period.
local function disable_autosave()
    if not config.disable_autosave then return end
    local ok, autosave = pcall(require, "HarnessAutosave")
    if not ok then return core.log.warn(TAG, "HarnessAutosave is not available: " .. tostring(autosave)) end
    local changes, problem = autosave.disable()
    if not changes then return core.log.warn(TAG, "disable_autosave failed: " .. tostring(problem)) end
    core.log.info(TAG, "disable_autosave sent")
end

---------------------------------------------------------------------------------------------
-- Settings in the mod state
---------------------------------------------------------------------------------------------

local function current_settings()
    local fixed = state:get("size_class_fixed")
    return {
        difficulty = state:get("difficulty"), first_raid_years = state:get("first_raid_years"),
        size_class = fixed >= 1 and fixed or config.defaults.size_class, size_random = fixed == 0,
        great_raids = state:get("great_raids"),
    }
end

-- The player's choice: the difficulty counts as chosen. "settings_applied" says the settings exist.
local function apply(selection)
    S.holding = false
    invasion.set_difficulty(selection.difficulty)
    state:set("first_raid_years", selection.first_raid_years)
    state:set("size_class_fixed", selection.size_class)
    state:set("great_raids", selection.great_raids)
    state:set("settings_applied", 1)
    invasion.settings_changed()
    core.log.info(TAG, string.format("settings applied: difficulty=%d first_raid_years=%d size_class=%d great_raids=%d",
        selection.difficulty, selection.first_raid_years, selection.size_class, selection.great_raids))
end

-- A save without settings (made before this feature): the defaults, no menu. A difficulty the player chose stays.
local function apply_old_save()
    S.holding = false
    local defaults = rules.defaults(config)
    if state:get("difficulty_chosen") == 0 then state:set("difficulty", defaults.difficulty) end
    state:set("first_raid_years", defaults.first_raid_years)
    state:set("size_class_fixed", defaults.size_class)
    state:set("great_raids", defaults.great_raids)
    state:set("settings_applied", 1)
    invasion.settings_changed()
    core.log.info(TAG, "an old save without settings got the defaults")
end

---------------------------------------------------------------------------------------------
-- The widget
---------------------------------------------------------------------------------------------

local function set_text(block, text)
    if isValid(block) then block:SetText(FText(text)) end
end

local function show_selection()
    if not isValid(S.widget) then return end
    for row_index, row in ipairs(rules.ROWS) do
        local selected = rules.selected_index(S.selection, row.key)
        for index = 1, #row.values do
            local slot = S.choices[row_index] and S.choices[row_index][index]
            if slot then clickhooks.set_text(slot.handle, rules.choice_text(config, row.key, index, index == selected)) end
        end
    end
end

local function release_buttons()
    local handles = {}
    for _, row in pairs(S.choices) do
        for _, slot in pairs(row) do handles[#handles + 1] = slot.handle end
    end
    for _, slot in pairs(S.buttons) do handles[#handles + 1] = slot.handle end
    clickhooks.release(handles)
end

local function reset_widget()
    release_buttons()
    S.widget, S.title, S.background, S.labels, S.choices, S.buttons = nil, nil, nil, {}, {}, {}
end

local function border_names()
    local names = { "DefaultsButton", "BeginButton" }
    for row = 0, #rules.ROWS - 1 do
        for choice = 0, MAX_CHOICES - 1 do names[#names + 1] = "Choice" .. row .. "_" .. choice end
    end
    return names
end

-- The base menu calls this with the made widget. On a failure this function cleans up and returns nil and a message.
local function on_open(made)
    S.widget = made
    local label_names = { "SettingsTitle", "BackgroundText" }
    for row = 0, #rules.ROWS - 1 do label_names[#label_names + 1] = "RowLabel" .. row end
    local texts = menu.find_named(made, "TextBlock", label_names)
    local borders = menu.find_named(made, "Border", border_names())
    local controller = FindFirstOf("PlayerController")
    local handles = {}
    S.choices, S.buttons = {}, {}
    local function attach(border_name, tag)
        local border = borders[border_name]
        if border == nil then return nil, "the widget has no " .. border_name end
        local handle, problem = clickhooks.attach(border, controller, tag)
        if not handle then return nil, problem end
        handles[#handles + 1] = handle
        return { handle = handle }
    end
    for row_index, row in ipairs(rules.ROWS) do
        S.choices[row_index] = {}
        for index, value in ipairs(row.values) do
            local slot, problem = attach("Choice" .. (row_index - 1) .. "_" .. (index - 1), { owner = S, action = "choose", key = row.key, value = value })
            if not slot then reset_widget(); return nil, problem end
            S.choices[row_index][index] = slot
        end
        for index = #row.values + 1, MAX_CHOICES do -- a row with fewer choices: hide the unused border
            local border = borders["Choice" .. (row_index - 1) .. "_" .. (index - 1)]
            if border then border:SetVisibility(1) end -- Collapsed
        end
    end
    for _, name in ipairs({ "defaults", "begin" }) do
        local slot, problem = attach(name == "defaults" and "DefaultsButton" or "BeginButton", { owner = S, action = name })
        if not slot then reset_widget(); return nil, problem end
        S.buttons[name] = slot
    end
    local bound, bind_problem = clickhooks.bind_texts(handles)
    if not bound then reset_widget(); return nil, bind_problem end
    S.title, S.background = texts.SettingsTitle, texts.BackgroundText
    if S.title == nil or S.background == nil then reset_widget(); return nil, "the title or the background text was not found in the widget" end
    set_text(S.title, config.title)
    set_text(S.background, config.background_text)
    for row_index, row in ipairs(rules.ROWS) do
        S.labels[row_index] = texts["RowLabel" .. (row_index - 1)]
        set_text(S.labels[row_index], config.labels[row.key])
    end
    clickhooks.set_text(S.buttons.defaults.handle, config.defaults_label)
    clickhooks.set_text(S.buttons.begin.handle, config.begin_label)
    show_selection()
    return true
end

---------------------------------------------------------------------------------------------
-- Open, close, clicks
---------------------------------------------------------------------------------------------

local function is_open() return menu.is_open(MENU_ID) end

-- The menu closed (the Begin button, the Close button, or the game removed the widget): store the choice, un-pause.
local function on_close()
    local was_session = S.session
    reset_widget()
    S.session = false
    if not was_session then return end
    apply(S.selection)
    if S.paused then
        S.paused = false
        set_paused(false)
    end
    disable_autosave()
end

-- Shows the menu with the stored settings (or the defaults). Pauses the game. When the menu cannot open, the defaults apply and
-- the game runs (spec "The menu follows the approved look").
local function open_menu()
    S.selection = rules.defaults(config)
    S.session = true
    local result = menu.open(MENU_ID)
    if not result.ok then
        S.session = false
        S.last_error = result.error
        core.log.warn(TAG, "the settings menu did not open (" .. tostring(result.error) .. "); the defaults apply and the game is not paused")
        apply(rules.defaults(config))
        disable_autosave()
        return result
    end
    local paused, problem = set_paused(true)
    S.paused = paused
    if not paused then core.log.warn(TAG, "the game is not paused: " .. tostring(problem)) end
    return result
end

local function handle_click(action, key, value)
    S.clicks = S.clicks + 1
    local selection, begin = rules.click(S.selection, config, action, key, value)
    if not selection then
        S.last_error = begin
        return core.log.warn(TAG, "click refused: " .. tostring(begin))
    end
    S.selection = selection
    if begin then return menu.close() end
    show_selection()
end

local function drain_clicks()
    for _, handle in ipairs(clickhooks.drain(S)) do
        handle_click(handle.tag.action, handle.tag.key, handle.tag.value)
    end
end

local function after_open_tick()
    if S.session and not is_open() then on_close() end -- the game removed the widget (a load)
    if S.session then drain_clicks() end
end

---------------------------------------------------------------------------------------------
-- New game or loaded save (once per game session)
---------------------------------------------------------------------------------------------

local function decide()
    if S.decided or not state.loaded then return end
    local info = { save_file = save_file_name(), applied = state:get("settings_applied"), day = current_day() }
    local kind = rules.kind_of_game(info, config)
    if kind == "unknown" then
        if not S.unknown_logged then
            S.unknown_logged = true
            core.log.info(TAG, "the game is not known as new or loaded yet (no MLGameInstance); the menu waits")
        end
        return
    end
    S.decided, S.kind = true, kind
    core.log.info(TAG, string.format("game is %s (save_file=%q applied=%d day=%s)", kind, tostring(info.save_file), info.applied, tostring(info.day)))
    S.holding = kind == "new"
    if kind == "old_save" then apply_old_save() end
    if kind == "loaded" or kind == "old_save" then invasion.settings_changed() end
end

-- A new game waits for the end of the intro, then opens the menu.
local function open_after_intro()
    if S.kind ~= "new" or S.session or state:get("settings_applied") == 1 then return end
    S.waiting_since = S.waiting_since or os.clock()
    if intro_playing() and os.clock() - S.waiting_since < config.intro_wait_s then return end
    if player() == nil then return end
    disable_autosave() -- after the intro (the first call right after a new game is undone)
    S.kind = "opened"
    open_menu()
end

local function tick()
    decide()
    open_after_intro()
    after_open_tick()
end

require("scheduler").every(TAG, config.poll_ms, tick)

-- The invasion feature asks before each daily step. The decision runs first, so a new game is held before its first banner.
invasion.set_hold_gate(function()
    decide()
    return S.holding
end)

menu.register({
    id = MENU_ID, label = "Scenario", bar = false,
    class_path = "/Game/HarnessMod/WBP_ScenarioSettings.WBP_ScenarioSettings_C", package_path = "/Game/HarnessMod", asset_name = "WBP_ScenarioSettings",
    z_order = config.z_order, position = config.position,
    on_open = on_open, on_close = on_close,
})

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local function describe()
    local settings = current_settings()
    return {
        difficulty = settings.difficulty, first_raid_years = settings.first_raid_years, size_class = settings.size_class,
        size_random = settings.size_random, great_raids = settings.great_raids,
        settings_applied = state:get("settings_applied") == 1, difficulty_chosen = state:get("difficulty_chosen") == 1,
        kind = S.kind, decided = S.decided, open = is_open(), paused = S.paused, selection = S.selection, clicks = S.clicks,
        last_error = S.last_error, save_file = save_file_name(), day = current_day(), intro_playing = intro_playing(),
    }
end

-- Close the menu (if open) and apply the defaults. In a new game that has not opened the menu yet, the menu does not open.
local function command_skip()
    S.selection = rules.defaults(config)
    if S.session then
        menu.close() -- on_close applies the selection
    else
        apply(S.selection)
    end
    S.decided = true
    if S.kind == "new" then S.kind = "skipped" end
    return describe()
end

-- Set any of the four settings by name, apply them and close the menu. A setting that is not named stays as it is now.
local function command_set(args)
    local selection = rules.defaults(config)
    local now = current_settings()
    selection.difficulty, selection.first_raid_years, selection.great_raids = now.difficulty, now.first_raid_years, now.great_raids
    selection.size_class = now.size_class
    for _, key in ipairs({ "difficulty", "first_raid_years", "size_class", "great_raids" }) do
        if args[key] ~= nil then
            local chosen, problem = rules.choose(selection, key, args[key])
            if not chosen then return nil, problem end
            selection = chosen
        end
    end
    S.selection = selection
    if S.session then
        menu.close()
    else
        apply(selection)
    end
    S.decided = true
    if S.kind == "new" then S.kind = "skipped" end
    return describe()
end

local function command_open()
    S.decided = true
    local result = open_menu()
    if not result.ok then return nil, result.error end
    return describe()
end

-- A click on the menu without the mouse (for tests): the same code a click button hook runs through.
local function command_click(args)
    if not S.session then return nil, "the settings menu is not open" end
    handle_click(args.action, args.key, args.value)
    return describe()
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.scenario_settings_state", describe, {})
    commands.register("InvasionMod.scenario_settings_skip", command_skip, {})
    commands.register("InvasionMod.scenario_settings_open", command_open, {})
    commands.register("InvasionMod.scenario_settings_set", command_set, {
        difficulty = { type = "integer", min = 1, max = 3 },
        first_raid_years = { type = "integer", min = 1, max = 3 },
        size_class = { type = "integer", min = 1, max = 3 },
        great_raids = { type = "integer", min = 0, max = 1 },
    })
    commands.register("InvasionMod.scenario_settings_click", command_click, {
        action = { type = "string", required = true, oneOf = { "choose", "defaults", "begin" } },
        key = { type = "string" }, value = { type = "integer" },
    })
end

core.log.info(TAG, "feature scenario_settings loaded (the menu opens when a new game starts)")
-- on_close is exported for the fake game tests, which replace the widget part of the base menu.
return { open = open_menu, state = describe, on_close = on_close }
