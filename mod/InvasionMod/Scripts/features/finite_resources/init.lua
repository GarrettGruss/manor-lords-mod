-- Feature finite_resources (M10). Home deposits (iron first) are a mod-owned stock: the mod counts what the player buildings produce
-- (ProductionTrackerComponent:getGoodsProducedOver, summed over the buildings) and, when the stock is used up, sets the production limit
-- of the good to 0 for the player region (Region:setProductionLimit). Goods from vassals (tribute) do not count and are not blocked.
-- Spike: docs/mod/M10-finite_resources/implementation-notes/iteration-01-iron-deposit.md
local core = require("ManorCore")
local ModState = require("ModState")
local rules = require("features.finite_resources.rules")
local world = require("features.finite_resources.world")
local config = require("config").finite_resources

local TAG = "InvasionMod.finite_resources"
local STATE_VERSION = 1

local state = ModState.open("invasion", "pawn", STATE_VERSION)

-- name -> { good, size }. A test command may change an entry for this session.
local resources = {}
local names = {}
for name, entry in pairs(config.resources) do
    resources[name] = { good = entry.good, size = entry.size }
    names[#names + 1] = name
    state:register("fin_" .. name .. "_mined", 0, "integer")
    state:register("fin_" .. name .. "_last", rules.UNKNOWN, "integer")
end
table.sort(names)

local last_totals = {}
local all_totals = {}   -- good -> units produced, all goods, as of the last poll
local limit_errors = {}

local function key(name, field) return "fin_" .. name .. "_" .. field end

local function remaining(name)
    return rules.remaining(resources[name].size, state:get(key(name, "mined")))
end

local function enforce_limit(name)
    local entry = resources[name]
    if remaining(name) > 0 then return end
    if world.limit_of(entry.good) == 0 then return end
    local ok, why = world.set_limit(entry.good, 0)
    if not ok then
        limit_errors[name] = why
        return core.log.error(TAG, string.format("FINITE %s: production limit failed: %s", name, tostring(why)))
    end
    limit_errors[name] = nil
    core.log.info(TAG, string.format("FINITE %s deposit is empty: production of good %d is limited to 0", name, entry.good))
end

local function count(name, totals)
    local total = totals[resources[name].good] or 0
    last_totals[name] = total
    local last = state:get(key(name, "last"))
    local mined = rules.delta(total, last)
    if last ~= total then state:set(key(name, "last"), total) end
    if mined > 0 then
        state:set(key(name, "mined"), state:get(key(name, "mined")) + mined)
        core.log.info(TAG, string.format("FINITE %s mined +%d, %d left", name, mined, remaining(name)))
    end
end

local function poll()
    if not state.loaded then return end
    local totals = world.produced_by_good(config.window_days)
    if totals == nil then return end
    all_totals = totals
    for _, name in ipairs(names) do
        count(name, totals)
        enforce_limit(name)
    end
end

require("scheduler").every(TAG, config.poll_ms, poll)

local function resource_row(name)
    local entry, mined = resources[name], state:get(key(name, "mined"))
    return { name = name, good = entry.good, size = entry.size, mined = mined, remaining = rules.remaining(entry.size, mined),
        empty = rules.is_empty(entry.size, mined), limit = world.limit_of(entry.good), produced_total = last_totals[name], error = limit_errors[name] }
end

local function command_state()
    local rows = {}
    for _, name in ipairs(names) do rows[#rows + 1] = resource_row(name) end
    local produced = {}
    for good, amount in pairs(all_totals) do produced[tostring(good)] = amount end
    return { resources = rows, produced = produced }
end

-- Session-only, for scenarios: use another good and size for a resource (a real mine cannot be placed without the mouse).
local function command_test_set(args)
    local entry = resources[args.resource]
    if entry == nil then return nil, "unknown resource " .. tostring(args.resource) end
    world.clear_limit(entry.good)
    entry.good, entry.size = args.good, args.size
    state:set(key(args.resource, "mined"), 0)
    state:set(key(args.resource, "last"), rules.UNKNOWN)
    core.log.info(TAG, string.format("FINITE test: %s now uses good %d with size %d", args.resource, args.good, args.size))
    return command_state()
end

local function command_test_clear(args)
    local entry = resources[args.resource]
    if entry == nil then return nil, "unknown resource " .. tostring(args.resource) end
    local ok, why = world.clear_limit(entry.good)
    if not ok then return nil, why end
    return command_state()
end

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.finite_resources_state", command_state, {})
    commands.register("InvasionMod.finite_resources_test_set", command_test_set,
        { resource = { type = "string", required = true }, good = { type = "integer", required = true }, size = { type = "integer", required = true } })
    commands.register("InvasionMod.finite_resources_test_clear", command_test_clear, { resource = { type = "string", required = true } })
end

core.log.info(TAG, "feature finite_resources loaded: " .. table.concat(names, ", "))
return { state = state, remaining = remaining }
