-- Feature tech_tree_widget (M12 iteration 02; layout of change update-tech-tree-widget-layout): the menu of the tech tree.
-- The pak InvasionMod_P.pak holds a cooked Widget Blueprint with POOLS of controls on one canvas (mod/InvasionMod/ue/make_tech_widget.py).
-- Lua puts a click button (WBP_ClickButton, shared module HarnessClickHooks) into each button Border. A click is a hook event, not a poll (spec 34).
-- The tree is data driven: Lua labels, shows, hides, colours and moves the controls from the nodes of the tech_tree feature
-- (data/tech_tree/tree.json, with the layout data). The window follows the mockup in openspec/specs/mod/tech_tree_widget/mockups/:
-- header (title, picks counter, close), column heads I to IV, rows Oppression / Prosperity / Common, cards with links, laws strip, footer.
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
local PATH_BUTTON_COUNT, NODE_COUNT, LINK_COUNT, STRIP_COUNT, ROW_COUNT, COLUMN_COUNT = 2, 16, 6, 2, 3, 4
local VISIBLE, COLLAPSED, SELF_HIT_TEST_INVISIBLE = 0, 1, 4 -- ESlateVisibility
local ROW_PATHS = { "oppression", "prosperity", "common" }

local S = {
    widget = nil, texts = {}, flats = {}, paths = {}, nodes = {}, laws = {}, strip = {}, close = nil,
    clicks = 0, last_error = nil, last_view = nil, last_refresh = 0, message = lines.START_MESSAGE, shown = {},
}
local isValid, read = core.isValid, core.read

---------------------------------------------------------------------------------------------
-- Small control helpers
---------------------------------------------------------------------------------------------

-- A button is a click button in a Border. The Border is collapsed too, or the empty pool entry would eat clicks.
-- A shown Border is SelfHitTestInvisible, as the base menu sets it (core/menu.lua let_clicks_reach_the_backdrop).
local function set_visible(slot, shown)
    if slot.shown_state == shown then return end
    slot.shown_state = shown
    pcall(clickhooks.set_visible, slot.handle, shown)
    pcall(function() slot.border:SetVisibility(shown and SELF_HIT_TEST_INVISIBLE or COLLAPSED) end)
end

local function set_label(slot, text)
    clickhooks.set_text(slot.handle, text)
end

-- A text block or flat Border of the pool. The text is set only when it changes.
local function set_text(name, text)
    local block = S.texts[name]
    local key = "t:" .. name
    if block == nil or S.shown[key] == text then return end
    S.shown[key] = text
    block:SetText(FText(text))
end

local function set_shown(name, widget, shown)
    local key = "v:" .. name
    if widget == nil or S.shown[key] == shown then return end
    S.shown[key] = shown
    pcall(function() widget:SetVisibility(shown and SELF_HIT_TEST_INVISIBLE or COLLAPSED) end)
end

local function set_brush(name, widget, rgba)
    if widget == nil then return end
    local key = string.format("%.2f/%.2f/%.2f", rgba.R, rgba.G, rgba.B)
    name = "b:" .. name
    if S.shown[name] == key then return end
    S.shown[name] = key
    pcall(function() widget:SetBrushColor(rgba) end)
end

local function move(name, widget, x, y)
    if widget == nil then return end
    local key = x .. "/" .. y
    name = "m:" .. name
    if S.shown[name] == key then return end
    S.shown[name] = key
    local ok, problem = pcall(function() widget.Slot:SetPosition({ X = x, Y = y }) end)
    if not ok and not S.position_error then
        S.position_error = tostring(problem)
        core.log.warn(TAG, "position failed: " .. S.position_error)
    end
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
    local text = source and lines.effect_lines(source, tech_tree.tree) or ""
    if text == "" and source then return "No standing effect" end
    return text
end

---------------------------------------------------------------------------------------------
-- Refresh: header, rows, cards, links, strip, footer
---------------------------------------------------------------------------------------------

local function refresh_header(view)
    set_text("PicksText", "Tech picks: " .. lines.picks_text(view))
    set_text("FooterMsg", S.message)
    set_text("FooterFixed", lines.FIXED_TEXT)
    for c = 1, COLUMN_COUNT do set_text("ColHead" .. (c - 1), lines.column_head(c)) end
    for r = 1, ROW_COUNT do
        local path_id = ROW_PATHS[r]
        local info = tech_tree.tree.path_ids[path_id]
        set_text("RowName" .. (r - 1), info and info.name or "Common")
        set_text("RowStatus" .. (r - 1), lines.row_status_text(path_id, view))
    end
