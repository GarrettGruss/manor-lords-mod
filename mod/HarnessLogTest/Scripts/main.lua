-- Smoke test for HarnessLog: confirms the shared module loads and the log
-- file is written and flushed while the game is running.
-- It is also the test mod for hot reload (spec 06): reload_mods.py waits for the version line below.
-- Change VERSION, run reload_mods.py, and the new number shows in mod.log without a game restart.
local log = require("HarnessLog")

local VERSION = "1"
local TAG = "HarnessLogTest"

log.say(TAG, "loaded version " .. VERSION .. ", writing to " .. log.path())

local n = 0
LoopAsync(5000, function()
    n = n + 1
    log.info(TAG, "heartbeat " .. n .. " v" .. VERSION)
    return n >= 6  -- stop after ~30s
end)
