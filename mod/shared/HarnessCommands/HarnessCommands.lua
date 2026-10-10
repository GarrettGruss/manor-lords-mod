-- HarnessCommands: a registry so any mod can add its own commands to the harness command channel.
-- Spec: docs/specs/10-invasion-testability/README.md (U10), notes: implementation-notes/mod-state-contract.md
--
-- A mod registers a command once:
--   HarnessCommands.register("MyMod.add_gold", function(args) return { gold = ... } end,
--       { amount = { type = "integer", required = true, min = 1, max = 1000 } })
-- The harness sends {"command":"MyMod.add_gold","args":{"amount":5}} through the HarnessActions channel.
-- HarnessActions hands every unknown command name that contains a dot to HarnessCommands.handleRequest.
--
-- Rules:
--   A name is <modName>.<command>: letters, digits and underscore, a letter first. The name "harness.*" is reserved.
--   The schema lists every allowed argument. Unknown, missing and wrongly typed arguments are refused
--   before the handler runs. The handler only gets checked values.
--   The handler runs on the game thread, inside pcall. It must be quick: a slow handler is logged, not stopped.
--   The handler returns a value that HarnessJson can encode. To refuse on purpose, return nil and a message.
--   There is no eval. Request text is only decoded as data (HarnessJson.decode).

local log = require("HarnessLog")
local json = require("HarnessJson")

local M = {}

local TAG = "HarnessCommands"
local NAME_PATTERN = "^[A-Za-z][A-Za-z0-9_]*%.[A-Za-z][A-Za-z0-9_]*$"
local ARG_NAME_PATTERN = "^[A-Za-z][A-Za-z0-9_]*$"
local RESERVED_PREFIX = "harness."
local DEFAULT_MAX_STRING_CHARS = 64
local SLOW_HANDLER_S = 0.05

local registry = {}   -- name -> { handler = function, schema = table }

---------------------------------------------------------------------------------------------
-- Schema
---------------------------------------------------------------------------------------------

local function isNumber(value)
    return type(value) == "number" and value == value and value ~= math.huge and value ~= -math.huge
end

local TYPE_CHECKS = {
    number = isNumber,
    integer = function(value) return isNumber(value) and value == math.floor(value) end,
    string = function(value) return type(value) == "string" end,
    boolean = function(value) return type(value) == "boolean" end,
}

local NUMERIC = { number = true, integer = true }
local RULE_KEYS = { type = true, required = true, min = true, max = true, maxLength = true, oneOf = true }

