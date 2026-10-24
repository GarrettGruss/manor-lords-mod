-- Feature tech_tree_widget (M12 iteration 02): the menu of the tech tree.
-- The pak InvasionMod_P.pak holds a cooked Widget Blueprint with a POOL of Borders on a canvas (mod/InvasionMod/ue/make_tech_widget.py).
-- Lua puts a click button (WBP_ClickButton, shared module HarnessClickHooks) into each Border. A click is a hook event, not a poll (spec 34).
-- The tree is data driven: Lua labels, shows, hides, colours and moves the buttons from the nodes of the tech_tree feature
-- (data/tech_tree/tree.json, with the layout data). A click on a path button or a node button calls the tech_tree feature.
-- The menu is built on the base menu (core/menu.lua): it gets a bottom bar button, opens fullscreen and blocks clicks to the game.
-- F9 stays as a shortcut.
-- Rules: game objects are touched on the game thread only (the scheduler runs jobs there). No LoopAsync of its own.
local core = require("ManorCore")
local menu = require("core.menu")
local lines = require("features.tech_tree_widget.lines")
local tech_tree = require("features.tech_tree.init")
local config = require("config").tech_tree_widget
local clickhooks = require("HarnessClickHooks")

local TAG = "InvasionMod.tech_tree_widget"
local MENU_ID = "tech"
local LINE_COUNT, PATH_BUTTON_COUNT, NODE_COUNT, LAW_COUNT = 3, 2, 16, 3

local S = { widget = nil, lines = {}, laws_line = nil, paths = {}, nodes = {}, laws = {}, clicks = 0, last_error = nil, last_view = nil, shown_lines = {}, shown_laws_line = nil, last_refresh = 0 }
local isValid, read = core.isValid, core.read

local function set_visible(slot, shown)
    pcall(clickhooks.set_visible, slot.handle, shown)
end

local function set_line(index, text)
    if S.shown_lines[index] == text then return end
    S.shown_lines[index] = text
    S.lines[index]:SetText(FText(text))
end

-- The tooltip is the UMG property ToolTipText of the Border around the click button (spike: notes/hover-route.md).
-- It is set again only when the text changes.
local function set_tooltip(slot, text)
    if slot.tooltip == text then return end
    local ok, problem = pcall(function() slot.border:SetToolTipText(FText(text)) end)
    if ok then
        slot.tooltip = text
    elseif not S.tooltip_error then
        S.tooltip_error = tostring(problem)
        core.log.warn(TAG, "tooltip failed: " .. S.tooltip_error)
    end
end

local function tooltip_text(row, by_id)
    local source = by_id[row.id]
    return source and lines.effect_lines(source, tech_tree.tree) or ""
end

local function place(slot)
    local position = lines.position(slot.row.layout, config.step_x, config.step_y)
    local ok, problem = pcall(function() slot.border.Slot:SetPosition(position) end)
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
            set_visible(slot, row ~= nil)
            if row then
                clickhooks.set_text(slot.handle, lines.node_label(row))
                if slot.status ~= row.status then
                    slot.status = row.status
                    pcall(function() slot.handle.widget:SetColorAndOpacity(lines.color(row.status)) end)
                end
                place(slot)
                set_tooltip(slot, tooltip_text(row, tech_tree.tree.by_id))
            else
                set_tooltip(slot, "")
            end
        end
    end
end

local function refresh_laws(view)
    if S.laws_line then
        local text = lines.laws_line(view)
        if S.shown_laws_line ~= text then
            S.shown_laws_line = text
            S.laws_line:SetText(FText(text))
        end
    end
    for i = 1, LAW_COUNT do
        local slot = S.laws[i]
        if slot then
            slot.row = view.laws[i]
            set_visible(slot, slot.row ~= nil)
            if slot.row then clickhooks.set_text(slot.handle, lines.law_label(slot.row)) end
            set_tooltip(slot, slot.row and tooltip_text(slot.row, tech_tree.tree.laws_by_id) or "")
        end
    end
end

