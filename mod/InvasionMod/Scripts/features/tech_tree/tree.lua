-- Pure loader of the tech tree data (M12). No game access, so plain Lua and the fake game can test it.
-- The data file is JSON (data/tech_tree/tree.json). Every problem stops the load with a clear message (error with level 0).
local M = {}

M.EFFECT_KINDS = {
    public_order = "add",          -- value is added to Public Order
    approval = "add",              -- value is added to the approval that the Public Order debuff uses
    buy_back_price = "percent",    -- value is a change of the buy-back price (0.25 is +25%)
    militia_attack = "percent",
    militia_defence = "percent",
    retinue_capacity = "add",      -- value is added to the retinue limit of the manor (men)
    tribute_share = "percent",     -- value is a change of the tribute share of all vassals (0.25 is +25%)
    manor_storage = "add",         -- value is added to the capacity of a manor module (units of goods)
}

local function fail(message) error("tech tree data: " .. message, 0) end

local function require_type(value, expected, what)
    if type(value) ~= expected then fail(what .. " must be a " .. expected .. ", got " .. type(value)) end
    return value
end

local function read_paths(doc)
    local paths, by_id = {}, {}
    require_type(doc.paths, "table", "'paths'")
    if #doc.paths ~= 2 then fail("'paths' must list exactly 2 paths, got " .. #doc.paths) end
    for _, path in ipairs(doc.paths) do
        require_type(path.id, "string", "path id")
        require_type(path.name, "string", "name of path '" .. path.id .. "'")
        if by_id[path.id] then fail("duplicate path id '" .. path.id .. "'") end
        by_id[path.id] = { id = path.id, name = path.name }
        paths[#paths + 1] = by_id[path.id]
    end
    return paths, by_id
end

local function read_effect(effect, node_id)
    local where = "effect of node '" .. node_id .. "'"
    require_type(effect, "table", where)
    if M.EFFECT_KINDS[effect.kind] == nil then fail(where .. " has unknown kind '" .. tostring(effect.kind) .. "'") end
    require_type(effect.value, "number", where .. " value")
    if effect.min_garrison_squads ~= nil then require_type(effect.min_garrison_squads, "number", where .. " min_garrison_squads") end
    return { kind = effect.kind, value = effect.value, min_garrison_squads = effect.min_garrison_squads }
end

local function read_node(raw, path_ids)
    require_type(raw, "table", "a node")
    require_type(raw.id, "string", "node id")
    local id = raw.id
    -- ModState keeps the unlocked ids in one text with dots between them.
    if id:find("[^%w_%-]") then fail("node id '" .. id .. "' may hold only letters, digits, _ and -") end
    require_type(raw.name, "string", "name of node '" .. id .. "'")
    if not path_ids[raw.path] then fail("node '" .. id .. "' has unknown path '" .. tostring(raw.path) .. "'") end
    require_type(raw.requires, "table", "'requires' of node '" .. id .. "'")
    require_type(raw.effect, "table", "'effect' of node '" .. id .. "'")
    if #raw.effect < 1 then fail("node '" .. id .. "' has no effect") end
    local node = { id = id, path = raw.path, name = raw.name, requires = {}, effects = {} }
    for _, required in ipairs(raw.requires) do
        node.requires[#node.requires + 1] = require_type(required, "string", "a 'requires' entry of node '" .. id .. "'")
    end
    for _, effect in ipairs(raw.effect) do node.effects[#node.effects + 1] = read_effect(effect, id) end
    if raw.layout ~= nil then
        require_type(raw.layout, "table", "'layout' of node '" .. id .. "'")
        node.layout = { x = require_type(raw.layout.x, "number", "layout x of node '" .. id .. "'"),
                        y = require_type(raw.layout.y, "number", "layout y of node '" .. id .. "'") }
    end
    return node
end

local function check_requires(nodes, by_id)
    for _, node in ipairs(nodes) do
        for _, required in ipairs(node.requires) do
            local other = by_id[required]
            if other == nil then fail("node '" .. node.id .. "' requires unknown node '" .. required .. "'") end
            if other.path ~= node.path then fail("node '" .. node.id .. "' requires '" .. required .. "' of another path") end
        end
    end
end

-- Depth-first search. A cycle is reported with the nodes on it.
local function check_cycles(nodes, by_id)
    local state = {}
    local function visit(node, trail)
        if state[node.id] == "done" then return end
        if state[node.id] == "visiting" then fail("cycle in requires: " .. table.concat(trail, " -> ") .. " -> " .. node.id) end
        state[node.id] = "visiting"
        trail[#trail + 1] = node.id
        for _, required in ipairs(node.requires) do visit(by_id[required], trail) end
        trail[#trail] = nil
        state[node.id] = "done"
    end
    for _, node in ipairs(nodes) do visit(node, {}) end
end

-- Depth of a node = longest chain of requires below it. Used for the default layout.
local function depth_of(node, by_id, memo)
    if memo[node.id] then return memo[node.id] end
    local depth = 0
    for _, required in ipairs(node.requires) do depth = math.max(depth, depth_of(by_id[required], by_id, memo) + 1) end
    memo[node.id] = depth
    return depth
end

-- A node with no layout gets x = depth and y = row of its path, then half a row for each node at the same depth.
local function fill_default_layout(nodes, by_id, paths)
    local memo, rows, path_row = {}, {}, {}
    for index, path in ipairs(paths) do path_row[path.id] = index - 1 end
    for _, node in ipairs(nodes) do
        if node.layout == nil then
            local depth = depth_of(node, by_id, memo)
            local key = node.path .. ":" .. depth
            rows[key] = (rows[key] or 0) + 1
            node.layout = { x = depth, y = path_row[node.path] + (rows[key] - 1) * 0.5 }
        end
    end
end

-- Laws (M12.04): { id, path, name, requires (node ids of the same path), effect }. The id may not equal a node id.
local function read_laws(doc, by_id, path_ids)
    local laws, laws_by_id = {}, {}
    if doc.laws == nil then return laws, laws_by_id end
    require_type(doc.laws, "table", "'laws'")
    for _, raw in ipairs(doc.laws) do
        require_type(raw, "table", "a law")
        local id = require_type(raw.id, "string", "law id")
        if by_id[id] or laws_by_id[id] then fail("law id '" .. id .. "' is not unique") end
        if not path_ids[raw.path] then fail("law '" .. id .. "' has unknown path '" .. tostring(raw.path) .. "'") end
        require_type(raw.name, "string", "name of law '" .. id .. "'")
        require_type(raw.requires, "table", "'requires' of law '" .. id .. "'")
        require_type(raw.effect, "table", "'effect' of law '" .. id .. "'")
        if #raw.effect < 1 then fail("law '" .. id .. "' has no effect") end
        local law = { id = id, path = raw.path, name = raw.name, requires = {}, effects = {} }
        for _, required in ipairs(raw.requires) do
            local node = by_id[required]
            if node == nil then fail("law '" .. id .. "' requires unknown node '" .. tostring(required) .. "'") end
            if node.path ~= raw.path then fail("law '" .. id .. "' requires '" .. required .. "' of another path") end
            law.requires[#law.requires + 1] = required
        end
        for _, effect in ipairs(raw.effect) do law.effects[#law.effects + 1] = read_effect(effect, id) end
        laws[#laws + 1] = law
        laws_by_id[id] = law
    end
    return laws, laws_by_id
end

-- Vassal policies that need a path and nodes (M12.04): { policy, path, requires }. The policy "fair" is always open.
local function read_policy_gates(doc, by_id, path_ids)
    local gates = {}
    if doc.vassal_policies == nil then return gates end
    require_type(doc.vassal_policies, "table", "'vassal_policies'")
    for _, raw in ipairs(doc.vassal_policies) do
        local name = require_type(raw.policy, "string", "vassal policy name")
        if not path_ids[raw.path] then fail("vassal policy '" .. name .. "' has unknown path '" .. tostring(raw.path) .. "'") end
        require_type(raw.requires, "table", "'requires' of vassal policy '" .. name .. "'")
        for _, required in ipairs(raw.requires) do
            if by_id[required] == nil then fail("vassal policy '" .. name .. "' requires unknown node '" .. tostring(required) .. "'") end
        end
        gates[name] = { path = raw.path, requires = raw.requires }
    end
    return gates
end

-- Build the tree from a decoded document. Returns { paths, path_ids, nodes (in file order), by_id, laws, laws_by_id, policy_gates }.
function M.build(doc)
    require_type(doc, "table", "the document")
    if doc.version ~= 1 then fail("unsupported version " .. tostring(doc.version)) end
    local paths, path_ids = read_paths(doc)
    require_type(doc.nodes, "table", "'nodes'")
    local nodes, by_id = {}, {}
    for _, raw in ipairs(doc.nodes) do
        local node = read_node(raw, path_ids)
        if by_id[node.id] then fail("duplicate node id '" .. node.id .. "'") end
        by_id[node.id] = node
        nodes[#nodes + 1] = node
    end
    if #nodes == 0 then fail("no nodes") end
    check_requires(nodes, by_id)
    check_cycles(nodes, by_id)
    fill_default_layout(nodes, by_id, paths)
    local laws, laws_by_id = read_laws(doc, by_id, path_ids)
    return { paths = paths, path_ids = path_ids, nodes = nodes, by_id = by_id, laws = laws, laws_by_id = laws_by_id,
             policy_gates = read_policy_gates(doc, by_id, path_ids) }
end

-- Read and build a tree from a file. `decode` is HarnessJson.decode.
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