end

local function refresh_paths(view)
    for i = 1, PATH_BUTTON_COUNT do
        local slot = S.paths[i]
        if slot then
            local shown = view.path_name == nil and view.paths[i] ~= nil
            set_visible(slot, shown)
            if shown then set_label(slot, lines.path_button_label()) end
        end
    end
end

-- Position of a card from the layout data of its node (config: origin and steps).
local function card_position(card)
    return lines.position(card.layout, config.step_x, config.step_y, config.origin_x, config.origin_y)
end

local function refresh_card(i, card, view, law_rows)
    local slot = S.nodes[i]
    if not slot then return end
    slot.row = card
    local source = tech_tree.tree.by_id[card.id]
    local position = card_position(card)
    set_visible(slot, true)
    move("node" .. i, slot.border, position.X, position.Y)
    set_label(slot, lines.card_text(card, source, tech_tree.tree))
    local shown_status = lines.display_status(card)
    if slot.status ~= shown_status then
        slot.status = shown_status
        pcall(function() slot.handle.widget:SetColorAndOpacity(lines.color(shown_status)) end)
    end
    set_tooltip(slot, tooltip_text(card, tech_tree.tree.by_id))
    -- ring with the letter of the path (flat colour instead of an icon)
    local path = lines.card_path(card)
    set_shown("ring" .. i, S.flats["RingBg" .. (i - 1)], true)
    set_brush("ringc" .. i, S.flats["RingBg" .. (i - 1)], lines.path_color(path))
    move("ringbg" .. i, S.flats["RingBg" .. (i - 1)], position.X + 8, position.Y + 8)
    set_shown("ringl" .. i, S.texts["RingLetter" .. (i - 1)], true)
    set_text("RingLetter" .. (i - 1), lines.path_letter(path))
    move("ringlt" .. i, S.texts["RingLetter" .. (i - 1)], position.X + 15, position.Y + 9)
    -- the law of the tech and its button
    local law = lines.law_of_node(card.id, tech_tree.tree)
    set_shown("claw" .. i, S.texts["CardLaw" .. (i - 1)], true)
    set_text("CardLaw" .. (i - 1), lines.card_law_text(law))
    move("claw" .. i, S.texts["CardLaw" .. (i - 1)], position.X + 8, position.Y + config.card_h - config.law_row_h)
    local law_slot = S.laws[i]
    if not law_slot then return end
    local row = law and law_rows[law.id] or nil
    local label = lines.law_button_label(row)
    law_slot.row = label and row or nil
    set_visible(law_slot, label ~= nil)
    if label then
        set_label(law_slot, label)
        move("lawb" .. i, law_slot.border, position.X + 8, position.Y + config.card_h - config.law_row_h + 20)
        set_tooltip(law_slot, tooltip_text(row, tech_tree.tree.laws_by_id))
    else
        set_tooltip(law_slot, "")
    end
end

local function hide_card(i)
    local slot = S.nodes[i]
    if not slot then return end
    slot.row = nil
    set_visible(slot, false)
    set_tooltip(slot, "")
    set_shown("ring" .. i, S.flats["RingBg" .. (i - 1)], false)
    set_shown("ringl" .. i, S.texts["RingLetter" .. (i - 1)], false)
    set_shown("claw" .. i, S.texts["CardLaw" .. (i - 1)], false)
    local law_slot = S.laws[i]
    if law_slot then
        law_slot.row = nil
        set_visible(law_slot, false)
    end
end

