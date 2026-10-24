## Why

Issue #476. The spike `spike-lua-crash-after-spawn` found that off-thread Lua (`LoopAsync`, key bind callbacks) is the best explanation for many game crashes. It moved the scheduler and four harness modules to game-thread timers (`HarnessLoop`). The cause is not proven, but the fix is cheap. This change finishes the move and measures the effect.

## What Changes

- Move the remaining `LoopAsync` users to `HarnessLoop`: `UEBridge` (two loops, small local patch), `HarnessBoot`, `HarnessReload` (two loops). Keep intervals and stop conditions.
- Key bind callbacks (menu toggle, raid widget, tech tree widget, Esc) do not change shared Lua tables. They hand the action to the game thread with `ExecuteInGameThread`.
- After a wave spawn, the unit scan runs in a later game-thread tick, not in the spawn tick. The other frequent `FindAllOf` loops check `IsValid` inside the loop body.
- The fake game kit gets `LoopInGameThreadWithDelay` and `CancelDelayedAction`, so the game mode of `HarnessLoop` is tested.
- Measure with 10 runs each of `invasion-first-raid` and `invasion-great-raid-waves` and compare with the spike numbers.

## Capabilities

### Modified Capabilities
- `mod/core`: the scheduler uses a game-thread timer; key binds hand work to the game thread.
- `harness/fake-game-kit`: the kit runs game-thread timers.

## Impact

`mod/UEBridge`, `mod/HarnessBoot`, `mod/HarnessReload`, `mod/InvasionMod` (menu, widgets, invasion), `mod/shared/HarnessTune`, `harness/fakegame`, wiki pages `engine-limits` and `shared-lua-modules`. No behavior change for the player.
