-- Feature raid_widget (M02 iteration 05, decision 4): one menu for all raid information.
-- The layout is a cooked Widget Blueprint in the pak InvasionMod_P.pak (mod/InvasionMod/ue/make_raid_widget.py): a title, LINE_COUNT text
-- lines and three Borders (unused since add-scenario-settings-menu: the player picks the difficulty in the scenario settings menu).
-- The menu is built on the base menu (core/menu.lua): it gets a bottom bar button, opens fullscreen and blocks clicks to the game.
-- F8 stays as a shortcut.
-- Rules: game objects are touched on the game thread only (the scheduler runs jobs there). No LoopAsync of its own.
local core = require("ManorCore")
local menu = require("core.menu")
local lines = require("features.raid_widget.lines")
local invasion = require("features.invasion.init")
local config = require("config").raid_widget

local TAG = "InvasionMod.raid_widget"
local MENU_ID = "raid"
local LINE_COUNT = 5

local S = { widget = nil, lines = {}, last_error = nil, shown_lines = {}, last_refresh = 0 }
local isValid, read = core.isValid, core.read

local function terms_summary()
    local loaded = package.loaded["features.sack_and_terms.terms"]
    if loaded == nil or loaded.summary == nil then return nil end
    local ok, summary = pcall(loaded.summary)
    return ok and summary or nil
end

local function current_lines()
    return lines.all(invasion.raid_info(), terms_summary())
end

local function refresh()
    if not isValid(S.widget) then return false end
    local texts = lines.all(invasion.raid_info(), terms_summary())
    for i = 1, LINE_COUNT do
        if S.lines[i] and S.shown_lines[i] ~= texts[i] then
            S.shown_lines[i] = texts[i]
            S.lines[i]:SetText(FText(texts[i]))
        end
    end
    return true
end

local function is_open() return menu.is_open(MENU_ID) end

local function tick()
    if not is_open() then
        S.widget = nil
        return
    end
    -- The labels change only when the game state changes. A refresh each tick made a lot of Lua garbage.
    local now = os.clock()
    if now - S.last_refresh >= config.refresh_ms / 1000 then
        S.last_refresh = now
        refresh()
    end
end

local function reset()
    S.widget, S.lines, S.shown_lines = nil, {}, {}
end

-- The base menu calls this with the made widget. On a failure this function cleans up and returns nil and a message.
local function on_open(made)
    S.widget = made
    local texts = menu.find_named(made, "TextBlock", menu.pool_names("RaidLine", LINE_COUNT))
    S.lines = {}
    for i = 1, LINE_COUNT do S.lines[i] = texts["RaidLine" .. (i - 1)] end
    if S.lines[1] == nil then
        reset()
        return nil, "the text lines were not found in the widget"
    end
    refresh()
    return true
end

menu.register({
    id = MENU_ID, label = "Raid",
    class_path = "/Game/HarnessMod/WBP_RaidMenu.WBP_RaidMenu_C", package_path = "/Game/HarnessMod", asset_name = "WBP_RaidMenu",
    z_order = config.z_order, position = config.position,
    on_open = on_open, on_close = reset,
})

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local function describe()
    local shown = {}
    for i = 1, LINE_COUNT do
        shown[i] = S.lines[i] and read(function() return S.lines[i]:GetText():ToString() end) or nil
    end
    return { open = is_open(), in_viewport = is_open() and read(function() return S.widget:IsInViewport() end) or false,
        lines = shown, wanted_lines = current_lines(), last_error = S.last_error }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.raid_widget_open", function() return menu.open(MENU_ID) end, {})
    commands.register("InvasionMod.raid_widget_close", function()
        if is_open() then return menu.close() end
        return { ok = true }
    end, {})
    commands.register("InvasionMod.raid_widget_state", describe, {})
end

require("scheduler").every(TAG, config.poll_ms, tick)
-- The key callback runs on the input thread. It must not touch the Lua state beyond one flag:
-- Lua calls from it raced with the game thread and crashed the game (UE4SS luaH_getint). The base menu tick does the work.
RegisterKeyBind(config.toggle_key, function() menu.request_toggle(MENU_ID) end)

core.log.info(TAG, "feature raid_widget loaded (the Raid button in the bottom bar, or F8, opens and closes the menu)")
return { open = function() return menu.open(MENU_ID) end, close = menu.close }
