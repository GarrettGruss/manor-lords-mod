# Recommendation

Cause status: not proven. The evidence for the main hypothesis (H1, off-thread Lua of `LoopAsync` damages the Lua state of the mod) is circumstantial:
- 53 of 143 crashes are garbage-pointer faults inside the Lua core (group A), 96 of 143 fault on the game thread inside `process_simple_actions`. A race between a `LoopAsync` thread and the game thread explains both.
- The InvasionMod state runs 4 `LoopAsync` threads next to its game-thread work (R1a, R1b, R1g, R1h).
- `LoopAsync` is deprecated in the installed UE4SS, and `LoopInGameThreadWithDelay` exists there.
- The A/B runs could not reproduce a crash in 18 runs (both variants), so they neither confirm nor reject H1.
Other groups have other causes: stale or invalid UObjects (group B, small addresses), frequent building list reads (R4a, lead data point), `GetChildAt` without `IsValid` (R6, lead data point), and a rethrow site in the game (group C).

## Done in this change (low risk, local)

1. New shared module `HarnessLoop` (`HarnessLoop.every(ms, fn)`, game thread). Used by `scheduler.lua`, `HarnessCommands`, `HarnessActions`, `HarnessTelemetry`, `HarnessTune` and `mod_state`. `HARNESS_LOOP_MODE=async` restores the old behavior. If the UE4SS functions are missing (the fake game kit), it falls back to `LoopAsync`.
2. `order_tooltip/widget.lua`: `IsValid` before each `GetChildAt` use (R6).
3. Host memory sample file `hostmem.jsonl` in each run folder (new, `harness/runlib/hostmem.py`).

## Follow-up change (list for the owner)

| Priority | Item | Why |
|---|---|---|
| 1 | Move `UEBridge` (`main.lua:1018`, `:1438`), `HarnessBoot` (`:643`), `HarnessReload` (`:113`, `:164`) to game-thread timers. `UEBridge` is vendor code with local patches. | The last off-thread Lua loops. Needs care for the bridge `busy` flag. |
| 2 | R2b: replace the `S.toggles` table append in the key bind callback (`menu.lua:318`) by a preallocated counter per menu id. | Table growth on the input thread. |
| 3 | R4a: cache the `manor_state` read in `liege_influence` (re-read every 2 s while missing). | Lead data point: 3 of 3 clean runs after the cache. |
| 4 | R4c, R4d: after a wave spawn, do not scan all `SMUnit` in the same tick. Wait a few ticks, or read the spawn result instead of scanning. | Spike goal 3, not measurable here. |
| 5 | Run a suite of 10 or more runs per variant on the crash-prone scenarios (`invasion-first-raid`, bandit camp scenarios, `liege-arms-shipment`) to measure the effect of the timer change. | The A/B here had zero crashes. |
| 6 | Fake game kit: add `LoopInGameThreadWithDelay` and `CancelDelayedAction`, so the kit tests the game-thread path. | Today the kit falls back to `LoopAsync`. |
| 7 | Do not run scenarios in several games at once on this PC (free memory fell to 1 GB). | Memory pressure is not proven, but it is cheap to avoid. |