-- The links join a path node to the node it requires. Lit when that node is unlocked.
local function refresh_links(cards)
    local index_of, unlocked = {}, {}
    for i, card in ipairs(cards) do
        index_of[card.id] = i
        unlocked[card.id] = card.status == "unlocked"
    end
    local link = 0
    for i, card in ipairs(cards) do
        local required = card.requires and card.requires[1]
        if required and index_of[required] and link < LINK_COUNT then
            link = link + 1
            local from = card_position(cards[index_of[required]])
            local widget = S.flats["LinkBg" .. (link - 1)]
            set_shown("link" .. link, widget, true)
            move("link" .. link, widget, from.X + config.card_w, from.Y + (config.card_h - config.law_row_h) // 2)
            set_brush("linkc" .. link, widget, lines.link_color(unlocked[required]))
        end
    end
    for k = link + 1, LINK_COUNT do set_shown("link" .. k, S.flats["LinkBg" .. (k - 1)], false) end
end

local function refresh_strip(view)
    set_text("StripCount", lines.strip_count_text(view))
    local enacted = lines.enacted_laws(view)
    for k = 1, STRIP_COUNT do
        local slot = S.strip[k]
        local law = enacted[k]
        set_text("StripName" .. (k - 1), lines.strip_place_text(law, tech_tree.tree))
        if slot then
            slot.row = law
            set_visible(slot, law ~= nil)
            if law then set_label(slot, "Repeal") end
        end
    end
end

local function refresh()
    if not isValid(S.widget) then return false end
    local view = tech_tree.view()
    S.last_view = view
    local cards = lines.cards(view)
    local law_rows = lines.law_rows_by_id(view)
    refresh_header(view)
    refresh_paths(view)
    for i = 1, NODE_COUNT do
        if cards[i] then refresh_card(i, cards[i], view, law_rows) else hide_card(i) end
    end
    refresh_links(cards)
    refresh_strip(view)
    return true
end

---------------------------------------------------------------------------------------------
-- Clicks. The handlers are what a click calls. The harness command press calls the same functions.
---------------------------------------------------------------------------------------------

local function report(kind, what, result, problem)
    S.clicks = S.clicks + 1
    S.message = lines.result_message(kind, what, result ~= nil, problem)
    if not result then
        S.last_error = problem
        core.log.warn(TAG, kind .. " " .. tostring(what) .. " refused: " .. tostring(problem))
    end
end

local function press_path(index)
    local path = S.last_view and S.last_view.paths[index]
    if not path then return nil, "no path button " .. tostring(index) end
    local result, problem = tech_tree.choose_path(path.id)
    report("choose", path.name, result, problem)
    return result, problem
end

local function press_node(index)
    local slot = S.nodes[index]
    if not (slot and slot.row) then return nil, "no node button " .. tostring(index) end
    local result, problem = tech_tree.unlock(slot.row.id)
    report("unlock", slot.row.name, result, problem)
    return result, problem
end

-- A law in force is repealed, any other law is enacted. The law button of a card has the index of the card.
local function press_law(index)
    local slot = S.laws[index]
    if not (slot and slot.row) then return nil, "no law button " .. tostring(index) end
    local act = slot.row.status == "enacted" and tech_tree.repeal_law or tech_tree.enact_law
    local kind = slot.row.status == "enacted" and "repeal" or "enact"
    local result, problem = act(slot.row.id)
    report(kind, slot.row.name, result, problem)
    return result, problem
end

-- A strip place repeals the law it shows.
local function press_strip(index)
    local slot = S.strip[index]
    if not (slot and slot.row) then return nil, "no law in strip place " .. tostring(index) end
    local result, problem = tech_tree.repeal_law(slot.row.id)
    report("repeal", slot.row.name, result, problem)
    return result, problem
end

local function is_open() return menu.is_open(MENU_ID) end

local function press_close()
    S.clicks = S.clicks + 1
    return menu.close()
end

local HANDLERS = { path = press_path, node = press_node, law = press_law, strip = press_strip, close = press_close }

-- The base menu sets all Borders of the new widget to SelfHitTestInvisible right after on_open. That undoes a Collapsed pool entry
-- of the first refresh. The first tick forgets the visibility that was set and sets it again.
local function reapply_visibility()
    S.fresh = false
    for key in pairs(S.shown) do
        if key:sub(1, 2) == "v:" then S.shown[key] = nil end
    end
    for _, group in ipairs({ S.paths, S.nodes, S.laws, S.strip }) do
        for _, slot in pairs(group) do slot.shown_state = nil end
    end
    refresh()
end

local function tick()
    if not is_open() then
        S.widget = nil
        return
    end
    if S.fresh then reapply_visibility() end
    local clicked = clickhooks.drain(S)
    for _, handle in ipairs(clicked) do
        HANDLERS[handle.tag.kind](handle.tag.index)
        if not is_open() then return end
    end
    -- The labels change only when the game state changes. A refresh each tick made a lot of Lua garbage and the Lua state broke.
    local now = os.clock()
    if #clicked > 0 or now - S.last_refresh >= config.refresh_ms / 1000 then
        S.last_refresh = now
        refresh()
    end
end

---------------------------------------------------------------------------------------------
-- Open and close
---------------------------------------------------------------------------------------------

local TEXT_NAMES = { "TitleText", "PicksText", "FooterMsg", "FooterFixed", "StripTitle", "StripCount" }
local FLAT_NAMES = {}

-- All names of the pools of one widget class, in one list (one scan of the class instead of one for each pool).
local function pool_names()
    local texts, flats = { table.unpack(TEXT_NAMES) }, { table.unpack(FLAT_NAMES) }
    for c = 0, COLUMN_COUNT - 1 do texts[#texts + 1] = "ColHead" .. c end
    for r = 0, ROW_COUNT - 1 do
        texts[#texts + 1] = "RowName" .. r
        texts[#texts + 1] = "RowStatus" .. r
    end
    for i = 0, NODE_COUNT - 1 do
        texts[#texts + 1] = "RingLetter" .. i
        texts[#texts + 1] = "CardLaw" .. i
        flats[#flats + 1] = "RingBg" .. i
    end
    for i = 0, LINK_COUNT - 1 do flats[#flats + 1] = "LinkBg" .. i end
    for i = 0, STRIP_COUNT - 1 do texts[#texts + 1] = "StripName" .. i end
    return texts, flats
end

-- Puts a click button into each Border of the pool. Returns the slots, or nil and a message.
local function make_slots(borders, prefix, kind, count)
    local controller = FindFirstOf("PlayerController")
    local slots = {}
    for i = 1, count do
        local border = borders[prefix .. (i - 1)]
        if border then
            local handle, problem = clickhooks.attach(border, controller, { owner = S, kind = kind, index = i })
            if not handle then return nil, problem end
            slots[i] = { border = border, handle = handle }
        end
    end
    return slots
end

local function all_handles()
    local handles = {}
    for _, group in ipairs({ S.paths, S.nodes, S.laws, S.strip }) do
        for _, slot in pairs(group) do handles[#handles + 1] = slot.handle end
    end
    if S.close then handles[#handles + 1] = S.close.handle end
    return handles
end

local function reset()
    clickhooks.release(all_handles())
    S.widget, S.texts, S.flats, S.paths, S.nodes, S.laws, S.strip, S.close = nil, {}, {}, {}, {}, {}, {}, nil
    S.shown = {}
end

local function border_names(prefix, count)
    local names = {}
    for i = 0, count - 1 do names[#names + 1] = prefix .. i end
    return names
end

-- The base menu calls this with the made widget. On a failure this function cleans up and returns nil and a message.
local function on_open(made)
    if #tech_tree.tree.nodes + #tech_tree.tree.common_nodes > NODE_COUNT then
        return nil, string.format("the tree has %d nodes, the widget has %d buttons", #tech_tree.tree.nodes + #tech_tree.tree.common_nodes, NODE_COUNT)
    end
    if require("config").tech_tree.max_active_laws > STRIP_COUNT then
        return nil, string.format("max_active_laws is %d, the laws strip has %d places", require("config").tech_tree.max_active_laws, STRIP_COUNT)
    end
    S.widget = made
    local text_names, flat_names = pool_names()
    S.texts = menu.find_named(made, "TextBlock", text_names)
    S.flats = menu.find_named(made, "Border", flat_names)
    local names = {}
    for _, group in ipairs({ border_names("PathButton", PATH_BUTTON_COUNT), border_names("NodeButton", NODE_COUNT),
        border_names("LawButton", NODE_COUNT), border_names("StripRepeal", STRIP_COUNT), { "CloseButton" } }) do
        for _, name in ipairs(group) do names[#names + 1] = name end
    end
    local borders = menu.find_named(made, "Border", names)
    local problem
    S.paths, problem = make_slots(borders, "PathButton", "path", PATH_BUTTON_COUNT)
    if S.paths then S.nodes, problem = make_slots(borders, "NodeButton", "node", NODE_COUNT) end
    if S.nodes then S.laws, problem = make_slots(borders, "LawButton", "law", NODE_COUNT) end
    if S.laws then S.strip, problem = make_slots(borders, "StripRepeal", "strip", STRIP_COUNT) end
    if S.strip then
        local closes
        closes, problem = make_slots({ Close0 = borders.CloseButton }, "Close", "close", 1)
        S.close = closes and closes[1] or nil
    end
    if S.close then
        local bound, bind_problem = clickhooks.bind_texts(all_handles())
        if not bound then S.close, problem = nil, bind_problem end
    end
    if not (S.paths and S.nodes and S.laws and S.strip and S.close) then
        reset()
        return nil, problem
    end
    if S.texts.TitleText == nil or S.texts.PicksText == nil or S.nodes[1] == nil or S.laws[1] == nil or S.texts.FooterMsg == nil then
        reset()
        return nil, "the text blocks or node buttons were not found in the widget"
    end
    S.message = lines.START_MESSAGE
    S.fresh = true
    set_text("TitleText", "Charters of the Realm")
    set_text("StripTitle", "Laws in force")
    set_label(S.close, "Close")
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
    local position = read(function() return slot.border.Slot:GetPosition() end)
    local row = { x = position and position.X, y = position and position.Y, visibility = read(function() return slot.handle.widget:GetVisibility() end),
        hovered = read(function() return slot.handle.widget:IsHovered() end),
        label = read(function() return slot.handle.text:GetText():ToString() end),
        tooltip = read(function() return slot.border.ToolTipText:ToString() end) }
    for key, value in pairs(extra or {}) do row[key] = value end
    return row
end

local function text_of(name)
    local block = S.texts[name]
    return block and read(function() return block:GetText():ToString() end) or nil
end

local function describe()
    local paths, nodes, laws, strip = {}, {}, {}, {}
    for i, slot in pairs(S.paths) do paths[#paths + 1] = button_row(slot, { index = i }) end
    for i, slot in pairs(S.laws) do
        laws[#laws + 1] = button_row(slot, { index = i, id = slot.row and slot.row.id, status = slot.row and slot.row.status })
    end
    for i, slot in pairs(S.strip) do strip[#strip + 1] = button_row(slot, { index = i, id = slot.row and slot.row.id, text = text_of("StripName" .. (i - 1)) }) end
    for i, slot in pairs(S.nodes) do
        nodes[#nodes + 1] = button_row(slot, { index = i, id = slot.row and slot.row.id, status = slot.row and slot.row.status,
            card_law = text_of("CardLaw" .. (i - 1)) })
    end
    local view = tech_tree.view()
    local columns, rows = {}, {}
    for c = 0, COLUMN_COUNT - 1 do columns[#columns + 1] = text_of("ColHead" .. c) end
    for r = 0, ROW_COUNT - 1 do rows[#rows + 1] = { name = text_of("RowName" .. r), status = text_of("RowStatus" .. r) } end
    return { open = is_open(), in_viewport = is_open() and read(function() return S.widget:IsInViewport() end) or false,
        title = text_of("TitleText"), picks = text_of("PicksText"), wanted_picks = "Tech picks: " .. lines.picks_text(view),
        footer = text_of("FooterMsg"), footer_fixed = text_of("FooterFixed"), columns = columns, rows = rows,
        strip_count = text_of("StripCount"), wanted_strip_count = lines.strip_count_text(view),
        paths = paths, nodes = nodes, laws = laws, strip = strip, clicks = S.clicks,
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
        local handler = HANDLERS[args.kind]
        if not handler then return nil, "kind must be path, node, law, strip or close" end
        local result, problem = handler(args.index)
        if is_open() then refresh() end -- also after a refusal: the footer shows the reason
        if not result then return nil, problem end
        return describe()
    end, { kind = { type = "string", required = true }, index = { type = "integer", required = true } })
end

require("scheduler").every(TAG, config.poll_ms, tick)
-- The key callback runs on the input thread. It must not touch the Lua state beyond one flag:
-- Lua calls from it raced with the game thread and crashed the game (UE4SS luaH_getint). The base menu tick does the work.
RegisterKeyBind(config.toggle_key, function() menu.request_toggle(MENU_ID) end)

core.log.info(TAG, "feature tech_tree_widget loaded (the Tech button in the bottom bar, or F9, opens and closes the menu)")
return { open = function() return menu.open(MENU_ID) end, close = menu.close }
