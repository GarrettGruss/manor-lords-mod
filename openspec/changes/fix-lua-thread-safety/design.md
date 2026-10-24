## Decisions

- Use `HarnessLoop.every(ms, fn)` everywhere. The mode `HARNESS_LOOP_MODE=async` stays for A/B tests.
- `UEBridge` is vendor code. The patch only replaces `LoopAsync(ms, fn)` by `HarnessLoop.every(ms, fn)` (and keeps the `busy` flag). It is listed in the vendor patch notes.
- Key binds: the callback only calls `ExecuteInGameThread(function() ... end)`. The table work is done in the closure. The closure allocation on the input thread is accepted, because it is the documented way to leave that thread.
- Wave spawn: the scan runs from the scheduler on a later tick (one tick delay, 100 ms).
- `liege_influence` manor state cache: check only. Leave it if present.

## Risks

Game-thread timers run inside the engine tick. A long body can drop frames. The bodies are short (flag read, file read).
