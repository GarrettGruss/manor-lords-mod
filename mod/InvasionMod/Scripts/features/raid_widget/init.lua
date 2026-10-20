-- Feature raid_widget (M02 iteration 05, decision 4): one menu for all raid information.
-- The layout is a cooked Widget Blueprint in the pak raidmenu_P.pak (mod/InvasionMod/ue/make_raid_widget.py): a title, LINE_COUNT text
-- lines and three Borders. Lua puts a click button (WBP_ClickButton, shared module HarnessClickHooks) into each Border.
-- A click is a hook event, not a poll (spec 34).
-- F8 opens and closes the menu. A click on a difficulty button picks the difficulty (until the first raid or the first pick).
-- Rules: game objects are touched on the game thread only (the scheduler runs jobs there). No LoopAsync of its own.
local core = require("ManorCore")
local lines = require("features.raid_widget.lines")
local invasion = require("features.invasion.init")
local config = require("config").raid_widget
local clickhooks = require("HarnessClickHooks")

local TAG = "InvasionMod.raid_widget"
local CLASS_PATH = "/Game/HarnessMod/WBP_RaidMenu.WBP_RaidMenu_C"
local PACKAGE_PATH, ASSET_NAME = "/Game/HarnessMod", "WBP_RaidMenu"
local LINE_COUNT, BUTTON_COUNT = 5, 3

local S = { widget = nil, lines = {}, buttons = {}, picks = 0, last_error = nil, shown_lines = {}, last_refresh = 0 }
local isValid, read = core.isValid, core.read

-- LoadAsset does not load an asset of a mod pak. The asset registry call does (spec 16 pak-widget-spike.md).
local function find_class()
    local found = StaticFindObject(CLASS_PATH)
    if isValid(found) then return found end
    local registry = StaticFindObject("/Script/AssetRegistry.Default__AssetRegistryHelpers")
    if not isValid(registry) then return nil, "AssetRegistryHelpers not found" end
    local data = {
        PackageName = FName(PACKAGE_PATH .. "/" .. ASSET_NAME), PackagePath = FName(PACKAGE_PATH), AssetName = FName(ASSET_NAME),
        AssetClassPath = { PackageName = FName("/Script/UMGEditor"), AssetName = FName("WidgetBlueprint") },
    }
    local ok, err = pcall(function() return registry:GetAsset(data) end)
    if not ok then return nil, "GetAsset: " .. tostring(err) end
    found = StaticFindObject(CLASS_PATH)
    if not isValid(found) then return nil, "class not found; is the pak raidmenu_P.pak in Paks/~mods?" end
    return found
end

local function make_widget()
    local class, problem = find_class()
    if not class then return nil, problem end
    local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
    local controller = FindFirstOf("PlayerController")
    if not (isValid(library) and isValid(controller)) then return nil, "widget library or player controller not found" end
    local made = library:Create(controller, class, controller)
    if not isValid(made) then return nil, "WidgetBlueprintLibrary:Create returned no widget" end
    return made
end

-- The children of the widget tree have names like RaidLine0 and DifficultyButton2. Python cannot mark them as variables.
local function find_named(widget, class_name, prefix, count)
    local widget_name = read(function() return widget:GetFName():ToString() end)
    local found = {}
    for _, object in ipairs(FindAllOf(class_name) or {}) do
        local full = read(function() return object:GetFullName() end) or ""
        local index = full:match(prefix .. "(%d+)$") or full:match(prefix .. "(%d+) ")
        if index and widget_name and full:find(widget_name, 1, true) and tonumber(index) < count then found[tonumber(index) + 1] = object end
    end
    return found
end

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
    local info = invasion.raid_info()
    local texts = lines.all(info, terms_summary())
    for i = 1, LINE_COUNT do
        if S.lines[i] and S.shown_lines[i] ~= texts[i] then
            S.shown_lines[i] = texts[i]
            S.lines[i]:SetText(FText(texts[i]))
        end
    end
    for i = 1, BUTTON_COUNT do
        if S.buttons[i] then clickhooks.set_visible(S.buttons[i].handle, info.picks_allowed) end
    end
    return true
end

local function pick(value)
    local result, problem = invasion.pick_difficulty(value)
    if not result then
        S.last_error = problem
        core.log.warn(TAG, "pick refused: " .. tostring(problem))
        return
    end
    S.picks = S.picks + 1
    refresh()
end

local toggle_requested = false
local toggle -- defined below

-- Spike 308: a "Mods" button put straight into the viewport. A click toggles the raid menu.
local is_open_fn
local entry = { handle = nil, clicks = 0 }

local function entry_open()
    local x, y = 100, 100
    if entry.handle and isValid(entry.handle.widget) then return { ok = true, already_open = true } end
    local controller = FindFirstOf("PlayerController")
    local handle, problem = clickhooks.create_standalone(controller, { owner = entry })
    if not handle then return { ok = false, error = problem } end
    local bound, bind_problem = clickhooks.bind_texts({ handle })
    if not bound then return { ok = false, error = bind_problem } end
    clickhooks.set_text(handle, "Mods")
    handle.widget:AddToViewport(config.z_order + 5)
    handle.widget:SetPositionInViewport({ X = x or 20, Y = y or 20 }, false)
    entry.handle = handle
    return { ok = true }
