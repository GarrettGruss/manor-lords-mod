-- HarnessActions: runs a small, fixed list of commands inside the game for the Python action kit (spec 07).
-- Why: the bridge cannot pass object references, and some game functions need them (for example sendLetter).
--
--   client  ->  writes  <HARNESS_RUN_DIR>/commands/<id>.json         (write .tmp, then rename)
--   this mod -> runs it on the game thread, writes <id>.result.json  (write .tmp, then rename)
--
-- The ids are the numbers 0001, 0002, ... in order. UE4SS Lua cannot list a folder, so the mod
-- waits for the next number. The client must use the numbers in order.
-- Request shapes (a fixed small JSON, read with patterns, never run as code):
--   {"id":"0001","command":"ping"}
--   {"id":"0002","command":"send_letter","sender":1,"paragraphs":["name_one","name_two"]}
--   {"id":"0003","command":"autosave_status"}      read the autosave timer (read only)
--   {"id":"0004","command":"disable_autosave"}     restart the autosave timer with a one year period
--   {"id":"0005","command":"datatable_info"}       row count and names of the item table (read only)
--   {"id":"0006","command":"datatable_read","row":"name","field":"Value"}              one number field of one row
--   {"id":"0007","command":"datatable_write","row":"name","field":"Value","value":5}  change one number field
--   {"id":"0008","command":"ModName.command","args":{...}}   a command that another mod registered in HarnessCommands
--   {"id":"0009","command":"harness.list_commands"}           the registered commands and their argument schemas
-- Result: {"id","command","ok","error",...fields of the command}. A HarnessCommands command answers {"ok","result"}.
-- Rules: no eval, only the commands below, an id is handled once, every input is checked before it is used.

local log = require("HarnessLog")
local json = require("HarnessJson")
local autosave = require("HarnessAutosave")
local datatable = require("HarnessDataTable")
local commands = require("HarnessCommands")

local VERSION = "3"
local TAG = "HarnessActions"
local POLL_MS = 100
local MAX_PARAGRAPHS = 10
local MAX_NAME_CHARS = 64
local COMMANDS_DIR = log.dir() .. "/commands"

local nextNumber = 1

local function idOf(number) return string.format("%04d", number) end
local function requestPath(number) return COMMANDS_DIR .. "/" .. idOf(number) .. ".json" end
local function resultPath(number) return COMMANDS_DIR .. "/" .. idOf(number) .. ".result.json" end

local function readFile(path)
    local f = io.open(path, "rb")
    if not f then return nil end
    local text = f:read("a")
    f:close()
    return text
end

-- Write the result so a reader never sees half of it: write a .tmp file, then rename it.
local function writeResult(number, result)
    local tmp = resultPath(number) .. ".tmp"
    local f = io.open(tmp, "wb")
    if not f then
        log.error(TAG, "cannot write " .. tmp)
        return
    end
    f:write(json.encode(result))
    f:close()
    os.remove(resultPath(number))
    local ok, err = os.rename(tmp, resultPath(number))
    if not ok then log.error(TAG, "cannot rename result: " .. tostring(err)) end
end

