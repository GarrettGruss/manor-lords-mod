-- Feature liege_influence: the player sends silver from the lord's treasury to the liege and gains influence.
-- The influence is a saved ModState value. It has no decay and no cap (owner decision 2026-10-19).
local core = require("ManorCore")
local ModState = require("ModState")
local rules = require("features.liege_influence.rules")
local config = require("config").liege_influence

local TAG = "InvasionMod.liege_influence"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("liege_influence", 0, "number")

local function engine()
    local found = FindFirstOf("RTSMultiEngineCPP")
    if core.isValid(found) then return found end
    return nil
end

local function silver()
    local e = engine()
    if e == nil then return nil end
    local ok, value = pcall(function() return e.playerRef.silver end)
    if ok and type(value) == "number" then return value end
    return nil
end

-- A direct write to silver does not raise the HUD update event, so the lord panel keeps the old number (spike 2026-10-19).
-- The panel's own updatePlayerStats function reads playerRef.silver again.
local function refresh_hud()
    local ok, problem = pcall(function()
        local panel = FindFirstOf("W_HUD_LordPanel_V2_C")
        if core.isValid(panel) then panel:updatePlayerStats() end
    end)
    if not ok then core.log.warn(TAG, "HUD refresh failed: " .. tostring(problem)) end
end

-- The menu and the command call this function. Returns a result table, or nil and a reason.
local function send_tribute(amount)
    local before = silver()
    local reason = rules.refusal(amount, before)
    if reason then
        core.log.warn(TAG, "LIEGE tribute refused: " .. reason)
        return nil, reason
    end
    local ok, problem = pcall(function() engine().playerRef.silver = before - amount end)
    if not ok then return nil, "silver write failed: " .. tostring(problem) end
    refresh_hud()
    local influence_before = state:get("liege_influence")
    state:set("liege_influence", influence_before + rules.gain(amount, config.influence_per_unit))
    local result = { amount = amount, silver_before = before, silver = silver(), influence_before = influence_before,
        influence = state:get("liege_influence") }
    core.log.info(TAG, string.format("LIEGE tribute %d silver: influence %s -> %s", amount, tostring(influence_before), tostring(result.influence)))
    return result
end

local function command_state()
    return { influence = state:get("liege_influence"), silver = silver(), influence_per_unit = config.influence_per_unit,
        tribute_button_amount = config.tribute_button_amount }
end

---------------------------------------------------------------------------------------------
-- The tribute menu: a cooked Widget Blueprint in the pak raidmenu_P.pak (mod/InvasionMod/ue/make_liege_widget.py).
-- Lua puts a click button into each Border (shared module HarnessClickHooks). A click is a hook event, not a poll (spec 34).
-- The 2-click HUD entry point is a later change (add-mod-menu-access-rule). Now the commands liege_menu_open and liege_menu_close open it.
---------------------------------------------------------------------------------------------
local clickhooks = require("HarnessClickHooks")
local isValid, read = core.isValid, core.read
local CLASS_PATH = "/Game/HarnessMod/WBP_LiegeTribute.WBP_LiegeTribute_C"
local PACKAGE_PATH, ASSET_NAME = "/Game/HarnessMod", "WBP_LiegeTribute"
local BUTTON_NAMES = { "TributeButton", "CloseButton" } -- the tag value of a button is its name

local S = { widget = nil, texts = {}, buttons = {}, shown = {}, last_refresh = 0, tributes = 0, last_error = nil }

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

-- Finds the children of the widget tree by name (Python cannot mark them as variables).
local function find_named(widget, class_name, names)
    local widget_name = read(function() return widget:GetFName():ToString() end)
    local wanted, found = {}, {}
    for _, name in ipairs(names) do wanted[name] = true end
    for _, object in ipairs(FindAllOf(class_name) or {}) do
        local full = read(function() return object:GetFullName() end) or ""
        local name = full:match("%.([%w_]+)$") or full:match("%.([%w_]+) ")
        if name and wanted[name] and widget_name and full:find(widget_name, 1, true) then found[name] = object end
    end
    return found
end

local function wanted_texts()
    return {
        InfluenceText = string.format("Influence: %g", math.floor((state:get("liege_influence") or 0) * 100 + 0.5) / 100),
        TributeInfoText = string.format("Tribute: %d silver (you have %d)", config.tribute_button_amount, silver() or 0),
    }
end

local function is_open() return isValid(S.widget) end

