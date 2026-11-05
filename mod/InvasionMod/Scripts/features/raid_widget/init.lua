-- Feature raid_widget (M02 iteration 05, decision 4): one menu for all raid information.
-- The layout is a cooked Widget Blueprint in the pak InvasionMod_P.pak (mod/InvasionMod/ue/make_raid_widget.py), in the look of the
-- game's own windows (update-raid-menu-style): a title, an info line (the raid levels) and rows. Each of the LINE_COUNT lines is split at
-- the first ": " into a label (RaidLabel<i>) and a value (RaidLine<i>); an empty line collapses its row (RaidRow<i>).
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
local INFO_LINE = 4 -- the raid levels line: shown under the title, its label ends with a colon
local VISIBLE, COLLAPSED = 4, 1 -- ESlateVisibility: SelfHitTestInvisible (the row takes no clicks), Collapsed

local S = { widget = nil, lines = {}, labels = {}, rows = {}, last_error = nil, shown_lines = {}, last_refresh = 0 }
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

-- Writes one line into its label, its value and its row. A widget that is gone is skipped (IsValid first).
local function show_line(i, text)
    local label, value = lines.split(text)
    if i == INFO_LINE and label ~= "" then label = label .. ":" end
    if isValid(S.labels[i]) then S.labels[i]:SetText(FText(label)) end
    if isValid(S.lines[i]) then S.lines[i]:SetText(FText(value)) end
    if isValid(S.rows[i]) then
        -- The widgets of an empty row are also made invisible: the row must show nothing even if the collapse is ignored.
        S.rows[i]:SetVisibility(text == "" and COLLAPSED or VISIBLE)
        S.rows[i]:SetRenderOpacity(text == "" and 0 or 1)
    end
end

local function refresh()
    if not isValid(S.widget) then return false end
    local texts = lines.all(invasion.raid_info(), terms_summary())
    for i = 1, LINE_COUNT do
        if S.shown_lines[i] ~= texts[i] then
            S.shown_lines[i] = texts[i]
            show_line(i, texts[i])
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
    S.widget, S.lines, S.labels, S.rows, S.shown_lines = nil, {}, {}, {}, {}
end

-- The base menu calls this with the made widget. On a failure this function cleans up and returns nil and a message.
local function on_open(made)
    S.widget = made
    local texts = menu.find_named(made, "TextBlock", menu.pool_names("RaidLine", LINE_COUNT))
    local labels = menu.find_named(made, "TextBlock", menu.pool_names("RaidLabel", LINE_COUNT))
    local rows = menu.find_named(made, "SizeBox", menu.pool_names("RaidRow", LINE_COUNT))
    S.lines, S.labels, S.rows, S.shown_lines = {}, {}, {}, {}
    for i = 1, LINE_COUNT do
        S.lines[i], S.labels[i], S.rows[i] = texts["RaidLine" .. (i - 1)], labels["RaidLabel" .. (i - 1)], rows["RaidRow" .. (i - 1)]
    end
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
        -- The state keeps the full line: the label (no colon) and the value are joined again.
        local label = isValid(S.labels[i]) and read(function() return S.labels[i]:GetText():ToString() end) or nil
        local value = isValid(S.lines[i]) and read(function() return S.lines[i]:GetText():ToString() end) or nil
        if value ~= nil then
            label = (label or ""):gsub(":$", "")
            shown[i] = label ~= "" and (label .. ": " .. value) or value
        end
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
