-- Base menu of the Invasion Mod (change add-mod-menu-access-rule, issue #308).
-- Every mod menu is built on this module. It owns what is the same for all menus:
--   * a button for the menu in the game's bottom bar, after the game's own buttons (a clone of the game's bar button class);
--   * the open and close of the menu, one menu at a time;
--   * a full-screen layer under the menu content that dims the view and blocks clicks to the game (notes/click-blocking.md:
--     a full-screen Button blocks a click, a Border does not);
--   * a Close button (a clone of the bar button class) at the top left, over the layer. A click on the layer does nothing:
--     OnClicked:Add on a Button made at run time crashes the game (notes/menu-findings.md), so the layer has no click callback.
-- A menu adds only its own parts through `register`. The menu content is a cooked Widget Blueprint of the pak.
-- Rules: game objects are touched on the game thread only (the scheduler runs the jobs there). A hook or a key callback only
-- sets a flag or pushes to a queue. Only this module makes a mod menu widget (test_menu_widget_sites.py).
local core = require("ManorCore")

local TAG = "InvasionMod.menu"
local BLOCKER_Z = 450          -- above the HUD, below the menu content (the features use 500)
local CONTENT_Z = 500
local BACKDROP_ALPHA = 0.55
local BAR_POLL_MS = 1000
local TICK_MS = 100
local BAR_BUTTON_CLASS = "/Game/UI/HUD/mainTabButton.mainTabButton_C"
local HUD_CLASS, PANEL_NAME = "MainUICPP_C", "main_tabs_HB"
local LABEL_SCALE = 0.5
local LABEL_COLOR = { R = 1.0, G = 1.0, B = 1.0, A = 1.0 }

local isValid = core.isValid
local M = {}

local menus, order = {}, {}   -- id -> spec; the ids in the order of registration (the order of the buttons)
local S = {
    open_id = nil, content = nil, blocker = nil, close_button = nil,
    toggles = {},              -- ids to toggle at the next tick (a key or a bar click)
    bar_clicks = {},           -- ids of bar buttons clicked since the last tick
    buttons = {},              -- id -> { widget, name }
    hud_name = nil, hooked = false, hover_id = nil,
    last_error = nil, bar_error = nil, press_count = 0, close_presses = 0, bar_polls = 0, hud_found = false, pass_through = 0,
}

local set_label, install_hooks -- defined in the bottom bar part
local function library() return StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary") end

---------------------------------------------------------------------------------------------
-- Registration
---------------------------------------------------------------------------------------------

-- spec = { id, label, class_path, package_path, asset_name, position, z_order,
--          on_open(widget) -> true | nil, problem   (attach the buttons, show the first values; clean up on a failure),
--          on_close() }
function M.register(spec)
    for _, field in ipairs({ "id", "label", "class_path", "package_path", "asset_name", "on_open", "on_close" }) do
        if spec[field] == nil then error("menu.register: missing field " .. field, 0) end
    end
    if menus[spec.id] then error("menu.register: duplicate menu id " .. spec.id, 0) end
    menus[spec.id] = spec
    order[#order + 1] = spec.id
end

---------------------------------------------------------------------------------------------
-- Widgets
---------------------------------------------------------------------------------------------

-- LoadAsset does not load an asset of a mod pak. The asset registry call does (spec 16 pak-widget-spike.md).
local function find_class(spec)
    local found = StaticFindObject(spec.class_path)
    if isValid(found) then return found end
    local registry = StaticFindObject("/Script/AssetRegistry.Default__AssetRegistryHelpers")
    if not isValid(registry) then return nil, "AssetRegistryHelpers not found" end
    local data = {
        PackageName = FName(spec.package_path .. "/" .. spec.asset_name), PackagePath = FName(spec.package_path),
        AssetName = FName(spec.asset_name),
        AssetClassPath = { PackageName = FName("/Script/UMGEditor"), AssetName = FName("WidgetBlueprint") },
    }
    local ok, err = pcall(function() return registry:GetAsset(data) end)
    if not ok then return nil, "GetAsset: " .. tostring(err) end
    found = StaticFindObject(spec.class_path)
    if not isValid(found) then return nil, "class not found; is the pak with " .. spec.asset_name .. " in Paks/~mods?" end
    return found
end

-- Makes the content widget of a menu from its pak asset. Returns the widget, or nil and a message.
function M.create_pak_widget(spec)
    local class, problem = find_class(spec)
    if not class then return nil, problem end
    local lib = library()
    local controller = FindFirstOf("PlayerController")
    if not (isValid(lib) and isValid(controller)) then return nil, "widget library or player controller not found" end
    local made = lib:Create(controller, class, controller)
    if not isValid(made) then return nil, "WidgetBlueprintLibrary:Create returned no widget" end
    return made
end

-- Finds the children of a pak widget by name (Python cannot mark them as variables). `names` is a list of exact names.
-- Returns name -> object.
function M.find_named(widget, class_name, names)
    local widget_name = core.read(function() return widget:GetFName():ToString() end)
    local wanted, found = {}, {}
    for _, name in ipairs(names) do wanted[name] = true end
    for _, object in ipairs(FindAllOf(class_name) or {}) do
        local full = core.read(function() return object:GetFullName() end) or ""
        local name = full:match("%.([%w_]+)$") or full:match("%.([%w_]+) ")
        if name and wanted[name] and widget_name and full:find(widget_name, 1, true) then found[name] = object end
    end
    return found
end

-- Names of a pool: prefix0, prefix1, ... prefix<count-1>.
function M.pool_names(prefix, count)
    local names = {}
    for i = 0, count - 1 do names[#names + 1] = prefix .. i end
    return names
end

-- A pool of children prefix0 .. prefix<count-1>. Returns a list: the object of prefix<i-1> is at index i (nil when missing).
function M.find_pool(widget, class_name, prefix, count)
    local found = M.find_named(widget, class_name, M.pool_names(prefix, count))
    local pool = {}
    for i = 1, count do pool[i] = found[prefix .. (i - 1)] end
    return pool
end

local function make_blocker()
    local controller = FindFirstOf("PlayerController")
    local lib = library()
    local widget = lib:Create(controller, StaticFindObject("/Script/UMG.UserWidget"), controller)
    local tree = StaticConstructObject(StaticFindObject("/Script/UMG.WidgetTree"), widget, FName("MenuBlockerTree"))
    widget.WidgetTree = tree
    local button = StaticConstructObject(StaticFindObject("/Script/UMG.Button"), tree, FName("MenuBlockerButton"))
    tree.RootWidget = button
    button:SetBackgroundColor({ R = 0, G = 0, B = 0, A = BACKDROP_ALPHA })
    widget:SetVisibility(0) -- Visible (a hit-testable widget); a click does not reach the game
    button:SetVisibility(0)
    widget:AddToViewport(BLOCKER_Z)
    widget:SetAnchorsInViewport({ Minimum = { X = 0, Y = 0 }, Maximum = { X = 1, Y = 1 } })
    widget:SetAlignmentInViewport({ X = 0, Y = 0 })
    return widget
end

local function remove_widget(widget)
    if isValid(widget) then widget:RemoveFromParent() end
end

-- A Border of the menu content is Visible, so a click on it is not handled and reaches the game behind the menu
-- (run 20261022-034616-e668: a click on the background of the menu opened the church panel). SelfHitTestInvisible lets the
-- click pass to its children (the click buttons) and, where there is no child, down to the backdrop Button, which blocks it.
local SELF_HIT_TEST_INVISIBLE = 4
local function let_clicks_reach_the_backdrop(content)
    local name = core.read(function() return content:GetFName():ToString() end)
    local count = 0
    for _, border in ipairs(FindAllOf("Border") or {}) do
        local full = core.read(function() return border:GetFullName() end) or ""
        if name and full:find(name, 1, true) then
            border:SetVisibility(SELF_HIT_TEST_INVISIBLE)
            count = count + 1
        end
    end
    content:SetVisibility(SELF_HIT_TEST_INVISIBLE)
    return count
end

local CLOSE_ID = "__close"

-- A clone of the game's bar button at the top left, above the menu content. Its click is the HandleClicked hook (install_hooks).
local function make_close_button()
    local class = StaticFindObject(BAR_BUTTON_CLASS)
    if not isValid(class) then error("bar button class not loaded: " .. BAR_BUTTON_CLASS, 0) end
    local controller = FindFirstOf("PlayerController")
    local widget = library():Create(controller, class, controller)
    if not isValid(widget) then error("Create returned no close button", 0) end
    widget:AddToViewport(CONTENT_Z + 10)
    widget:SetPositionInViewport({ X = 24, Y = 24 }, false)
    set_label(widget, "Close")
    return { widget = widget, name = widget:GetFName():ToString() }
end

---------------------------------------------------------------------------------------------
-- Open and close
---------------------------------------------------------------------------------------------

function M.is_open(id)
    if S.open_id == nil or not isValid(S.content) then return false end
    return id == nil or id == S.open_id
end

local function fail(message)
    S.last_error = message
    core.log.warn(TAG, message)
    return { ok = false, error = message }
end

function M.close()
    local id = S.open_id
    if id == nil then return { ok = true, already_closed = true } end
    core.log.try(TAG, menus[id].on_close)
    remove_widget(S.content)
    remove_widget(S.blocker)
    if S.close_button then remove_widget(S.close_button.widget) end
    S.open_id, S.content, S.blocker, S.close_button = nil, nil, nil, nil
    return { ok = true }
end

function M.open(id)
    local spec = menus[id]
    if not spec then return fail("unknown menu: " .. tostring(id)) end
    if M.is_open(id) then return { ok = true, already_open = true } end
    if S.open_id ~= nil then M.close() end -- one menu at a time
    S.hover_id = nil -- a hover event names a button only when the mouse enters it, so forget the old one
    local content, problem = M.create_pak_widget(spec)
    if not content then return fail(problem) end
    local ok_on_open, opened, open_problem = pcall(spec.on_open, content)
    if not ok_on_open or not opened then
        remove_widget(content)
        return fail("menu " .. id .. " did not open: " .. tostring(ok_on_open and open_problem or opened))
    end
    local made, blocker = pcall(make_blocker)
    local close_made, close_button
    if made then close_made, close_button = pcall(make_close_button) end
    if not (made and close_made) then
        remove_widget(content)
        if made then remove_widget(blocker) end
        core.log.try(TAG, spec.on_close)
        return fail("the backdrop or close button of menu " .. id .. " failed: " .. tostring(made and close_button or blocker))
    end
    S.pass_through = let_clicks_reach_the_backdrop(content)
    install_hooks()
    S.open_id, S.content, S.blocker, S.close_button, S.last_error = id, content, blocker, close_button, nil
    content:AddToViewport(spec.z_order or CONTENT_Z)
    if spec.position then content:SetPositionInViewport(spec.position, false) end
    return { ok = true }
end

function M.toggle(id)
    if M.is_open(id) then return M.close() end
    return M.open(id)
end

-- For a key callback or a hook: it only sets a flag. The tick does the work on the game thread.
function M.request_toggle(id) S.toggles[#S.toggles + 1] = id end

---------------------------------------------------------------------------------------------
-- The bottom bar
---------------------------------------------------------------------------------------------

local function child_count(widget)
    local ok, count = pcall(function() return widget:GetChildrenCount() end)
    return ok and count or 0
end

-- Depth first search of a widget tree by name (the bar panel is not a variable of the HUD widget in every game version).
local function find_in(widget, needle, depth)
    if depth > 14 then return nil end
    if widget:GetFName():ToString():lower():find(needle, 1, true) then return widget end
    for i = 0, child_count(widget) - 1 do
        local child = widget:GetChildAt(i)
        if isValid(child) then
            local hit = find_in(child, needle, depth + 1)
            if hit then return hit end
        end
    end
    local tree = widget.WidgetTree
    if isValid(tree) and isValid(tree.RootWidget) then
        local hit = find_in(tree.RootWidget, needle, depth + 1)
        if hit then return hit end
    end
    return nil
end

local function find_bar_panel(hud)
    local direct = hud[PANEL_NAME]
    if isValid(direct) then return direct end
    return find_in(hud, PANEL_NAME:lower(), 0)
end

-- A short text on the button, because the clone has no icon of its own. Best effort: a missing label is logged, not fatal.
function set_label(widget, text)
    local ok, problem = pcall(function()
        local tree = widget.WidgetTree
        local overlay = find_in(widget, "overlay", 0)
        local block = StaticConstructObject(StaticFindObject("/Script/UMG.TextBlock"), tree, FName("ModMenuLabel"))
        block:SetText(FText(text))
        local slot = overlay:AddChildToOverlay(block)
        -- The default font is larger than the 60 px button. Shrink the text and put it under the icon. All optional.
        local styled, style_problem = pcall(function()
            block:SetRenderScale({ X = LABEL_SCALE, Y = LABEL_SCALE })
            block:SetJustification(1) -- Center
            slot:SetHorizontalAlignment(2) -- Center
            slot:SetVerticalAlignment(3)   -- Bottom
        end)
        if not styled then core.log.info(TAG, "bar label style not set: " .. tostring(style_problem)) end
        -- The colour is optional: the default text colour is white. A failure here must not lose the label.
        local colored, color_problem = pcall(function()
            block:SetColorAndOpacity({ SpecifiedColor = LABEL_COLOR, ColorUseRule = 0 })
        end)
        if not colored then core.log.info(TAG, "bar label colour not set: " .. tostring(color_problem)) end
    end)
    if not ok then core.log.warn(TAG, "bar button label failed: " .. tostring(problem)) end
    -- The game's tooltip text of the clone is "mainTab_0". Try to set our own; the game may use its own tooltip widget.
    local tipped, tip_problem = pcall(function() widget:SetToolTipText(FText(text)) end)
    if not tipped then core.log.info(TAG, "bar button tooltip not set: " .. tostring(tip_problem)) end
    return ok
end

local function id_of_button(name)
    if S.close_button and S.close_button.name == name then return CLOSE_ID end
    for id, button in pairs(S.buttons) do
        if button.name == name then return id end
    end
    return nil
end

-- The hook runs for every button of the game's class. It only records ours, by widget name.
local function button_name_of(self)
    local widget = self ~= nil and self:get() or nil
    if widget == nil or not widget:IsValid() then return nil end
    return widget:GetFName():ToString()
end

function install_hooks()
    if S.hooked then return true end
    local ok, problem = pcall(function()
        RegisterHook(BAR_BUTTON_CLASS .. ":HandleClicked", function(self)
            local id = id_of_button(button_name_of(self))
            if id then S.bar_clicks[#S.bar_clicks + 1] = id end
        end)
        RegisterHook(BAR_BUTTON_CLASS .. ":HandleHovered", function(self)
            local id = id_of_button(button_name_of(self))
            if id then S.hover_id = id end
        end)
    end)
    if not ok then
        S.bar_error = "RegisterHook: " .. tostring(problem)
        return false
    end
    S.hooked = true
    return true
end

local function add_bar_button(panel, spec)
    local class = StaticFindObject(BAR_BUTTON_CLASS)
    if not isValid(class) then return nil, "bar button class not loaded: " .. BAR_BUTTON_CLASS end
    local controller = FindFirstOf("PlayerController")
    local widget = library():Create(controller, class, controller)
    if not isValid(widget) then return nil, "Create returned no bar button" end
    panel:AddChildToHorizontalBox(widget)
    set_label(widget, spec.label)
    return { widget = widget, name = widget:GetFName():ToString() }
end

local function missing_buttons()
    for _, id in ipairs(order) do
        local button = S.buttons[id]
        if button == nil or not isValid(button.widget) then return true end
    end
    return false
end

-- Adds the buttons that are missing. A new HUD widget (a game load) has no buttons yet, so all are added again.
function M.ensure_bar()
    S.bar_polls = S.bar_polls + 1
    local hud = FindFirstOf(HUD_CLASS)
    if not isValid(hud) then
        S.hud_found = false
        if S.bar_polls % 20 == 1 then core.log.info(TAG, "the HUD widget " .. HUD_CLASS .. " is not found yet (poll " .. S.bar_polls .. ")") end
        return false
    end
    S.hud_found = true
    local hud_name = hud:GetFullName()
    if hud_name ~= S.hud_name then
        S.hud_name, S.buttons = hud_name, {}
    end
    if not missing_buttons() then return true end
    local ok, panel = pcall(find_bar_panel, hud)
    if not (ok and isValid(panel)) then
        S.bar_error = "the bottom bar panel " .. PANEL_NAME .. " was not found in " .. HUD_CLASS .. " (the game changed?)"
        core.log.warn(TAG, S.bar_error)
        return false
    end
    if not install_hooks() then return false end
    for _, id in ipairs(order) do
        local button = S.buttons[id]
        if button == nil or not isValid(button.widget) then
            local made, problem = add_bar_button(panel, menus[id])
            if made then
                S.buttons[id] = made
                S.bar_error = nil
                core.log.info(TAG, "bottom bar button added for menu " .. id)
            else
                S.bar_error = problem
                core.log.warn(TAG, "bottom bar button for menu " .. id .. " failed: " .. tostring(problem))
            end
        end
    end
    return true
end

---------------------------------------------------------------------------------------------
-- Tick
---------------------------------------------------------------------------------------------

local function tick()
    local clicks, toggles = S.bar_clicks, S.toggles
    S.bar_clicks, S.toggles = {}, {}
    for _, id in ipairs(clicks) do
        if id == CLOSE_ID then
            S.close_presses = S.close_presses + 1
            core.log.info(TAG, "close button clicked")
            M.close()
        else
            S.press_count = S.press_count + 1
            core.log.info(TAG, "bottom bar button clicked: " .. id)
            core.log.try(TAG, function() M.toggle(id) end)
        end
    end
    for _, id in ipairs(toggles) do core.log.try(TAG, function() M.toggle(id) end) end
    if S.open_id ~= nil and not isValid(S.content) then M.close() end -- the game removed the widget (a load)
end

function M.state()
    local buttons = {}
    for _, id in ipairs(order) do
        local button = S.buttons[id]
        local row = { id = id, label = menus[id].label, in_bar = button ~= nil and isValid(button.widget) }
        if row.in_bar then row.name = button.name end
        buttons[#buttons + 1] = row
    end
    local blocker_visibility = isValid(S.blocker) and core.read(function() return S.blocker:GetVisibility() end) or nil
    return {
        open_id = S.open_id, open = M.is_open(), registered = order, buttons = buttons, hover_id = S.hover_id,
        press_count = S.press_count, blocker = isValid(S.blocker), blocker_visibility = blocker_visibility,
        close_button = S.close_button ~= nil and isValid(S.close_button.widget), close_presses = S.close_presses, bar_polls = S.bar_polls, pass_through = S.pass_through, hud_found = S.hud_found, bar_error = S.bar_error, last_error = S.last_error,
    }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.menu_state", M.state, {})
    commands.register("InvasionMod.menu_open", function(args) return M.open(args.id) end, { id = { type = "string", required = true } })
    commands.register("InvasionMod.menu_close", M.close, {})
    -- The same path a bar click takes after the hook: the request goes through the tick.
    commands.register("InvasionMod.menu_press", function(args)
        if menus[args.id] == nil then return nil, "unknown menu: " .. tostring(args.id) end
        S.bar_clicks[#S.bar_clicks + 1] = args.id
        return { ok = true }
    end, { id = { type = "string", required = true } })
end

require("scheduler").every(TAG, TICK_MS, tick)
require("scheduler").every(TAG .. ".bar", BAR_POLL_MS, function() core.log.try(TAG, M.ensure_bar) end)

return M
