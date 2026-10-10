-- HarnessLog: line-buffered, flush-on-write log for harness/agent consumption.
-- UE4SS.log is buffered while the game runs; this file is readable live.
--
-- Output: $HARNESS_RUN_DIR/mod.log if the env var is set (harness launcher),
-- otherwise ue4ss/harness/mod.log relative to the game's Win64 dir.
-- Format: one line per entry: "<unix_time> <LEVEL> [<tag>] <message>"

local M = {}

local run_dir = os.getenv("HARNESS_RUN_DIR")
local dir = run_dir and run_dir ~= "" and run_dir or "ue4ss/harness"
local path = dir .. "/mod.log"
local file = nil
local seq = 0

local function open()
    if file then return file end
    -- Best effort directory creation; harmless if it already exists.
    os.execute('mkdir "' .. dir:gsub("/", "\\") .. '" >nul 2>&1')
    local f, err = io.open(path, "a")
    if not f then
        print(string.format("[HarnessLog] cannot open %s: %s\n", path, tostring(err)))
        return nil
    end
    file = f
    return f
end

function M.write(level, tag, msg)
    local f = open()
    if not f then return false end
    seq = seq + 1
    f:write(string.format("%d %d %s [%s] %s\n", os.time(), seq, level, tag or "-", tostring(msg)))
    f:flush()
    return true
end

function M.info(tag, msg) return M.write("INFO", tag, msg) end
function M.warn(tag, msg) return M.write("WARN", tag, msg) end
function M.error(tag, msg) return M.write("ERROR", tag, msg) end

-- Log and also mirror to the UE4SS console.
function M.say(tag, msg)
    print(string.format("[%s] %s\n", tag or "-", tostring(msg)))
    return M.info(tag, msg)
end

-- Call a function, logging any Lua error instead of letting it vanish.
function M.try(tag, fn, ...)
    local ok, result = xpcall(fn, debug.traceback, ...)
    if not ok then M.error(tag, result) end
    return ok, result
end

function M.path() return path end

-- Folder that holds mod.log. Other harness files (boot.json, ready.marker) go here too.
function M.dir() return dir end

-- Make a folder (and its parents). Harmless if it exists. Only pass a path that the harness built from checked names.
function M.make_dir(folder)
    if folder:find('[^%w_%-%./:\\ ~]') then error("unsafe folder path: " .. folder, 2) end
    os.execute('mkdir "' .. folder:gsub("/", "\\") .. '" >nul 2>&1')
end

function M.close()
    if file then file:close(); file = nil end
end

return M
