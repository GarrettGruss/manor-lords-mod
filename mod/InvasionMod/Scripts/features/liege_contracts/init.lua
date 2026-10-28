-- Feature liege_contracts (change update-liege-tribute-to-contracts, #505): the liege offers three contracts at each start of spring.
-- The player picks one. The contracts are data (data/liege_contracts/contracts.json). A completed contract pays rewards at once; a
-- contract that is not complete when winter begins costs influence (config fail_penalty). The state is saved with ModState.
-- The liege window is a pak widget (mod/InvasionMod/ue/make_liege_widget.py) built on the base menu (core/menu.lua).
-- Rules: game objects are touched on the game thread only (the scheduler runs the jobs there).
local core = require("ManorCore")
local ModState = require("ModState")
local json = require("HarnessJson")
local loader = require("features.liege_contracts.loader")
local rules = require("features.liege_contracts.rules")
local view = require("features.liege_contracts.view")
local world = require("features.liege_contracts.world")
local liege = require("features.liege_influence.init")
local invasion = require("features.invasion.init")
local raid_behavior = require("features.raid_behavior.init")
local bandits = require("features.bandits.init")
local all_config = require("config")
local config = all_config.liege_contracts
local menu_config = all_config.liege_influence

local TAG = "InvasionMod.liege_contracts"
local STATE_VERSION = 2
local SPRING = config.spring_season -- the same value as tech_tree.spring_season (notes/season-values.md); an own key so that a test of one feature does not change the other
local WINTER = config.winter_season

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("contracts_spring_no", -1, "integer") -- season counter of the last spring that was seen (-1: no look yet)
state:register("contracts_offer", "", "string")      -- ids of the offered contracts, dot separated
state:register("contracts_active", "", "string")     -- id of the active contract, empty for none
state:register("contracts_start_day", -1, "integer") -- game day of the pick
state:register("contracts_baseline", "", "string")   -- numbers taken at the pick: o<index>-<value>, and s-<season counter>
state:register("contracts_progress", "", "string")   -- progress of each objective: o<index>-<value>
state:register("contracts_done", 0, "integer")
state:register("contracts_failed", 0, "integer")

local table_path = world.data_path(config.data_file)
local contracts = loader.load_file(table_path, json.decode)

local S = { failed_rewards = 0, override = {}, last_message = nil, picks = 0, completes = 0, last_offer = nil }

---------------------------------------------------------------------------------------------
-- State access
---------------------------------------------------------------------------------------------

local function offer_ids() return rules.split_ids(state:get("contracts_offer")) end

local function active_contract()
    local id = state:get("contracts_active")
    if id == "" then return nil end
    return contracts.by_id[id], id
end

local function baseline() return rules.decode_numbers(state:get("contracts_baseline")) end
local function progress() return rules.decode_numbers(state:get("contracts_progress")) end

-- Write only a change: a Tags write at each poll was a crash risk in real runs.
local function set_if_changed(key, value)
    if state:get(key) ~= value then state:set(key, value) end
end

local function reset_active()
    state:set("contracts_active", "")
    state:set("contracts_start_day", -1)
    state:set("contracts_baseline", "")
    state:set("contracts_progress", "")
    S.override = {}
end

---------------------------------------------------------------------------------------------
-- Progress
---------------------------------------------------------------------------------------------

-- One reading of the world for the objectives of a contract.
local function read_world(contract)
    local reading = { stock = {}, buildings = {} }
    for _, objective in ipairs(contract.objectives) do
        if objective.type == "deliver_goods" then reading.stock[objective.good] = world.stock(objective.good)
        elseif objective.type == "build_count" then reading.buildings[objective.building_type] = world.building_count(objective.building_type)
        elseif objective.type == "kill_raiders" then reading.kills = raid_behavior.raiders_killed()
        elseif objective.type == "raise_militia_squads" then reading.squads = world.squad_count()
        elseif objective.type == "hold_public_order" then
            local terms = bandits.order_terms()
            reading.order = terms and terms.order
        end
    end
    reading.day = world.current_day()
    return reading
end

-- The baseline numbers for a new pick.
local function make_baseline(contract, reading, season_no)
    local values = {}
    for index, objective in ipairs(contract.objectives) do
        if objective.type == "build_count" then values[index] = reading.buildings[objective.building_type] or 0
        elseif objective.type == "kill_raiders" then values[index] = reading.kills or 0
        elseif objective.type == "hold_public_order" then values[index] = reading.day or 0 -- the last day that was counted
        else values[index] = 0 end
    end
    values.s = season_no
    return values
end

-- Compute the progress of the active contract, save a change and return the progress table (1-based).
local function update_progress(contract)
    local reading = read_world(contract)
    local base, old, new = baseline(), progress(), {}
    for index, objective in ipairs(contract.objectives) do
        local value
        if S.override[index] ~= nil then
            value = S.override[index]
        elseif objective.type == "kill_raiders" then
            value, S.kill_seen = rules.add_kills(old[index] or 0, S.kill_seen, reading.kills)
        elseif objective.type == "hold_public_order" then
            local last_day = base[index] or reading.day
            value, base[index] = rules.hold_step(old[index] or 0, last_day, reading.day, reading.order, objective.min)
        else
            value = rules.measure(objective, reading, base[index]) or old[index] or 0
        end
        new[index] = value
    end
    set_if_changed("contracts_baseline", rules.encode_numbers(base, { "s" }))
    set_if_changed("contracts_progress", rules.encode_numbers(new))
    return new
end

---------------------------------------------------------------------------------------------
-- Offer, pick, reward, complete, fail
---------------------------------------------------------------------------------------------

local function make_offer(ids)
    local chosen = ids
    if chosen == nil then
        local drawn, why = rules.draw(contracts.contracts, contracts.offer_size, math.random)
        if drawn == nil then return nil, why end
        chosen = drawn
    end
    state:set("contracts_offer", rules.join_ids(chosen))
    return chosen
end

local function pick(id)
    local refusal = rules.pick_refusal(offer_ids(), state:get("contracts_active"), id)
    if refusal then
        core.log.warn(TAG, "LIEGE_CONTRACTS pick refused: " .. refusal)
        return nil, refusal
    end
    local contract = contracts.by_id[id]
    local info = invasion.season_info()
    local reading = read_world(contract)
    local day = reading.day or world.current_day() or 0
    -- Saved before the log. The offer is gone: the other contracts are discarded. The window of this session still shows them as discarded.
    S.last_offer = offer_ids()
    S.kill_seen = reading.kills
    state:set("contracts_active", id)
    state:set("contracts_start_day", day)
    state:set("contracts_baseline", rules.encode_numbers(make_baseline(contract, reading, info and info.no), { "s" }))
    state:set("contracts_progress", "")
    state:set("contracts_offer", "")
    S.override = {}
    S.picks = S.picks + 1
    core.log.info(TAG, string.format("LIEGE_CONTRACTS picked %s on day %d", id, day))
    update_progress(contract)
    return { id = id, name = contract.name, start_day = day }
end

local function fail_reward(reward, why)
    S.failed_rewards = S.failed_rewards + 1
    core.log.warn(TAG, string.format("LIEGE_CONTRACTS reward %s failed: %s", reward.type, tostring(why)))
end

local function tech_picks_state_exists()
    return (pcall(function() return state:get("tech_picks_earned") end))
end

-- Pays one reward. A failure is logged and counted; it does not stop the other rewards.
local function pay_reward(reward)
    local kind = reward.type
    if kind == "influence" then
        liege.change_influence(reward.amount)
    elseif kind == "silver" then
        local ok, why = liege.add_silver(reward.amount)
        if not ok then return fail_reward(reward, why) end
    elseif kind == "goods" then
        local ok, why = world.add_goods(reward.good, reward.amount)
        if not ok then return fail_reward(reward, why) end
    elseif kind == "public_order" then
        local ok, why = pcall(bandits.adjust_order, reward.amount)
        if not ok then return fail_reward(reward, why) end
    elseif kind == "tech_pick" then
        -- The picks belong to the tech tree (change update-tech-tree-yearly-picks, #499).
        if not tech_picks_state_exists() then return fail_reward(reward, "the tech tree has no pick state (change update-tech-tree-yearly-picks is not built)") end
        -- -1 means the start pick was not given yet: keep it (the tech tree gives it when the picks start).
        local earned = state:get("tech_picks_earned")
        if earned < 0 then earned = (all_config.tech_tree and all_config.tech_tree.initial_picks) or 0 end
        state:set("tech_picks_earned", earned + reward.amount)
    end
end

-- Take the goods of the deliver_goods objectives. On a shortage the units taken are put back and the call is refused.
local function take_goods(contract)
    local taken = {}
    for _, objective in ipairs(contract.objectives) do
        if objective.type == "deliver_goods" then
            local got, why = world.take_goods(objective.good, objective.amount)
            if got ~= nil and got > 0 then taken[#taken + 1] = { good = objective.good, amount = got } end
            if got == nil or got < objective.amount then
                for _, row in ipairs(taken) do world.add_goods(row.good, row.amount) end
                return nil, string.format("only %d of %d units of goods %d could be taken from the stores%s", got or 0, objective.amount, objective.good,
                    why and (": " .. tostring(why)) or "")
            end
        end
    end
    return true
end

-- Completes the active contract. `automatic`: the deadline came and the objectives were met (no click).
local function complete(automatic)
    local contract, id = active_contract()
    if contract == nil then return nil, "no contract is active" end
    local current = update_progress(contract)
    local short = rules.missing(contract.objectives, current)
    if short then
        local reason = string.format("objective %d is short by %d", short.index, short.missing)
        core.log.warn(TAG, "LIEGE_CONTRACTS complete refused: " .. reason)
        return nil, reason, short
    end
    local ok, why = take_goods(contract)
    if not ok then
        core.log.warn(TAG, "LIEGE_CONTRACTS complete refused: " .. why)
        return nil, why
    end
    local failed_before = S.failed_rewards
    for _, reward in ipairs(contract.rewards) do core.log.try(TAG, pay_reward, reward) end
    state:set("contracts_done", state:get("contracts_done") + 1)
    reset_active()
    S.completes = S.completes + 1
    local result = { id = id, name = contract.name, failed_rewards = S.failed_rewards - failed_before, automatic = automatic == true }
    core.log.info(TAG, string.format("LIEGE_CONTRACTS completed %s failed_rewards=%d", id, result.failed_rewards))
    return result
end

local function fail_active(why)
    local contract, id = active_contract()
    if contract == nil then return end
    local before = state:get("liege_influence")
    local after = liege.change_influence(rules.after_penalty(before, config.fail_penalty) - before)
    state:set("contracts_failed", state:get("contracts_failed") + 1)
    reset_active()
    core.log.info(TAG, string.format("LIEGE_CONTRACTS failed %s (%s): influence %s -> %s", id, why, tostring(before), tostring(after)))
end

---------------------------------------------------------------------------------------------
-- The tick
---------------------------------------------------------------------------------------------

-- Spring: one offer for each spring counter value. The first look only takes the counter, so a new game or a save makes no offer.
local function yearly_step(info)
    local seen = state:get("contracts_spring_no")
    if seen < 0 then
        state:set("contracts_spring_no", info.no)
        return
    end
    if info.season ~= SPRING or info.no <= seen then return end
    state:set("contracts_spring_no", info.no) -- saved before the draw and the log, so a load never draws twice
    local dropped = offer_ids()
    local ids, why = make_offer(nil)
    if ids == nil then return core.log.error(TAG, "LIEGE_CONTRACTS draw failed: " .. tostring(why)) end
    core.log.info(TAG, string.format("LIEGE_CONTRACTS spring offer no=%d ids=%s dropped=%s", info.no, table.concat(ids, ","), table.concat(dropped, ",")))
end

local function deadline_step(info)
    local contract, id = active_contract()
    if state:get("contracts_active") ~= "" and contract == nil then
        core.log.warn(TAG, "LIEGE_CONTRACTS the active contract '" .. state:get("contracts_active") .. "' is not in the table: dropped without a penalty")
        reset_active()
        return
    end
    if contract == nil then return end
    local current = update_progress(contract)
    local picked = { day = state:get("contracts_start_day"), season_no = baseline().s }
    local now = { day = world.current_day(), season = info and info.season, season_no = info and info.no }
    if not rules.is_due(contract.duration, picked, now, WINTER) then return end
    if rules.is_complete(contract.objectives, current) then
        local result, why = complete(true)
        if result == nil then fail_active("deadline, objectives met but " .. tostring(why)) end
        return
    end
    fail_active("deadline")
end

local function tick()
    local info = invasion.season_info()
    if info ~= nil then yearly_step(info) end
    deadline_step(info)
end

-- A catch-up call for the window and the commands: no new tick, only the progress.
local function refresh_progress()
    local contract = active_contract()
    if contract then return update_progress(contract) end
    return {}
end

require("scheduler").every(TAG, math.max(100, config.poll_ms), tick)

---------------------------------------------------------------------------------------------
-- Views (the window and the state command)
---------------------------------------------------------------------------------------------

local function deadline_view(contract)
    if contract.duration == "winter_start" then return { kind = "winter_start" } end
    local start = state:get("contracts_start_day")
    local day = world.current_day()
    local left = (day and start >= 0) and (start + contract.duration - day) or contract.duration
    return { kind = "days", left = left, day = start + contract.duration }
end

local function window_view()
    local influence = math.floor((state:get("liege_influence") or 0) * 100 + 0.5) / 100
    local result = {
        influence_text = string.format("Influence: %g", influence),
        silver_text = string.format("Silver: %d", liege.silver() or 0),
        cards = {}, active = nil, empty_text = nil,
    }
    local contract = active_contract()
    if contract then
        local current = progress()
        local lines = view.active_lines(contract, current)
        result.active = { id = contract.id, name = contract.name, lines = lines, days_text = view.days_text(deadline_view(contract)),
                          complete = rules.is_complete(contract.objectives, current) }
        -- The cards of the pick stay on the window as "Active" and "Discarded" (only in the session of the pick).
        local picked_here = false
        for _, id in ipairs(S.last_offer or {}) do
            if id == contract.id then picked_here = true end
        end
        if picked_here then
            for _, id in ipairs(S.last_offer) do
                local offered = contracts.by_id[id]
                if offered then
                    local card = view.card(offered, contracts.items, config.fail_penalty)
                    card.state = id == contract.id and "Active" or "Discarded"
                    result.cards[#result.cards + 1] = card
                end
            end
        end
    else
        for _, id in ipairs(offer_ids()) do
            local offered = contracts.by_id[id]
            if offered then result.cards[#result.cards + 1] = view.card(offered, contracts.items, config.fail_penalty) end
        end
        if #result.cards == 0 then
            result.empty_text = "The liege sends new contracts at the start of spring."
        end
    end
    return result
end

local function command_state()
    local contract, id = active_contract()
    local active
    if contract then
        local current = progress()
        local rows = {}
        for index, objective in ipairs(contract.objectives) do
            rows[#rows + 1] = { index = index, type = objective.type, progress = current[index] or 0, target = rules.target(objective) }
        end
        active = { id = id, name = contract.name, start_day = state:get("contracts_start_day"), objectives = rows,
                   complete = rules.is_complete(contract.objectives, current), deadline = deadline_view(contract) }
    end
    local info = invasion.season_info()
    return { offer = offer_ids(), active = active, done = state:get("contracts_done"), failed = state:get("contracts_failed"),
             failed_rewards = S.failed_rewards, spring_no = state:get("contracts_spring_no"), season = info and info.season, season_no = info and info.no,
             influence = state:get("liege_influence"), silver = liege.silver(), picks = S.picks, completes = S.completes,
             fail_penalty = config.fail_penalty, contract_count = #contracts.contracts }
end

---------------------------------------------------------------------------------------------
-- The window: a cooked Widget Blueprint in the pak InvasionMod_P.pak (mod/InvasionMod/ue/make_liege_widget.py).
-- Fixed pools of controls; Lua fills, shows and hides them. Lua puts a click button into each button Border (HarnessClickHooks);
-- a click is a hook event, not a poll (spec 34). No Button.OnClicked:Add on a run-time button (#308).
---------------------------------------------------------------------------------------------
local menu = require("core.menu")
local clickhooks = require("HarnessClickHooks")
local isValid, read = core.isValid, core.read

local MENU_ID = "liege"
local CARDS, OBJ_ITEMS, REW_ITEMS = 3, 2, 3
local COLLAPSED, VISIBLE = 1, 0 -- ESlateVisibility
local NAMES = {
    texts = { "TitleText", "InfluenceText", "SilverText", "EmptyText", "FooterText", "ArmsInfoText", "ActiveName", "ActiveLine0", "ActiveLine1", "ActiveDays" },
    borders = { "ActivePanel" },
    buttons = { "PickButton0", "PickButton1", "PickButton2", "CompleteButton", "ArmsButton", "CloseButton" },
}
for card = 0, CARDS - 1 do
    for _, prefix in ipairs({ "CardName", "CardQuote", "CardPenalty", "CardState" }) do NAMES.texts[#NAMES.texts + 1] = prefix .. card end
    NAMES.borders[#NAMES.borders + 1] = "Card" .. card
    for item = 0, OBJ_ITEMS - 1 do
        for _, prefix in ipairs({ "ObjIcon", "ObjText" }) do NAMES.texts[#NAMES.texts + 1] = prefix .. card .. "_" .. item end
        NAMES.borders[#NAMES.borders + 1] = "ObjItem" .. card .. "_" .. item
    end
    for item = 0, REW_ITEMS - 1 do
        for _, prefix in ipairs({ "RewIcon", "RewText" }) do NAMES.texts[#NAMES.texts + 1] = prefix .. card .. "_" .. item end
        NAMES.borders[#NAMES.borders + 1] = "RewItem" .. card .. "_" .. item
    end
end

local W = { widget = nil, texts = {}, borders = {}, buttons = {}, shown = {}, visible = {}, tooltips = {}, last_refresh = 0, last_error = nil, arms_label = nil, arms_disabled = nil }

local function is_open() return menu.is_open(MENU_ID) end

local function set_text(name, text)
    local block = W.texts[name]
    if block == nil or W.shown[name] == text then return end
    W.shown[name] = text
    block:SetText(FText(text))
end

local function set_visible(name, shown)
    local border = W.borders[name]
    if border == nil or W.visible[name] == shown then return end
    W.visible[name] = shown
    border:SetVisibility(shown and VISIBLE or COLLAPSED)
end

local function set_tooltip(name, text)
    local border = W.borders[name]
    if border == nil or W.tooltips[name] == text then return end
    local ok = pcall(function() border:SetToolTipText(FText(text)) end)
    if ok then W.tooltips[name] = text end
end

local function set_button_visible(name, shown)
    local slot = W.buttons[name]
    if slot == nil or W.visible[name] == shown then return end
    W.visible[name] = shown
    pcall(clickhooks.set_visible, slot.handle, shown)
end

-- Disabled look: a grey tint of the click button (SetColorAndOpacity, as the tech tree widget does). Clicks are ignored in press()
-- while the rule says disabled. SetIsEnabled is not used: a Lua error inside a UObject call can crash UE4SS.
local ENABLED_TINT = { R = 1, G = 1, B = 1, A = 1 }
local DISABLED_TINT = { R = 0.4, G = 0.4, B = 0.4, A = 1 }

local function set_disabled(name, disabled)
    local slot = W.buttons[name]
    if slot == nil or slot.disabled == disabled then return end
    if isValid(slot.handle.widget) then
        slot.disabled = disabled
        slot.handle.widget:SetColorAndOpacity(disabled and DISABLED_TINT or ENABLED_TINT)
    end
end

local function arms_info(status)
    local cfg = liege.arms_config
    local parts = {}
    for _, good in ipairs(cfg.goods) do parts[#parts + 1] = good.amount .. " " .. good.name .. "s" end
    local info = string.format("Arms shipment: %d silver for %s", cfg.cost, table.concat(parts, " and "))
    if not status.enabled then info = info .. "\n" .. tostring(status.reason) end
    return info
end

local function fill_card(index, card)
    local c = index - 1
    set_visible("Card" .. c, card ~= nil)
    set_button_visible("PickButton" .. c, card ~= nil and card.state == nil)
    set_text("CardState" .. c, card and card.state or "")
    if card == nil then return end
    set_text("CardName" .. c, card.name)
    set_text("CardQuote" .. c, card.quote ~= "" and ('"' .. card.quote .. '"') or "")
    set_text("CardPenalty" .. c, card.penalty)
    for item = 0, OBJ_ITEMS - 1 do
        local row = card.objectives[item + 1]
        local key = c .. "_" .. item
        set_visible("ObjItem" .. key, row ~= nil)
        if row then
            set_text("ObjIcon" .. key, row.letter)
            set_text("ObjText" .. key, row.text)
            set_tooltip("ObjItem" .. key, row.tooltip)
        end
    end
    for item = 0, REW_ITEMS - 1 do
        local row = card.rewards[item + 1]
        local key = c .. "_" .. item
        set_visible("RewItem" .. key, row ~= nil)
        if row then
            set_text("RewIcon" .. key, row.letter)
            set_text("RewText" .. key, row.text)
            set_tooltip("RewItem" .. key, row.tooltip)
        end
    end
end

local function refresh()
    if not isValid(W.widget) then return false end
    local model = window_view()
    set_text("TitleText", "Liege")
    set_text("InfluenceText", model.influence_text)
    set_text("SilverText", model.silver_text)
    for index = 1, CARDS do fill_card(index, model.cards[index]) end
    set_text("EmptyText", model.empty_text or "")
    local active = model.active
    set_visible("ActivePanel", active ~= nil)
    set_button_visible("CompleteButton", active ~= nil)
    if not active then
        set_text("ActiveName", "")
    else
        set_text("ActiveName", active.name)
        set_text("ActiveLine0", active.lines[1] or "")
        set_text("ActiveLine1", active.lines[2] or "")
        set_text("ActiveDays", active.days_text)
        set_disabled("CompleteButton", not active.complete)
    end
    set_text("FooterText", W.last_error or W.hover_text or S.last_message or "")
    local status = liege.shipment_status(true)
    set_text("ArmsInfoText", arms_info(status))
    set_disabled("ArmsButton", not status.enabled)
    return true
end

local function release_buttons()
    local handles = {}
    for _, slot in pairs(W.buttons) do handles[#handles + 1] = slot.handle end
    clickhooks.release(handles)
end

local function reset_window()
    release_buttons()
    W.widget, W.texts, W.borders, W.buttons, W.shown, W.visible, W.tooltips = nil, {}, {}, {}, {}, {}, {}
end

local function on_open(made)
    W.widget = made
    W.opened_at, W.reapplied = os.clock(), false
    W.texts = menu.find_named(made, "TextBlock", NAMES.texts)
    local borders = menu.find_named(made, "Border", NAMES.borders)
    local button_borders = menu.find_named(made, "Border", NAMES.buttons)
    W.borders = borders
    if W.texts.InfluenceText == nil then
        reset_window()
        return nil, "the text lines were not found in the widget"
    end
    local controller = FindFirstOf("PlayerController")
    W.buttons = {}
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
    end
    local handles = {}
    for _, slot in pairs(W.buttons) do handles[#handles + 1] = slot.handle end
    local bound, bind_problem = clickhooks.bind_texts(handles)
    if not bound then
        reset_window()
        return nil, bind_problem
    end
    for index = 0, CARDS - 1 do clickhooks.set_text(W.buttons["PickButton" .. index].handle, "PICK") end
    clickhooks.set_text(W.buttons.CompleteButton.handle, "Complete")
    clickhooks.set_text(W.buttons.ArmsButton.handle, "Request arms shipment")
    clickhooks.set_text(W.buttons.CloseButton.handle, "Close")
    liege.reset_manor_cache()
    refresh()
    return true
end

menu.register({
    id = MENU_ID, label = "Liege",
    class_path = "/Game/HarnessMod/WBP_LiegeContracts.WBP_LiegeContracts_C", package_path = "/Game/HarnessMod", asset_name = "WBP_LiegeContracts",
    z_order = menu_config.z_order, position = menu_config.position,
    on_open = on_open, on_close = reset_window,
})

local function remember(result, reason)
    W.last_error = nil
    S.last_message = nil
    if result == nil then W.last_error = reason end
end

local function press(name)
    if name == "CloseButton" then
        menu.close()
        return
    end
    if name == "ArmsButton" then
        if not liege.shipment_status().enabled then
            refresh() -- a disabled button ignores the click
            return
        end
        local result, reason = liege.request_arms_shipment()
        remember(result, reason)
        if result then W.shipments = (W.shipments or 0) + 1 end
    elseif name == "CompleteButton" then
        local contract = active_contract()
        if contract == nil or not rules.is_complete(contract.objectives, refresh_progress()) then
            refresh() -- a disabled button ignores the click
            return
        end
        local result, reason = complete(false)
        remember(result, reason)
        if result then S.last_message = "Completed: " .. result.name end
    else
        local card = tonumber(name:match("^PickButton(%d)$"))
        local id = card and offer_ids()[card + 1]
        if id == nil then return refresh() end
        local result, reason = pick(id)
        remember(result, reason)
        if result then S.last_message = "Picked: " .. result.name end
    end
    refresh()
end

-- A hover tooltip (SetToolTipText on the item Border) does not show in the real game (notes/tooltip-hover.md). The text of the item
-- under the mouse shows in the footer line instead. Reads IsHovered of the visible items only.
local function look_for_hover()
    local found
    for name, tip in pairs(W.tooltips) do
        local border = W.borders[name]
        if W.visible[name] and tip ~= "" and border ~= nil and read(function() return border:IsHovered() end) == true then
            found = (tip:gsub("\n", " - "))
            break
        end
    end
    W.hover_text = found
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
    -- A collapse that is set in the first refresh does not hold for some borders (real runs 20261028-031836 and -034612): the
    -- visibility is written once more, 1.5 s after the open.
    if not W.reapplied and W.opened_at and now - W.opened_at >= 1.5 then
        W.reapplied, W.visible = true, {}
        refresh()
    end
    if now - W.last_refresh >= menu_config.refresh_ms / 1000 then
        W.last_refresh = now
        refresh_progress()
        look_for_hover()
        refresh()
    end
end

local function menu_state()
    local shown = {}
    for name, block in pairs(W.texts) do shown[name] = read(function() return block:GetText():ToString() end) end
    local buttons = {}
    for name, slot in pairs(W.buttons) do
        buttons[#buttons + 1] = { name = name, visibility = read(function() return slot.handle.widget:GetVisibility() end),
            hovered = read(function() return slot.handle.widget:IsHovered() end), disabled = slot.disabled }
    end
    local model = window_view()
    local status = liege.shipment_status()
    return { open = is_open(), in_viewport = is_open() and read(function() return W.widget:IsInViewport() end) or false,
             texts = shown, view = model, wanted_texts = { InfluenceText = model.influence_text, SilverText = model.silver_text, ArmsInfoText = arms_info(status) },
             arms_label = "Request arms shipment", arms_disabled = not status.enabled, buttons = buttons, shipments = W.shipments or 0,
             last_error = W.last_error, picks = S.picks, completes = S.completes, tooltips = W.tooltips, visible = W.visible, hover_text = W.hover_text,
             panel_visibility = W.borders.ActivePanel and read(function() return W.borders.ActivePanel:GetVisibility() end),
             card_visibility = W.borders.Card0 and read(function() return W.borders.Card0:GetVisibility() end),
             panel_name = W.borders.ActivePanel and read(function() return W.borders.ActivePanel:GetFullName() end) }
end

require("scheduler").every(TAG .. ".window", math.max(100, menu_config.poll_ms), tick_window)

---------------------------------------------------------------------------------------------
-- Named commands and telemetry
---------------------------------------------------------------------------------------------

local function answer(result, reason, detail)
    if result == nil then return nil, reason, detail end
    return result
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.liege_menu_open", function() return menu.open(MENU_ID) end, {})
    commands.register("InvasionMod.liege_menu_close", function()
        if is_open() then return menu.close() end
        return { ok = true }
    end, {})
    commands.register("InvasionMod.liege_menu_state", menu_state, {})
    commands.register("InvasionMod.liege_contracts_state", function()
        refresh_progress()
        return command_state()
    end, {})
    commands.register("InvasionMod.liege_contract_pick", function(args) return answer(pick(args.id)) end, { id = { type = "string", required = true } })
    commands.register("InvasionMod.liege_contract_complete", function()
        local result, reason = complete(false)
        return answer(result, reason)
    end, {})
    -- Test command: make an offer now, with no wait for a spring. `ids` (dot separated) names the offer; without it the draw runs.
    commands.register("InvasionMod.liege_contracts_offer_now", function(args)
        local ids
        if args.ids ~= nil and args.ids ~= "" then
            ids = rules.split_ids(args.ids)
            if #ids > contracts.offer_size then return nil, "at most " .. contracts.offer_size .. " ids" end
            for _, id in ipairs(ids) do
                if contracts.by_id[id] == nil then return nil, "unknown contract id: " .. id end
            end
        end
        local made, why = make_offer(ids)
        if made == nil then return nil, why end
        return command_state()
    end, { ids = { type = "string" } })
    -- Test command: set the progress of one objective of the active contract (1-based index) until the contract ends.
    commands.register("InvasionMod.liege_contracts_test_progress", function(args)
        local contract = active_contract()
        if contract == nil then return nil, "no contract is active" end
        if contract.objectives[args.index] == nil then return nil, "the contract has no objective " .. args.index end
        S.override[args.index] = args.value
        refresh_progress()
        return command_state()
    end, { index = { type = "integer", required = true, min = 1, max = 2 }, value = { type = "integer", required = true, min = 0, max = 1000000 } })
end

local has_telemetry, telemetry = pcall(require, "HarnessTelemetry")
if has_telemetry then
    telemetry.register("liege_contract_active", function() return state.loaded and state:get("contracts_active") or nil end)
    telemetry.register("liege_contracts_done", function() return state.loaded and state:get("contracts_done") or nil end)
    telemetry.register("liege_contracts_failed", function() return state.loaded and state:get("contracts_failed") or nil end)
end

core.log.info(TAG, string.format("feature liege_contracts loaded: %d contracts", #contracts.contracts))
return { state = state, contracts = contracts, command_state = command_state, pick = pick, complete = complete,
         open = function() return menu.open(MENU_ID) end, close = menu.close }
