-- Feature tech_tree_widget (M12 iteration 02): the menu of the tech tree.
-- The pak techmenu_P.pak holds a cooked Widget Blueprint with a POOL of node buttons on a canvas (mod/InvasionMod/ue/make_tech_widget.py).
-- The tree is data driven: Lua labels, shows, hides, colours and moves the buttons from the nodes of the tech_tree feature
-- (data/tech_tree/tree.json, with the layout data). A click on a path button or a node button calls the tech_tree feature.
-- Rules: game objects are touched on the game thread only (the scheduler runs jobs there). No LoopAsync of its own.
local core = require("ManorCore")
local lines = require("features.tech_tree_widget.lines")
local tech_tree = require("features.tech_tree.init")
local config = require("config").tech_tree_widget

local TAG = "InvasionMod.tech_tree_widget"
local CLASS_PATH = "/Game/HarnessMod/WBP_TechTreeMenu.WBP_TechTreeMenu_C"
local PACKAGE_PATH, ASSET_NAME = "/Game/HarnessMod", "WBP_TechTreeMenu"
local LINE_COUNT, PATH_BUTTON_COUNT, NODE_COUNT = 3, 2, 16
local VISIBLE, COLLAPSED = 0, 1 -- ESlateVisibility

local S = { widget = nil, lines = {}, paths = {}, nodes = {}, clicks = 0, last_error = nil, last_view = nil }
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
    if not isValid(found) then return nil, "class not found; is the pak techmenu_P.pak in Paks/~mods?" end
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

-- Children have names like NodeButton3. Python cannot mark them as variables, so they are found by name.
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

local function set_visible(button, shown)
    pcall(function() button:SetVisibility(shown and VISIBLE or COLLAPSED) end)
end

local function place(slot)
    local position = lines.position(slot.row.layout, config.step_x, config.step_y)
    local ok, problem = pcall(function() slot.button.Slot:SetPosition(position) end)
    if not ok and not S.position_error then
        S.position_error = tostring(problem)
        core.log.warn(TAG, "node position failed: " .. S.position_error)
    end
end

local function refresh_nodes(view)
    for i = 1, NODE_COUNT do
        local slot, row = S.nodes[i], view.nodes[i]
        if slot then
            slot.row = row
            set_visible(slot.button, row ~= nil)
            if row then
                slot.label:SetText(FText(lines.node_label(row)))
                pcall(function() slot.button:SetBackgroundColor(lines.color(row.status)) end)
                place(slot)
            end
        end
    end
end

local function refresh()
    if not isValid(S.widget) then return false end
    local view = tech_tree.view()
    S.last_view = view
    local texts = lines.header(view)
    for i = 1, LINE_COUNT do
        if S.lines[i] then S.lines[i]:SetText(FText(texts[i])) end
    end
    for i = 1, PATH_BUTTON_COUNT do
        local slot = S.paths[i]
        if slot then
            set_visible(slot.button, view.path_name == nil and view.paths[i] ~= nil)
            if view.paths[i] then slot.label:SetText(FText(lines.path_label(view.paths[i]))) end
        end
    end
    refresh_nodes(view)
    return true
end

-- A click is a press that ends while the mouse is on the button (same rule as PolicyMenu and the raid widget).
local function was_clicked(slot)
    local pressed = read(function() return slot.button:IsPressed() end) == true
    if pressed then slot.hovered = read(function() return slot.button:IsHovered() end) == true end
    local released = slot.was_pressed and not pressed
    slot.was_pressed = pressed
    if not (released and slot.hovered) or os.clock() - slot.last_click < config.click_cooldown_s then return false end
    slot.last_click = os.clock()
    return true
end

local function report(result, problem, what)
    S.clicks = S.clicks + 1
    if not result then
        S.last_error = problem
        core.log.warn(TAG, what .. " refused: " .. tostring(problem))
    end
end

