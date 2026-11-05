-- Pure view model of the Vassals menu (feature vassals_menu, change add-vassals-menu, #564). No game access.
-- It turns the vassal state, the wiped records and the tribute rules into the texts and flags that the widget shows.
-- The status comes from existing flags only (stalled, rebuilding, a handover) and from a wiped record. Nothing is saved here.
local M = {}

M.TITLE_TEXT = "VASSALS"
M.POLICIES = { "light", "fair", "heavy" }
M.STAT_LABELS = { "Status", "Rich resources", "Tribute", "Families", "Buildings", "Vassal for" }
M.FREE_TITLE = "Free slot"
M.FREE_NOTE = "Claim and settle a region to gain a vassal."

-- Status keys and the words on the card (owner decision 6: "Thriving" means not stalled and not rebuilding).
M.STATUS_TEXT = { thriving = "Thriving", stalled = "Stalled", rebuilding = "Rebuilding", wiped = "Wiped", claimed = "Claimed" }

local NO_LORD = "none" -- the registry text for "no lord" (features.vassals.rules.NO_REGION)

function M.region_text(name)
    if name == nil or name == "" or name == NO_LORD then return "-" end
    return name:sub(1, 1):upper() .. name:sub(2)
end

-- "1" for 1.0, "1.5" for 1.5, "0.5" for 0.5
function M.factor_text(factor)
    return string.format("%g", factor)
end

function M.policy_text(name)
    return name:sub(1, 1):upper() .. name:sub(2)
end

-- Days since the handover. `handed_day` is stored as day + 1 (0 = no handover).
function M.days_as_vassal(handed_day, today)
    if type(handed_day) ~= "number" or handed_day <= 0 or type(today) ~= "number" then return 0 end
    return math.max(0, today + 1 - handed_day)
end

function M.days_text(days)
    return string.format("%d %s", days, days == 1 and "day" or "days")
end

function M.status_of(row)
    if row.rebuilding then return "rebuilding" end
    if row.lord == nil or row.lord == NO_LORD then return "claimed" end
    if row.stalled then return "stalled" end
    return "thriving"
end

-- A vassal pays when its lord took over and the village is not rebuilding (the tribute tick uses the same rule).
function M.pays(row)
    return row.lord ~= nil and row.lord ~= NO_LORD and not row.rebuilding
end

function M.note_of(status, config)
    if status == "thriving" then return "The lord sends the rich resources of the region each month." end
    if status == "stalled" then
        return string.format("The lord has built fewer than %d buildings in %d days.", config.growth_min_buildings, config.growth_check_days)
    end
    if status == "rebuilding" then return "No tribute until the village is rebuilt." end
    if status == "wiped" then return "A Hussite sack ruined the village. The land is rubble." end
    return "The region pays tribute after a lord takes it over."
end

-- "100 stone, 100 flax" (one amount for each good, in the order of the goods list)
function M.tribute_text(goods, amount)
    if #goods == 0 then return "none" end
    local parts = {}
    for _, good in ipairs(goods) do parts[#parts + 1] = string.format("%d %s", amount, good) end
    return table.concat(parts, ", ")
end

function M.hint_text(factor, amount)
    return string.format("Tribute x%s: %d of each rich resource", M.factor_text(factor), amount)
end

function M.restore_hint(cost, enough)
    if enough then return string.format("Costs %d silver.", cost) end
    return string.format("Needs %d silver.", cost)
end

-- Wiped records in the order of their day, oldest first (a record without a day goes last; ties keep the record order).
function M.wiped_in_order(wiped)
    local list = {}
    for position, record in ipairs(wiped or {}) do list[#list + 1] = { record = record, position = position } end
    table.sort(list, function(a, b)
        local day_a, day_b = a.record.day or math.huge, b.record.day or math.huge
        if day_a ~= day_b then return day_a < day_b end
        return a.position < b.position
    end)
    local ordered = {}
    for _, item in ipairs(list) do ordered[#ordered + 1] = item.record end
    return ordered
end

-- Adds `amount` of each good to the totals (a list of { good, amount } in first-seen order).
local function add_total(totals, good, amount)
    for _, entry in ipairs(totals) do
        if entry.good == good then entry.amount = entry.amount + amount; return end
    end
    totals[#totals + 1] = { good = good, amount = amount }
end

function M.total_text(totals)
    if #totals == 0 then return "none" end
    local parts = {}
    for _, entry in ipairs(totals) do parts[#parts + 1] = string.format("%d %s", entry.amount, entry.good) end
    return table.concat(parts, ", ")
end

local function vassal_card(position, row, input, totals)
    local config = input.config
    local status = M.status_of(row)
    local policy = config.policies[row.policy] and row.policy or "fair"
    local factor = (config.policies[policy] or { tribute = 1.0 }).tribute
    local amount = input.amount(factor)
    local goods = input.goods_of(row.region) or {}
    local pays = M.pays(row)
    if pays then
        for _, good in ipairs(goods) do add_total(totals, good, amount) end
    end
    local policies = {}
    for _, name in ipairs(M.POLICIES) do policies[#policies + 1] = { name = name, text = M.policy_text(name), selected = name == policy } end
    return {
        position = position - 1, kind = "vassal", slot = row.slot, region = row.region, status = status, status_text = M.STATUS_TEXT[status],
        title = input.name_of(row.region) or M.region_text(row.region),
        lord_line = (row.lord ~= nil and row.lord ~= NO_LORD) and ("Lord " .. row.lord) or "No lord yet",
        stats = {
            M.STATUS_TEXT[status],
            #goods > 0 and table.concat(goods, ", ") or "-",
            pays and M.tribute_text(goods, amount) or "none",
            tostring(row.families or 0),
            tostring(row.buildings or 0),
            M.days_text(M.days_as_vassal(row.handed_day, input.today)),
        },
        note = M.note_of(status, config),
        policy = policy, policies = policies, policy_hint = M.hint_text(factor, amount),
        restore = nil, dim = false,
    }
end

local function wiped_card(position, record, input)
    local cost = input.config.restore.silver
    local enough = type(input.silver) == "number" and input.silver >= cost
    return {
        position = position - 1, kind = "wiped", region = record.region, status = "wiped", status_text = M.STATUS_TEXT.wiped,
        title = input.name_of(record.region) or M.region_text(record.region), lord_line = "No lord",
        stats = { M.STATUS_TEXT.wiped, "", "", "", "", "" },
        note = M.note_of("wiped", input.config), policies = {},
        restore = { text = "Restore the village", cost = cost, enabled = enough, hint = M.restore_hint(cost, enough), region = record.region },
        dim = false,
    }
end

local function free_card(position)
    return { position = position - 1, kind = "free", status = "free", status_text = "", title = M.FREE_TITLE, lord_line = "",
             stats = { "", "", "", "", "", "" }, note = M.FREE_NOTE, policies = {}, dim = true }
end

-- input = {
--   config = config.vassals (max_vassals, policies, restore, growth_*),
--   rows = the registered vassals (list of { slot, region, lord, handed_day, stalled, rebuilding, policy, families, buildings }),
--   wiped = the wiped records ({ region, lord, day }), silver = number or nil, today = game day or nil,
--   goods_of = function(region) -> list of paid good names, amount = function(policy factor) -> units of each good,
-- }
-- Cards stay in slot order (owner decision 7). Wiped villages fill the free slots, oldest first (decision 1). A slot that was never
-- claimed is a dim "Free slot" card (decision 2).
function M.build(input)
    -- name_of(region) gives the display name that the game shows (region.regionName), or nil: then the internal name is capitalised.
    input.name_of = input.name_of or function() return nil end
    local max = input.config.max_vassals
    local by_slot = {}
    for _, row in ipairs(input.rows) do by_slot[row.slot] = row end
    local wiped = M.wiped_in_order(input.wiped)
    local next_wiped = 1
    local totals, cards, count = {}, {}, 0
    for position = 1, max do
        local row = by_slot[position]
        if row then
            count = count + 1
            cards[position] = vassal_card(position, row, input, totals)
        elseif wiped[next_wiped] then
            cards[position] = wiped_card(position, wiped[next_wiped], input)
            next_wiped = next_wiped + 1
        else
            cards[position] = free_card(position)
        end
    end
    local silver = type(input.silver) == "number" and math.floor(input.silver) or nil
    return {
        count = count, max = max, count_text = string.format("%d / %d", count, max),
        tribute_totals = totals, tribute_text = M.total_text(totals),
        silver = silver, silver_text = silver and string.format("%d silver", silver) or "-",
        cards = cards,
    }
end

return M
