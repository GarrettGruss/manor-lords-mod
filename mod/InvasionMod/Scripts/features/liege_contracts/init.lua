-- Feature liege_contracts (changes update-liege-tribute-to-contracts, #505, update-liege-contracts-tiers, #533, and
-- update-liege-contracts-tier-goods, #569): each spring the liege offers 9 contracts, 3 for each tier Small, Medium and Large.
-- A Small or Medium contract asks for a delivery of one good, a Large contract asks for a cost (a squad loan, families, tribute).
-- Each contract pays one reward.
-- The player fulfils contracts at will, up to a limit for each tier and year, and only with a built manor. The offer ends when
-- winter begins; there is no penalty. The pools are data (data/liege_contracts/contracts.json); the numbers are in config.
-- The state is saved with ModState. The liege window is a pak widget (mod/InvasionMod/ue/make_liege_widget.py) on the base menu (core/menu.lua).
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
local tech_tree = require("features.tech_tree.init")
-- The Laws menu is loaded after this feature (the menu buttons keep their order), so its entry points are looked up when a reward is paid.
local function laws() return require("features.laws_menu.init") end
local tribute = require("features.tribute.init")
local all_config = require("config")
local config = all_config.liege_contracts
local menu_config = all_config.liege_influence

local TAG = "InvasionMod.liege_contracts"
local STATE_VERSION = 2
local SPRING = config.spring_season -- the same value as tech_tree.spring_season (notes/season-values.md); an own key so that a test of one feature does not change the other
local WINTER = config.winter_season

local state = ModState.open("invasion", "pawn", STATE_VERSION)
state:register("contracts_spring_no", -1, "integer") -- season counter of the last spring that was seen (-1: no look yet)
state:register("contracts_offer", "", "string")      -- the offered contracts in text form (rules.encode_offer)
state:register("contracts_used", "", "string")       -- contracts fulfilled in each tier, "s-1.m-0.l-0"
state:register("contracts_done", 0, "integer")
state:register("contracts_loans", "", "string")      -- squads that are on loan: "<template>-<men>-<experience>-<due day>" (rules.encode_loans)

state:register("contracts_retinue_squads", 0, "integer") -- reward squads paid so far (cap: config retinue_squad_cap)
state:register("retinue_squad_ids", "", "string")        -- ids of the retinue squads, "22.24" (rules.encode_ids); no safe read tells a retinue squad

local table_path = world.data_path(config.data_file)
local contracts = loader.load_file(table_path, json.decode)

local S = { failed_rewards = 0, fulfils = 0, loans_started = 0, loans_returned = 0, ticks = 0 }
local loan_failed = {} -- the loan records whose return failed (logged once each)

---------------------------------------------------------------------------------------------
-- State access
---------------------------------------------------------------------------------------------

-- A saved contract is known when the table still has its request good (or its cost).
local function is_known(contract)
    local pool = contracts.tiers[contract.tier]
    if pool == nil then return false end
    for _, request in ipairs(pool.requests) do
        if request.good == contract.good and request.cost == contract.cost then return true end
    end
    return false
end

local function offer()
    return (rules.decode_offer(state:get("contracts_offer"), is_known))
end

local function used() return rules.decode_used(state:get("contracts_used")) end

local function save_offer(list)
    state:set("contracts_offer", rules.encode_offer(list))
end

local function find_contract(list, id)
    for _, contract in ipairs(list) do
        if contract.id == id then return contract end
    end
    return nil
end

local function limit_of(tier) return config.tier_limits[tier] or 1 end

local function locked_laws()
    return rules.locked_laws(tech_tree.tree.laws, tech_tree.unlocked_nodes(), tech_tree.granted_laws())
end

local function slot_cap_reached() return tech_tree.law_slots() >= all_config.tech_tree.max_total_laws end

-- A reward kind that cannot be paid now is not drawn: no law while all laws are unlocked, no law slot at the cap (owner decision 2026-11-04).
local function reward_allowed(kind)
    if kind == "law" then return #locked_laws() > 0 end
    if kind == "law_slot" then return not slot_cap_reached() end
    if kind == "retinue_squad" then return rules.retinue_below_cap(state:get("contracts_retinue_squads"), config.retinue_squad_cap) end
    return true
end

local function retinue_ids() return rules.decode_ids(state:get("retinue_squad_ids")) end

local function note_retinue_id(id)
    if id == nil then return end
    local list, changed = rules.add_id(retinue_ids(), id)
    if changed then state:set("retinue_squad_ids", rules.encode_ids(list)) end
end

local function cost_allowed(cost)
    if cost == "loan_units" then return config.loan_enabled == true end
    return true
end

---------------------------------------------------------------------------------------------
-- The manor check. The window asks for a cached answer: a built manor stays built while the window is open, and a missing manor is
-- looked for again after `manor_recheck_s`. Without this the building list was read twice a second (two real runs crashed the
-- game after such reads, change fix-arms-button-manor, #455). A click and the commands read the manor fresh.
---------------------------------------------------------------------------------------------
local manor_cache = { built = false, checked = nil }

local function reset_manor_cache() manor_cache = { built = false, checked = nil } end

local function manor_built_cached()
    if manor_cache.built then return true end
    local now = os.clock()
    if manor_cache.checked == nil or now - manor_cache.checked >= config.manor_recheck_s then
        manor_cache = { built = world.manor_built() == true, checked = now }
    end
    return manor_cache.built
end

---------------------------------------------------------------------------------------------
-- Offer, fulfil, expiry
---------------------------------------------------------------------------------------------

local function difficulty()
    local level = invasion.level and invasion.level("yearly")
    return rules.difficulty_for(level, config.difficulty)
end

local function make_offer()
    local setup = { tiers = contracts.tiers, base = config.base, weight = config.weight, difficulty = difficulty(), allowed = reward_allowed,
                    cost_allowed = cost_allowed }
    local list, why = rules.draw_offer(setup, contracts.offer_per_tier, math.random)
    if list == nil then return nil, why end
    -- Saved before any log line, with the fulfilled counts set to 0.
    state:set("contracts_used", rules.encode_used({}))
    save_offer(list)
    return list
end

local function fail_reward(reward, why)
    S.failed_rewards = S.failed_rewards + 1
    core.log.warn(TAG, string.format("LIEGE_CONTRACTS reward %s failed: %s", reward.kind, tostring(why)))
end

-- The King's Favour that a law slot reward pays at the slot cap: the amount of the kings_favour reward of the table (10 if it has none).
local function kings_favour_default()
    for _, row in ipairs(contracts.tiers.large.rewards) do
        if row.kind == "kings_favour" then return row.min end
    end
    return 10
end

local function pay_goods(reward)
    local ok, why = world.add_goods(reward.good, reward.amount)
    if not ok then return fail_reward(reward, why) end
end

local function pay_law(reward, contract)
    local locked = locked_laws()
    if #locked == 0 then return fail_reward(reward, "no law is locked") end
    local law_id = locked[math.random(1, #locked)]
    local source = string.format("Contract: %s %d", view.TIER_NAMES[contract.tier], contract.number)
    local unlocked, why = laws().laws_unlock(law_id, source)
    if not unlocked then return fail_reward(reward, why) end
    reward.law = law_id
end

-- The cap of a reward is reached: King's Favour instead (owner decisions 2026-11-05 and 2026-11-06).
local function pay_favour_instead(reward, what)
    local amount = kings_favour_default()
    local ok, why = world.add_kings_favour(amount)
    if not ok then return fail_reward(reward, why) end
    reward.fallback = { kind = "kings_favour", amount = amount }
    core.log.info(TAG, string.format("LIEGE_CONTRACTS %s cap reached: paid %d King's Favour instead", what, amount))
end

local function pay_law_slot(reward)
    local added = laws().laws_add_slot()
    if added == nil then return fail_reward(reward, "laws_add_slot gave no answer") end
    if added.added then return end
    pay_favour_instead(reward, "law slot")
end

-- A native retinue squad of config.retinue_squad_men men (the game saves it). At the cap: King's Favour.
local function pay_retinue_squad(reward)
    if not rules.retinue_below_cap(state:get("contracts_retinue_squads"), config.retinue_squad_cap) then
        return pay_favour_instead(reward, "retinue squad")
    end
    local id, why = world.add_retinue_squad(config.retinue_squad_men)
    if id == nil then return fail_reward(reward, why) end
    state:set("contracts_retinue_squads", state:get("contracts_retinue_squads") + 1)
    note_retinue_id(id)
    reward.squad = id
    core.log.info(TAG, string.format("LIEGE_CONTRACTS retinue squad %d with %d men paid (%d of %d)", id, config.retinue_squad_men,
        state:get("contracts_retinue_squads"), config.retinue_squad_cap))
end

-- Pays one reward. A failure is logged and counted; it is not retried.
local function pay_reward(reward, contract)
    local kind = reward.kind
    if kind == "goods" or kind == "weapons" or kind == "armor" then
        pay_goods(reward)
    elseif kind == "law" then
        pay_law(reward, contract)
    elseif kind == "kings_favour" then
        local ok, why = world.add_kings_favour(reward.amount)
        if not ok then return fail_reward(reward, why) end
    elseif kind == "law_slot" then
        pay_law_slot(reward)
    elseif kind == "retinue_squad" then
        pay_retinue_squad(reward)
    elseif kind == "relief_promise" then
        invasion.add_relief_bonus(reward.amount)
    end
end

---------------------------------------------------------------------------------------------
-- Large costs. `cost_facts` only reads; `take_cost` changes the game after the checks of `refusal_for`.
---------------------------------------------------------------------------------------------

local function loan_days() return config.loan_days end

-- The squads that a loan takes: retinue squads only (change add-contract-retinue-reward), the `amount` squads with the fewest men, each with
-- its template. `fresh`: read the manor bound squad now (a fulfilment); the window and the tick use the saved ids. Returns the list, or nil, a reason
-- and the number of retinue squads of the player.
local function loan_candidates(amount, fresh)
    if fresh then note_retinue_id(world.bound_retinue_squad_id()) end
    local squads, problem = world.player_squads()
    if squads == nil then return nil, problem end
    local live = rules.retinue_squads(squads, retinue_ids(), world.known_template)
    if #live == 0 then return nil, view.NEEDS_RETINUE_TEXT, 0 end
    if #live < amount then return nil, string.format("%d more retinue %s needed", amount - #live, amount - #live == 1 and "squad" or "squads"), #live end
    local picked = {}
    for index = 1, amount do
        local squad = live[index]
        picked[#picked + 1] = { id = squad.id, men = squad.men, experience = squad.experience, template = rules.loan_template(world.known_template(squad.id)) }
    end
    return picked, nil, #live
end

-- What the player holds for a cost, and why the cost cannot be paid now (nil: it can). Returns held, problem.
local function cost_facts(contract)
    local cost, amount = contract.cost, contract.amount
    if cost == "send_families" then
        local held = world.family_count()
        if held == nil then return nil, "the families are not known" end
        local need = amount + config.min_families_left
        if held < need then return held, string.format("%d more %s needed (%d must stay)", need - held, need - held == 1 and "family" or "families", config.min_families_left) end
        return held
    elseif cost == "loan_units" then
        local _, problem, held = loan_candidates(amount)
        return held, problem
    elseif cost == "tribute_season" then
        local held = tribute.paying_vassals()
        if held < 1 then return held, "no vassal pays tribute" end
        return held
    end
    return nil, "unknown cost " .. tostring(cost)
end

local function save_loans(list) state:set("contracts_loans", rules.encode_loans(list)) end

local function loans() return rules.decode_loans(state:get("contracts_loans")) end

-- Takes the cost of a Large contract. Returns true, or nil and a reason. The checks were done by refusal_for.
local function take_cost(contract)
    local cost, amount = contract.cost, contract.amount
    if cost == "send_families" then
        local removed, why = world.remove_families(amount)
        if removed == nil then return nil, why end
        if removed < amount then return nil, string.format("only %d of %d families could be removed", removed, amount) end
        return true
    elseif cost == "tribute_season" then
        tribute.skip_months(amount)
        return true
    elseif cost == "loan_units" then
        local day = world.current_day()
        if day == nil then return nil, "the game day is not known" end
        local picked, why = loan_candidates(amount, true)
        if picked == nil then return nil, why end
        for _, squad in ipairs(picked) do
            local ok, problem = world.remove_squad(squad.id)
            if not ok then return nil, problem end
            -- Saved at once after the removal: the squad comes back at the due day, also after a load.
            local list = loans()
            list[#list + 1] = { template = squad.template, men = squad.men, experience = squad.experience, due = day + loan_days() }
            save_loans(list)
            S.loans_started = S.loans_started + 1
            core.log.info(TAG, string.format("LIEGE_CONTRACTS loan started: squad %d (%s, %d men) back on day %d", squad.id, squad.template, squad.men, day + loan_days()))
        end
        return true
    end
    return nil, "unknown cost " .. tostring(cost)
end

-- Returns the squads whose loan is due. The record is removed (and saved) before the spawn, so a load never returns a squad twice;
-- a failed spawn puts the record back and logs once.
local function return_loans()
    local list = loans()
    if #list == 0 then return end
    local due, kept = rules.split_loans(list, world.current_day())
    for _, loan in ipairs(due) do
        save_loans(kept)
        local id, why
        if loan.template == rules.NATIVE_RETINUE then
            id, why = world.add_retinue_squad(loan.men)
            if id ~= nil then
                note_retinue_id(id)
                world.set_squad_experience(id, loan.experience)
            end
        else
            id, why = world.spawn_squad(loan.template, loan.experience)
        end
        if id ~= nil then
            S.loans_returned = S.loans_returned + 1
            core.log.info(TAG, string.format("LIEGE_CONTRACTS loan ended: squad %d (%s, %d men) is back", id, loan.template, loan.men))
            local shown, problem = world.show_banner(view.loan_return_text(loan.men))  -- title and subtext
            if not shown then core.log.warn(TAG, "LIEGE_CONTRACTS loan banner failed: " .. tostring(problem)) end
        else
            kept[#kept + 1] = loan
            save_loans(kept)
            local key = rules.encode_loans({ loan })
            if not loan_failed[key] then
                loan_failed[key] = true
                core.log.error(TAG, string.format("LIEGE_CONTRACTS loan return failed, tries again: %s", tostring(why)))
            end
        end
    end
end

---------------------------------------------------------------------------------------------

-- Why the contract cannot be fulfilled now, or nil. `fresh_manor`: read the manor now (a click, a command) instead of the cache.
local function refusal_for(contract, fresh_manor)
    if contract == nil then return rules.refusal(nil, {}) end
    local manor
    if fresh_manor then manor = world.manor_built() == true else manor = manor_built_cached() end
    local facts = { manor = manor, used = used()[contract.tier], limit = limit_of(contract.tier) }
    if contract.cost then
        if fresh_manor and contract.cost == "loan_units" then note_retinue_id(world.bound_retinue_squad_id()) end
        local _, problem = cost_facts(contract)
        facts.cost_problem = problem
    else
        facts.stock = world.stock(contract.good)
    end
    return rules.refusal(contract, facts)
end

-- The click and the command call this. Returns a result table, or nil and a reason. A refused call changes nothing.
local function fulfil(id)
    local list = offer()
    local contract = find_contract(list, id)
    local why = refusal_for(contract, true)
    if why then
        core.log.warn(TAG, string.format("LIEGE_CONTRACTS fulfil %s refused: %s", tostring(id), why))
        return nil, why
    end
    if contract.cost then
        local taken, problem = take_cost(contract)
        if not taken then
            core.log.warn(TAG, string.format("LIEGE_CONTRACTS fulfil %s refused: the cost %s could not be taken: %s", id, contract.cost, tostring(problem)))
            return nil, tostring(problem)
        end
    else
        local got, problem = world.take_goods(contract.good, contract.amount)
        if got == nil or got < contract.amount then
            if got ~= nil and got > 0 then world.add_goods(contract.good, got) end -- put the units back
            local reason = string.format("only %d of %d units of goods %d could be taken from the stores (the goods lie %s)%s", got or 0, contract.amount, contract.good,
                world.holders(contract.good), problem and (": " .. tostring(problem)) or "")
            core.log.warn(TAG, "LIEGE_CONTRACTS fulfil refused: " .. reason)
            return nil, reason
        end
    end
    -- Saved before the reward and the log, so a crash after the take never lets the contract be fulfilled twice.
    contract.done = true
    save_offer(list)
    local counts = used()
    counts[contract.tier] = counts[contract.tier] + 1
    state:set("contracts_used", rules.encode_used(counts))
    state:set("contracts_done", state:get("contracts_done") + 1)
    local failed_before = S.failed_rewards
    core.log.try(TAG, pay_reward, contract.reward, contract)
    S.fulfils = S.fulfils + 1
    local result = { id = id, tier = contract.tier, good = contract.good, cost = contract.cost, amount = contract.amount, reward = contract.reward,
                     failed_rewards = S.failed_rewards - failed_before }
    core.log.info(TAG, string.format("LIEGE_CONTRACTS fulfilled %s: %s for %s failed_rewards=%d", id,
        contract.cost and view.cost_text(contract.cost, contract.amount, loan_days()) or string.format("%d of goods %d", contract.amount, contract.good),
        view.reward_text(contract.reward, contracts.names), result.failed_rewards))
    return result
end

local function expire(info)
    local list = offer()
    if #list == 0 and state:get("contracts_offer") == "" then return end
    state:set("contracts_offer", "")
    state:set("contracts_used", rules.encode_used({}))
    core.log.info(TAG, string.format("LIEGE_CONTRACTS winter begins no=%d: the offer ended with %d contracts, no penalty", info.no, #list))
end

-- Spring: one offer for each spring counter value. The first look of a game with no contract state takes the counter. A game that
-- starts in spring is dealt its offer at once; a game in another season waits for the next spring. A save keeps its counter,
-- so a load in the same spring never deals twice.
local function yearly_step(info)
    local seen = state:get("contracts_spring_no")
    if seen < 0 then
        if info.season ~= SPRING then
            state:set("contracts_spring_no", info.no)
            return
        end
        seen = info.no - 1
    end
    if info.season == WINTER then return expire(info) end
    if info.season ~= SPRING or info.no <= seen then return end
    state:set("contracts_spring_no", info.no) -- saved before the draw and the log, so a load never draws twice
    local list, why = make_offer()
    if list == nil then return core.log.error(TAG, "LIEGE_CONTRACTS draw failed: " .. tostring(why)) end
    core.log.info(TAG, string.format("LIEGE_CONTRACTS spring offer no=%d contracts=%s", info.no, state:get("contracts_offer")))
end

-- A saved contract that the table does not know (or an offer of the old format) is dropped with no penalty; the log names it.
local function drop_unknown()
    local list, dropped = rules.decode_offer(state:get("contracts_offer"), is_known)
    if #dropped == 0 then return end
    save_offer(list)
    core.log.warn(TAG, "LIEGE_CONTRACTS dropped contracts that the table does not know (no penalty): " .. table.concat(dropped, ","))
end

local function tick()
    if not state.loaded then return end
    drop_unknown()
    S.ticks = S.ticks + 1
    -- The manor bound squad is the newest retinue squad (a squad that the player made by hand). A slow look: the building list is not read at each tick.
    if S.ticks % config.retinue_scan_ticks == 1 then note_retinue_id(world.bound_retinue_squad_id()) end
    return_loans()
    local info = invasion.season_info()
    if info ~= nil then yearly_step(info) end
end

require("scheduler").every(TAG, math.max(100, config.poll_ms), tick)

---------------------------------------------------------------------------------------------
-- Views (the window and the state command)
---------------------------------------------------------------------------------------------

local function days_to_winter() return rules.days_until(world.day_of_year(), config.winter_start_day, config.year_days) end
local function days_to_spring() return rules.days_until(world.day_of_year(), config.spring_start_day, config.year_days) end

-- One card for the window and the state command. `manor`: is the manor built (cached or fresh as the caller decides).
local function card_of(contract, manor)
    local facts = { manor = manor, used = used()[contract.tier], limit = limit_of(contract.tier) }
    local stock, held, short, have
    if contract.cost then
        local problem
        held, problem = cost_facts(contract)
        facts.cost_problem = problem
        short = problem ~= nil
        have = view.cost_have_text(contract.cost, held)
    else
        stock = world.stock(contract.good)
        facts.stock = stock
        short = (stock or 0) < contract.amount
        have = view.have_text(stock, contract.amount)
    end
    local reason = rules.refusal(contract, facts)
    return { id = contract.id, tier = contract.tier, number = contract.number, good = contract.good, cost = contract.cost, amount = contract.amount, done = contract.done,
             requirement = view.requirement_text(contract, contracts.names, loan_days()), have = have, stock = stock, held = held, short = short,
             reward_text = view.reward_text(contract.reward, contracts.names), reward = contract.reward,
             enabled = reason == nil, reason = reason, label = contract.done and "Fulfilled" or "Fulfil" }
end

local function window_view(manor)
    local list = offer()
    local info = invasion.season_info()
    local in_winter = info ~= nil and info.season == WINTER
    local counts = used()
    local result = { tiers = {}, cards = {}, offered = #list, manor = manor }
    for _, tier in ipairs(rules.TIERS) do
        result.tiers[tier] = { name = view.TIER_NAMES[tier], count_text = view.tier_count_text(counts[tier], limit_of(tier)), used = counts[tier], limit = limit_of(tier) }
    end
    for _, contract in ipairs(list) do result.cards[#result.cards + 1] = card_of(contract, manor) end
    result.remaining_text = in_winter and view.no_contracts_remaining_text() or view.remaining_text(days_to_winter())
    result.refresh_text = view.refresh_text(days_to_spring())
    if #list == 0 then result.notice_text = view.NO_OFFER_TEXT
    elseif not manor then result.notice_text = rules.NO_MANOR
    else result.notice_text = "" end
    return result
end

local function command_state()
    local info = invasion.season_info()
    local manor = world.manor_built() == true
    local model = window_view(manor)
    local tiers = {}
    for _, tier in ipairs(rules.TIERS) do tiers[tier] = { used = model.tiers[tier].used, limit = model.tiers[tier].limit } end
    local ids = {}
    for _, card in ipairs(model.cards) do ids[#ids + 1] = card.id end
    return { contracts = model.cards, offer = ids, tiers = tiers, manor = manor, done = state:get("contracts_done"), failed_rewards = S.failed_rewards,
             spring_no = state:get("contracts_spring_no"), season = info and info.season, season_no = info and info.no,
             days_to_winter = days_to_winter(), days_to_spring = days_to_spring(), influence = state:get("liege_influence"), silver = liege.silver(),
             fulfils = S.fulfils, loans_started = S.loans_started, loans_returned = S.loans_returned, loans_text = state:get("contracts_loans"),
             relief_bonus_squads = invasion.relief_bonus(), retinue_squads = state:get("contracts_retinue_squads"), retinue_ids = state:get("retinue_squad_ids"), law_slots = tech_tree.law_slots(), kings_favour = world.kings_favour(), difficulty = difficulty(), offer_text = state:get("contracts_offer"), used_text = state:get("contracts_used"),
             notice_text = model.notice_text, remaining_text = model.remaining_text, refresh_text = model.refresh_text }
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
local ROWS, PER_ROW = 3, 3
local COLLAPSED, VISIBLE = 1, 0 -- ESlateVisibility
local NOTICE_S = 6              -- real seconds that a refused click shows its reason
local CARD_TEXTS = { "ReqLabel", "ReqText", "HaveText", "HaveMiss", "RewLabel", "RewText", "FulfilledText" }
local DIMMED_OPACITY = 0.45     -- render opacity of a card that cannot be fulfilled
local NAMES = {
    texts = { "TitleText", "RemainLabel", "RemainValue", "RefreshLabel", "RefreshValue", "NoticeText" },
    borders = {},
    buttons = {},
}
for row = 0, ROWS - 1 do
    for _, prefix in ipairs({ "TierName", "TierCount" }) do NAMES.texts[#NAMES.texts + 1] = prefix .. row end
    for card = 0, PER_ROW - 1 do
        local key = row .. "_" .. card
        for _, prefix in ipairs(CARD_TEXTS) do NAMES.texts[#NAMES.texts + 1] = prefix .. key end
        NAMES.borders[#NAMES.borders + 1] = "Card" .. key
        NAMES.buttons[#NAMES.buttons + 1] = "FulfilButton" .. key
    end
end

local W = { widget = nil, texts = {}, borders = {}, buttons = {}, shown = {}, visible = {}, labels = {}, dim = {}, last_refresh = 0, notice = nil, notice_until = 0, presses = 0 }

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

-- A card that cannot be fulfilled is dimmed (render opacity of its Border; a plain float call).
local function set_dim(name, dimmed)
    local border = W.borders[name]
    if border == nil or W.dim[name] == dimmed then return end
    if isValid(border) then
        W.dim[name] = dimmed
        border:SetRenderOpacity(dimmed and DIMMED_OPACITY or 1)
    end
end

local function set_button_visible(name, shown)
    local slot = W.buttons[name]
    if slot == nil or W.visible[name] == shown then return end
    W.visible[name] = shown
    pcall(clickhooks.set_visible, slot.handle, shown)
end

-- The label is written only when it changes: a rewrite at each refresh was a crash risk (spec 34).
local function set_button_label(name, text)
    local slot = W.buttons[name]
    if slot == nil or W.labels[name] == text then return end
    W.labels[name] = text
    clickhooks.set_text(slot.handle, text)
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

local function key_of(card) return (rules.TIERS_INDEX[card.tier] - 1) .. "_" .. (card.number - 1) end

local function current_view() return window_view(manor_built_cached()) end

local function fill_card(row, number, card)
    local key = row .. "_" .. number
    set_visible("Card" .. key, card ~= nil)
    if card == nil then
        set_button_visible("FulfilButton" .. key, false)
        for _, prefix in ipairs(CARD_TEXTS) do set_text(prefix .. key, "") end
        return
    end
    local verb, goods = view.split_requirement(card.requirement)
    local reward_label, reward = view.split_reward(card.reward_text)
    local short = card.short
    set_text("ReqLabel" .. key, verb)
    set_text("ReqText" .. key, goods)
    set_text("HaveText" .. key, short and "" or card.have)
    set_text("HaveMiss" .. key, short and card.have or "")
    set_text("RewLabel" .. key, reward_label)
    set_text("RewText" .. key, reward)
    set_text("FulfilledText" .. key, card.done and "Fulfilled" or "")
    -- A fulfilled card shows the gold text and no button; a card that cannot be fulfilled is dimmed.
    set_button_visible("FulfilButton" .. key, not card.done)
    set_button_label("FulfilButton" .. key, card.label)
    set_disabled("FulfilButton" .. key, not card.enabled)
    set_dim("Card" .. key, not card.enabled and not card.done)
end

local function notice_line(model)
    if W.notice and os.clock() < W.notice_until then return W.notice end
    return model.notice_text
end

local function refresh()
    if not isValid(W.widget) then return false end
    local model = current_view()
    set_text("TitleText", view.TITLE_TEXT)
    set_text("RemainLabel", select(1, view.split_label(model.remaining_text)))
    set_text("RemainValue", select(2, view.split_label(model.remaining_text)))
    set_text("RefreshLabel", select(1, view.split_label(model.refresh_text)))
    set_text("RefreshValue", select(2, view.split_label(model.refresh_text)))
    set_text("NoticeText", notice_line(model))
    local by_slot = {}
    for _, card in ipairs(model.cards) do by_slot[key_of(card)] = card end
    for row, tier in ipairs(rules.TIERS) do
        set_text("TierName" .. (row - 1), model.tiers[tier].name)
        set_text("TierCount" .. (row - 1), model.tiers[tier].count_text)
        for number = 0, PER_ROW - 1 do fill_card(row - 1, number, by_slot[(row - 1) .. "_" .. number]) end
    end
    return true
end

local function release_buttons()
    local handles = {}
    for _, slot in pairs(W.buttons) do handles[#handles + 1] = slot.handle end
    clickhooks.release(handles)
end

local function reset_window()
    release_buttons()
    W.widget, W.texts, W.borders, W.buttons, W.shown, W.visible, W.labels, W.dim = nil, {}, {}, {}, {}, {}, {}, {}
end

local function on_open(made)
    W.widget = made
    W.opened_at, W.reapplied, W.notice = os.clock(), false, nil
    W.texts = menu.find_named(made, "TextBlock", NAMES.texts)
    W.borders = menu.find_named(made, "Border", NAMES.borders)
    local button_borders = menu.find_named(made, "Border", NAMES.buttons)
    if W.texts.RemainValue == nil then
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
    -- Fulfil is plain text: the click button keeps its label and loses its box (transparent background).
    for _, handle in ipairs(handles) do
        local ok, inner = pcall(function() return handle.widget.Button01 end)
        if ok and isValid(inner) then inner:SetBackgroundColor({ R = 1, G = 1, B = 1, A = 0 }) end
    end
    local bound, bind_problem = clickhooks.bind_texts(handles)
    if bound then
        -- The label sits in the TextBorder (child 1 of the content box, as bind_texts finds it): make its box transparent too.
        for _, handle in ipairs(handles) do
            local ok, text_border = pcall(function() return handle.widget.Button01:GetContent():GetChildAt(1) end)
            if ok and isValid(text_border) then text_border:SetBrushColor({ R = 1, G = 1, B = 1, A = 0 }) end
        end
    end
    if not bound then
        reset_window()
        return nil, bind_problem
    end
    reset_manor_cache()
    refresh()
    return true
end

menu.register({
    id = MENU_ID, label = "Liege",
    class_path = "/Game/HarnessMod/WBP_LiegeContracts.WBP_LiegeContracts_C", package_path = "/Game/HarnessMod", asset_name = "WBP_LiegeContracts",
    z_order = menu_config.z_order, -- the widget is centred by its own anchors (make_liege_widget.py), so there is no position
    on_open = on_open, on_close = reset_window,
})

local function say(text)
    W.notice, W.notice_until = text, os.clock() + NOTICE_S
end

local function press(name)
    local row, number = name:match("^FulfilButton(%d)_(%d)$")
    local tier = row and rules.TIERS[tonumber(row) + 1]
    local contract = tier and find_contract(offer(), tier .. "-" .. (tonumber(number) + 1))
    -- A disabled button ignores the click (the rule is the same as the command's, read from the cached manor answer).
    if contract == nil or refusal_for(contract, false) ~= nil then return refresh() end
    W.presses = W.presses + 1
    local result, reason = fulfil(contract.id)
    if result == nil then say(reason) else W.notice = nil end
    refresh()
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
        refresh()
    end
end

local function menu_state()
    local shown = {}
    for name, block in pairs(W.texts) do shown[name] = read(function() return block:GetText():ToString() end) end
    local buttons = {}
    for name, slot in pairs(W.buttons) do
        buttons[#buttons + 1] = { name = name, visibility = read(function() return slot.handle.widget:GetVisibility() end),
            hovered = read(function() return slot.handle.widget:IsHovered() end), disabled = slot.disabled, label = W.labels[name] }
    end
    local model = window_view(manor_built_cached())
    local remain_label, remain_value = view.split_label(model.remaining_text)
    local refresh_label, refresh_value = view.split_label(model.refresh_text)
    local wanted = { RemainLabel = remain_label, RemainValue = remain_value, RefreshLabel = refresh_label, RefreshValue = refresh_value,
                     NoticeText = notice_line(model) }
    for row, tier in ipairs(rules.TIERS) do
        wanted["TierName" .. (row - 1)] = model.tiers[tier].name
        wanted["TierCount" .. (row - 1)] = model.tiers[tier].count_text
    end
    for _, card in ipairs(model.cards) do
        local key = key_of(card)
        local _, goods = view.split_requirement(card.requirement)
        local _, reward = view.split_reward(card.reward_text)
        wanted["ReqText" .. key], wanted["RewText" .. key] = goods, reward
        wanted[(card.short and "HaveMiss" or "HaveText") .. key] = card.have
    end
    return { open = is_open(), in_viewport = is_open() and read(function() return W.widget:IsInViewport() end) or false,
             texts = shown, view = model, wanted_texts = wanted, buttons = buttons, presses = W.presses, fulfils = S.fulfils,
             visible = W.visible, notice = W.notice,
             card_visibility = W.borders.Card0_0 and read(function() return W.borders.Card0_0:GetVisibility() end) }
end

require("scheduler").every(TAG .. ".window", math.max(100, menu_config.poll_ms), tick_window)

---------------------------------------------------------------------------------------------
-- Named commands and telemetry
---------------------------------------------------------------------------------------------

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.liege_menu_open", function() return menu.open(MENU_ID) end, {})
    commands.register("InvasionMod.liege_menu_close", function()
        if is_open() then return menu.close() end
        return { ok = true }
    end, {})
    commands.register("InvasionMod.liege_menu_state", menu_state, {})
    -- Test command: the same code as a click on a window button (`button` is a button name such as FulfilButton0_0).
    -- A real mouse click needs a mouse device; this PC may have none.
    commands.register("InvasionMod.liege_menu_press", function(args)
        if not is_open() then return nil, "the window is not open" end
        press(args.button)
        return { ok = true, presses = W.presses, fulfils = S.fulfils }
    end, { button = { type = "string", required = true } })
    commands.register("InvasionMod.liege_contracts_state", command_state, {})
    commands.register("InvasionMod.liege_contract_fulfil", function(args)
        local result, reason = fulfil(args.id)
        if result == nil then return nil, reason end
        return result
    end, { id = { type = "string", required = true } })
    -- Test command: every loan is due now (a real loan is 60 game days; the next tick returns the squads).
    commands.register("InvasionMod.liege_contracts_loans_due_now", function()
        local day = world.current_day()
        if day == nil then return nil, "the game day is not known" end
        local list = loans()
        for _, loan in ipairs(list) do loan.due = day end
        save_loans(list)
        return { loans = #list, day = day }
    end, {})
    -- Test command: make an offer now, with no wait for a spring. `ids` names the offer in the saved text form (rules.encode_offer);
    -- without it the draw runs.
    commands.register("InvasionMod.liege_contracts_offer_now", function(args)
        if args.ids ~= nil and args.ids ~= "" then
            local list, dropped = rules.decode_offer(args.ids, is_known)
            if #dropped > 0 then return nil, "unknown contract: " .. table.concat(dropped, ",") end
            if #list > contracts.offer_per_tier * #rules.TIERS then return nil, "too many contracts" end
            state:set("contracts_used", rules.encode_used({}))
            save_offer(list)
        else
            local made, why = make_offer()
            if made == nil then return nil, why end
        end
        return command_state()
    end, { ids = { type = "string", maxLength = 600 } })
end

local has_telemetry, telemetry = pcall(require, "HarnessTelemetry")
if has_telemetry then
    telemetry.register("liege_contracts_done", function() return state.loaded and state:get("contracts_done") or nil end)
    telemetry.register("liege_contracts_offered", function() return state.loaded and #offer() or nil end)
end

core.log.info(TAG, string.format("feature liege_contracts loaded: %d requests", #contracts.tiers.small.requests + #contracts.tiers.medium.requests + #contracts.tiers.large.requests))
return { state = state, contracts = contracts, command_state = command_state, fulfil = fulfil,
         open = function() return menu.open(MENU_ID) end, close = menu.close }