local function tick()
    if not isValid(S.widget) then
        S.widget = nil
        return
    end
    for i, slot in ipairs(S.paths) do
        if was_clicked(slot) and S.last_view and S.last_view.paths[i] then
            local result, problem = tech_tree.choose_path(S.last_view.paths[i].id)
            report(result, problem, "choose path")
        end
    end
    for _, slot in ipairs(S.nodes) do
        if was_clicked(slot) and slot.row then
            local result, problem = tech_tree.unlock(slot.row.id)
            report(result, problem, "unlock " .. slot.row.id)
        end
    end
    refresh()
end

local function is_open() return isValid(S.widget) end

local function make_slots(widget, prefix, label_prefix, count)
    local buttons = find_named(widget, "Button", prefix, count)
    local labels = find_named(widget, "TextBlock", label_prefix, count)
    local slots = {}
    for i = 1, count do
        if buttons[i] and labels[i] then
            slots[i] = { button = buttons[i], label = labels[i], was_pressed = false, hovered = false, last_click = -100 }
        end
    end
    return slots
end

local function open()
    if is_open() then return { ok = true, already_open = true } end
    local made, problem = make_widget()
    if not made then return { ok = false, error = problem } end
    if #tech_tree.tree.nodes > NODE_COUNT then
        return { ok = false, error = string.format("the tree has %d nodes, the widget has %d buttons", #tech_tree.tree.nodes, NODE_COUNT) }
    end
    S.widget = made
    S.lines = find_named(made, "TextBlock", "TechLine", LINE_COUNT)
    S.paths = make_slots(made, "PathButton", "PathLabel", PATH_BUTTON_COUNT)
    S.nodes = make_slots(made, "NodeButton", "NodeLabel", NODE_COUNT)
    if S.lines[1] == nil or S.nodes[1] == nil then
        made:RemoveFromParent()
        S.widget = nil
        return { ok = false, error = "the text lines or node buttons were not found in the widget" }
    end
    made:AddToViewport(config.z_order)
    made:SetPositionInViewport(config.position, false)
    refresh()
    return { ok = true }
end

local function close()
    if is_open() then S.widget:RemoveFromParent() end
    S.widget, S.lines, S.paths, S.nodes = nil, {}, {}, {}
    return { ok = true }
end

local function toggle()
    if is_open() then return close() end
    return open()
end

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local function button_row(slot, extra)
    local row = { visibility = read(function() return slot.button:GetVisibility() end), hovered = read(function() return slot.button:IsHovered() end),
        label = read(function() return slot.label:GetText():ToString() end) }
    for key, value in pairs(extra or {}) do row[key] = value end
    return row
end

local function describe()
    local shown = {}
    for i = 1, LINE_COUNT do
        shown[i] = S.lines[i] and read(function() return S.lines[i]:GetText():ToString() end) or nil
    end
    local paths, nodes = {}, {}
    for i, slot in pairs(S.paths) do paths[#paths + 1] = button_row(slot, { index = i }) end
    for i, slot in pairs(S.nodes) do
        local position = read(function() return slot.button.Slot:GetPosition() end)
        nodes[#nodes + 1] = button_row(slot, { index = i, id = slot.row and slot.row.id, status = slot.row and slot.row.status,
            x = position and position.X, y = position and position.Y })
    end
    return { open = is_open(), in_viewport = is_open() and read(function() return S.widget:IsInViewport() end) or false,
        lines = shown, wanted_lines = lines.header(tech_tree.view()), paths = paths, nodes = nodes, clicks = S.clicks,
        last_error = S.last_error, position_error = S.position_error }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.tech_tree_widget_open", open, {})
    commands.register("InvasionMod.tech_tree_widget_close", close, {})
    commands.register("InvasionMod.tech_tree_widget_state", describe, {})
end

require("scheduler").every(TAG, config.poll_ms, tick)
RegisterKeyBind(config.toggle_key, function()
    ExecuteInGameThread(function() core.log.try(TAG, toggle) end)
end)

core.log.info(TAG, "feature tech_tree_widget loaded (F9 opens and closes the menu)")
return { open = open, close = close }
