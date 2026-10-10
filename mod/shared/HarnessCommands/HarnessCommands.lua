-- HarnessCommands: a registry so any mod can add its own commands and metrics for the harness.
-- Spec: docs/specs/10-invasion-testability/README.md (U10), notes: implementation-notes/mod-state-contract.md
--
-- A mod registers a command once:
--   HarnessCommands.register("MyMod.add_gold", function(args) return { gold = ... } end,
--       { amount = { type = "integer", required = true, min = 1, max = 1000 } })
-- and a metric:
--   HarnessCommands.metric("MyMod.gold", function() return gold end)
--
-- Why each mod serves its own commands: UE4SS gives every Lua mod its OWN Lua state. This module is loaded once
-- per mod state, so the registries of two mods are separate tables. Tables and functions cannot cross states,
-- but files can. So the first register or metric call in a state starts a small poller in that state:
--   client   ->  writes  <HARNESS_RUN_DIR>/modcmd/<ModName>/<number>.json        {"command":"MyMod.add_gold","args":{"amount":5}}
--   this mod ->  runs it on the game thread, writes <number>.result.json         {"ok":true,"result":...} or {"ok":false,"error":...}
-- Both files are written as .tmp first and then renamed. The numbers are 0001, 0002, ... in order, because
-- UE4SS Lua cannot list a folder (same rule as HarnessActions). Without HARNESS_RUN_DIR no poller starts.
--
-- Rules:
--   A name is <modName>.<command>: letters, digits and underscore, a letter first. The name "harness.*" is reserved.
--   The poller of mod X only runs commands named X.* and the built-in harness.* commands.
--   Built-in commands: harness.list_commands (the commands of that mod) and harness.metrics (the metrics of that mod).
--   The schema lists every allowed argument. Unknown, missing and wrongly typed arguments are refused
--   before the handler runs. The handler only gets checked values.
--   The handler runs on the game thread, inside pcall. It must be quick: a slow handler is logged, not stopped.
--   The handler returns a value that HarnessJson can encode. To refuse on purpose, return nil and a message.
--   There is no eval. Request text is only decoded as data (HarnessJson.decode).
--
-- Hot reload: UE4SS gives a restarted mod a new Lua state and stops the loops of the old state (spec 06 notes).
-- As a second guard, each poller writes a random token to <ModName>/owner.txt and stops when the file holds another token.

local log = require("HarnessLog")
local json = require("HarnessJson")

local M = {}

local TAG = "HarnessCommands"
local NAME_PATTERN = "^[A-Za-z][A-Za-z0-9_]*%.[A-Za-z][A-Za-z0-9_]*$"
local MOD_NAME_PATTERN = "^[A-Za-z][A-Za-z0-9_]*$"
local ARG_NAME_PATTERN = "^[A-Za-z][A-Za-z0-9_]*$"
local RESERVED_PREFIX = "harness."
local DEFAULT_MAX_STRING_CHARS = 64
local SLOW_HANDLER_S = 0.05
local POLL_MS = 100
local MODCMD_DIR = "modcmd"

local registry = {}   -- name -> { handler = function, schema = table }
local metrics = {}    -- name -> function
local pollers = {}    -- modName -> true, one poller for each mod name in this state

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

-- `modName` is the mod whose folder the request came from. Only the built-in commands use it.
local function runHandler(name, entry, args, modName)
    local started = os.clock()
    local ok, value, message = pcall(entry.handler, args, modName)
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
function M.dispatch(name, args, modName)
    local entry = type(name) == "string" and registry[name] or nil
    if not entry then return refuse("unknown command: " .. tostring(name)) end
    local checked, problem = checkArguments(entry.schema, args)
    if not checked then return refuse(name .. ": " .. problem) end
    return runHandler(name, entry, checked, modName)
end

function M.isName(name)
    return type(name) == "string" and name:match(NAME_PATTERN) ~= nil
end

