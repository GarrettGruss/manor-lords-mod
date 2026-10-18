-- One timer for all features of InvasionMod. Each job runs on the game thread.
-- Why one: every LoopAsync callback runs Lua on its own thread. Five loops in one Lua state raced with the game thread
-- and crashed 120 day runs (issue 163). One loop with a short body keeps the off-thread Lua work small.
local core = require("ManorCore")

local TICK_MS = 100
local M = {}

local jobs = {}   -- { name, every_ms, next_ms, run }
local clock_ms = 0
local started = false

local function run_due()
    for _, job in ipairs(jobs) do
        if clock_ms >= job.next_ms then
            job.next_ms = clock_ms + job.every_ms
            core.log.try(job.name, job.run)
        end
    end
end

local function start()
    started = true
    LoopAsync(TICK_MS, function()
        clock_ms = clock_ms + TICK_MS
        ExecuteInGameThread(run_due)
        return false
    end)
end

-- Run `run` on the game thread about every `every_ms`.
function M.every(name, every_ms, run)
    jobs[#jobs + 1] = { name = name, every_ms = every_ms, next_ms = every_ms, run = run }
    if not started then start() end
end

return M