-- The labels change only when the value changes (no SetText each tick).
local function refresh()
    if not is_open() then return false end
    for name, text in pairs(wanted_texts()) do
        if S.texts[name] and S.shown[name] ~= text then
            S.shown[name] = text
            S.texts[name]:SetText(FText(text))
            -- The silver changed (a tribute, or another mod): keep the HUD number in step with the menu.
            if name == "TributeInfoText" then refresh_hud() end
        end
    end
    return true
end

local function release_buttons()
    local handles = {}
    for _, slot in pairs(S.buttons) do handles[#handles + 1] = slot.handle end
    clickhooks.release(handles)
end

local function close_menu()
    if is_open() then S.widget:RemoveFromParent() end
    release_buttons()
    S.widget, S.texts, S.buttons, S.shown = nil, {}, {}, {}
    return { ok = true }
end

local function abort_open(made, problem)
    release_buttons()
    if made then made:RemoveFromParent() end
    S.widget, S.texts, S.buttons, S.shown = nil, {}, {}, {}
    return { ok = false, error = problem }
end

local function open_menu()
    if is_open() then return { ok = true, already_open = true } end
    local made, problem = make_widget()
    if not made then return { ok = false, error = problem } end
    S.widget = made
    S.texts = find_named(made, "TextBlock", { "InfluenceText", "TributeInfoText" })
    local borders = find_named(made, "Border", BUTTON_NAMES)
    if S.texts.InfluenceText == nil then return abort_open(made, "the text lines were not found in the widget") end
    local controller = FindFirstOf("PlayerController")
    S.buttons = {}
    for _, name in ipairs(BUTTON_NAMES) do
        if borders[name] == nil then return abort_open(made, "button not found in the widget: " .. name) end
        local handle, attach_problem = clickhooks.attach(borders[name], controller, { owner = S, value = name })
        if not handle then return abort_open(made, attach_problem) end
        S.buttons[name] = { handle = handle }
    end
    local handles = {}
    for _, slot in pairs(S.buttons) do handles[#handles + 1] = slot.handle end
    local bound, bind_problem = clickhooks.bind_texts(handles)
    if not bound then return abort_open(made, bind_problem) end
    clickhooks.set_text(S.buttons.TributeButton.handle, "Send tribute")
    clickhooks.set_text(S.buttons.CloseButton.handle, "Close")
    made:AddToViewport(config.z_order)
    made:SetPositionInViewport(config.position, false)
    refresh()
    return { ok = true }
end

local function press(name)
    if name == "CloseButton" then
        close_menu()
        return
    end
    local result, reason = send_tribute(config.tribute_button_amount)
    if result then
        S.tributes = S.tributes + 1
        S.last_error = nil
    else
        S.last_error = reason
    end
    refresh()
end

local function tick()
    if not is_open() then
        S.widget = nil
        return
    end
    local clicked = clickhooks.drain(S)
    for _, handle in ipairs(clicked) do
        press(handle.tag.value)
        if not is_open() then return end
    end
    local now = os.clock()
    if now - S.last_refresh >= config.refresh_ms / 1000 then
        S.last_refresh = now
        refresh()
    end
end

local function menu_state()
    local shown = {}
    for name, block in pairs(S.texts) do shown[name] = read(function() return block:GetText():ToString() end) end
    local buttons = {}
    for name, slot in pairs(S.buttons) do
        buttons[#buttons + 1] = { name = name, visibility = read(function() return slot.handle.widget:GetVisibility() end),
            hovered = read(function() return slot.handle.widget:IsHovered() end) }
    end
    return { open = is_open(), in_viewport = is_open() and read(function() return S.widget:IsInViewport() end) or false,
        texts = shown, wanted_texts = wanted_texts(), buttons = buttons, tributes = S.tributes, last_error = S.last_error }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.liege_menu_open", open_menu, {})
    commands.register("InvasionMod.liege_menu_close", close_menu, {})
    commands.register("InvasionMod.liege_menu_state", menu_state, {})
    commands.register("InvasionMod.liege_state", command_state, {})
    commands.register("InvasionMod.liege_send_tribute", function(args)
        local result, reason = send_tribute(args.amount)
        if not result then return nil, reason end
        return result
    end, { amount = { type = "integer", required = true, min = 1, max = 1000000 } })
end

-- The scheduler runs the tick on the game thread. The poll time has a floor of 100 ms.
require("scheduler").every(TAG, math.max(100, config.poll_ms), tick)

core.log.info(TAG, "feature liege_influence loaded")
return { state = state, send_tribute = send_tribute, command_state = command_state, open = open_menu, close = close_menu }