local function belongsToMod(name, modName)
    return name:sub(1, #RESERVED_PREFIX) == RESERVED_PREFIX or name:sub(1, #modName + 1) == modName .. "."
end

-- Decode one request text of a mod folder and run its command. Never raises.
-- A mod only runs its own commands (ModName.*) and the built-in harness.* commands.
function M.serve(requestText, modName)
    local request, problem = json.decode(requestText)
    if request == nil then return refuse("the request is not valid JSON: " .. tostring(problem)) end
    if not json.isObject(request) then return refuse("the request must be a JSON object") end
    local name = request.command
    if type(name) ~= "string" then return refuse("the request has no command name") end
    if not belongsToMod(name, modName) then
        return refuse(name .. " does not belong to mod " .. modName .. ". Send it to the folder of its own mod")
    end
    local answer = M.dispatch(name, request.args, modName)
    answer.command = name
    return answer
end

---------------------------------------------------------------------------------------------
-- Registry
---------------------------------------------------------------------------------------------

local function modNameOf(name)
    return name:match("^([^%.]+)%.")
end

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

---------------------------------------------------------------------------------------------
-- The poller of one mod
---------------------------------------------------------------------------------------------

local function modFolder(modName) return log.dir() .. "/" .. MODCMD_DIR .. "/" .. modName end
local function idOf(number) return string.format("%04d", number) end
local function requestPath(modName, number) return modFolder(modName) .. "/" .. idOf(number) .. ".json" end
local function resultPath(modName, number) return modFolder(modName) .. "/" .. idOf(number) .. ".result.json" end
local function ownerPath(modName) return modFolder(modName) .. "/owner.txt" end

local function readFile(path)
    local f = io.open(path, "rb")
    if not f then return nil end
    local text = f:read("a")
    f:close()
    return text
end

-- Write so a reader never sees half a file: write a .tmp file, then rename it.
local function writeAtomic(path, text)
    local tmp = path .. ".tmp"
    local f = io.open(tmp, "wb")
    if not f then
        log.error(TAG, "cannot write " .. tmp)
        return false
    end
    f:write(text)
    f:close()
    os.remove(path)
    local ok, err = os.rename(tmp, path)
    if not ok then log.error(TAG, "cannot rename " .. tmp .. ": " .. tostring(err)) end
    return ok
end

local function hasRunFolder()
    local runDir = os.getenv("HARNESS_RUN_DIR")
    return runDir ~= nil and runDir ~= ""
end

local tokenCount = 0
-- Why random: two states (an old and a reloaded mod) must never get the same token.
local function newToken()
    tokenCount = tokenCount + 1
    return string.format("%s-%s-%d-%d", tostring({}), tostring(os.time()), math.random(1, 1000000000), tokenCount)
end

local function answerRequest(modName, number, raw)
    local answer = M.serve(raw, modName)
    answer.id = idOf(number)
    writeAtomic(resultPath(modName, number), json.encode(answer))
    log.info(TAG, modName .. " request " .. idOf(number) .. " " .. tostring(answer.command) .. " ok=" .. tostring(answer.ok))
end

local function firstUnhandledNumber(modName)
    local number = 1
    while readFile(resultPath(modName, number)) do number = number + 1 end
    return number
end

-- Start the poller of a mod in this state. One poller for each mod name. It does nothing without HARNESS_RUN_DIR.
local function startPoller(modName)
    if pollers[modName] or not hasRunFolder() then return end
    pollers[modName] = true
    log.make_dir(modFolder(modName))
    local token = newToken()
    writeAtomic(ownerPath(modName), token)
    local nextNumber = firstUnhandledNumber(modName)
    LoopAsync(POLL_MS, function()
        local owner = readFile(ownerPath(modName))
        if owner ~= nil and owner ~= token then
            pollers[modName] = nil
            log.info(TAG, "poller of " .. modName .. " stops: another state took the folder")
            return true
        end
        local raw = readFile(requestPath(modName, nextNumber))
        if not raw then return false end
        local number = nextNumber
        nextNumber = nextNumber + 1
        ExecuteInGameThread(function() log.try(TAG, answerRequest, modName, number, raw) end)
        return false
    end)
    log.info(TAG, "poller of " .. modName .. " waits for " .. requestPath(modName, nextNumber))
end

---------------------------------------------------------------------------------------------
-- Public registration
---------------------------------------------------------------------------------------------

-- Add a command. A bad name, schema or handler, and a second registration of a name, raise an error.
-- The first call for a mod name starts the poller of that mod in this state.
function M.register(name, handler, schema)
    if type(name) == "string" and name:sub(1, #RESERVED_PREFIX) == RESERVED_PREFIX then
        error("the command prefix harness. is reserved: " .. name, 2)
    end
    addEntry(name, handler, schema)
    startPoller(modNameOf(name))
end

-- Remove a command. A mod that can reload calls this before it registers again.
function M.unregister(name)
    local existed = registry[name] ~= nil
    registry[name] = nil
    return existed
end

-- Add a metric: a function that returns a number, a boolean or a string. The client reads it with harness.metrics.
-- A second call with the same name replaces the function (a reload runs the mod file again).
function M.metric(name, read)
    if not M.isName(name) then
        error("metric name must look like ModName.metric (letters, digits, underscore): " .. tostring(name), 2)
    end
    if name:sub(1, #RESERVED_PREFIX) == RESERVED_PREFIX then error("the prefix harness. is reserved: " .. name, 2) end
    if type(read) ~= "function" then error(name .. ": the metric must be a function", 2) end
    metrics[name] = read
    startPoller(modNameOf(name))
end

local function describeRule(rule)
    local description = {}
    for key, value in pairs(rule) do description[key] = value end
    return description
end

local function isListed(name, modName)
    return modName == nil or name:sub(1, #RESERVED_PREFIX) == RESERVED_PREFIX or name:sub(1, #modName + 1) == modName .. "."
end

-- The registered commands, sorted by name: { { name = "Mod.cmd", args = { argName = rule } } }.
-- With `modName`, only the commands of that mod and the built-in commands.
function M.list(modName)
    local commands = {}
    for _, name in ipairs(sortedKeys(registry)) do
        if isListed(name, modName) then
            local args = json.object({})
            for argName, rule in pairs(registry[name].schema) do args[argName] = describeRule(rule) end
            commands[#commands + 1] = { name = name, args = args }
        end
    end
    return commands
end

-- The metric values of a mod: { values = { name = value }, errors = { name = text } }.
-- A metric that raises an error, or returns something else than a number, boolean or string, is left out and named in errors.
function M.readMetrics(modName)
    local values, errors = json.object({}), json.object({})
    for _, name in ipairs(sortedKeys(metrics)) do
        if name:sub(1, #modName + 1) == modName .. "." then
            local ok, value = pcall(metrics[name])
            local kind = type(value)
            if ok and (kind == "number" or kind == "boolean" or kind == "string") then
                values[name] = value
            else
                errors[name] = ok and ("the metric returned a " .. kind) or tostring(value)
            end
        end
    end
    return { metrics = values, errors = errors }
end

addEntry("harness.list_commands", function(_args, modName) return { commands = M.list(modName) } end, {})
addEntry("harness.metrics", function(_args, modName) return M.readMetrics(modName or "") end, {})

return M
