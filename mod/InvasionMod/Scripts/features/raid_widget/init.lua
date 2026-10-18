-- Feature raid_widget (M02 iteration 05, decision 4): one menu for all raid information.
-- The layout is a cooked Widget Blueprint in the pak raidmenu_P.pak (mod/InvasionMod/ue/make_raid_widget.py): a title, LINE_COUNT text
-- lines and three difficulty buttons. Lua fills the texts and polls the buttons (the Blueprint has no graph, spec 16).
-- F8 opens and closes the menu. A click on a difficulty button picks the difficulty (until the first raid or the first pick).
-- Rules: game objects are touched on the game thread only (the scheduler runs jobs there). No LoopAsync of its own.
local core = require("ManorCore")
local lines = require("features.raid_widget.lines")
local invasion = require("features.invasion.init")
local config = require("config").raid_widget

local TAG = "InvasionMod.raid_widget"
local CLASS_PATH = "/Game/HarnessMod/WBP_RaidMenu.WBP_RaidMenu_C"
local PACKAGE_PATH, ASSET_NAME = "/Game/HarnessMod", "WBP_RaidMenu"
local LINE_COUNT, BUTTON_COUNT = 5, 3
local VISIBLE, COLLAPSED = 0, 1 -- ESlateVisibility

local S = { widget = nil, lines = {}, buttons = {}, picks = 0, last_error = nil }
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
        if S.lines[i] then S.lines[i]:SetText(FText(texts[i])) end
    end
    for i = 1, BUTTON_COUNT do
        if S.buttons[i] then S.buttons[i].button:SetVisibility(info.picks_allowed and VISIBLE or COLLAPSED) end
    end
    return true
end

-- A click is a press that ends while the mouse is on the button (same rule as PolicyMenu).
local function check_button(slot, value)
    local pressed = read(function() return slot.button:IsPressed() end) == true
    if pressed then slot.hovered = read(function() return slot.button:IsHovered() end) == true end
    local released = slot.was_pressed and not pressed
    slot.was_pressed = pressed
    if not (released and slot.hovered) or os.clock() - slot.last_click < config.click_cooldown_s then return end
    slot.last_click = os.clock()
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

local function tick()
    if toggle_requested then
        toggle_requested = false
        core.log.try(TAG, toggle)
    end
    if not isValid(S.widget) then
        S.widget = nil
        return
    end
    for value, slot in ipairs(S.buttons) do check_button(slot, value) end
    refresh()
end

local function is_open()
    return isValid(S.widget)
end

local function open()
    if is_open() then return { ok = true, already_open = true } end
    local made, problem = make_widget()
    if not made then return { ok = false, error = problem } end
    S.widget = made
    S.lines = find_named(made, "TextBlock", "RaidLine", LINE_COUNT)
    local buttons = find_named(made, "Button", "DifficultyButton", BUTTON_COUNT)
    local labels = find_named(made, "TextBlock", "DifficultyLabel", BUTTON_COUNT)
    S.buttons = {}
    for i = 1, BUTTON_COUNT do
        if buttons[i] and labels[i] then
            S.buttons[i] = { button = buttons[i], was_pressed = false, hovered = false, last_click = -100 }
            labels[i]:SetText(FText("Pick difficulty " .. i))
        end
    end
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
    S.widget, S.lines, S.buttons = nil, {}, {}
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
        buttons[#buttons + 1] = { value = value, visibility = read(function() return slot.button:GetVisibility() end),
            hovered = read(function() return slot.button:IsHovered() end) }
    end
    return { open = is_open(), in_viewport = is_open() and read(function() return S.widget:IsInViewport() end) or false,
        lines = shown, wanted_lines = current_lines(), buttons = buttons, picks = S.picks, last_error = S.last_error }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.raid_widget_open", open, {})
    commands.register("InvasionMod.raid_widget_close", close, {})
    commands.register("InvasionMod.raid_widget_state", describe, {})
end

require("scheduler").every(TAG, config.poll_ms, tick)
-- The key callback runs on the input thread. It must not touch the Lua state beyond one flag:
-- Lua calls from it raced with the game thread and crashed the game (UE4SS luaH_getint). The tick does the work.
RegisterKeyBind(config.toggle_key, function() toggle_requested = true end)

core.log.info(TAG, "feature raid_widget loaded (F8 opens and closes the menu)")
return { open = open, close = close }
