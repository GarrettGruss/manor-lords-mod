-- HarnessUiProbe: spike helper for the bottom bar button (change add-mod-menu-access-rule, task 1.3, #308).
-- One command, ui_probe, with an `action`: scan, tree, add_button, add_overlay, state, close.
-- Why a ladder of pcall steps: it is not known which UMG calls UE4SS can make on game widgets. Each step is logged.
-- Rules: game thread only. No save function. No Lua string goes to an FName argument of a widget function.
-- Nothing reads a Brush struct back (struct reads with soft objects can crash the game).
local log = require("HarnessLog")

local M = {}
local TAG = "HarnessUiProbe"
local S = { steps = {}, clicks = 0, added = nil, overlay = nil }

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function step(name, fn)
    local ok, value = pcall(fn)
    local text = ok and "ok" or tostring(value)
    log.info(TAG, name .. ": " .. text)
    S.steps[#S.steps + 1] = { name = name, ok = ok, error = (not ok) and text or nil }
    if ok then return value, true end
    return nil, false
end

local function className(object)
    local ok, name = pcall(function() return object:GetClass():GetFullName() end)
    return ok and tostring(name) or "?"
end

local function fullName(object)
    local ok, name = pcall(function() return object:GetFullName() end)
    return ok and tostring(name) or "?"
end

local function controller() return FindFirstOf("PlayerController") end

local function describe(widget, depth, budget, lines)
    if budget.n <= 0 or depth > 12 then return end
    budget.n = budget.n - 1
    local vis, size = "?", ""
    pcall(function() vis = tostring(widget:GetVisibility()) end)
    pcall(function()
        local d = widget:GetDesiredSize()
        size = string.format(" desired=%.0fx%.0f", d.X, d.Y)
    end)
    local pad = string.rep("  ", depth)
    local line = string.format("%s%s [%s] vis=%s%s", pad, widget:GetFName():ToString(), className(widget), vis, size)
    lines[#lines + 1] = line
    log.info(TAG, "tree " .. line)
    local count = 0
    local ok = pcall(function() count = widget:GetChildrenCount() end)
    if ok and count > 0 then
        for i = 0, count - 1 do
            local child
            pcall(function() child = widget:GetChildAt(i) end)
            if isValid(child) then describe(child, depth + 1, budget, lines) end
        end
    end
    -- a UserWidget holds its content in WidgetTree
    pcall(function()
        local tree = widget.WidgetTree
        if isValid(tree) and isValid(tree.RootWidget) then describe(tree.RootWidget, depth + 1, budget, lines) end
    end)
    -- a ContentWidget (Button, Border, SizeBox) holds one child
    if not (ok and count > 0) then
        pcall(function()
            local content = widget:GetContent()
            if isValid(content) then describe(content, depth + 1, budget, lines) end
        end)
    end
end

-- Lists the user widgets of the game. in_viewport and visibility tell which are the HUD.
local function scan()
    S.steps = {}
    local all = FindAllOf("UserWidget") or {}
    local list = {}
    for _, widget in ipairs(all) do
        if isValid(widget) then
            local inViewport, vis = nil, nil
            pcall(function() inViewport = widget:IsInViewport() end)
            pcall(function() vis = widget:GetVisibility() end)
            local line = string.format("%s | %s | inViewport=%s vis=%s", widget:GetFName():ToString(), className(widget), tostring(inViewport), tostring(vis))
            log.info(TAG, "widget " .. line)
            list[#list + 1] = line
        end
    end
    return { ok = true, count = #list }
end

local function find_widget(request)
    local needle = (request.name or ""):lower()
    for _, widget in ipairs(FindAllOf("UserWidget") or {}) do
        if isValid(widget) and (widget:GetFName():ToString():lower():find(needle, 1, true) or className(widget):lower():find(needle, 1, true)) then
            return widget
        end
    end
end

local function tree(request)
    S.steps = {}
    local lines, budget = {}, { n = tonumber(request.limit) or 400 }
    local widget = find_widget(request)
    if not widget then return { ok = false, error = "no widget matches " .. tostring(request.name) } end
    describe(widget, 0, budget, lines)
    return { ok = true, root = fullName(widget), nodes = #lines }
end

-- Finds a widget in the tree of `root` by name part, depth first.
local function find_in(widget, needle, depth)
    if depth > 14 then return nil end
    if widget:GetFName():ToString():lower():find(needle, 1, true) then return widget end
    local count = 0
    local ok = pcall(function() count = widget:GetChildrenCount() end)
    if ok then
        for i = 0, count - 1 do
            local child
            pcall(function() child = widget:GetChildAt(i) end)
            if isValid(child) then
                local hit = find_in(child, needle, depth + 1)
                if hit then return hit end
            end
        end
    end
    local found
    pcall(function()
        local t = widget.WidgetTree
        if isValid(t) and isValid(t.RootWidget) then found = find_in(t.RootWidget, needle, depth + 1) end
    end)
    if found then return found end
    pcall(function()
        local content = widget:GetContent()
        if isValid(content) then found = find_in(content, needle, depth + 1) end
    end)
    return found
end

-- Adds a Button (with a TextBlock) as the last child of the panel `panel` (a name part inside widget `name`).
-- If `template` names a game button inside the same widget, the new button copies its style (Button:SetStyle).
local function add_button(request)
    S.steps = {}
    local root = find_widget(request)
    if not root then return { ok = false, error = "no widget matches " .. tostring(request.name) } end
    local panel = find_in(root, (request.panel or ""):lower(), 0)
    if not panel then return { ok = false, error = "panel not found: " .. tostring(request.panel) } end
    log.info(TAG, "panel = " .. fullName(panel))
    local template = request.template and find_in(root, request.template:lower(), 0) or nil
    if template then log.info(TAG, "template = " .. fullName(template) .. " class " .. className(template)) end
    local owner = root.WidgetTree
    local button, made = step("construct Button", function()
        return StaticConstructObject(StaticFindObject("/Script/UMG.Button"), owner, FName("ModMenuProbeButton"))
    end)
    if not made or not isValid(button) then return { ok = false, error = "no button", steps = S.steps } end
    if template then
        step("copy Button style", function() button:SetStyle(template.WidgetStyle) end)
        step("copy Button colors", function()
            button:SetBackgroundColor(template.BackgroundColor)
            button:SetColorAndOpacity(template.ColorAndOpacity)
        end)
    end
    local text = step("construct TextBlock", function()
        return StaticConstructObject(StaticFindObject("/Script/UMG.TextBlock"), owner, FName("ModMenuProbeText"))
    end)
    if isValid(text) then
        step("SetText", function() text:SetText(FText("Mod")) end)
        step("button content", function() button:SetContent(text) end)
    end
    local slot = step("AddChild", function() return panel:AddChild(button) end)
    if not isValid(slot) then return { ok = false, error = "AddChild failed", steps = S.steps } end
    step("OnClicked bind", function()
        button.OnClicked:Add(function() S.clicks = S.clicks + 1; log.info(TAG, "CLICK callback " .. S.clicks) end)
    end)
    S.added = button
    return { ok = true, steps = S.steps, panel = fullName(panel), button = fullName(button) }
end


-- Clone of a game bar button: Create(class) + AddChildToHorizontalBox, hooks on the click functions of the class.
local CLASS_PATH = "/Game/UI/HUD/mainTabButton.mainTabButton_C"
local hooked = false
local clones = {}

local function install_click_hooks(classObject)
    if hooked then return end
    local names = {}
    pcall(function()
        classObject:ForEachFunction(function(fn)
            names[#names + 1] = fn:GetFName():ToString()
        end)
    end)
    log.info(TAG, "class functions: " .. table.concat(names, ", "))
    for _, name in ipairs(names) do
        local lower = name:lower()
        if lower:find("click", 1, true) or lower:find("press", 1, true) or lower:find("hover", 1, true) then
            step("RegisterHook " .. name, function()
                RegisterHook(CLASS_PATH .. ":" .. name, function(self)
                    local who = "?"
                    pcall(function() who = self:get():GetFName():ToString() end)
                    log.info(TAG, "HOOK " .. name .. " on " .. who)
                    if clones[who] and name:lower():find("click", 1, true) then
                        S.clicks = S.clicks + 1
                        log.info(TAG, "CLICK callback on our button " .. S.clicks)
                    end
                end)
            end)
        end
    end
    hooked = true
end

local function add_clone(request)
    S.steps = {}
    local root = find_widget(request)
    if not root then return { ok = false, error = "no widget matches " .. tostring(request.name) } end
    local panel = find_in(root, (request.panel or ""):lower(), 0)
    if not panel then return { ok = false, error = "panel not found" } end
    local class = StaticFindObject(CLASS_PATH)
    if not isValid(class) then return { ok = false, error = "button class not loaded" } end
    install_click_hooks(class)
    local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
    local widget = step("Create clone", function() return library:Create(controller(), class, controller()) end)
    if not isValid(widget) then return { ok = false, error = "no clone", steps = S.steps } end
    local name = widget:GetFName():ToString()
    clones[name] = true
    local slot = step("AddChildToHorizontalBox", function() return panel:AddChildToHorizontalBox(widget) end)
    S.added = widget
    S.addedName = name
    local before
    step("tint", function() widget:SetColorAndOpacity({ R = 1.0, G = 0.6, B = 0.6, A = 1.0 }) end)
    local size = ""
    pcall(function() local d = widget:GetDesiredSize(); size = string.format("%.0fx%.0f", d.X, d.Y) end)
    return { ok = isValid(slot), steps = S.steps, name = name, desired = size, children = (function() local n; pcall(function() n = panel:GetChildrenCount() end); return n end)() }
end

local function state()
    local hovered, pressed = nil, nil
    if isValid(S.added) then
        pcall(function() hovered = S.added:IsHovered() end)
        pcall(function() pressed = S.added:IsPressed() end)
    end
    return { ok = true, clicks = S.clicks, hovered = hovered, pressed = pressed, added = isValid(S.added) }
end

-- Fullscreen widget with a Border, visibility Visible, for the click-blocking test.
-- Move the camera pawn over a building, so a click at the screen centre hits a building (the click test needs a world target).
local function focus(request)
    local list = FindAllOf("SMBuilding") or {}
    local names = {}
    local target
    for _, b in ipairs(list) do
        if isValid(b) then
            local cn = className(b)
            names[#names + 1] = cn
            if not target and (not request.name or cn:find(request.name, 1, true)) then target = b end
        end
    end
    local pawn
    for _, p in ipairs(FindAllOf("PawnCPP") or {}) do if isValid(p) then pawn = p break end end
    if not target or not pawn then return { ok = false, error = "no building or pawn", count = #list, sample = { table.unpack(names, 1, 8) } } end
    local at = target:K2_GetActorLocation()
    local moved = step("move pawn", function() pawn:K2_SetActorLocation({ X = at.X, Y = at.Y, Z = at.Z }, false, {}, true) end)
    return { ok = true, target = fullName(target), count = #list, sample = { table.unpack(names, 1, 8) } }
end

local function add_overlay(request)
    local mode = request.mode or "border"
    local input = request.input or "none"
    S.steps = {}
    local userClass = StaticFindObject("/Script/UMG.UserWidget")
    local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
    local widget = step("Create", function() return library:Create(controller(), userClass, controller()) end)
    if not isValid(widget) then return { ok = false, error = "no widget", steps = S.steps } end
    local tree = step("tree", function() return StaticConstructObject(StaticFindObject("/Script/UMG.WidgetTree"), widget, FName("OverlayTree")) end)
    step("set tree", function() widget.WidgetTree = tree end)
    local class = mode == "button" and "/Script/UMG.Button" or "/Script/UMG.Border"
    local border = step(mode, function() return StaticConstructObject(StaticFindObject(class), tree, FName("OverlayRoot")) end)
    step("root", function() tree.RootWidget = border end)
    step("color", function()
        if mode == "button" then border:SetBackgroundColor({ R = 0, G = 0, B = 0, A = 0.35 })
        else border:SetBrushColor({ R = 0, G = 0, B = 0, A = 0.35 }) end
    end)
    step("visible", function() widget:SetVisibility(0) end)
    step("border visible", function() border:SetVisibility(0) end)
    step("AddToViewport", function() widget:AddToViewport(50) end)
    step("fill", function() widget:SetAnchorsInViewport({ Minimum = { X = 0, Y = 0 }, Maximum = { X = 1, Y = 1 } }) end)
    step("fill align", function() widget:SetAlignmentInViewport({ X = 0, Y = 0 }) end)
    S.overlay = widget
    S.input = input
    if input == "uionly" then
        step("UIOnly", function() library:SetInputMode_UIOnlyEx(controller(), widget, 0, true) end)
    elseif input == "gameandui" then
        step("GameAndUI", function() library:SetInputMode_GameAndUIEx(controller(), widget, 0, false, true) end)
    end
    return { ok = true, steps = S.steps }
end

local function close()
    if isValid(S.overlay) then pcall(function() S.overlay:RemoveFromParent() end) end
    S.overlay = nil
    if S.input and S.input ~= "none" then
        local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
        step("restore input", function() library:SetInputMode_GameAndUIEx(controller(), nil, 0, false, true) end)
    end
    S.input = nil
    return { ok = true }
end

local function parseOwn(request, raw)
    raw = raw or ""
    request.action = raw:match('"action"%s*:%s*"([%w_]+)"')
    request.name = raw:match('"name"%s*:%s*"([^"]*)"')
    request.mode = raw:match('"mode"%s*:%s*"([%w_]+)"')
    request.input = raw:match('"input"%s*:%s*"([%w_]+)"')
    request.panel = raw:match('"panel"%s*:%s*"([^"]*)"')
    request.template = raw:match('"template"%s*:%s*"([^"]*)"')
    request.limit = tonumber(raw:match('"limit"%s*:%s*(-?[%d%.]+)'))
end

function M.ui_probe(request, raw)
    parseOwn(request, raw)
    local a = request.action
    if a == "scan" then return scan() end
    if a == "tree" then return tree(request) end
    if a == "add_button" then return add_button(request) end
    if a == "add_overlay" then return add_overlay(request) end
    if a == "add_clone" then return add_clone(request) end
    if a == "focus" then return focus(request) end
    if a == "state" then return state() end
    if a == "close" then return close() end
    return { ok = false, error = "unknown action" }
end

return M