local function refresh()
    if not isValid(S.widget) then return false end
    local view = tech_tree.view()
    S.last_view = view
    local texts = lines.header(view)
    for i = 1, LINE_COUNT do
        if S.lines[i] then set_line(i, texts[i]) end
    end
    for i = 1, PATH_BUTTON_COUNT do
        local slot = S.paths[i]
        if slot then
            set_visible(slot, view.path_name == nil and view.paths[i] ~= nil)
            if view.paths[i] then clickhooks.set_text(slot.handle, lines.path_label(view.paths[i])) end
        end
    end
    refresh_nodes(view)
    refresh_laws(view)
    return true
end

local function report(result, problem, what)
    S.clicks = S.clicks + 1
    if not result then
        S.last_error = problem
        core.log.warn(TAG, what .. " refused: " .. tostring(problem))
    end
end

-- The handlers below are what a click calls. The harness command press calls the same functions.
local function press_path(index)
    local path = S.last_view and S.last_view.paths[index]
    if not path then return nil, "no path button " .. tostring(index) end
    local result, problem = tech_tree.choose_path(path.id)
    report(result, problem, "choose path")
    return result, problem
end

local function press_node(index)
    local slot = S.nodes[index]
    if not (slot and slot.row) then return nil, "no node button " .. tostring(index) end
    local result, problem = tech_tree.unlock(slot.row.id)
    report(result, problem, "unlock " .. slot.row.id)
    return result, problem
end

-- A law in force is repealed, any other law is enacted.
local function press_law(index)
    local slot = S.laws[index]
    if not (slot and slot.row) then return nil, "no law button " .. tostring(index) end
    local act = slot.row.status == "enacted" and tech_tree.repeal_law or tech_tree.enact_law
    local result, problem = act(slot.row.id)
    report(result, problem, "law " .. slot.row.id)
    return result, problem
end

local function is_open() return menu.is_open(MENU_ID) end

local function tick()
    if not is_open() then
        S.widget = nil
        return
    end
    local handlers = { path = press_path, node = press_node, law = press_law }
    local clicked = clickhooks.drain(S)
    for _, handle in ipairs(clicked) do
        handlers[handle.tag.kind](handle.tag.index)
    end
    -- The labels change only when the game state changes. A refresh each tick made a lot of Lua garbage and the Lua state broke.
    local now = os.clock()
    if #clicked > 0 or now - S.last_refresh >= config.refresh_ms / 1000 then
        S.last_refresh = now
        refresh()
    end
end

-- Puts a click button into each Border of the pool. Returns the slots, or nil and a message.
local function make_slots(widget, prefix, kind, count)
    local borders = menu.find_pool(widget, "Border", prefix, count)
    local controller = FindFirstOf("PlayerController")
    local slots = {}
    for i = 1, count do
        if borders[i] then
            local handle, problem = clickhooks.attach(borders[i], controller, { owner = S, kind = kind, index = i })
            if not handle then return nil, problem end
            slots[i] = { border = borders[i], handle = handle }
        end
    end
    return slots
end

