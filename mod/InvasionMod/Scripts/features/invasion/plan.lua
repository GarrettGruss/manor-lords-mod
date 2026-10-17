-- Pure rules of the raid plan (no game calls), so a test can run them without a game.
local M = {}

M.SIZE_CLASSES = { small = 1, medium = 2, large = 3 }
M.SIZE_NAMES = { "small", "medium", "large" }

-- A random whole number from low to high. The random function is a parameter so a test can fix it.
function M.pick(random, low, high)
    if high < low then error("plan: bad range " .. low .. ".." .. high, 0) end
    return random(low, high)
end

-- Raid size in squads: base size multiplier times difficulty (decisions 8 and 22).
function M.squads(size_class, difficulty, multipliers)
    local multiplier = multipliers[M.SIZE_NAMES[size_class]]
    if multiplier == nil then error("plan: unknown size class " .. tostring(size_class), 0) end
    return multiplier * difficulty
end

-- Plan the first raid. `today` is the game day when the plan is made.
-- The warning cannot start before the plan exists, so a short wait gives a shorter warning.
function M.first_raid(today, difficulty, config, random)
    local wait = M.pick(random, config.first_raid_days_min, config.first_raid_days_max)
    local warning = math.min(M.pick(random, config.warning_days_min, config.warning_days_max), wait)
    local size_class = M.pick(random, 1, #M.SIZE_NAMES)
    return {
        plan_day = today,
        raid_day = today + wait,
        warning_day = today + wait - warning,
        size_class = size_class,
        squads = M.squads(size_class, difficulty, config.size_multipliers),
    }
end

-- Hussite roles (M05 iteration 02). Pure rules: which template each squad of a raid gets.
-- Rounding half up, so a share of 0.5 of 1 squad gives 1.
local function round_half_up(value)
    return math.floor(value + 0.5)
end

-- Split `total` over weights by largest remainder. A tie goes to the lower index.
function M.apportion(total, weights)
    local sum = 0
    for _, weight in ipairs(weights) do sum = sum + weight end
    if sum <= 0 then error("plan: the weights must have a positive sum", 0) end
    local counts, remainders, given = {}, {}, 0
    for index, weight in ipairs(weights) do
        local exact = total * weight / sum
        counts[index] = math.floor(exact)
        remainders[index] = exact - counts[index]
        given = given + counts[index]
    end
    while given < total do
        local best = 1
        for index = 2, #weights do
            if remainders[index] > remainders[best] + 1e-9 then best = index end
        end
        counts[best], remainders[best], given = counts[best] + 1, -1, given + 1
    end
    return counts
end

local function pick_from(list, random)
    if #list == 0 then error("plan: a tier has no template", 0) end
    return list[M.pick(random, 1, #list)]
end

-- Counts of squads by role and tier: { melee = {n1, n2, n3}, ranged = {n1, n2} }.
function M.role_counts(squads, difficulty, roles)
    local weights = roles.melee_tier_weights[difficulty]
    local crossbows = roles.crossbow_share[difficulty]
    if weights == nil or crossbows == nil then error("plan: no role table for difficulty " .. tostring(difficulty), 0) end
    local ranged = round_half_up(squads * roles.ranged_share)
    local tier2 = round_half_up(ranged * crossbows)
    return { melee = M.apportion(squads - ranged, weights), ranged = { ranged - tier2, tier2 } }
end

-- The template of each squad: melee from tier I up, then ranged from tier I up. `random` picks a template of a tier.
function M.composition(squads, difficulty, roles, random)
    if squads < 1 then error("plan: a raid needs at least 1 squad", 0) end
    local counts = M.role_counts(squads, difficulty, roles)
    local list = {}
    for _, role in ipairs({ "melee", "ranged" }) do
        for tier, count in ipairs(counts[role]) do
            for _ = 1, count do list[#list + 1] = pick_from(roles.templates[role][tier], random) end
        end
    end
    return list
end

-- ModState strings allow only A-Z a-z 0-9 _ . - so the list is joined with "-".
function M.join(list)
    return table.concat(list, "-")
end

function M.split(text)
    local list = {}
    for name in text:gmatch("[^-]+") do list[#list + 1] = name end
    return list
end

function M.expected_units(list, template_units)
    local total = 0
    for _, name in ipairs(list) do
        local units = template_units[name]
        if units == nil then error("plan: no unit count for template " .. name, 0) end
        total = total + units
    end
    return total
end

function M.banner_text(days_left, raiders)
    local unit = days_left == 1 and "day" or "days"
    return string.format("Raid in %d %s, about %d raiders", days_left, unit, raiders)
end

return M
