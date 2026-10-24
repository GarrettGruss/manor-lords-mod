-- Base menu of the Invasion Mod (change add-mod-menu-access-rule, issue #308).
-- Every mod menu is built on this module. It owns what is the same for all menus:
--   * a button for the menu in the game's bottom bar, after the game's own buttons (a clone of the game's bar button class);
--   * the open and close of the menu, one menu at a time;
--   * a full-screen layer under the menu content that dims the view and blocks clicks to the game (notes/click-blocking.md:
--     a full-screen Button blocks a click, a Border does not);
--   * a Close button at the bottom middle, over the layer: the game's own Close button class (menuButton_C, the Close label of the
--     Diplomacy screen: serif text with a fleur-de-lis on each side). A click on the layer does nothing:
--     OnClicked:Add on a Button made at run time crashes the game (notes/menu-findings.md), so the layer has no click callback;
--   * the pause: a menu pauses the game when it opens and puts back the speed when it closes (change update-mod-menu-close-and-pause);
--   * the Esc key closes the open menu, and the game's own Esc menu is closed again on that press (notes/esc-key.md).
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
local CLOSE_CLASS = "/Game/UI/Common/menuButton.menuButton_C"   -- the game's Close button (Diplomacy screen)
local CLOSE_ANCHOR = { X = 0.5, Y = 0.95 }                      -- the centre of the Close button: bottom middle, 95 percent down
local ESC_MENU_CLASS = "mainMenu_widget_C"                      -- the game's Esc menu (made on demand, kept, collapsed when closed)
local ESC_GUARD_S = 1.5                                         -- real seconds to watch for the game's Esc menu after a mod menu closed on Esc
local COLLAPSED = 1
-- gameSpeed of the engine (0 paused, 1, 4, 8) -> the index of changeGameSpeed (spec 04 time-measurements)
local SPEED_INDEX = { [1] = 1, [4] = 2, [8] = 3 }
local HUD_CLASS, PANEL_NAME = "MainUICPP_C", "main_tabs_HB"
local LABEL_SCALE = 0.5
local LABEL_COLOR = { R = 1.0, G = 1.0, B = 1.0, A = 1.0 }

local isValid = core.isValid
local M = {}

local menus, order = {}, {}   -- id -> spec; the ids in the order of registration (the order of the buttons)
local S = {
    open_id = nil, content = nil, blocker = nil, close_button = nil,
    saved_speed = nil,         -- the game speed factor before the open (0: it was paused); nil: not read, or the menu manages its speed
    esc_requests = 0, esc_guard_until = nil, esc_guard_speed = nil, esc_closes = 0, esc_menu_hidden = 0,
    pauses = 0, restores = 0,
    toggles = {},              -- ids to toggle at the next tick (a key or a bar click)
    bar_clicks = {},           -- ids of bar buttons clicked since the last tick
    buttons = {},              -- id -> { widget, name }
    hud_name = nil, hooked = false, hover_id = nil,
    last_error = nil, bar_error = nil, press_count = 0, close_presses = 0, bar_polls = 0, hud_found = false, pass_through = 0,
}

local set_label, install_hooks, set_close_text -- defined in the bottom bar part
local function library() return StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary") end

---------------------------------------------------------------------------------------------
-- Registration
---------------------------------------------------------------------------------------------

-- spec = { id, label, class_path, package_path, asset_name, position, z_order,
--          bar = false (optional: no bottom bar button; the mod opens the menu itself),
--          on_open(widget) -> true | nil, problem   (attach the buttons, show the first values; clean up on a failure),
--          on_close() }
function M.register(spec)
    for _, field in ipairs({ "id", "label", "class_path", "package_path", "asset_name", "on_open", "on_close" }) do
        if spec[field] == nil then error("menu.register: missing field " .. field, 0) end
    end
    if menus[spec.id] then error("menu.register: duplicate menu id " .. spec.id, 0) end
    menus[spec.id] = spec
    if spec.bar ~= false then order[#order + 1] = spec.id end -- bar = false: no bottom bar button (a menu the mod opens itself)
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

-- The game's Close button class, made at run time. It sits at the bottom middle (an anchor and an alignment need no viewport size),
-- above the menu content. Its click is the DoOnReleased hook (install_hooks).
local function make_close_button()
    local class = StaticFindObject(CLOSE_CLASS)
    if not isValid(class) then error("close button class not loaded: " .. CLOSE_CLASS, 0) end
    local controller = FindFirstOf("PlayerController")
    local widget = library():Create(controller, class, controller)
    if not isValid(widget) then error("Create returned no close button", 0) end
    widget:AddToViewport(CONTENT_Z + 10)
    widget:SetAnchorsInViewport({ Minimum = CLOSE_ANCHOR, Maximum = CLOSE_ANCHOR })
    widget:SetAlignmentInViewport({ X = 0.5, Y = 0.5 })
    set_close_text(widget, "Close")
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

-- The game speed factor now: 0 paused, 1, 4 or 8. nil when it cannot be read.
local function read_speed()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil end
    local speed = core.read(function() return engine.gameSpeed end)
    return type(speed) == "number" and speed or nil
end

local function player_pawn()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil end
    local pawn = core.read(function() return engine.playerRef end)
    if isValid(pawn) then return pawn end
    return nil
end

-- Pause the game and remember the speed it had. A paused game stays "paused" (saved speed 0).
local function pause_for_menu()
    local pawn = player_pawn()
    if pawn == nil then return core.log.warn(TAG, "the game is not paused by the menu: no player pawn") end
    S.saved_speed = read_speed()
    local ok, problem = pcall(function() pawn:pauseGame() end)
    if not ok then
        S.saved_speed = nil
        return core.log.warn(TAG, "pauseGame failed: " .. tostring(problem))
    end
    S.pauses = S.pauses + 1
end

-- Put back the speed from before the open. A game that was paused stays paused. A speed that cannot be read: nothing changes.
local function restore_speed(speed)
    if speed == nil or speed == 0 then return end
    local pawn = player_pawn()
    if pawn == nil then return core.log.warn(TAG, "the game speed was not restored: no player pawn") end
    local ok, problem = pcall(function()
        pawn:unPauseGame()
        pawn:changeGameSpeed(SPEED_INDEX[speed] or 1, false)
    end)
    if not ok then return core.log.warn(TAG, "the game speed was not restored: " .. tostring(problem)) end
    S.restores = S.restores + 1
end

-- Closes the widgets and calls on_close. `keep_speed`: the next menu opens at once, so the saved speed stays for it.
local function close_menu(keep_speed)
    local id = S.open_id
    if id == nil then return { ok = true, already_closed = true } end
    local speed = S.saved_speed
    S.saved_speed = nil
    core.log.try(TAG, menus[id].on_close)
    remove_widget(S.content)
    remove_widget(S.blocker)
    if S.close_button then remove_widget(S.close_button.widget) end
    S.open_id, S.content, S.blocker, S.close_button = nil, nil, nil, nil
    if keep_speed then
        S.saved_speed = speed
    elseif not menus[id].manages_speed then
        restore_speed(speed)
    end
    return { ok = true, speed = speed }
end

function M.close() return close_menu(false) end

function M.open(id)
    local spec = menus[id]
    if not spec then return fail("unknown menu: " .. tostring(id)) end
    if M.is_open(id) then return { ok = true, already_open = true } end
    local carried = nil
    if S.open_id ~= nil then -- one menu at a time; the speed from before the first menu stays
        carried = S.saved_speed
        close_menu(true)
        S.saved_speed = nil
    end
    S.hover_id = nil -- a hover event names a button only when the mouse enters it, so forget the old one
    local content, problem = M.create_pak_widget(spec)
    if not content then
        restore_speed(carried)
        return fail(problem)
    end
    local ok_on_open, opened, open_problem = pcall(spec.on_open, content)
    if not ok_on_open or not opened then
        remove_widget(content)
        restore_speed(carried)
        return fail("menu " .. id .. " did not open: " .. tostring(ok_on_open and open_problem or opened))
    end
    local made, blocker = pcall(make_blocker)
    local close_made, close_button
    if made then close_made, close_button = pcall(make_close_button) end
    if not (made and close_made) then
        remove_widget(content)
        if made then remove_widget(blocker) end
        core.log.try(TAG, spec.on_close)
        restore_speed(carried)
        return fail("the backdrop or close button of menu " .. id .. " failed: " .. tostring(made and close_button or blocker))
    end
    S.pass_through = let_clicks_reach_the_backdrop(content)
    install_hooks()
    S.open_id, S.content, S.blocker, S.close_button, S.last_error = id, content, blocker, close_button, nil
    content:AddToViewport(spec.z_order or CONTENT_Z)
    if spec.position then content:SetPositionInViewport(spec.position, false) end
    if not spec.manages_speed then
        pause_for_menu()
        if carried ~= nil then S.saved_speed = carried end -- the game was already paused by the first menu
    end
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

-- The label of the game's Close button: the text key "Close" is the game's own text; the TextBlock is set as a fallback.
function set_close_text(widget, text)
    local ok, problem = pcall(function()
        widget.TextKey = FName(text)
        widget:updateText()
    end)
    if not ok then core.log.info(TAG, "close button text key not set: " .. tostring(problem)) end
    local block = find_in(widget, "textblock", 0)
    if block and isValid(block) then
        local set, set_problem = pcall(function() block:SetText(FText(text)) end)
        if not set then core.log.info(TAG, "close button text not set: " .. tostring(set_problem)) end
    end
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
        -- The Close button is the game's menuButton_C: it has no HandleClicked, but DoOnReleased runs on a click.
        RegisterHook(CLOSE_CLASS .. ":DoOnReleased", function(self)
            local id = id_of_button(button_name_of(self))
            if id then S.bar_clicks[#S.bar_clicks + 1] = id end
        end)
        RegisterHook(CLOSE_CLASS .. ":OnMouseEnter", function(self)
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

---------------------------------------------------------------------------------------------
-- The Esc key
---------------------------------------------------------------------------------------------

-- The game opens its own Esc menu on the same press (UE4SS does not swallow the key). It is a widget that the game keeps after the
-- first use and collapses when it is closed. After a mod menu closed on Esc, watch for it for a short time and close it again,
-- then put back the game speed (the game's menu pauses the game and may undo our restore).
local function hide_game_esc_menu()
    local widget = FindFirstOf(ESC_MENU_CLASS)
    if not isValid(widget) then return false end
    local visibility = core.read(function() return widget:GetVisibility() end)
    if visibility == nil or visibility == COLLAPSED then return false end
    -- `continue` is the Continue button of the menu: it closes the menu and gives the HUD back. DoCloseAndHideSelf only collapses
    -- the widget and leaves the HUD hidden (spike notes/esc-key.md), so it is the fallback.
    local ok, problem = pcall(function() widget:continue() end)
    if not ok then ok, problem = pcall(function() widget:DoCloseAndHideSelf() end) end
    if not ok then
        core.log.warn(TAG, "the game Esc menu could not be closed: " .. tostring(problem))
        return false
    end
    S.esc_menu_hidden = S.esc_menu_hidden + 1
    core.log.info(TAG, "the game Esc menu opened on the press that closed a mod menu; closed it again")
    return true
end

local function esc_guard_tick()
    if S.esc_guard_until == nil then return end
    if hide_game_esc_menu() then
        restore_speed(S.esc_guard_speed)
        S.esc_guard_until, S.esc_guard_speed = nil, nil
    elseif os.clock() > S.esc_guard_until then
        S.esc_guard_until, S.esc_guard_speed = nil, nil
    end
end

-- Esc with a mod menu open: close it like the Close button. With no mod menu open nothing happens here, so the game opens its menu.
local function handle_esc()
    if S.open_id == nil then return end
    local speed = S.saved_speed
    local spec = menus[S.open_id]
    S.esc_closes = S.esc_closes + 1
    core.log.info(TAG, "Esc pressed: closing the menu " .. S.open_id)
    M.close()
    S.esc_guard_until = os.clock() + ESC_GUARD_S
    S.esc_guard_speed = (spec ~= nil and not spec.manages_speed) and speed or nil
end

local function tick()
    for _ = 1, S.esc_requests do handle_esc() end
    S.esc_requests = 0
    esc_guard_tick()
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
        press_count = S.press_count, saved_speed = S.saved_speed, pauses = S.pauses, restores = S.restores,
        esc_closes = S.esc_closes, esc_menu_hidden = S.esc_menu_hidden, esc_guard = S.esc_guard_until ~= nil, blocker = isValid(S.blocker), blocker_visibility = blocker_visibility,
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

-- A key callback only counts the press. The tick does the work on the game thread.
RegisterKeyBind(Key.ESCAPE, function() S.esc_requests = S.esc_requests + 1 end)

-- A named command for tests: the same path as the key press.
if has_commands then
    commands.register("InvasionMod.menu_press_esc", function() S.esc_requests = S.esc_requests + 1; return { ok = true } end, {})
end

require("scheduler").every(TAG, TICK_MS, tick)
require("scheduler").every(TAG .. ".bar", BAR_POLL_MS, function() core.log.try(TAG, M.ensure_bar) end)

return M
