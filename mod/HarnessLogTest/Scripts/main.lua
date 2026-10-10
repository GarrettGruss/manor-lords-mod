-- Smoke test for HarnessLog: confirms the shared module loads and the log
-- file is written and flushed while the game is running.
local log = require("HarnessLog")

log.say("HarnessLogTest", "loaded, writing to " .. log.path())

local n = 0
LoopAsync(5000, function()
    n = n + 1
    log.info("HarnessLogTest", "heartbeat " .. n)
    return n >= 6  -- stop after ~30s
end)
