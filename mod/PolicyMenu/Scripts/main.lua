-- PolicyMenu: a menu that lists the policies of the player region. A click signs or unsigns a policy (spec 16, issue #60).
-- Parts:
--   The layout is a cooked Widget Blueprint in the pak policymenu_P.pak (mod/PolicyMenu/ue/make_widget.py): a title and
--   SLOT_COUNT buttons with a text label each. Lua fills the labels, the colours and the visibility at run time.
--   Click: the Blueprint has no graph. Lua polls Button:IsPressed on a short timer. A press that ends while the mouse is on the
--   button is one click. It calls Region:setPolicySigned through ManorCore.
--   Key: F7 opens and closes the menu (CONFIG.toggle_key).
-- Rules: game objects are touched on the game thread only. No save function. No eval. The mod needs only ManorCore.
-- HarnessCommands is optional: without it the mod runs by itself and only the test commands are missing.

local core = require("ManorCore")
local log = core.log
local hasCommands, commands = pcall(require, "HarnessCommands")

local VERSION = "0.1.0"
local TAG = "PolicyMenu"
local PREFIX = "PolicyMenu."

local CONFIG = {
    toggle_key = Key.F7,        -- not known to be used by the base game; change it here if it clashes
    poll_ms = 40,               -- real time between two checks of the buttons (a click lasts longer than this)
    refresh_ms = 1000,          -- real time between two reads of the policy state (it can change outside the menu)
    click_cooldown_s = 0.4,     -- a second click on the same button within this time is ignored
    z_order = 500,
    position = { X = 300, Y = 200 },
}

local CLASS_PATH = "/Game/HarnessMod/WBP_PolicyMenu.WBP_PolicyMenu_C"
local PACKAGE_PATH = "/Game/HarnessMod"
local ASSET_NAME = "WBP_PolicyMenu"
local SLOT_COUNT = 20
local VISIBLE, COLLAPSED = 0, 1 -- ESlateVisibility
local COLOR_SIGNED = { R = 0.15, G = 0.55, B = 0.2, A = 1.0 }
local COLOR_FREE = { R = 0.35, G = 0.35, B = 0.35, A = 1.0 }
local MARK_SIGNED, MARK_FREE = "[x] ", "[ ] "

local S = { widget = nil, slots = {}, entries = {}, clicks = 0, last_error = nil, last_refresh = 0 }

local isValid, read = core.isValid, core.read

---------------------------------------------------------------------------------------------
-- Widget
---------------------------------------------------------------------------------------------

-- LoadAsset does not load an asset of a mod pak. The asset registry call does (spec 16 pak-widget-spike.md).
local function findClass()
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
    if not isValid(found) then return nil, "class not found; is the pak policymenu_P.pak in Paks/~mods?" end
    return found
end

-- The buttons and labels are children of the widget tree, found by name. Why: Python cannot mark them as variables.
local function findSlots(widget)
    local widgetName = read(function() return widget:GetFName():ToString() end)
    local buttons, labels = {}, {}
    local function collect(className, prefix, into)
        for _, object in ipairs(FindAllOf(className) or {}) do
            local full = read(function() return object:GetFullName() end) or ""
            local index = full:match(prefix .. "(%d+)$") or full:match(prefix .. "(%d+) ")
            if index and widgetName and full:find(widgetName, 1, true) then into[tonumber(index) + 1] = object end
        end
    end
    collect("Button", "PolicyButton", buttons)
    collect("TextBlock", "PolicyLabel", labels)
    local slots = {}
    for i = 1, SLOT_COUNT do
        if buttons[i] and labels[i] then slots[i] = { button = buttons[i], label = labels[i], was_pressed = false, hovered = false, last_click = -100 } end
    end
    return slots
end

local function makeWidget()
    local class, problem = findClass()
    if not class then return nil, problem end
    local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
    local controller = FindFirstOf("PlayerController")
    if not (isValid(library) and isValid(controller)) then return nil, "widget library or player controller not found" end
    local made = library:Create(controller, class, controller)
    if not isValid(made) then return nil, "WidgetBlueprintLibrary:Create returned no widget" end
    return made
end

---------------------------------------------------------------------------------------------
-- Fill
---------------------------------------------------------------------------------------------

local function labelText(entry)
    return (entry.signed and MARK_SIGNED or MARK_FREE) .. entry.name
end

local function fillSlot(slot, entry)
    if not entry then
        slot.button:SetVisibility(COLLAPSED)
        return
    end
    slot.label:SetText(FText(labelText(entry)))
    slot.button:SetBackgroundColor(entry.signed and COLOR_SIGNED or COLOR_FREE)
    slot.button:SetVisibility(VISIBLE)
end

-- Read the policies of the game and show them. The slot i shows the entry i.
local function refresh()
    if not isValid(S.widget) then return false end
    local state, problem = core.policy_list()
    if not state then
        S.last_error = problem
        return false
    end
    S.entries = state.policies
    for i = 1, SLOT_COUNT do
        if S.slots[i] then fillSlot(S.slots[i], S.entries[i]) end
    end
    S.last_refresh = os.clock()
    return true
end

---------------------------------------------------------------------------------------------
-- Click
---------------------------------------------------------------------------------------------

local function toggle(entry)
    local ok, err = core.set_policy_signed(entry.id, not entry.signed)
    if not ok then
        S.last_error = err
        log.warn(TAG, "toggle failed: " .. tostring(err))
        return
    end
    S.clicks = S.clicks + 1
    log.info(TAG, string.format("policy %d (%s) %s", entry.id, entry.name, entry.signed and "unsigned" or "signed"))
    refresh()
end

-- One check of one button. A click is a press that ends while the mouse is on the button.
local function checkSlot(slot, entry)
    local pressed = read(function() return slot.button:IsPressed() end) == true
    if pressed then slot.hovered = read(function() return slot.button:IsHovered() end) == true end
    local released = slot.was_pressed and not pressed
    slot.was_pressed = pressed
    if released and slot.hovered and os.clock() - slot.last_click >= CONFIG.click_cooldown_s then
        slot.last_click = os.clock()
        toggle(entry)
    end
end

local function tick()
    if not isValid(S.widget) then
        S.widget = nil
        return
    end
    for i, entry in ipairs(S.entries) do
        if S.slots[i] then checkSlot(S.slots[i], entry) end
    end
    if os.clock() - S.last_refresh >= CONFIG.refresh_ms / 1000 then refresh() end
end

---------------------------------------------------------------------------------------------
-- Open and close
---------------------------------------------------------------------------------------------

local function isOpen()
    return isValid(S.widget)
end

local function open()
    if isOpen() then return { ok = true, already_open = true } end
    local made, problem = makeWidget()
    if not made then return { ok = false, error = problem } end
    S.widget = made
    S.slots = findSlots(made)
    if S.slots[1] == nil then
        made:RemoveFromParent()
        S.widget = nil
        return { ok = false, error = "the policy buttons were not found in the widget" }
    end
    made:AddToViewport(CONFIG.z_order)
    made:SetPositionInViewport(CONFIG.position, false)
    refresh()
    return { ok = true, entries = #S.entries }
end

local function close()
    if isOpen() then S.widget:RemoveFromParent() end
    S.widget, S.slots, S.entries = nil, {}, {}
    return { ok = true }
end

local function toggleMenu()
    if isOpen() then return close() end
    return open()
end

---------------------------------------------------------------------------------------------
-- Test commands (only with the harness)
---------------------------------------------------------------------------------------------

-- Where a button is on the screen, as fractions of the viewport. A test uses it to click with the real mouse.
local function buttonCentre(slot)
    -- Which geometry call gives a real size depends on the paint state. Try each one.
    local geometry
    for _, getter in ipairs({ "GetPaintSpaceGeometry", "GetCachedGeometry", "GetTickSpaceGeometry" }) do
        local candidate = read(function() return slot.button[getter](slot.button) end)
        local slateLib = StaticFindObject("/Script/UMG.Default__SlateBlueprintLibrary")
        local candidateSize = candidate and isValid(slateLib) and read(function() return slateLib:GetLocalSize(candidate) end)
        if candidateSize and (candidateSize.X or 0) > 0 then geometry = candidate break end
    end
    local slate = StaticFindObject("/Script/UMG.Default__SlateBlueprintLibrary")
    local layout = StaticFindObject("/Script/UMG.Default__WidgetLayoutLibrary")
    local controller = FindFirstOf("PlayerController")
    if geometry == nil or not isValid(slate) or not isValid(layout) then return nil end
    local size = read(function() return slate:GetLocalSize(geometry) end)
    local origin = read(function() return slate:LocalToAbsolute(geometry, { X = 0, Y = 0 }) end)
    local viewport = read(function() return layout:GetViewportSize(controller) end)
    if not (size and origin and viewport) or (viewport.X or 0) <= 0 then return nil end
    local centreX, centreY = origin.X + size.X / 2, origin.Y + size.Y / 2
    return { x = centreX, y = centreY, width = size.X, height = size.Y, viewport_x = viewport.X, viewport_y = viewport.Y,
             fx = centreX / viewport.X, fy = centreY / viewport.Y }
end

local function describe()
    local slots = {}
    for i, entry in ipairs(S.entries) do
        local slot = S.slots[i]
        slots[#slots + 1] = {
            id = entry.id, name = entry.name, signed = entry.signed,
            pressed = slot and read(function() return slot.button:IsPressed() end),
            hovered = slot and read(function() return slot.button:IsHovered() end),
            visibility = slot and read(function() return slot.button:GetVisibility() end),
            centre = slot and buttonCentre(slot),
        }
    end
    return {
        ok = true, open = isOpen(), in_viewport = isOpen() and read(function() return S.widget:IsInViewport() end) or false,
        clicks = S.clicks, last_error = S.last_error, slots = slots,
    }
end

local COMMANDS = {
    open = { schema = {}, run = function() return open() end },
    close = { schema = {}, run = function() return close() end },
    toggle = { schema = {}, run = function() return toggleMenu() end },
    read = { schema = {}, run = function() return describe() end },
}
local METRICS = {
    open = function() return isOpen() end,
    clicks = function() return S.clicks end,
    entries = function() return #S.entries end,
}

if hasCommands then
    for name, definition in pairs(COMMANDS) do
        commands.unregister(PREFIX .. name) -- a hot reload runs this file again
        commands.register(PREFIX .. name, function(args) return definition.run(args) end, definition.schema)
    end
    for name, readValue in pairs(METRICS) do commands.metric(PREFIX .. name, readValue) end
end

---------------------------------------------------------------------------------------------
-- Start
---------------------------------------------------------------------------------------------

RegisterKeyBind(CONFIG.toggle_key, function()
    ExecuteInGameThread(function() log.try(TAG, toggleMenu) end)
end)

LoopAsync(CONFIG.poll_ms, function()
    ExecuteInGameThread(function() log.try(TAG, tick) end)
    return false
end)

log.say(TAG, "loaded version " .. VERSION .. " (F7 opens and closes the menu)")
