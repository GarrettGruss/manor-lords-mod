-- Repeating timers that run their Lua on the game thread.
-- Why: LoopAsync runs the callback on its own thread, at the same time as game-thread Lua of the same mod. A Lua state is
-- not thread safe, so this can damage the Lua heap (spike-lua-crash-after-spawn). LoopInGameThreadWithDelay runs on the game thread.
-- The environment variable HARNESS_LOOP_MODE=async switches back to LoopAsync (for A/B tests).
local M = {}

function M.mode()
    local wanted = os.getenv("HARNESS_LOOP_MODE")
    if wanted == "async" or LoopInGameThreadWithDelay == nil or CancelDelayedAction == nil then return "async" end
    return "game"
end

-- Calls fn about every `ms`. The loop ends when fn returns true (the same contract as LoopAsync).
function M.every(ms, fn)
    if M.mode() == "async" then
        LoopAsync(ms, fn)
        return
    end
    local handle
    handle = LoopInGameThreadWithDelay(ms, function()
        if fn() == true then CancelDelayedAction(handle) end
    end)
end

return M
