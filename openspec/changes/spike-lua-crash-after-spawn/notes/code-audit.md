# Code audit

Scope: `mod/InvasionMod`, `mod/shared`, `mod/HarnessActions`, `mod/UEBridge` and the other Harness mods. Method: grep for `LoopAsync`, `ExecuteWithDelay`, `RegisterKeyBind`, `NotifyOnNewObject`, `RegisterHook`, `FindAllOf`, then read each site. File and line numbers are from `main` at commit `c2cf81c`.

## Facts from the installed UE4SS (`ue4ss/Docs`, `Changelog.md`, `UE4SS.dll` strings)

- `LoopAsync`, `ExecuteAsync` and `ExecuteWithDelay` run the Lua callback on a separate `std::thread`. The 2 abort crashes show `std::thread`, then `update_async`, then `process_delayed_actions`, then `call_function`. `ExecuteInGameThread` and hook callbacks run on the game thread (`engine_tick_hook`, then `process_simple_actions`).
- A Lua state is not thread safe. Each mod has its own state. A `LoopAsync` callback runs Lua (allocation, garbage collection, table writes) at the same time as game-thread Lua of the same mod.
- `LoopAsync` and `ExecuteAsync` are deprecated in this UE4SS build. The documented replacement is `LoopInGameThreadWithDelay(ms, fn)` (cancel with `CancelDelayedAction(handle)`), plus `ExecuteInGameThreadWithDelay`. The names are in `UE4SS.dll`. The repo uses none of them yet. (An archived note, `legacy-13-mod-inspection/implementation-notes/tree-regeneration.md`, shows that a third-party mod uses `LoopInGameThreadWithDelay(50, ...)` as its worker.)
- `RegisterKeyBind` callbacks run on the input thread (already in the wiki, `architecture/invasion-features.md`).

## Risky sites

R1 = Lua work in a `LoopAsync` callback that is more than a flag read. These run off-thread Lua in a state that game-thread code uses at the same time.

| Id | File:line | Period | Off-thread Lua work | State shared with |
|---|---|---|---|---|
| R1a | `mod/shared/HarnessCommands/HarnessCommands.lua:318` | 100 ms | 2 `readFile` calls (io.open, read, close, path string concatenation), token compare, closure for `ExecuteInGameThread` | every mod that uses commands, including InvasionMod |
| R1b | `mod/InvasionMod/Scripts/scheduler.lua:24` | 100 ms | `clock_ms` update, `ExecuteInGameThread(run_due)` | InvasionMod state: all 19 feature jobs run on the game thread of the same state |
| R1c | `mod/HarnessActions/Scripts/main.lua:680` | 100 ms | `readFile`, closure | HarnessActions state |
| R1d | `mod/UEBridge/scripts/main.lua:1438` | 50 ms | `readFile`, `os.remove`, `json.decode`, `handle(req)` | UEBridge state (the `busy` flag, patch P4, limits the overlap) |
| R1e | `mod/UEBridge/scripts/main.lua:1018` | stream interval | flag reads, `ExecuteInGameThread(sample)` | UEBridge state |
| R1f | `mod/shared/HarnessTelemetry/HarnessTelemetry.lua:232` | 1 s | closure with `pcall` allocated off-thread | the mod that starts telemetry |
| R1g | `mod/shared/HarnessTune/HarnessTune.lua:111` | 2 s | `next(overrides)`, closure | InvasionMod state |
| R1h | `mod/InvasionMod/Scripts/features/mod_state/init.lua:38` and `:61` | 500 ms, 3 s | counter, closure, `pcall(hook_begin_play)` (calls `RegisterHook` off-thread) | InvasionMod state |
| R1i | `mod/HarnessBoot/Scripts/main.lua:643` | 500 ms | `finished()`, closure | HarnessBoot state |
| R1j | `mod/HarnessReload/Scripts/main.lua:113` and `:164` | 200 ms | `readFile`, `os.remove`, `log.try(handle)` (whole handler off-thread) | HarnessReload state |
| R1k | `mod/shared/HarnessTelemetryProbe/HarnessTelemetryProbe.lua:71` and `:347` | 1 s and 20 ms | whole probe work off-thread | probe mods only |
| R1l | `mod/OrderProbe/Scripts/main.lua:48`, `mod/HarnessLoadProbe/Scripts/main.lua:72`, `mod/HarnessLogTest/Scripts/main.lua:13` | 100 to 5000 ms | closures, log writes | probe mods only |

Notes:
- InvasionMod has 4 `LoopAsync` threads in one Lua state (R1a, R1b, R1g, R1h), next to the game-thread work. The scheduler comment (`scheduler.lua:2`) records that 5 loops crashed 120-day runs (issue 163) and that the fix was "one loop with a short body". The short body still allocates and calls into Lua. It lowered the rate but did not remove the race.
- Crash group A (53 of 143) is damage inside Lua tables with garbage pointers (`0xffffffffffffffff`), found later on the game thread. This matches a damaged Lua heap.
- R1d: `handle(req)` and `json.decode` run off-thread. Every scenario uses the bridge about once per second (see the UEBridge lines in each `mod.log`).

