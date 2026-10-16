-- HarnessReload: restarts one Lua mod inside the running game, on request from a file.
-- Spec: docs/harness/06-dev-loop-and-fixtures/README.md (part A).
--
--   external  ->  writes  <HARNESS_RUN_DIR>/reload.json         {"mod": "Name", "id": "unique-id"}
--   this mod  ->  polls it, calls RestartMod(Name) on the game thread,
--                 waits for the line "[Name] loaded version <v>" in mod.log,
--                 writes <HARNESS_RUN_DIR>/reload.result.json
--
-- Result: {"id", "mod", "ok", "version", "line", "error", "seconds"}.
-- A mod that wants to be reloaded must log "loaded version <v>" through HarnessLog (tag = its folder name).
-- RestartMod gives the mod a new Lua state, so the old hooks, loops and key binds of that mod are gone.
-- Rules: the request file is deleted when read, an id is handled once, the wait has a time limit.

local log = require("HarnessLog")

local VERSION = "2.0"
local TAG = "HarnessReload"
local POLL_MS = 200
local VERSION_WAIT_S = 20
local RUN_DIR = log.dir()
local REQUEST = RUN_DIR .. "/reload.json"
local RESULT = RUN_DIR .. "/reload.result.json"
local RESULT_TMP = RESULT .. ".tmp"
local MOD_LOG = log.path()
local SELF = "HarnessReload"

-- RestartMod does not fail for an unknown name (UE4SS only logs it), so the folder is checked here.
local function modsDir()
    local ok, dirs = pcall(IterateGameDirectories)
    local win64 = ok and dirs and dirs.Game and dirs.Game.Binaries and dirs.Game.Binaries.Win64
    if win64 and win64.__absolute_path then return win64.__absolute_path .. "/ue4ss/Mods" end
    return nil
end

local function modExists(name)
    local dir = modsDir()
    if not dir then return true end -- cannot check: let RestartMod decide
    local f = io.open(dir .. "/" .. name .. "/Scripts/main.lua", "rb")
    if not f then return false end
    f:close()
    return true
end

local lastId = nil
local waiting = false

local function readFile(path)
    local f = io.open(path, "rb")
    if not f then return nil end
    local text = f:read("a")
    f:close()
    return text
end

local function logSize()
    local f = io.open(MOD_LOG, "rb")
    if not f then return 0 end
    local size = f:seek("end")
    f:close()
    return size
end

local function jsonString(value)
    if value == nil then return "null" end
    local text = tostring(value):gsub("[%c\"\\]", function(c)
        if c == '"' then return '\\"' end
        if c == "\\" then return "\\\\" end
        return string.format("\\u%04x", c:byte())
    end)
    return '"' .. text .. '"'
end

-- Write the result so a reader never sees half of it: write a .tmp file, then rename it.
local function writeResult(result)
    local body = string.format(
        '{"id":%s,"mod":%s,"ok":%s,"version":%s,"line":%s,"error":%s,"seconds":%s}',
        jsonString(result.id), jsonString(result.mod), tostring(result.ok == true),
        jsonString(result.version), jsonString(result.line), jsonString(result.error),
        string.format("%d", result.seconds or 0))
    local f = io.open(RESULT_TMP, "wb")
    if not f then
        log.error(TAG, "cannot write " .. RESULT_TMP)
        return
    end
    f:write(body)
    f:close()
    os.remove(RESULT)
    local ok, err = os.rename(RESULT_TMP, RESULT)
    if not ok then log.error(TAG, "cannot rename result: " .. tostring(err)) end
end

-- The request has a fixed small shape, so two patterns are enough. A name that is not a plain word is refused.
local function parseRequest(raw)
    return raw:match('"id"%s*:%s*"([^"\\]+)"'), raw:match('"mod"%s*:%s*"([%w_]+)"')
end

-- Find the version line the new mod wrote after `offset`.
local function findVersionLine(modName, offset)
    local f = io.open(MOD_LOG, "rb")
    if not f then return nil end
    f:seek("set", offset)
    local text = f:read("a") or ""
    f:close()
    local pattern = "%[" .. modName .. "%] loaded version ([%w%._%-]+)"
    for line in text:gmatch("[^\r\n]+") do
        local version = line:match(pattern)
        if version then return version, line end
    end
    return nil
end

local function waitForVersion(request, offset, startedAt)
    LoopAsync(POLL_MS, function()
        local version, line = findVersionLine(request.mod, offset)
        local elapsed = os.time() - startedAt
        if version then
            writeResult({ id = request.id, mod = request.mod, ok = true, version = version, line = line, seconds = elapsed })
        elseif elapsed >= VERSION_WAIT_S then
            writeResult({ id = request.id, mod = request.mod, ok = false, seconds = elapsed,
                error = "restart was called, but no 'loaded version' line came in " .. VERSION_WAIT_S .. " s" })
        else
            return false
        end
        waiting = false
        return true
    end)
end

local function restart(request)
    local offset = logSize()
    local startedAt = os.time()
    waiting = true
    ExecuteInGameThread(function()
        local ok, err = pcall(RestartMod, request.mod)
        if not ok then
            writeResult({ id = request.id, mod = request.mod, ok = false, error = "RestartMod failed: " .. tostring(err) })
            waiting = false
            return
        end
        log.info(TAG, "RestartMod called for " .. request.mod .. " (id " .. request.id .. ")")
        waitForVersion(request, offset, startedAt)
    end)
end

local function handle(raw)
    local id, modName = parseRequest(raw)
    if not id then
        writeResult({ id = "?", ok = false, error = "request has no valid id" })
        return
    end
    if id == lastId then return end
    lastId = id
    if not modName then
        writeResult({ id = id, ok = false, error = "request has no valid mod name (letters, digits, underscore)" })
    elseif modName == SELF then
        writeResult({ id = id, mod = modName, ok = false, error = "HarnessReload cannot restart itself" })
    elseif not modExists(modName) then
        writeResult({ id = id, mod = modName, ok = false, error = "no mod folder with Scripts/main.lua: " .. modName })
    else
        restart({ id = id, mod = modName })
    end
end

LoopAsync(POLL_MS, function()
    if waiting then return false end
    local raw = readFile(REQUEST)
    if not raw then return false end
    os.remove(REQUEST)
    log.try(TAG, handle, raw)
    return false
end)

log.say(TAG, "loaded version " .. VERSION .. ", polling " .. REQUEST)