local function sortedKeys(t)
    local keys = {}
    for key in pairs(t) do keys[#keys + 1] = tostring(key) end
    table.sort(keys)
    return keys
end

local function checkRuleKeys(argName, rule)
    for key in pairs(rule) do
        if not RULE_KEYS[key] then return "argument " .. argName .. " has an unknown rule key: " .. tostring(key) end
    end
end

local function checkRuleLimits(argName, rule)
    local isNum = NUMERIC[rule.type] == true
    if (rule.min ~= nil or rule.max ~= nil) and not isNum then return "argument " .. argName .. ": min and max need a number type" end
    if rule.min ~= nil and not isNumber(rule.min) then return "argument " .. argName .. ": min must be a number" end
    if rule.max ~= nil and not isNumber(rule.max) then return "argument " .. argName .. ": max must be a number" end
    if rule.maxLength ~= nil and (rule.type ~= "string" or not isNumber(rule.maxLength)) then
        return "argument " .. argName .. ": maxLength needs a string type and a number"
    end
    if rule.oneOf ~= nil and (rule.type ~= "string" or type(rule.oneOf) ~= "table" or #rule.oneOf == 0) then
        return "argument " .. argName .. ": oneOf needs a string type and a list of strings"
    end
    if rule.required ~= nil and type(rule.required) ~= "boolean" then return "argument " .. argName .. ": required must be a boolean" end
end

-- Returns a private copy of the schema, or nil and the reason.
local function copySchema(schema)
    if type(schema) ~= "table" then return nil, "schema must be a table" end
    local copy = {}
    for argName, rule in pairs(schema) do
        if type(argName) ~= "string" or not argName:match(ARG_NAME_PATTERN) then
            return nil, "bad argument name: " .. tostring(argName)
        end
        if type(rule) ~= "table" or not TYPE_CHECKS[rule.type] then
            return nil, "argument " .. argName .. " needs a type: number, integer, string or boolean"
        end
        local problem = checkRuleKeys(argName, rule) or checkRuleLimits(argName, rule)
        if problem then return nil, problem end
        local ruleCopy = {}
        for key, value in pairs(rule) do ruleCopy[key] = value end
        copy[argName] = ruleCopy
    end
    return copy
end

---------------------------------------------------------------------------------------------
-- Argument checks
---------------------------------------------------------------------------------------------

local function describe(value)
    if value == json.null then return "null" end
    return type(value)
end

local function checkLimits(argName, rule, value)
    if rule.min ~= nil and value < rule.min then return "argument " .. argName .. " must be at least " .. rule.min end
    if rule.max ~= nil and value > rule.max then return "argument " .. argName .. " must be at most " .. rule.max end
end

local function checkString(argName, rule, value)
    local limit = rule.maxLength or DEFAULT_MAX_STRING_CHARS
    if #value > limit then return "argument " .. argName .. " is longer than " .. limit .. " characters" end
    if rule.oneOf then
        for _, allowed in ipairs(rule.oneOf) do
            if value == allowed then return nil end
        end
        return "argument " .. argName .. " must be one of: " .. table.concat(rule.oneOf, ", ")
    end
end

local function checkValue(argName, rule, value)
    if not TYPE_CHECKS[rule.type](value) then
        return "argument " .. argName .. " must be " .. (rule.type == "integer" and "an integer" or "a " .. rule.type) .. ", got " .. describe(value)
    end
    if NUMERIC[rule.type] then return checkLimits(argName, rule, value) end
    if rule.type == "string" then return checkString(argName, rule, value) end
end

local function findUnknownArgument(schema, args)
    for _, key in ipairs(sortedKeys(args)) do
        if not schema[key] then
            return "unknown argument " .. key .. " (allowed: " .. table.concat(sortedKeys(schema), ", ") .. ")"
        end
    end
end

-- Returns the checked arguments, or nil and the reason.
local function checkArguments(schema, args)
    if args == nil then args = {} end
    if type(args) ~= "table" then return nil, "args must be an object" end
    local unknown = findUnknownArgument(schema, args)
    if unknown then return nil, unknown end
    local checked = {}
    for _, argName in ipairs(sortedKeys(schema)) do
        local rule, value = schema[argName], args[argName]
        if value == nil then
            if rule.required then return nil, "missing argument " .. argName end
        else
            local problem = checkValue(argName, rule, value)
            if problem then return nil, problem end
            checked[argName] = value
        end
    end
    return checked
end

---------------------------------------------------------------------------------------------
-- Running a command
---------------------------------------------------------------------------------------------

local function refuse(message)
    return { ok = false, error = message }
end

local function runHandler(name, entry, args)
    local started = os.clock()
    local ok, value, message = pcall(entry.handler, args)
    local seconds = os.clock() - started
    if seconds > SLOW_HANDLER_S then
        log.warn(TAG, name .. " took " .. string.format("%.3f", seconds) .. " s. A handler runs on the game thread and must be quick")
    end
    if not ok then return refuse(name .. " failed: " .. tostring(value)) end
    if value == nil then return refuse(name .. " refused: " .. tostring(message or "the handler returned nothing")) end
    local encodable, problem = pcall(json.encode, value)
    if not encodable then return refuse(name .. " returned a value that is not JSON: " .. tostring(problem)) end
    return { ok = true, result = value }
end

-- Run a registered command. Never raises. Returns { ok = true, result = value } or { ok = false, error = text }.
function M.dispatch(name, args)
    local entry = type(name) == "string" and registry[name] or nil
    if not entry then return refuse("unknown command: " .. tostring(name)) end
    local checked, problem = checkArguments(entry.schema, args)
    if not checked then return refuse(name .. ": " .. problem) end
    return runHandler(name, entry, checked)
end

function M.isName(name)
    return type(name) == "string" and name:match(NAME_PATTERN) ~= nil
end

-- Decode a request text of the command channel and run its command with request.args. Never raises.
function M.handleRequest(name, requestText)
    local request, problem = json.decode(requestText)
    if request == nil then return refuse(name .. ": the request is not valid JSON: " .. tostring(problem)) end
    if not json.isObject(request) then return refuse(name .. ": the request must be a JSON object") end
    return M.dispatch(name, request.args)
end

---------------------------------------------------------------------------------------------
-- Registry
---------------------------------------------------------------------------------------------

local function addEntry(name, handler, schema)
    if not M.isName(name) then
        error("command name must look like ModName.command (letters, digits, underscore): " .. tostring(name), 3)
    end
    if type(handler) ~= "function" then error(name .. ": the handler must be a function", 3) end
    local copy, problem = copySchema(schema == nil and {} or schema)
    if not copy then error(name .. ": " .. problem, 3) end
    if registry[name] then error(name .. " is already registered", 3) end
    registry[name] = { handler = handler, schema = copy }
end

-- Add a command. A bad name, schema or handler, and a second registration of a name, raise an error.
function M.register(name, handler, schema)
    if type(name) == "string" and name:sub(1, #RESERVED_PREFIX) == RESERVED_PREFIX then
        error("the command prefix harness. is reserved: " .. name, 2)
    end
    addEntry(name, handler, schema)
end

-- Remove a command. A mod that can reload calls this before it registers again.
function M.unregister(name)
    local existed = registry[name] ~= nil
    registry[name] = nil
    return existed
end

local function describeRule(rule)
    local description = {}
    for key, value in pairs(rule) do description[key] = value end
    return description
end

-- The registered commands, sorted by name: { { name = "Mod.cmd", args = { argName = rule } } }.
function M.list()
    local commands = {}
    for _, name in ipairs(sortedKeys(registry)) do
        local args = json.object({})
        for argName, rule in pairs(registry[name].schema) do args[argName] = describeRule(rule) end
        commands[#commands + 1] = { name = name, args = args }
    end
    return commands
end

addEntry("harness.list_commands", function() return { commands = M.list() } end, {})

return M
