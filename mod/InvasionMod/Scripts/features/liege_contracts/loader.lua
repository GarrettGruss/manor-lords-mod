-- Pure loader of the contracts table (change update-liege-contracts-tiers, #533). No game access.
-- The data file is JSON (data/liege_contracts/contracts.json). Every problem stops the load with a message that names the
-- tier and the field (error with level 0), as the tech tree loader does.
local M = {}

M.TIERS = { "small", "medium", "large" } -- the order of the rows in the window
M.DEFAULT_OFFER_PER_TIER = 3

-- Reward kinds. `goods` lists the kinds that need a list of good ids.
M.REWARD_KINDS = { goods = true, weapons = true, regional_wealth = false, silver = false, tech_point = false, influence = false }

local function fail(message) error("liege contracts data: " .. message, 0) end

local function whole(value, where, least)
    if type(value) ~= "number" or value ~= value or value ~= math.floor(value) or value < least then
        fail(where .. " must be a whole number of at least " .. least .. ", got " .. tostring(value))
    end
end

local function read_request(raw, tier, position)
    local where = string.format("tier '%s' request %d", tier, position)
    if type(raw) ~= "table" then fail(where .. " must be a table") end
    if raw.good == nil then fail(where .. " is missing the field 'good'") end
    whole(raw.good, where .. " field 'good'", 0)
    if type(raw.weight) ~= "number" or raw.weight ~= raw.weight or raw.weight <= 0 then
        fail(where .. " field 'weight' must be a number above 0, got " .. tostring(raw.weight))
    end
    return { good = math.tointeger(raw.good) or raw.good, weight = raw.weight }
end

local function read_reward(raw, tier, position, lists)
    local where = string.format("tier '%s' reward %d", tier, position)
    if type(raw) ~= "table" then fail(where .. " must be a table") end
    local needs_goods = M.REWARD_KINDS[raw.kind]
    if needs_goods == nil then fail(where .. " has unknown kind '" .. tostring(raw.kind) .. "'") end
    if raw.min == nil then fail(where .. " is missing the field 'min'") end
    if raw.max == nil then fail(where .. " is missing the field 'max'") end
    whole(raw.min, where .. " field 'min'", 1)
    whole(raw.max, where .. " field 'max'", raw.min)
    local reward = { kind = raw.kind, min = math.tointeger(raw.min) or raw.min, max = math.tointeger(raw.max) or raw.max }
    if needs_goods then
        -- The data file names a list of good ids (JSON nesting is limited, so the lists are in the top level field 'good_lists').
        local list = lists[raw.goods]
        if list == nil then fail(where .. " (" .. raw.kind .. ") needs the field 'goods' with the name of a list in 'good_lists', got " .. tostring(raw.goods)) end
        reward.goods = list
    end
    return reward
end

local function read_tier(raw, tier, offer_per_tier, lists)
    if type(raw) ~= "table" then fail("tier '" .. tier .. "' is missing") end
    if type(raw.requests) ~= "table" or #raw.requests < offer_per_tier then
        fail(string.format("tier '%s' has %d requests, but offer_per_tier is %d", tier, type(raw.requests) == "table" and #raw.requests or 0, offer_per_tier))
    end
    if type(raw.rewards) ~= "table" or #raw.rewards < 1 then fail("tier '" .. tier .. "' needs at least 1 reward") end
    local requests, seen = {}, {}
    for position, entry in ipairs(raw.requests) do
        local request = read_request(entry, tier, position)
        if seen[request.good] then fail(string.format("tier '%s' lists the good %d twice", tier, request.good)) end
        seen[request.good] = true
        requests[#requests + 1] = request
    end
    local rewards = {}
    for position, entry in ipairs(raw.rewards) do rewards[#rewards + 1] = read_reward(entry, tier, position, lists) end
    return { requests = requests, rewards = rewards }
end

-- Build the table from a decoded document. Returns { version, offer_per_tier, tiers, names }.
function M.build(doc)
    if type(doc) ~= "table" then fail("the document must be a table") end
    if doc.version ~= 2 then fail("field 'version' must be 2, got " .. tostring(doc.version)) end
    local per_tier = doc.offer_per_tier == nil and M.DEFAULT_OFFER_PER_TIER or doc.offer_per_tier
    per_tier = math.tointeger(per_tier) or per_tier
    whole(per_tier, "field 'offer_per_tier'", 1)
    if type(doc.tiers) ~= "table" then fail("field 'tiers' must be a table") end
    local lists = {}
    for name, ids in pairs(doc.good_lists or {}) do
        if type(ids) ~= "table" or #ids < 1 then fail("good list '" .. tostring(name) .. "' needs at least 1 good id") end
        lists[name] = {}
        for index, good in ipairs(ids) do
            whole(good, "good list '" .. tostring(name) .. "' entry " .. index, 0)
            lists[name][#lists[name] + 1] = math.tointeger(good) or good
        end
    end
    local tiers = {}
    for _, tier in ipairs(M.TIERS) do tiers[tier] = read_tier(doc.tiers[tier], tier, per_tier, lists) end
    local names = {}
    for key, name in pairs(doc.names or {}) do
        if type(name) ~= "string" or name == "" then fail("name of good " .. tostring(key) .. " must be text") end
        names[tonumber(key) or key] = name
    end
    return { version = doc.version, offer_per_tier = per_tier, tiers = tiers, names = names }
end

-- Read and build a table from a file. `decode` is HarnessJson.decode.
function M.load_file(file_path, decode)
    local handle, why = io.open(file_path, "rb")
    if not handle then fail("cannot open " .. file_path .. ": " .. tostring(why)) end
    local text = handle:read("*a")
    handle:close()
    local doc, problem = decode(text)
    if doc == nil then fail(file_path .. ": " .. tostring(problem)) end
    return M.build(doc)
end

return M