R2 = key bind callbacks (input thread) that write to Lua state:

| Id | File:line | Work |
|---|---|---|
| R2a | `mod/InvasionMod/Scripts/core/menu.lua:602` | `S.esc_requests = S.esc_requests + 1` (field write, no allocation) |
| R2b | `mod/InvasionMod/Scripts/core/menu.lua:318`, called from `raid_widget/init.lua:109` and `tech_tree_widget/init.lua:300` | `S.toggles[#S.toggles + 1] = id` grows a table off-thread. It can reallocate the table array while the game thread reads it. |
| R2c | `mod/HarnessLoadProbe/Scripts/main.lua:111` | probe only |

R3 = no `NotifyOnNewObject` call exists in `mod/` (checked by grep).

R4 = frequent or large `FindAllOf` and building or unit scans from timers. They run on the game thread, so they cannot race. They are risky because a scan wraps many objects in Lua userdata and touches objects that are being destroyed or just spawned.

| Id | File:line | Trigger | Scan |
|---|---|---|---|
| R4a | `mod/shared/HarnessManor/HarnessManor.lua:149` (`manor_state`, `manorBuildings` at `:82`) | every liege menu refresh and every `liege_menu_state` poll (`mod/InvasionMod/Scripts/features/liege_influence/init.lua:76`) | `region:GetBuildings()` and `typeOf` per building. Lead report: two crashes (`20261024-025200-6707`, `20261024-025737-e905`, both in the crash table, group C). Caching the read (re-read every 2 s while missing) gave 3 of 3 clean runs. |
| R4b | `mod/shared/HarnessTune/HarnessTune.lua:54` | every 2 s while overrides exist | `FindAllOf("SMUnit")`, each unit read |
| R4c | `mod/InvasionMod/Scripts/features/invasion/init.lua:736` | after a wave spawn | `FindAllOf("SMUnit")` over up to 448 new units |
| R4d | `raid_behavior/world.lua:41`, `unit_balance/init.lua:278`, `manor_stronghold/squads.lua:32` (all under `mod/InvasionMod/Scripts/features/`) | raid tick, balance tick | `FindAllOf("SMUnit")` |
| R4e | `mod/InvasionMod/Scripts/features/bandits/world.lua:73` | each bandits poll | `FindAllOf("PawnCPP")`, `GetFullName` |
| R4f | `mod/InvasionMod/Scripts/core/menu.lua:111`, `:162` | when a menu opens | `FindAllOf(class)`, `GetFullName` per object |
| R4g | `mod/shared/HarnessBattle/HarnessBattle.lua:204` to `:531` (8 sites) | scenario commands | `FindAllOf("SMUnit")` |

R5 = stale UObject references across ticks. A grep for module-level or state-level caches of pawns, units, widgets or camps found none in `mod/InvasionMod`: features find objects again at each use. Probe modules keep `S.widget`, `S.added`, `S.overlay` (`HarnessTexProbe.lua:74`, `HarnessUiProbe.lua:228`, `:289`): probes only. 19 feature files use `IsValid`. The loop bodies after `FindAllOf` (for example `invasion/init.lua:736`) were not all checked and stay a follow-up.

## Ranking (evidence and simplicity of the fix)

1. R1a, R1b, R1g, R1h in InvasionMod, and R1c and R1d in the harness mods: move all timers to `LoopInGameThreadWithDelay`. This removes all off-thread Lua. One helper and local edits.
2. R2b: remove the table append from the key bind callback.
3. R4a: cache the manor read (the armsbutton worktree already shows the effect).
4. R4c: do not scan all units in the same tick as a spawn (tested in `ab-results.md`).

## R6 child-widget lookups without IsValid (lead data point: uparrow spike)

`GetChildAt(i)` can return an invalid wrapper. Calling a method on it (`GetClass`, `GetVisibility`) dereferences a null object (group B, small addresses such as `0x10`).

| File:line | Check before use? |
|---|---|
| `mod/InvasionMod/Scripts/core/menu.lua:334` | yes (`isValid(child)`) |
| `mod/InvasionMod/Scripts/features/order_tooltip/widget.lua:17` | **no**: `box:GetChildAt(i):SetVisibility(COLLAPSED)` |
| `mod/InvasionMod/Scripts/features/order_tooltip/widget.lua:49` | **no**: `child:GetVisibility()` and `child.DescriptionText:GetText()` |
| `mod/shared/HarnessClickHooks/HarnessClickHooks.lua:94` | partly: inside `pcall`, then `valid(text)`. A `pcall` does not catch an access violation. |
| `mod/shared/HarnessGameSetup/HarnessGameSetup.lua:86` | through `step()` (pcall wrapper), no `IsValid` |
| `mod/shared/HarnessUiProbe/HarnessUiProbe.lua:57`, `:120` | `pcall` only, probe module |

A Lua `pcall` cannot stop a native access violation, so only an `IsValid` check before the call helps. The two `order_tooltip` sites are the clear fixes.