local function parseParagraphs(raw)
    local inner = raw:match('"paragraphs"%s*:%s*%[(.-)%]')
    if not inner then return nil end
    local names = {}
    for name in inner:gmatch('"([^"]*)"') do
        if #names >= MAX_PARAGRAPHS then return nil, "too many paragraphs (limit " .. MAX_PARAGRAPHS .. ")" end
        if #name == 0 or #name > MAX_NAME_CHARS or name:find("[^%w_]") then
            return nil, "a paragraph name must be letters, digits and underscore, 1 to " .. MAX_NAME_CHARS .. " characters"
        end
        names[#names + 1] = FName(name)
    end
    if #names == 0 then return nil, "no paragraphs" end
    return names
end

local function parseRequest(raw)
    return {
        id = raw:match('"id"%s*:%s*"([%w_]+)"'),
        command = raw:match('"command"%s*:%s*"([%w_%.]+)"'),
        sender = tonumber(raw:match('"sender"%s*:%s*(%d+)')),
        row = raw:match('"row"%s*:%s*"([%w_ %-]+)"'),
        field = raw:match('"field"%s*:%s*"([%w_]+)"'),
        value = tonumber(raw:match('"value"%s*:%s*(-?[%d%.]+)')),
    }
end

local function inboxCount(pawn)
    return pawn.InBox:GetArrayNum()
end

-- The sender is an AI lord, counted from 1 in the order FindAllOf gives. The recipient is always the player.
local function sendLetter(request, raw)
    local paragraphs, problem = parseParagraphs(raw)
    if not paragraphs then return { ok = false, error = problem or "request has no paragraphs" } end
    local lords = FindAllOf("PawnCPP_AI") or {}
    local sender = request.sender and lords[request.sender]
    if not sender or not sender:IsValid() then
        return { ok = false, error = "no AI lord with sender number " .. tostring(request.sender) .. " (found " .. #lords .. ")" }
    end
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local player = engine and engine:IsValid() and engine.playerRef
    if not player or not player:IsValid() then return { ok = false, error = "the player pawn is not loaded" } end
    local before = inboxCount(player)
    sender:sendLetter(player, paragraphs)
    return { ok = true, inbox_before = before, inbox_after = inboxCount(player), paragraphs = #paragraphs }
end

local function autosaveStatus()
    return { ok = true, status = autosave.status() }
end

-- Not a save function: it only restarts the autosave timer with a very long period.
local function disableAutosave()
    local changes, problem = autosave.disable()
    if not changes then return { ok = false, error = problem } end
    return { ok = true, changes = changes }
end

local function datatableInfo()
    local info, problem = datatable.info()
    if not info then return { ok = false, error = problem } end
    return { ok = true, info = info }
end

local function datatableRead(request)
    if not request.row or not request.field then return { ok = false, error = "row and field are required" } end
    local values, problem = datatable.read_row(request.row, { request.field })
    if not values then return { ok = false, error = problem } end
    return { ok = true, row = request.row, values = values }
end

local function datatableWrite(request)
    if not request.row or not request.field or not request.value then
        return { ok = false, error = "row, field and value are required" }
    end
    local change, problem = datatable.write_number(request.row, request.field, request.value)
    if not change then return { ok = false, error = problem } end
    return { ok = true, row = request.row, field = request.field, change = change }
end

local COMMANDS = {
    ping = function() return { ok = true, version = VERSION } end,
    send_letter = sendLetter,
    autosave_status = autosaveStatus,
    disable_autosave = disableAutosave,
    datatable_info = datatableInfo,
    datatable_read = datatableRead,
    datatable_write = datatableWrite,
}

local function runCommand(number, raw)
    local request = parseRequest(raw)
    local result
    local handler = request.command and COMMANDS[request.command]
    if not request.id or request.id ~= idOf(number) then
        result = { ok = false, error = "request id must be " .. idOf(number) }
    elseif not handler and commands.isName(request.command) then
        result = commands.handleRequest(request.command, raw)
    elseif not handler then
        result = { ok = false, error = "unknown command: " .. tostring(request.command) }
    else
        local ok, answer = pcall(handler, request, raw)
        result = ok and answer or { ok = false, error = tostring(answer) }
    end
    result.id = idOf(number)
    result.command = request.command
    writeResult(number, result)
    log.info(TAG, "command " .. idOf(number) .. " " .. tostring(request.command) .. " ok=" .. tostring(result.ok))
end

local function skipHandled()
    while readFile(resultPath(nextNumber)) do nextNumber = nextNumber + 1 end
end

skipHandled()

LoopAsync(POLL_MS, function()
    local raw = readFile(requestPath(nextNumber))
    if not raw then return false end
    local number = nextNumber
    nextNumber = nextNumber + 1
    ExecuteInGameThread(function() log.try(TAG, runCommand, number, raw) end)
    return false
end)

log.say(TAG, "loaded version " .. VERSION .. ", waiting for " .. requestPath(nextNumber))
