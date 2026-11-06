-- Pure rules of the feature liege_contracts (changes update-liege-contracts-tiers, #533, and update-liege-contracts-tier-goods, #569). No game access, so plain Lua and the fake game can test them.
local M = {}

M.TIERS = { "small", "medium", "large" }
M.TIERS_INDEX = { small = 1, medium = 2, large = 3 }
local TIER_LETTER = { small = "s", medium = "m", large = "l" }
local LETTER_TIER = { s = "small", m = "medium", l = "large" }
local KIND_LETTER = { goods = "g", weapons = "w", armor = "a", law = "l", kings_favour = "k", law_slot = "s", relief_promise = "p" }
-- A Large contract has a cost in place of a good. The saved text holds the cost code in the place of the good id.
M.COST_CODE = { loan_units = 1, send_families = 2, tribute_season = 3 }
local CODE_COST = {}
for cost, code in pairs(M.COST_CODE) do CODE_COST[code] = cost end
local LETTER_KIND = {}
for kind, letter in pairs(KIND_LETTER) do LETTER_KIND[letter] = kind end

---------------------------------------------------------------------------------------------
-- The request amount
---------------------------------------------------------------------------------------------

-- Rounds half up. A small bias keeps 0.5 products such as 15 * 0.35 * 1.0 = 5.25 and 50 * 1.4 = 70.0 stable.
local function round_half_up(value) return math.floor(value + 0.5 + 1e-9) end

-- amount = max(1, round(base(tier) * weight(good) * difficulty))
function M.request_amount(base, weight, difficulty)
    return math.max(1, round_half_up(base * weight * difficulty))
end

-- The difficulty multiplier of a raid level (0 to 3). `table` is config liege_contracts.difficulty. An unknown level counts as 1.0.
function M.difficulty_for(level, table)
    return table[level] or 1.0
end

---------------------------------------------------------------------------------------------
-- The draw
---------------------------------------------------------------------------------------------

-- A random whole number from low to high. `rng()` returns a number in [0, 1).
local function between(low, high, rng) return low + math.floor(rng() * (high - low + 1)) end

local function pick_distinct(list, count, rng)
    local pool = {}
    for index, entry in ipairs(list) do pool[index] = entry end
    local picked = {}
    for _ = 1, count do
        local at = between(1, #pool, rng)
        picked[#picked + 1] = table.remove(pool, at)
    end
    return picked
end

-- One reward from the pool of a tier. `allowed(kind)` filters the kinds that cannot be drawn now (no locked law, the slot cap). The
-- reward good is never the request good. Returns { kind, good, amount }, or nil and a message.
local function draw_reward(pool, request_good, allowed, rng)
    local rows = {}
    for _, row in ipairs(pool) do
        if allowed == nil or allowed(row.kind) then rows[#rows + 1] = row end
    end
    if #rows == 0 then return nil, "no reward in the pool can be paid" end
    local row = rows[between(1, #rows, rng)]
    local reward = { kind = row.kind, amount = between(row.min, row.max, rng) }
    if row.goods then
        local goods = {}
        for _, good in ipairs(row.goods) do
            if good ~= request_good then goods[#goods + 1] = good end
        end
        if #goods == 0 then return nil, "the reward pool holds only the request good" end
        reward.good = goods[between(1, #goods, rng)]
    end
    return reward
end

-- The amount of a Large cost: the drawn amount scaled by the difficulty (decision 11 of the change).
function M.cost_amount(amount, difficulty)
    return math.max(1, round_half_up(amount * difficulty))
end

-- Draws the offer: `per_tier` different requests for each tier, each with one reward.
-- `setup`: { tiers = the loaded table, base = { small, medium }, weight = { [good] = override }, difficulty = number, allowed = fn(kind),
--            cost_allowed = fn(cost kind) }
-- Returns a list of contracts { id, tier, number, good (or cost), amount, reward, done = false } in tier order, or nil and a message.
function M.draw_offer(setup, per_tier, rng)
    local offer = {}
    for _, tier in ipairs(M.TIERS) do
        local pool = setup.tiers[tier]
        if pool == nil then return nil, "tier " .. tier .. " is missing" end
        local requests = {}
        for _, request in ipairs(pool.requests) do
            if request.cost == nil or setup.cost_allowed == nil or setup.cost_allowed(request.cost) then requests[#requests + 1] = request end
        end
        if #requests < per_tier then return nil, string.format("tier %s has fewer than %d requests", tier, per_tier) end
        for number, request in ipairs(pick_distinct(requests, per_tier, rng)) do
            local reward, why = draw_reward(pool.rewards, request.good, setup.allowed, rng)
            if reward == nil then return nil, tier .. ": " .. tostring(why) end
            local contract = { id = tier .. "-" .. number, tier = tier, number = number, done = false, reward = reward }
            if request.cost then
                contract.cost = request.cost
                contract.amount = M.cost_amount(between(request.min, request.max, rng), setup.difficulty)
            else
                local weight = (setup.weight and setup.weight[request.good]) or request.weight
                contract.good = request.good
                contract.amount = M.request_amount(setup.base[tier], weight, setup.difficulty)
            end
            offer[#offer + 1] = contract
        end
    end
    return offer
end

---------------------------------------------------------------------------------------------
-- Saved text. ModState strings allow only letters, digits, _ . and -. One contract is
-- "<tier letter>-<good>-<amount>-<reward letter>-<reward good>-<reward amount>-<done 0|1>", contracts are separated by dots,
-- for example "s-17-50-g-146-30-0". The tier counts are "s-1.m-0.l-0".
---------------------------------------------------------------------------------------------

function M.encode_offer(offer)
    local parts = {}
    for _, c in ipairs(offer) do
        parts[#parts + 1] = string.format("%s-%d-%d-%s-%d-%d-%d", TIER_LETTER[c.tier], c.cost and M.COST_CODE[c.cost] or c.good, c.amount, KIND_LETTER[c.reward.kind],
            c.reward.good or 0, c.reward.amount, c.done and 1 or 0)
    end
    return table.concat(parts, ".")
end

-- Returns the list of contracts, and the list of texts that could not be read (to log them). `known(c)` may reject a contract
-- whose good (or cost) the table no longer has (it returns false and a reason).
function M.decode_offer(text, known)
    local offer, dropped, count = {}, {}, {}
    if text == nil or text == "" then return offer, dropped end
    for entry in string.gmatch(text, "[^%.]+") do
        local t, good, amount, k, rgood, ramount, done = entry:match("^(%a)%-(%d+)%-(%d+)%-(%a)%-(%d+)%-(%d+)%-([01])$")
        local tier, kind = LETTER_TIER[t or ""], LETTER_KIND[k or ""]
        if tier == nil or kind == nil then
            dropped[#dropped + 1] = entry
        else
            count[tier] = (count[tier] or 0) + 1
            local c = { id = tier .. "-" .. count[tier], tier = tier, number = count[tier], amount = tonumber(amount), done = done == "1",
                        reward = { kind = kind, good = tonumber(rgood) ~= 0 and tonumber(rgood) or nil, amount = tonumber(ramount) } }
            if tier == "large" then c.cost = CODE_COST[tonumber(good)] else c.good = tonumber(good) end
            if (tier ~= "large" or c.cost ~= nil) and (known == nil or known(c)) then offer[#offer + 1] = c else dropped[#dropped + 1] = entry end
        end
    end
    return offer, dropped
end

function M.encode_used(used)
    local parts = {}
    for _, tier in ipairs(M.TIERS) do parts[#parts + 1] = string.format("%s-%d", TIER_LETTER[tier], used[tier] or 0) end
    return table.concat(parts, ".")
end

function M.decode_used(text)
    local used = { small = 0, medium = 0, large = 0 }
    if text == nil or text == "" then return used end
    for entry in string.gmatch(text, "[^%.]+") do
        local t, number = entry:match("^(%a)%-(%d+)$")
        if LETTER_TIER[t or ""] then used[LETTER_TIER[t]] = tonumber(number) end
    end
    return used
end

---------------------------------------------------------------------------------------------
-- Fulfil
---------------------------------------------------------------------------------------------

M.NO_MANOR = "Build a manor to fulfil contracts."

-- Why a contract cannot be fulfilled now, or nil. The order of the checks is the order of the reasons shown to the player.
-- `facts`: { manor = bool, used = n of the tier, limit = n, stock = n or nil, cost_problem = text or nil (a Large cost that cannot be paid) }
function M.refusal(contract, facts)
    if contract == nil then return "the contract is not in the offer" end
    if contract.done then return "the contract is already fulfilled" end
    if not facts.manor then return M.NO_MANOR end
    if facts.used >= facts.limit then return string.format("the limit of %d for this tier is reached", facts.limit) end
    if contract.cost then return facts.cost_problem end
    if facts.stock == nil then return "the stock is not known" end
    if facts.stock < contract.amount then return string.format("%d more needed", contract.amount - facts.stock) end
    return nil
end

---------------------------------------------------------------------------------------------
-- Squad loans (decision 12 of the change). A loan record is "<template>-<men>-<experience>-<due day>", records are separated by dots.
-- ModState strings allow letters, digits, _ . and -, so a template name such as retinue_tier1 is safe.
---------------------------------------------------------------------------------------------

function M.encode_loans(list)
    local parts = {}
    for _, loan in ipairs(list) do
        parts[#parts + 1] = string.format("%s-%d-%d-%d", loan.template, loan.men, loan.experience, loan.due)
    end
    return table.concat(parts, ".")
end

function M.decode_loans(text)
    local list = {}
    if text == nil or text == "" then return list end
    for entry in string.gmatch(text, "[^%.]+") do
        local template, men, experience, due = entry:match("^([%w_]+)%-(%d+)%-(%d+)%-(%d+)$")
        if template then list[#list + 1] = { template = template, men = tonumber(men), experience = tonumber(experience), due = tonumber(due) } end
    end
    return list
end

-- The loans that are due on `day` (the first list) and the loans that stay (the second).
function M.split_loans(list, day)
    local due, kept = {}, {}
    for _, loan in ipairs(list) do
        if day ~= nil and day >= loan.due then due[#due + 1] = loan else kept[#kept + 1] = loan end
    end
    return due, kept
end

-- The template of a squad. `known` is the template that the game helper registry knows (a squad that was spawned by a script), or nil.
-- Otherwise the smallest size in `sizes` ({ { men = 32, template = "spearMilitia" }, ... }, in rising order) that is at least `men`.
-- Returns the template, or nil and a reason.
function M.loan_template(men, known, sizes)
    if known ~= nil then return known end
    for _, row in ipairs(sizes) do
        if men <= row.men then return row.template end
    end
    return nil, "the squad type is not known"
end

-- The most men that a squad has among `squads` ({ id, men, ... }), or nil.
function M.largest_squad(squads)
    local best
    for _, squad in ipairs(squads) do
        if squad.men > 0 and (best == nil or squad.men > best.men) then best = squad end
    end
    return best
end

-- The ids of the laws that are still locked: no node of the law is unlocked and no contract granted it (the rule of the Laws menu).
function M.locked_laws(laws, unlocked_nodes, granted)
    local have_node, have_grant, locked = {}, {}, {}
    for _, id in ipairs(unlocked_nodes) do have_node[id] = true end
    for _, id in ipairs(granted) do have_grant[id] = true end
    for _, law in ipairs(laws) do
        local by_node = true
        for _, required in ipairs(law.requires) do
            if not have_node[required] then by_node = false end
        end
        if not by_node and not have_grant[law.id] then locked[#locked + 1] = law.id end
    end
    return locked
end

---------------------------------------------------------------------------------------------
-- The calendar
---------------------------------------------------------------------------------------------

-- Game days from `day` (day of the year, 0 to year_days - 1) to the next `start` day of a season. 0 on the start day itself.
function M.days_until(day, start, year_days)
    if type(day) ~= "number" or type(start) ~= "number" then return nil end
    return (start - day) % year_days
end

return M
