-- Feature vassals_menu (change add-vassals-menu, #564): the Vassals window in the bottom bar.
-- It shows the vassals (3 cards), what they pay, and two controls that already exist: the tribute policy of a vassal
-- (InvasionMod.vassals_set_policy) and the restore of a wiped village (InvasionMod.vassals_restore). It saves nothing and calls no
-- save function. The window is a pak widget (mod/InvasionMod/ue/make_vassals_widget.py) on the base menu (core/menu.lua).
-- Fixed pools of controls: Lua fills them. Lua puts a click button into each button Border (HarnessClickHooks); a click is a hook event.
-- No Button.OnClicked:Add on a run-time button (#308). Rules: game objects are touched on the game thread only (the scheduler runs the jobs there).
local core = require("ManorCore")
local menu = require("core.menu")
local clickhooks = require("HarnessClickHooks")
local vassals = require("features.vassals.init")
local tribute = require("features.tribute.init")
local vassal_world = require("features.vassals.world")
local silver_world = require("features.bandits.world")
local view = require("features.vassals_menu.view")
local all_config = require("config")
local config = all_config.vassals_menu
local vassal_config = all_config.vassals

local TAG = "InvasionMod.vassals_menu"
local MENU_ID = "vassals"
local MOD_NAME = "InvasionMod"
local isValid, read = core.isValid, core.read

local CARDS, STAT_ROWS, POLICIES = vassal_config.max_vassals, #view.STAT_LABELS, #view.POLICIES
local COLLAPSED, VISIBLE = 1, 0 -- ESlateVisibility
local ROWS_SHOWN = { vassal = STAT_ROWS, wiped = 1, free = 0 } -- stat rows that a card kind shows

-- Colours are the sRGB values of the mockup; a game colour is linear (v ^ 2.2).
local function linear(r, g, b, a) return { R = r ^ 2.2, G = g ^ 2.2, B = b ^ 2.2, A = a or 1 } end
local GOLD, WHITE, GREY, SOFT = linear(0.91, 0.78, 0.48), linear(0.95, 0.93, 0.89), linear(0.56, 0.53, 0.47), linear(0.79, 0.76, 0.69)
local RED = linear(0.69, 0.44, 0.36)
local STATUS_COLOUR = { thriving = linear(0.62, 0.70, 0.48), stalled = linear(0.82, 0.63, 0.31), rebuilding = linear(0.82, 0.63, 0.31),
                        wiped = RED, claimed = SOFT, free = SOFT }
local CLEAR = { R = 0, G = 0, B = 0, A = 0 }
local DIAMOND, ROW_LINE = linear(0.56, 0.53, 0.47), linear(0.23, 0.215, 0.19)
local CARD_BG, WIPED_BG = linear(0.08, 0.075, 0.065, 0.55), linear(0.235, 0.098, 0.078, 0.35)

local NAMES = { texts = { "TitleText" }, borders = {}, buttons = {} }
local function add(list, name) list[#list + 1] = name end
for head = 0, 2 do add(NAMES.texts, "HeadLabel" .. head); add(NAMES.texts, "HeadValue" .. head) end
for card = 0, CARDS - 1 do
    for _, prefix in ipairs({ "CardRegion", "CardLord", "NoteText", "PolicyLabel", "PolicyHint", "RestoreText", "RestoreHint" }) do add(NAMES.texts, prefix .. card) end
    add(NAMES.borders, "Card" .. card)
    for row = 0, STAT_ROWS - 1 do
        local key = card .. "_" .. row
        add(NAMES.texts, "StatLabel" .. key); add(NAMES.texts, "StatValue" .. key)
        add(NAMES.borders, "Diamond" .. key); add(NAMES.borders, "Line" .. key)
    end
    for policy = 0, POLICIES - 1 do
        local key = card .. "_" .. policy
        add(NAMES.texts, "PolicyText" .. key)
        add(NAMES.borders, "Under" .. key)
        add(NAMES.buttons, "PolicyButton" .. key)
    end
    add(NAMES.buttons, "RestoreButton" .. card)
end

local W = { widget = nil, texts = {}, borders = {}, buttons = {}, shown = {}, painted = {}, tinted = {}, visible = {}, dim = {},
            last_refresh = 0, notes = {}, presses = 0, clicks_done = 0 }
local S = { stats = {}, goods = {}, stats_at = nil } -- families, buildings and rich goods of each region, read every stats_s seconds

local function is_open() return menu.is_open(MENU_ID) end

---------------------------------------------------------------------------------------------
-- The model: the same data as vassals_state and tribute_state, through the existing code
---------------------------------------------------------------------------------------------

-- The region numbers are game reads: they are cached for stats_s seconds (the window refreshes twice a second).
local function refresh_stats(force)
    local now = os.clock()
    if not force and S.stats_at and now - S.stats_at < config.stats_s then return end
    S.stats_at = now
    for _, row in ipairs(vassals.slot_rows(true)) do
        S.stats[row.region] = { families = row.families, buildings = row.buildings }
        S.goods[row.region] = tribute.paid_goods(row.region)
    end
end

local function goods_of(region) return S.goods[region] end

local function current_model(force)
    refresh_stats(force)
    local rows = vassals.slot_rows(false)
    for _, row in ipairs(rows) do
        local stats = S.stats[row.region]
        if stats then row.families, row.buildings = stats.families, stats.buildings end
    end
    return view.build({ config = vassal_config, rows = rows, wiped = vassals.wiped_rows(), silver = silver_world.silver(),
                        today = vassal_world.current_day(), goods_of = goods_of, amount = tribute.amount_for })
end

---------------------------------------------------------------------------------------------
-- Widget writes (each one only when the value changes)
---------------------------------------------------------------------------------------------

local function set_text(name, text)
    local block = W.texts[name]
    if block == nil or W.shown[name] == text then return end
    W.shown[name] = text
    block:SetText(FText(text))
end

local function paint(name, colour_name, colour)
    local block = W.texts[name]
    if block == nil or W.painted[name] == colour_name then return end
    if isValid(block) then
        W.painted[name] = colour_name
        block:SetColorAndOpacity({ SpecifiedColor = colour, ColorUseRule = 0 })
    end
end

-- A colour change is safer than a visibility change for a Border (notes of change update-scenario-settings-window-style).
local function tint(name, colour_name, colour)
    local border = W.borders[name]
    if border == nil or W.tinted[name] == colour_name then return end
    if isValid(border) then
        W.tinted[name] = colour_name
        border:SetBrushColor(colour)
    end
end

local function set_dim(name, dimmed)
    local border = W.borders[name]
    if border == nil or W.dim[name] == dimmed then return end
    if isValid(border) then
        W.dim[name] = dimmed
        border:SetRenderOpacity(dimmed and config.dim_opacity or 1)
    end
end

local function set_button_visible(name, shown)
    local slot = W.buttons[name]
    if slot == nil or W.visible[name] == shown then return end
    W.visible[name] = shown
    pcall(clickhooks.set_visible, slot.handle, shown)
end

local function note_of(card)
    local note = W.notes[card.position]
    if note and os.clock() < note.until_clock then return note.text end
    return card.note
end

local function fill_stat_rows(card, key_card)
    local shown = ROWS_SHOWN[card.kind] or 0
    for row = 0, STAT_ROWS - 1 do
        local key = key_card .. "_" .. row
        local on = row < shown
        set_text("StatLabel" .. key, on and view.STAT_LABELS[row + 1] or "")
        set_text("StatValue" .. key, on and card.stats[row + 1] or "")
        tint("Diamond" .. key, on and "on" or "off", on and DIAMOND or CLEAR)
        tint("Line" .. key, on and "on" or "off", on and ROW_LINE or CLEAR)
    end
    paint("StatValue" .. key_card .. "_0", card.status, STATUS_COLOUR[card.status] or SOFT)
end

local function fill_policies(card, key_card)
    local is_vassal = card.kind == "vassal"
    set_text("PolicyLabel" .. key_card, is_vassal and "POLICY" or "")
    set_text("PolicyHint" .. key_card, is_vassal and card.policy_hint or "")
    for policy = 0, POLICIES - 1 do
        local key = key_card .. "_" .. policy
        local option = card.policies[policy + 1]
        set_text("PolicyText" .. key, option and option.text or "")
        paint("PolicyText" .. key, option and option.selected and "gold" or "grey", option and option.selected and GOLD or GREY)
        tint("Under" .. key, option and option.selected and "gold" or "clear", option and option.selected and GOLD or CLEAR)
        set_button_visible("PolicyButton" .. key, is_vassal)
    end
end

local function fill_restore(card, key_card)
    local restore = card.restore
    set_text("RestoreText" .. key_card, restore and restore.text or "")
    set_text("RestoreHint" .. key_card, restore and restore.hint or "")
    paint("RestoreText" .. key_card, restore and restore.enabled and "white" or "grey", restore and restore.enabled and WHITE or GREY)
    paint("RestoreHint" .. key_card, restore and restore.enabled and "soft" or "red", restore and restore.enabled and SOFT or RED)
    set_button_visible("RestoreButton" .. key_card, restore ~= nil)
end

local function fill_card(card)
    local key = tostring(card.position)
    set_text("CardRegion" .. key, card.title)
    set_text("CardLord" .. key, card.lord_line)
    set_text("NoteText" .. key, note_of(card))
    fill_stat_rows(card, key)
    fill_policies(card, key)
    fill_restore(card, key)
    set_dim("Card" .. key, card.dim)
    tint("Card" .. key, card.kind == "wiped" and "wiped" or "normal", card.kind == "wiped" and WIPED_BG or CARD_BG)
end

local function fill_header(model)
    set_text("TitleText", view.TITLE_TEXT)
    set_text("HeadLabel0", "Vassals:")
    set_text("HeadValue0", model.count_text)
    set_text("HeadLabel1", "Tribute each month:")
    set_text("HeadValue1", model.tribute_text)
    set_text("HeadLabel2", "Treasury:")
    set_text("HeadValue2", model.silver_text)
end

local function refresh(force)
    if not isValid(W.widget) then return false end
    local model = current_model(force)
    fill_header(model)
    for _, card in ipairs(model.cards) do fill_card(card) end
    return true
end

local function release_buttons()
    local handles = {}
    for _, slot in pairs(W.buttons) do handles[#handles + 1] = slot.handle end
    clickhooks.release(handles)
end

local function reset_window()
    release_buttons()
    W.widget, W.texts, W.borders, W.buttons = nil, {}, {}, {}
    W.shown, W.painted, W.tinted, W.visible, W.dim, W.notes = {}, {}, {}, {}, {}, {}
end

-- The click button keeps its hookable click but not its look: no box and no label (the widget text and underline show instead).
local function hide_button_look(handle)
    local ok, inner = pcall(function() return handle.widget.Button01 end)
    if ok and isValid(inner) then inner:SetBackgroundColor(CLEAR) end
    local text_ok, text_border = pcall(function() return handle.widget.Button01:GetContent():GetChildAt(1) end)
    if text_ok and isValid(text_border) then text_border:SetBrushColor(CLEAR) end
    if isValid(handle.text) then handle.text:SetColorAndOpacity({ SpecifiedColor = CLEAR, ColorUseRule = 0 }) end
end

local function on_open(made)
    W.widget = made
    W.opened_at, W.reapplied, W.notes = os.clock(), false, {}
    S.stats, S.goods, S.stats_at = {}, {}, nil
    W.texts = menu.find_named(made, "TextBlock", NAMES.texts)
    W.borders = menu.find_named(made, "Border", NAMES.borders)
    local button_borders = menu.find_named(made, "Border", NAMES.buttons)
    if W.texts.TitleText == nil then
        reset_window()
        return nil, "the text lines were not found in the widget"
    end
    local controller = FindFirstOf("PlayerController")
    W.buttons = {}
    local handles = {}
    for _, name in ipairs(NAMES.buttons) do
        if button_borders[name] == nil then
            reset_window()
            return nil, "button not found in the widget: " .. name
        end
        local handle, attach_problem = clickhooks.attach(button_borders[name], controller, { owner = W, value = name })
        if not handle then
            reset_window()
            return nil, attach_problem
        end
        W.buttons[name] = { handle = handle }
        handles[#handles + 1] = handle
    end
    local bound, bind_problem = clickhooks.bind_texts(handles)
    if not bound then
        reset_window()
        return nil, bind_problem
    end
    for _, handle in ipairs(handles) do hide_button_look(handle) end
    refresh(true)
    return true
end

menu.register({
    id = MENU_ID, label = "Vassals",
    class_path = "/Game/HarnessMod/WBP_Vassals.WBP_Vassals_C", package_path = "/Game/HarnessMod", asset_name = "WBP_Vassals",
    z_order = config.z_order, -- the widget is centred by its own anchors (make_vassals_widget.py), so there is no position
    on_open = on_open, on_close = reset_window,
})

---------------------------------------------------------------------------------------------
-- Clicks: both go through the existing named commands
---------------------------------------------------------------------------------------------

local function say(position, text)
    W.notes[position] = { text = text, until_clock = os.clock() + config.notice_s }
end

local function run_command(name, args)
    local commands = require("HarnessCommands")
    local answer = commands.dispatch(MOD_NAME .. "." .. name, args, MOD_NAME)
    if answer.ok then return true end
    -- The command layer writes "<command> refused: <reason>". The card shows only the reason.
    return nil, (tostring(answer.error):gsub("^%S+ refused: ", ""))
end

local function press_policy(card, policy_name)
    local ok, reason = run_command("vassals_set_policy", { slot = card.slot, policy = policy_name })
    if ok then W.notes[card.position] = nil else say(card.position, reason) end
    return ok
end

local function press_restore(card)
    if not card.restore.enabled then return nil, "not enough silver" end -- a disabled button ignores the click
    local ok, reason = run_command("vassals_restore", { region = card.region })
    if ok then W.notes[card.position] = nil else say(card.position, reason) end
    return ok
end

-- `name` is a button name: PolicyButton<card>_<policy> or RestoreButton<card>. Returns true when a command ran and was accepted.
local function press(name)
    local model = current_model(true)
    local card_text, policy_text = name:match("^PolicyButton(%d)_(%d)$")
    local result, why
    if card_text then
        local card = model.cards[tonumber(card_text) + 1]
        local policy_name = view.POLICIES[tonumber(policy_text) + 1]
        if card and card.kind == "vassal" and policy_name then
            W.presses = W.presses + 1
            result, why = press_policy(card, policy_name)
        end
    else
        local restore_text = name:match("^RestoreButton(%d)$")
        local card = restore_text and model.cards[tonumber(restore_text) + 1]
        if card and card.kind == "wiped" then
            W.presses = W.presses + 1
            result, why = press_restore(card)
        end
    end
    if result then W.clicks_done = W.clicks_done + 1 end
    refresh(true)
    return result, why
end

local function tick_window()
    if not is_open() then
        W.widget = nil
        return
    end
    for _, handle in ipairs(clickhooks.drain(W)) do
        press(handle.tag.value)
        if not is_open() then return end
    end
    local now = os.clock()
    -- A collapse that is set in the first refresh does not hold for some widgets (change update-liege-contracts-window-style):
    -- every value is written once more, 1.5 s after the open.
    if not W.reapplied and W.opened_at and now - W.opened_at >= 1.5 then
        W.reapplied, W.shown, W.painted, W.tinted, W.visible, W.dim = true, {}, {}, {}, {}, {}
        refresh()
    end
    if now - W.last_refresh >= config.refresh_ms / 1000 then
        W.last_refresh = now
        refresh()
    end
end

local function menu_state()
    local shown = {}
    for name, block in pairs(W.texts) do shown[name] = read(function() return block:GetText():ToString() end) end
    local buttons = {}
    for name, slot in pairs(W.buttons) do
        buttons[#buttons + 1] = { name = name, visibility = read(function() return slot.handle.widget:GetVisibility() end), shown = W.visible[name] }
    end
    local model = current_model(false)
    local wanted = { HeadValue0 = model.count_text, HeadValue1 = model.tribute_text, HeadValue2 = model.silver_text }
    for _, card in ipairs(model.cards) do
        local key = tostring(card.position)
        wanted["CardRegion" .. key], wanted["CardLord" .. key], wanted["NoteText" .. key] = card.title, card.lord_line, note_of(card)
        wanted["StatValue" .. key .. "_0"] = card.stats[1]
    end
    return { open = is_open(), in_viewport = is_open() and read(function() return W.widget:IsInViewport() end) or false,
             texts = shown, view = model, wanted_texts = wanted, buttons = buttons, presses = W.presses, clicks_done = W.clicks_done,
             painted = W.painted, tinted = W.tinted, visible = W.visible }
end

require("scheduler").every(TAG .. ".window", math.max(100, config.poll_ms), tick_window)

---------------------------------------------------------------------------------------------
-- Named commands
---------------------------------------------------------------------------------------------

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.vassals_menu_open", function() return menu.open(MENU_ID) end, {})
    commands.register("InvasionMod.vassals_menu_close", function()
        if is_open() then return menu.close() end
        return { ok = true }
    end, {})
    commands.register("InvasionMod.vassals_menu_state", menu_state, {})
    -- The values that the widget shows: the header and one card model for each slot.
    commands.register("InvasionMod.vassals_menu_view", function() return current_model(true) end, {})
    -- Test command: the same code as a click on a window button (`button` is a button name such as PolicyButton0_2 or RestoreButton1).
    -- A real mouse click needs a mouse device; this PC may have none.
    commands.register("InvasionMod.vassals_menu_press", function(args)
        if not is_open() then return nil, "the window is not open" end
        local ok, why = press(args.button)
        return { ok = true, accepted = ok == true, reason = why, presses = W.presses, clicks_done = W.clicks_done }
    end, { button = { type = "string", required = true } })
end

core.log.info(TAG, "feature vassals_menu loaded")
return { view = current_model, click = press, open = function() return menu.open(MENU_ID) end, close = menu.close }