local function release_slots()
    local handles = {}
    for _, group in ipairs({ S.paths, S.nodes, S.laws }) do
        for _, slot in pairs(group) do handles[#handles + 1] = slot.handle end
    end
    clickhooks.release(handles)
end

local function reset()
    release_slots()
    S.widget, S.lines, S.laws_line, S.paths, S.nodes, S.laws = nil, {}, nil, {}, {}, {}
    S.shown_lines, S.shown_laws_line = {}, nil
end

-- The base menu calls this with the made widget. On a failure this function cleans up and returns nil and a message.
local function on_open(made)
    if #tech_tree.tree.nodes > NODE_COUNT then
        return nil, string.format("the tree has %d nodes, the widget has %d buttons", #tech_tree.tree.nodes, NODE_COUNT)
    end
    S.widget = made
    S.lines = menu.find_pool(made, "TextBlock", "TechLine", LINE_COUNT)
    local slot_problem
    S.paths, slot_problem = make_slots(made, "PathButton", "path", PATH_BUTTON_COUNT)
    if S.paths then S.nodes, slot_problem = make_slots(made, "NodeButton", "node", NODE_COUNT) end
    if S.nodes then S.laws, slot_problem = make_slots(made, "LawButton", "law", LAW_COUNT) end
    if S.laws then
        local handles = {}
        for _, group in ipairs({ S.paths, S.nodes, S.laws }) do
            for _, slot in pairs(group) do handles[#handles + 1] = slot.handle end
        end
        local bound, bind_problem = clickhooks.bind_texts(handles)
        if not bound then S.laws, slot_problem = nil, bind_problem end
    end
    if not (S.paths and S.nodes and S.laws) then
        reset()
        return nil, slot_problem
    end
    S.laws_line = menu.find_pool(made, "TextBlock", "LawsLine", 1)[1]
    if S.lines[1] == nil or S.nodes[1] == nil or S.laws[1] == nil or S.laws_line == nil then
        reset()
        return nil, "the text lines or node buttons were not found in the widget"
    end
    refresh()
    return true
end

menu.register({
    id = MENU_ID, label = "Tech",
    class_path = "/Game/HarnessMod/WBP_TechTreeMenu.WBP_TechTreeMenu_C", package_path = "/Game/HarnessMod", asset_name = "WBP_TechTreeMenu",
    z_order = config.z_order, position = config.position,
    on_open = on_open, on_close = reset,
})

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local function button_row(slot, extra)
    local row = { visibility = read(function() return slot.handle.widget:GetVisibility() end),
        hovered = read(function() return slot.handle.widget:IsHovered() end),
        label = read(function() return slot.handle.text:GetText():ToString() end),
        tooltip = read(function() return slot.border.ToolTipText:ToString() end) }
    for key, value in pairs(extra or {}) do row[key] = value end
    return row
end

local function describe()
    local shown = {}
    for i = 1, LINE_COUNT do
        shown[i] = S.lines[i] and read(function() return S.lines[i]:GetText():ToString() end) or nil
    end
    local paths, nodes, laws = {}, {}, {}
    for i, slot in pairs(S.laws) do laws[#laws + 1] = button_row(slot, { index = i, id = slot.row and slot.row.id, status = slot.row and slot.row.status }) end
    for i, slot in pairs(S.paths) do paths[#paths + 1] = button_row(slot, { index = i }) end
    for i, slot in pairs(S.nodes) do
        local position = read(function() return slot.border.Slot:GetPosition() end)
        nodes[#nodes + 1] = button_row(slot, { index = i, id = slot.row and slot.row.id, status = slot.row and slot.row.status,
            x = position and position.X, y = position and position.Y })
    end
    return { open = is_open(), in_viewport = is_open() and read(function() return S.widget:IsInViewport() end) or false,
        lines = shown, wanted_lines = lines.header(tech_tree.view()), paths = paths, nodes = nodes, laws = laws, clicks = S.clicks,
        laws_line = S.laws_line and read(function() return S.laws_line:GetText():ToString() end) or nil,
        wanted_laws_line = lines.laws_line(tech_tree.view()),
        last_error = S.last_error, tooltip_error = S.tooltip_error, position_error = S.position_error }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.tech_tree_widget_open", function() return menu.open(MENU_ID) end, {})
    commands.register("InvasionMod.tech_tree_widget_close", function()
        if is_open() then return menu.close() end
        return { ok = true }
    end, {})
    commands.register("InvasionMod.tech_tree_widget_state", describe, {})
    -- Calls the click handler without the mouse. The widget must be open.
    commands.register("InvasionMod.tech_tree_widget_press", function(args)
        if not is_open() then return nil, "the widget is not open" end
        local handlers = { path = press_path, node = press_node, law = press_law }
        local handler = handlers[args.kind]
        if not handler then return nil, "kind must be path, node or law" end
        local result, problem = handler(args.index)
        if not result then return nil, problem end
        refresh()
        return describe()
    end, { kind = { type = "string", required = true }, index = { type = "integer", required = true } })
end

require("scheduler").every(TAG, config.poll_ms, tick)
-- The key callback runs on the input thread. It must not touch the Lua state beyond one flag:
-- Lua calls from it raced with the game thread and crashed the game (UE4SS luaH_getint). The base menu tick does the work.
RegisterKeyBind(config.toggle_key, function() menu.request_toggle(MENU_ID) end)

core.log.info(TAG, "feature tech_tree_widget loaded (the Tech button in the bottom bar, or F9, opens and closes the menu)")
return { open = function() return menu.open(MENU_ID) end, close = menu.close }