end

local function entry_state()
    local h = entry.handle
    return { exists = h ~= nil and isValid(h.widget), clicks = entry.clicks,
        in_viewport = h ~= nil and read(function() return h.widget:IsInViewport() end) or false,
        hovered = h ~= nil and read(function() return h.widget:IsHovered() end) or false, raid_open = is_open_fn and is_open_fn() or false }
end

local function tick()
    for _ in ipairs(clickhooks.drain(entry)) do
        entry.clicks = entry.clicks + 1
        toggle_requested = true
    end
    if toggle_requested then
        toggle_requested = false
        core.log.try(TAG, toggle)
    end
    if not isValid(S.widget) then
        S.widget = nil
        return
    end
    local clicked = clickhooks.drain(S)
    for _, handle in ipairs(clicked) do pick(handle.tag.value) end
    -- The labels change only when the game state changes. A refresh each tick made a lot of Lua garbage.
    local now = os.clock()
    if #clicked > 0 or now - S.last_refresh >= config.refresh_ms / 1000 then
        S.last_refresh = now
        refresh()
    end
end

local function is_open()
    return isValid(S.widget)
end

is_open_fn = is_open

local function release_buttons()
    local handles = {}
    for _, slot in pairs(S.buttons) do handles[#handles + 1] = slot.handle end
    clickhooks.release(handles)
end

local function open()
    if is_open() then return { ok = true, already_open = true } end
    local made, problem = make_widget()
    if not made then return { ok = false, error = problem } end
    S.widget = made
    S.lines = find_named(made, "TextBlock", "RaidLine", LINE_COUNT)
    local borders = find_named(made, "Border", "DifficultyButton", BUTTON_COUNT)
    local controller = FindFirstOf("PlayerController")
    S.buttons = {}
    for i = 1, BUTTON_COUNT do
        if borders[i] then
            local handle, problem = clickhooks.attach(borders[i], controller, { owner = S, value = i })
            if not handle then
                made:RemoveFromParent()
                S.widget = nil
                return { ok = false, error = problem }
            end
            S.buttons[i] = { handle = handle }
        end
    end
    local handles = {}
    for _, slot in pairs(S.buttons) do handles[#handles + 1] = slot.handle end
    local bound, bind_problem = clickhooks.bind_texts(handles)
    if not bound then
        release_buttons()
        made:RemoveFromParent()
        S.widget, S.buttons = nil, {}
        return { ok = false, error = bind_problem }
    end
    for i, slot in pairs(S.buttons) do clickhooks.set_text(slot.handle, "Pick difficulty " .. i) end
    if S.lines[1] == nil then
        made:RemoveFromParent()
        S.widget = nil
        return { ok = false, error = "the text lines were not found in the widget" }
    end
    made:AddToViewport(config.z_order)
    made:SetPositionInViewport(config.position, false)
    refresh()
    return { ok = true }
end

local function close()
    if is_open() then S.widget:RemoveFromParent() end
    release_buttons()
    S.widget, S.lines, S.buttons, S.shown_lines = nil, {}, {}, {}
    return { ok = true }
end

function toggle()
    if is_open() then return close() end
    return open()
end

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local function describe()
    local shown = {}
    for i = 1, LINE_COUNT do
        shown[i] = S.lines[i] and read(function() return S.lines[i]:GetText():ToString() end) or nil
    end
    local buttons = {}
    for value, slot in pairs(S.buttons) do
        buttons[#buttons + 1] = { value = value, visibility = read(function() return slot.handle.widget:GetVisibility() end),
            hovered = read(function() return slot.handle.widget:IsHovered() end) }
    end
    return { open = is_open(), in_viewport = is_open() and read(function() return S.widget:IsInViewport() end) or false,
        lines = shown, wanted_lines = current_lines(), buttons = buttons, picks = S.picks, last_error = S.last_error }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.raid_widget_open", open, {})
    commands.register("InvasionMod.raid_widget_close", close, {})
    commands.register("InvasionMod.raid_widget_state", describe, {})
    commands.register("InvasionMod.spike_entry_open", entry_open, {})
    commands.register("InvasionMod.spike_entry_state", entry_state, {})
end

require("scheduler").every(TAG, config.poll_ms, tick)
-- The key callback runs on the input thread. It must not touch the Lua state beyond one flag:
-- Lua calls from it raced with the game thread and crashed the game (UE4SS luaH_getint). The tick does the work.
RegisterKeyBind(config.toggle_key, function() toggle_requested = true end)

core.log.info(TAG, "feature raid_widget loaded (F8 opens and closes the menu)")
return { open = open, close = close }
