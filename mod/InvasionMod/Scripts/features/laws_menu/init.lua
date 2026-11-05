-- Feature laws_menu (change add-laws-menu, #563): the Laws menu. It lists the nine laws of the tech tree, and it is the one place where
-- the player enacts and revokes laws (the tech window only unlocks). Each action asks for a confirmation and uses one of the yearly
-- actions (1 enact and 1 revoke for each game year, refreshed at the start of spring).
-- The rules of the laws stay in feature tech_tree (path, node, slots). This feature adds: the yearly actions, the view, the dialog,
-- and the two entry points of the contracts change: laws_unlock(id, source) and laws_add_slot().
-- The menu is a pak widget (mod/InvasionMod/ue/make_laws_widget.py) on the base menu (core/menu.lua), built like the liege window:
-- fixed pools of controls, Lua fills them, and the clicks are hook events of click buttons (HarnessClickHooks, never Button.OnClicked:Add).
-- Rules: game objects are touched on the game thread only (the scheduler runs the jobs there).
local core = require("ManorCore")
local ModState = require("ModState")
local tech_tree = require("features.tech_tree.init")
local invasion = require("features.invasion.init")
local view = require("features.laws_menu.view")
local world = require("features.laws_menu.world")
local menu = require("core.menu")
local clickhooks = require("HarnessClickHooks")
local all_config = require("config")
local config = all_config.laws_menu

local TAG = "InvasionMod.laws_menu"
local SPRING = all_config.tech_tree.spring_season -- the clock of the tech picks: both refresh at the same start of spring

local state = ModState.open("invasion", "pawn") -- no version: the last feature that sets one wins, and this feature has no migration
state:register("laws_year_no", -1, "integer")   -- season counter of the last spring that was seen (-1: no look yet)
state:register("laws_enact_used", 0, "integer") -- enact actions used in this game year
state:register("laws_revoke_used", 0, "integer")

local S = { enacts = 0, revokes = 0, refused = 0 }
local filter = "all"   -- view state, not saved
local pending = nil    -- the open dialog: { kind = "enact" | "revoke", id = law id }

---------------------------------------------------------------------------------------------
-- The yearly actions
---------------------------------------------------------------------------------------------

-- The first look takes the counter (a game in any season starts with its actions). Each later start of spring gives them back.
local function year_step(info)
    local seen = state:get("laws_year_no")
    if seen < 0 then
        state:set("laws_year_no", info.no)
        return
    end
    if info.season ~= SPRING or info.no <= seen then return end
    state:set("laws_year_no", info.no) -- saved before the log line, so a load never refreshes twice
    state:set("laws_enact_used", 0)
    state:set("laws_revoke_used", 0)
    core.log.info(TAG, string.format("LAWS actions refreshed at spring no=%d", info.no))
end

local function refresh_year()
    if not state.loaded then return end
    local info = invasion.season_info()
    if info ~= nil then year_step(info) end
end

local function enact_left() return config.enacts_per_year - state:get("laws_enact_used") end
local function revoke_left() return config.revokes_per_year - state:get("laws_revoke_used") end

require("scheduler").every(TAG, math.max(100, config.year_poll_ms), refresh_year)

---------------------------------------------------------------------------------------------
-- The model of the menu
---------------------------------------------------------------------------------------------

local function days_to_refresh()
    local day = world.day_of_year()
    if day == nil then return nil end
    return (config.spring_start_day - day) % config.year_days
end

local function model(wanted_filter)
    return {
        tree = tech_tree.tree, path = tech_tree.path(), unlocked = tech_tree.unlocked_nodes(), granted = tech_tree.granted_laws(),
        source_of = tech_tree.law_source, enacted = tech_tree.enacted_laws(), slots = tech_tree.law_slots(),
        max_total = all_config.tech_tree.max_total_laws, enacts_per_year = config.enacts_per_year, revokes_per_year = config.revokes_per_year,
        enact_left = enact_left(), revoke_left = revoke_left(), days_to_refresh = days_to_refresh(), filter = wanted_filter or filter,
    }
end

local function current_view(wanted_filter) return view.build(model(wanted_filter)) end

local function card_of(id)
    for _, card in ipairs(current_view("all").cards) do
        if card.id == id then return card end
    end
    return nil
end

---------------------------------------------------------------------------------------------
-- Actions. A refused call changes nothing.
---------------------------------------------------------------------------------------------

-- The tech tree says "no free law place (1 in force of 1)"; the menu says what the player can do.
local function friendly(reason)
    if tostring(reason):find("^no free law place") then return view.SLOTS_FULL end
    return reason
end

local function enact(law_id)
    if not state.loaded then return nil, "the mod state is not loaded" end
    refresh_year()
    if enact_left() <= 0 then return nil, view.NO_ENACT end
    local ok, why = tech_tree.enact_law(law_id)
    if not ok then return nil, friendly(why) end
    state:set("laws_enact_used", state:get("laws_enact_used") + 1)
    S.enacts = S.enacts + 1
    core.log.info(TAG, string.format("LAWS enacted %s, enact actions left %d", law_id, enact_left()))
    return { kind = "enact", id = law_id, enact_left = enact_left(), revoke_left = revoke_left() }
end

local function revoke(law_id)
    if not state.loaded then return nil, "the mod state is not loaded" end
    refresh_year()
    if revoke_left() <= 0 then return nil, view.NO_REVOKE end
    local ok, why = tech_tree.repeal_law(law_id)
    if not ok then return nil, friendly(why) end
    state:set("laws_revoke_used", state:get("laws_revoke_used") + 1)
    S.revokes = S.revokes + 1
    core.log.info(TAG, string.format("LAWS revoked %s, revoke actions left %d", law_id, revoke_left()))
    return { kind = "revoke", id = law_id, enact_left = enact_left(), revoke_left = revoke_left() }
end

-- A click on Enact or Revoke opens the dialog. Nothing changes until the player confirms. Returns the dialog, or nil and a reason.
local function request(kind, law_id)
    if not state.loaded then return nil, "the mod state is not loaded" end
    refresh_year()
    local card = card_of(law_id)
    if card == nil then return nil, "unknown law '" .. tostring(law_id) .. "'" end
    if card.action ~= kind then return nil, string.format("'%s' cannot be %s now", card.name, kind == "enact" and "enacted" or "revoked") end
    if not card.enabled then return nil, card.hint end
    pending = { kind = kind, id = law_id }
    return view.dialog(kind, card)
end

local function confirm()
    if pending == nil then return nil, "no dialog is open" end
    local asked = pending
    pending = nil
    local act = asked.kind == "enact" and enact or revoke
    return act(asked.id)
end

local function cancel()
    local was_open = pending ~= nil
    pending = nil
    return was_open
end

local function set_filter(id)
    for _, entry in ipairs(view.FILTERS) do
        if entry.id == id then
            filter = id
            return true
        end
    end
    return nil, "unknown filter '" .. tostring(id) .. "'"
end

-- Entry points of the contracts change.
local function laws_unlock(law_id, source) return tech_tree.grant_law(law_id, source) end
local function laws_add_slot() return tech_tree.add_law_slot() end

---------------------------------------------------------------------------------------------
-- The widget: a cooked Widget Blueprint in the pak InvasionMod_P.pak (mod/InvasionMod/ue/make_laws_widget.py).
-- Fixed pools: nine law cards, three filter entries, one dialog. The text of a button is a text block of the widget; the click
-- button on top of it is invisible (as in the scenario settings window). A hidden entry has empty texts and clear brushes: a change
-- of colour and text is safer than a change of visibility (notes of change update-scenario-settings-window-style).
---------------------------------------------------------------------------------------------
local isValid, read = core.isValid, core.read

local CARDS, EFFECT_LINES = 9, 3
local function linear(r, g, b, a) return { R = r ^ 2.2, G = g ^ 2.2, B = b ^ 2.2, A = a or 1 } end
local TONES = {
    gain = linear(0.62, 0.70, 0.48), loss = linear(0.79, 0.54, 0.47), neutral = linear(0.79, 0.76, 0.69), gold = linear(0.91, 0.78, 0.48),
    warn = linear(0.82, 0.63, 0.31), bad = linear(0.69, 0.44, 0.36), muted = linear(0.56, 0.53, 0.47), soft = linear(0.66, 0.63, 0.56),
    white = linear(0.95, 0.93, 0.89), grey = linear(0.47, 0.44, 0.415),
}
local CLEAR = { R = 0, G = 0, B = 0, A = 0 }
local CARD_FILL = { force = linear(0.235, 0.196, 0.118, 0.55), open = linear(0.078, 0.075, 0.067, 0.55), locked = linear(0.078, 0.075, 0.067, 0.3) }
local CARD_TOP = { force = linear(0.91, 0.78, 0.48), open = linear(0.29, 0.275, 0.24), locked = linear(0.2, 0.19, 0.17) }
local SHADE, PANEL = linear(0.02, 0.02, 0.016, 0.72), linear(0.215, 0.205, 0.185, 0.98)
local ACT_UNDER = linear(0.29, 0.275, 0.24)
local RULE = linear(0.61, 0.52, 0.33)
local LOCKED_OPACITY = 0.62

local NAMES = { texts = { "TitleText", "RefreshText", "NoticeText", "HdrSlotsValue", "HdrSlotsMax", "HdrEnactValue", "HdrRevokeValue", "HdrUnlockValue",
    "DlgTitle", "DlgQuestion", "DlgCost", "DlgCancelText", "DlgConfirmText" },
    borders = { "DlgShade", "DlgPanel", "DlgRule", "DlgConfirmUnder" }, buttons = { "DlgCancelButton", "DlgConfirmButton" } }
for index = 0, #view.FILTERS - 1 do
    NAMES.texts[#NAMES.texts + 1] = "FilterText" .. index
    NAMES.borders[#NAMES.borders + 1] = "FilterUnder" .. index
    NAMES.buttons[#NAMES.buttons + 1] = "FilterButton" .. index
end
for line = 0, EFFECT_LINES - 1 do NAMES.texts[#NAMES.texts + 1] = "DlgEff" .. line end
for card = 0, CARDS - 1 do
    for _, prefix in ipairs({ "NameText", "StatusText", "SourceText", "HintText", "ActText" }) do NAMES.texts[#NAMES.texts + 1] = prefix .. card end
    for line = 0, EFFECT_LINES - 1 do NAMES.texts[#NAMES.texts + 1] = "EffText" .. card .. "_" .. line end
    for _, prefix in ipairs({ "Card", "CardTop", "ActUnder" }) do NAMES.borders[#NAMES.borders + 1] = prefix .. card end
    NAMES.buttons[#NAMES.buttons + 1] = "ActButton" .. card
end

local W = { widget = nil, texts = {}, borders = {}, buttons = {}, shown = {}, tone = {}, brush = {}, dim = {}, labels = {}, visible = {},
            card_ids = {}, last_refresh = 0, notice = nil, notice_until = 0, presses = 0 }

local function is_open() return menu.is_open("laws") end

local function set_text(name, text)
    local block = W.texts[name]
    if block == nil or W.shown[name] == text then return end
    W.shown[name] = text
    block:SetText(FText(text))
end

local function set_tone(name, tone)
    local block = W.texts[name]
    if block == nil or W.tone[name] == tone then return end
    if isValid(block) then
        W.tone[name] = tone
        block:SetColorAndOpacity({ SpecifiedColor = TONES[tone] or CLEAR, ColorUseRule = 0 })
    end
end

local function set_brush(name, rgba, key)
    local border = W.borders[name]
    if border == nil or W.brush[name] == key then return end
    if isValid(border) then
        W.brush[name] = key
        border:SetBrushColor(rgba)
    end
end

local function set_dim(name, dimmed)
    local border = W.borders[name]
    if border == nil or W.dim[name] == dimmed then return end
    if isValid(border) then
        W.dim[name] = dimmed
        border:SetRenderOpacity(dimmed and LOCKED_OPACITY or 1)
    end
end

local function set_button_visible(name, shown)
    local slot = W.buttons[name]
    if slot == nil or W.visible[name] == shown then return end
    W.visible[name] = shown
    pcall(clickhooks.set_visible, slot.handle, shown)
end

local function text_and_tone(name, text, tone)
    set_text(name, text)
    if text ~= "" then set_tone(name, tone) end
end

local function fill_card(index, card, dialog_open)
    local key = tostring(index)
    if card == nil then
        for _, prefix in ipairs({ "NameText", "StatusText", "SourceText", "HintText", "ActText" }) do set_text(prefix .. key, "") end
        for line = 0, EFFECT_LINES - 1 do set_text("EffText" .. key .. "_" .. line, "") end
        for _, prefix in ipairs({ "Card", "CardTop", "ActUnder" }) do set_brush(prefix .. key, CLEAR, "clear") end
        set_dim("Card" .. key, false)
        set_button_visible("ActButton" .. key, false)
        W.card_ids[index] = nil
        return
    end
    W.card_ids[index] = card.id
    local look = card.in_force and "force" or (card.unlocked and "open" or "locked")
    set_brush("Card" .. key, CARD_FILL[look], look)
    set_brush("CardTop" .. key, CARD_TOP[look], look)
    set_dim("Card" .. key, not card.unlocked)
    text_and_tone("NameText" .. key, card.name, "white")
    text_and_tone("StatusText" .. key, string.upper(card.status), card.status_tone)
    text_and_tone("SourceText" .. key, card.source, "muted")
    for line = 0, EFFECT_LINES - 1 do
        local effect = card.effects[line + 1]
        text_and_tone("EffText" .. key .. "_" .. line, effect and effect.text or "", effect and effect.tone or "neutral")
    end
    text_and_tone("HintText" .. key, card.hint, card.hint_tone)
    text_and_tone("ActText" .. key, card.button, card.enabled and "white" or "grey")
    set_brush("ActUnder" .. key, card.action and ACT_UNDER or CLEAR, card.action and "line" or "clear")
    set_button_visible("ActButton" .. key, card.action ~= nil and card.enabled and not dialog_open)
end

local function fill_dialog(dialog)
    local shown = dialog ~= nil
    set_brush("DlgShade", shown and SHADE or CLEAR, shown and "on" or "off")
    set_brush("DlgPanel", shown and PANEL or CLEAR, shown and "on" or "off")
    set_brush("DlgRule", shown and RULE or CLEAR, shown and "on" or "off")
    set_brush("DlgConfirmUnder", shown and TONES.gold or CLEAR, shown and "on" or "off")
    text_and_tone("DlgTitle", shown and string.upper(dialog.title) or "", "white")
    text_and_tone("DlgQuestion", shown and dialog.question or "", "white")
    for line = 0, EFFECT_LINES - 1 do
        local effect = shown and dialog.effects[line + 1] or nil
        text_and_tone("DlgEff" .. line, effect and effect.text or "", effect and effect.tone or "neutral")
    end
    text_and_tone("DlgCost", shown and dialog.cost or "", "warn")
    text_and_tone("DlgCancelText", shown and dialog.cancel or "", "soft")
    text_and_tone("DlgConfirmText", shown and dialog.confirm or "", "white")
    set_button_visible("DlgCancelButton", shown)
    set_button_visible("DlgConfirmButton", shown)
end

local function notice_line()
    if W.notice and os.clock() < W.notice_until then return W.notice end
    return ""
end

local function dialog_model()
    if pending == nil then return nil end
    local card = card_of(pending.id)
    if card == nil then return nil end
    return view.dialog(pending.kind, card)
end

local function refresh()
    if not isValid(W.widget) then return false end
    local current = current_view()
    local header = current.header
    set_text("TitleText", view.TITLE)
    text_and_tone("HdrSlotsValue", header.slots_text, header.slots_tone)
    text_and_tone("HdrSlotsMax", header.max_text, "muted")
    text_and_tone("HdrEnactValue", header.enact_text, header.enact_tone)
    text_and_tone("HdrRevokeValue", header.revoke_text, header.revoke_tone)
    text_and_tone("HdrUnlockValue", header.unlocked_text, "gold")
    text_and_tone("RefreshText", header.refresh_text, "muted")
    text_and_tone("NoticeText", notice_line(), "gold")
    for index, entry in ipairs(view.FILTERS) do
        local selected = entry.id == filter
        set_text("FilterText" .. (index - 1), entry.text)
        set_tone("FilterText" .. (index - 1), selected and "gold" or "muted")
        set_brush("FilterUnder" .. (index - 1), selected and TONES.gold or CLEAR, selected and "on" or "off")
        set_button_visible("FilterButton" .. (index - 1), pending == nil)
    end
    local dialog = dialog_model()
    for index = 0, CARDS - 1 do fill_card(index, current.cards[index + 1], dialog ~= nil) end
    fill_dialog(dialog)
    return true
end

local function release_buttons()
    local handles = {}
    for _, slot in pairs(W.buttons) do handles[#handles + 1] = slot.handle end
    clickhooks.release(handles)
end

local function reset_window()
    release_buttons()
    pending = nil
    W.widget, W.texts, W.borders, W.buttons = nil, {}, {}, {}
    W.shown, W.tone, W.brush, W.dim, W.visible, W.card_ids = {}, {}, {}, {}, {}, {}
end

-- The click button keeps its hookable click but not its look: no box and no label (the widget text shows instead).
local function hide_button_look(handle)
    local ok, inner = pcall(function() return handle.widget.Button01 end)
    if ok and isValid(inner) then inner:SetBackgroundColor(CLEAR) end
    local text_ok, text_border = pcall(function() return handle.widget.Button01:GetContent():GetChildAt(1) end)
    if text_ok and isValid(text_border) then text_border:SetBrushColor(CLEAR) end
    if isValid(handle.text) then handle.text:SetColorAndOpacity({ SpecifiedColor = CLEAR, ColorUseRule = 0 }) end
end

local function button_tag(name)
    local card = name:match("^ActButton(%d)$")
    if card then return { owner = W, action = "card", index = tonumber(card) } end
    local entry = name:match("^FilterButton(%d)$")
    if entry then return { owner = W, action = "filter", id = view.FILTERS[tonumber(entry) + 1].id } end
    if name == "DlgCancelButton" then return { owner = W, action = "cancel" } end
    return { owner = W, action = "confirm" }
end

local function on_open(made)
    W.widget = made
    W.notice = nil
    pending = nil
    W.texts = menu.find_named(made, "TextBlock", NAMES.texts)
    W.borders = menu.find_named(made, "Border", NAMES.borders)
    local button_borders = menu.find_named(made, "Border", NAMES.buttons)
    if W.texts.TitleText == nil or W.texts.HdrSlotsValue == nil or W.texts.DlgQuestion == nil then
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
        local handle, attach_problem = clickhooks.attach(button_borders[name], controller, button_tag(name))
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
    refresh()
    return true
end

menu.register({
    id = "laws", label = "Laws",
    class_path = "/Game/HarnessMod/WBP_Laws.WBP_Laws_C", package_path = "/Game/HarnessMod", asset_name = "WBP_Laws",
    z_order = config.z_order, -- the widget is centred by its own anchors (make_laws_widget.py), so there is no position
    on_open = on_open, on_close = reset_window,
    -- Esc closes the dialog first. A second Esc closes the menu.
    on_esc = function()
        if pending == nil then return false end
        cancel()
        refresh()
        return true
    end,
})

local function say(text)
    W.notice, W.notice_until = text, os.clock() + config.notice_s
end

-- The click handlers. The press command calls the same code, so a test needs no mouse.
local function press(action, argument)
    W.presses = W.presses + 1
    if action == "filter" then
        local ok, why = set_filter(argument)
        refresh()
        return ok, why
    end
    if action == "enact" or action == "revoke" then
        W.notice = nil
        local dialog, why = request(action, argument)
        if dialog == nil then say(why); refresh(); return nil, why end
        refresh()
        return true
    end
    if action == "cancel" then
        W.notice = nil
        cancel()
        refresh()
        return true
    end
    if action == "confirm" then
        local result, why = confirm()
        if result == nil then
            S.refused = S.refused + 1
            say(why)
            refresh()
            return nil, why
        end
        W.notice = nil
        refresh()
        return result
    end
    return nil, "action must be filter, enact, revoke, confirm or cancel"
end

local function on_click(tag)
    if tag.action == "card" then
        local id = W.card_ids[tag.index + 1]
        if id == nil then return end
        local card = card_of(id)
        if card == nil or card.action == nil then return end
        return press(card.action, id)
    end
    if tag.action == "filter" then return press("filter", tag.id) end
    return press(tag.action)
end

local function tick_window()
    if not is_open() then
        W.widget = nil
        return
    end
    for _, handle in ipairs(clickhooks.drain(W)) do
        core.log.try(TAG, on_click, handle.tag)
        if not is_open() then return end
    end
    local now = os.clock()
    if now - W.last_refresh >= config.refresh_ms / 1000 then
        W.last_refresh = now
        refresh()
    end
end

require("scheduler").every(TAG .. ".window", math.max(100, config.poll_ms), tick_window)

---------------------------------------------------------------------------------------------
-- Named commands
---------------------------------------------------------------------------------------------

local function menu_state()
    local texts = {}
    for name, block in pairs(W.texts) do texts[name] = read(function() return block:GetText():ToString() end) end
    local current = current_view()
    return {
        open = is_open(), in_viewport = is_open() and isValid(W.widget) and read(function() return W.widget:IsInViewport() end) or false,
        filter = filter, header = current.header, cards = current.cards, total = current.total, unlocked_count = current.unlocked_count,
        in_force = current.in_force, slots = current.slots, over_cap = current.over_cap, dialog = dialog_model(),
        enact_left = enact_left(), revoke_left = revoke_left(), laws = tech_tree.enacted_laws(), extra_slots = tech_tree.state:get("law_extra_slots"),
        granted = tech_tree.granted_laws(), texts = texts, presses = W.presses, enacts = S.enacts, revokes = S.revokes, notice = notice_line(),
        year_no = state:get("laws_year_no"), days_to_refresh = days_to_refresh(),
    }
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.laws_menu_open", function() return menu.open("laws") end, {})
    commands.register("InvasionMod.laws_menu_close", function()
        if is_open() then return menu.close() end
        return { ok = true }
    end, {})
    commands.register("InvasionMod.laws_menu_state", menu_state, {})
    -- Test command: the same code as a click (needs the open menu). `action` is filter (with `filter`), enact or revoke (with `id`: the
    -- dialog opens), confirm or cancel (the dialog buttons).
    commands.register("InvasionMod.laws_menu_press", function(args)
        if not is_open() then return nil, "the menu is not open" end
        local argument = args.id
        if args.action == "filter" then argument = args.filter end
        local result, why = press(args.action, argument)
        if result == nil then return nil, why end
        return menu_state()
    end, { action = { type = "string", required = true }, id = { type = "string" }, filter = { type = "string" } })
    commands.register("InvasionMod.laws_unlock", function(args)
        local result, why = laws_unlock(args.id, args.source)
        if result == nil then return nil, why end
        return result
    end, { id = { type = "string", required = true }, source = { type = "string", maxLength = 200 } })
    commands.register("InvasionMod.laws_add_slot", function() return laws_add_slot() end, {})
end

core.log.info(TAG, "feature laws_menu loaded")
return { state = state, laws_unlock = laws_unlock, laws_add_slot = laws_add_slot, enact = enact, revoke = revoke, request = request, confirm = confirm,
         cancel = cancel, view = current_view, open = function() return menu.open("laws") end, close = menu.close }
