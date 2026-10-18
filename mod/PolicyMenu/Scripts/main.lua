-- PolicyMenu: a menu that lists the policies of the player region. A click signs or unsigns a policy (spec 16, issue #60).
-- Parts:
--   The layout is a cooked Widget Blueprint in the pak policymenu_P.pak (mod/PolicyMenu/ue/make_widget.py): a title and
--   SLOT_COUNT Borders. Lua puts a click button (WBP_ClickButton, shared module HarnessClickHooks) into each Border and fills
--   its label, colour and visibility at run time.
--   Click: the OnClicked event of the click button is a hook event (spec 34). The hook only queues the click. The tick drains
--   the queue on the game thread and calls Region:setPolicySigned through ManorCore.
--   Key: F7 opens and closes the menu (CONFIG.toggle_key).
-- Rules: game objects are touched on the game thread only. No save function. No eval. The mod needs only ManorCore.
-- HarnessCommands is optional: without it the mod runs by itself and only the test commands are missing.

local core = require("ManorCore")
local log = core.log
local clickhooks = require("HarnessClickHooks")
local hasCommands, commands = pcall(require, "HarnessCommands")

local VERSION = "0.1.0"
local TAG = "PolicyMenu"
local PREFIX = "PolicyMenu."

local CONFIG = {
    toggle_key = Key.F7,        -- not known to be used by the base game; change it here if it clashes
    tick_ms = 100,              -- real time between two ticks. Not lower: a 50 ms tick corrupted the Lua state (spec 34)
    refresh_ms = 1000,          -- real time between two reads of the policy state (it can change outside the menu)
    z_order = 500,
    position = { X = 300, Y = 200 },
}

local CLASS_PATH = "/Game/HarnessMod/WBP_PolicyMenu.WBP_PolicyMenu_C"
local PACKAGE_PATH = "/Game/HarnessMod"
local ASSET_NAME = "WBP_PolicyMenu"
local SLOT_COUNT = 20
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

-- The Borders are children of the widget tree, found by name. Why: Python cannot mark them as variables.
local function findBorders(widget)
    local widgetName = read(function() return widget:GetFName():ToString() end)
    local borders = {}
    for _, object in ipairs(FindAllOf("Border") or {}) do
        local full = read(function() return object:GetFullName() end) or ""
        local index = full:match("PolicyButton(%d+)$") or full:match("PolicyButton(%d+) ")
        if index and widgetName and full:find(widgetName, 1, true) and tonumber(index) < SLOT_COUNT then borders[tonumber(index) + 1] = object end
    end
    return borders
end

-- Puts a click button into each Border. Returns the slots, or nil and a message.
local function attachSlots(widget)
    local borders = findBorders(widget)
    local controller = FindFirstOf("PlayerController")
    local slots, handles = {}, {}
    for i = 1, SLOT_COUNT do
        if borders[i] then
            local handle, problem = clickhooks.attach(borders[i], controller, { owner = S, index = i })
            if not handle then return nil, problem end
            slots[i] = { handle = handle }
            handles[#handles + 1] = handle
        end
    end
    if slots[1] == nil then return nil, "the policy buttons were not found in the widget" end
    local bound, problem = clickhooks.bind_texts(handles)
    if not bound then return nil, problem end
    return slots
end

local function releaseSlots()
    local handles = {}
    for _, slot in pairs(S.slots) do handles[#handles + 1] = slot.handle end
    clickhooks.release(handles)
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

-- The colour and the label change only when the policy changes. A game call for each button and tick broke the Lua state (spec 34).
local function fillSlot(slot, entry)
    if not entry then
        clickhooks.set_visible(slot.handle, false)
        return
    end
    clickhooks.set_text(slot.handle, labelText(entry))
    if slot.signed ~= entry.signed then
        slot.signed = entry.signed
        slot.handle.widget:SetColorAndOpacity(entry.signed and COLOR_SIGNED or COLOR_FREE)
    end
    clickhooks.set_visible(slot.handle, true)
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

local function tick()
    if not isValid(S.widget) then
        S.widget = nil
        return
    end
    local clicked = clickhooks.drain(S)
    for _, handle in ipairs(clicked) do
        local entry = S.entries[handle.tag.index]
        if entry then toggle(entry) end
    end
    if #clicked == 0 and os.clock() - S.last_refresh >= CONFIG.refresh_ms / 1000 then refresh() end
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
    local slots, slotProblem = attachSlots(made)
    if not slots then
        made:RemoveFromParent()
        return { ok = false, error = slotProblem }
    end
    S.widget, S.slots = made, slots
    made:AddToViewport(CONFIG.z_order)
    made:SetPositionInViewport(CONFIG.position, false)
    refresh()
    return { ok = true, entries = #S.entries }
end

local function close()
    if isOpen() then S.widget:RemoveFromParent() end
    releaseSlots()
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
        local candidate = read(function() return slot.handle.widget[getter](slot.handle.widget) end)
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
            hovered = slot and read(function() return slot.handle.widget:IsHovered() end),
            visibility = slot and read(function() return slot.handle.widget:GetVisibility() end),
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
    -- Calls the click handler without the mouse. The menu must be open.
    press = { schema = { index = { type = "integer", required = true } }, run = function(args)
        local entry = isOpen() and S.entries[args.index]
        if not entry then return { ok = false, error = "no policy button " .. tostring(args.index) } end
        toggle(entry)
        return describe()
    end },
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

-- The key callback runs on the input thread. It only sets a flag: Lua work there raced with the game thread and
-- crashed or hung the game (InvasionMod F9, PR #246). The game-thread tick does the toggle.
local toggleRequested = false
RegisterKeyBind(CONFIG.toggle_key, function() toggleRequested = true end)

local function tickWithToggle()
    if toggleRequested then
        toggleRequested = false
        toggleMenu()
    end
    tick()
end

LoopAsync(CONFIG.tick_ms, function()
    ExecuteInGameThread(function() log.try(TAG, tickWithToggle) end)
    return false
end)

log.say(TAG, "loaded version " .. VERSION .. " (F7 opens and closes the menu)")
