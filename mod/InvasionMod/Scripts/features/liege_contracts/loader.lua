-- Pure loader of the contracts table (change update-liege-tribute-to-contracts, #505). No game access.
-- The data file is JSON (data/liege_contracts/contracts.json). Every problem stops the load with a message that names the
-- contract and the field (error with level 0), as the tech tree loader does.
local M = {}

-- Fields of each objective type: name -> kind. "int" is a whole number of at least 1, "number" a number, "id" a whole number of at least 0.
M.OBJECTIVE_TYPES = {
    deliver_goods = { good = "id", amount = "int" },
    build_count = { building_type = "id", amount = "int" },
    kill_raiders = { amount = "int" },
    hold_public_order = { min = "order", days = "int" },
    raise_militia_squads = { amount = "int" },
}

M.REWARD_TYPES = {
    influence = { amount = "int" },
    silver = { amount = "int" },
    goods = { good = "id", amount = "int" },
    public_order = { amount = "int" },
    tech_pick = { amount = "int" },
}

M.MAX_OBJECTIVES, M.MAX_REWARDS, M.DEFAULT_OFFER_SIZE = 2, 3, 3

local function fail(message) error("liege contracts data: " .. message, 0) end

local function check_kind(value, kind, where)
    if type(value) ~= "number" or value ~= value or value ~= math.floor(value) and kind ~= "order" then
        fail(where .. " must be a number, got " .. tostring(value))
    end
    if kind == "int" and (value < 1 or value ~= math.floor(value)) then fail(where .. " must be a whole number of at least 1, got " .. tostring(value)) end
    if kind == "id" and (value < 0 or value ~= math.floor(value)) then fail(where .. " must be a whole number of at least 0, got " .. tostring(value)) end
    if kind == "order" and (value < 0 or value > 100) then fail(where .. " must be 0 to 100, got " .. tostring(value)) end
end

-- Copy the typed fields of one objective or reward item. `types` is OBJECTIVE_TYPES or REWARD_TYPES.
local function read_item(raw, types, label, contract_id)
    local where = string.format("contract '%s' %s", contract_id, label)
    if type(raw) ~= "table" then fail(where .. " must be a table") end
    local fields = types[raw.type]
    if fields == nil then fail(where .. " has unknown type '" .. tostring(raw.type) .. "'") end
    local item = { type = raw.type }
    for field, kind in pairs(fields) do
        if raw[field] == nil then fail(where .. " (" .. raw.type .. ") is missing the field '" .. field .. "'") end
        check_kind(raw[field], kind, where .. " field '" .. field .. "'")
        item[field] = raw[field]
    end
    return item
end

local function read_list(raw, types, label, max, contract_id)
    if type(raw) ~= "table" or #raw < 1 then fail(string.format("contract '%s' field '%s' must list at least 1 entry", contract_id, label)) end
    if #raw > max then fail(string.format("contract '%s' field '%s' lists %d entries, at most %d are allowed", contract_id, label, #raw, max)) end
    local list = {}
    for index, entry in ipairs(raw) do list[#list + 1] = read_item(entry, types, label .. " " .. index, contract_id) end
    return list
end

local function read_contract(raw, position)
    if type(raw) ~= "table" then fail("contract " .. position .. " must be a table") end
    local id = raw.id
    if type(id) ~= "string" or id == "" then fail("contract " .. position .. " is missing the field 'id'") end
    -- ModState keeps the offer ids in one text with dots between them.
    if id:find("[^%w_%-]") then fail("contract id '" .. id .. "' may hold only letters, digits, _ and -") end
    if type(raw.name) ~= "string" or raw.name == "" then fail(string.format("contract '%s' is missing the field 'name'", id)) end
    local quote = raw.quote
    if quote ~= nil and type(quote) ~= "string" then fail(string.format("contract '%s' field 'quote' must be text", id)) end
    if type(raw.weight) ~= "number" or raw.weight <= 0 then fail(string.format("contract '%s' field 'weight' must be a number above 0", id)) end
    local duration = raw.duration
    if duration ~= "winter_start" and not (type(duration) == "number" and duration >= 1) then
        fail(string.format("contract '%s' field 'duration' must be \"winter_start\" or a number of days, got %s", id, tostring(duration)))
    end
    return { id = id, name = raw.name, quote = quote or "", weight = raw.weight, duration = duration,
             objectives = read_list(raw.objectives, M.OBJECTIVE_TYPES, "objectives", M.MAX_OBJECTIVES, id),
             rewards = read_list(raw.rewards, M.REWARD_TYPES, "rewards", M.MAX_REWARDS, id) }
end

local function read_items(raw)
    local items = {}
    if raw == nil then return items end
    if type(raw) ~= "table" then fail("field 'items' must be a table") end
    for key, entry in pairs(raw) do
        if type(entry) ~= "table" or type(entry.name) ~= "string" then fail("item '" .. tostring(key) .. "' needs a 'name'") end
        items[key] = { name = entry.name, description = type(entry.description) == "string" and entry.description or "" }
    end
    return items
end

-- Build the table from a decoded document. Returns { version, offer_size, contracts, by_id, items }.
function M.build(doc)
    if type(doc) ~= "table" then fail("the document must be a table") end
    if doc.version ~= 1 then fail("field 'version' must be 1, got " .. tostring(doc.version)) end
    local offer_size = doc.offer_size == nil and M.DEFAULT_OFFER_SIZE or doc.offer_size
    if type(offer_size) ~= "number" or offer_size < 1 or offer_size ~= math.floor(offer_size) then fail("field 'offer_size' must be a whole number of at least 1") end
    if type(doc.contracts) ~= "table" then fail("field 'contracts' must be a list") end
    local contracts, by_id = {}, {}
    for position, raw in ipairs(doc.contracts) do
        local contract = read_contract(raw, position)
        if by_id[contract.id] then fail("duplicate contract id '" .. contract.id .. "'") end
        by_id[contract.id] = contract
        contracts[#contracts + 1] = contract
    end
    if #contracts < offer_size then fail(string.format("the table has %d contracts, but offer_size is %d", #contracts, offer_size)) end
    return { version = doc.version, offer_size = offer_size, contracts = contracts, by_id = by_id, items = read_items(doc.items) }
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
