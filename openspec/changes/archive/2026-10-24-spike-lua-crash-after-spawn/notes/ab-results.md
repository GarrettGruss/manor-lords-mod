# A/B results

Setup: one game at a time, slot auto, interleaved A, B, A, B. Code: branch `feat/spike-lua-crash-after-spawn` (commit with `HarnessLoop`). Variant `async` = `--env HARNESS_LOOP_MODE=async` (all timers as `LoopAsync`, the old behavior). Variant `game` = default (timers as `LoopInGameThreadWithDelay`: no off-thread Lua in InvasionMod, HarnessCommands, HarnessActions, HarnessTelemetry, HarnessTune, mod_state). `UEBridge`, `HarnessBoot` and `HarnessReload` still use `LoopAsync` in both variants. Scenarios are from `main`. Each run has `hostmem.jsonl` (free memory of the PC every 2 s, new in this spike).

## Experiment 1: long fast-forward (`invasion-first-raid`, about 470 s, speed 3)

| Variant | Runs | Crashes | Verdicts | Min free memory (MB) per run |
|---|---|---|---|---|
| async | `ab-ff-async-1` to `-4` | 0 of 4 | 4 pass | 2695, 1137, 984, 3788 |
| game | `ab-ff-game-1` to `-4` | 0 of 4 | 4 pass | 2533, 1307, 1039, 3857 |

Earlier crash rate of this scenario in the worktrees since 2026-10-22: 3 crashes in 11 runs (27 percent, from `rate.py` over all `summary.json`). Here 0 of 8. The A/B could not reproduce the crash, so it cannot show a difference.

## Experiment 2: great wave spawn (`invasion-great-raid-waves`, 15 squads, 448 raiders, about 160 s)

| Variant | Runs | Crashes | Verdicts | Min free memory (MB) per run |
|---|---|---|---|---|
| async | `ab-wave-async-1` to `-5` | 0 of 5 | 3 fail, 2 pass | 3773, 3824, 3748, 3728, 3462 |
| game | `ab-wave-game-1` to `-5` | 0 of 5 | 5 pass | 3489, 3585, 3509, 3366, 3619 |

The 3 failures (`ab-wave-async-1`, `-3`, `-4`) are not crashes (no crash folder). The scenario log says `TimeControlError: speed 3 should give gameSpeed 8.0, but the game reports 1 after 3 tries`. A speed command did not hold. This happened only in the `async` variant (3 of 5 against 0 of 5). A Fisher exact test gives p = 0.17 (two-sided), so it is a hint, not a result.

The planned third A/B (wave spawn with and without an immediate unit scan) was not run: the crash did not reproduce in 10 wave runs, so a scan effect cannot be measured. It stays open (R4c in `code-audit.md`).

## Memory

Free physical memory was between 984 MB and 3857 MB at the lowest point of each run (PC total 16332 MB, game resident about 4.2 GB). The lowest values (984 and 1039 MB, `ab-ff-async-3`, `ab-ff-game-3`) are runs without a crash. Memory pressure alone is not a cause: no crash in 18 runs at any free-memory level. It is not ruled out as a helper for the earlier crashes: those runs had no memory log. The new `hostmem.jsonl` shows it for future crashes.

## Verdict

- Not reproduced: 0 crashes in 18 runs, in both variants. No claim of cause is proven.
- The game-thread timers cost nothing visible: 9 of 9 runs in variant `game` passed, durations equal to variant `async`.
- Weak hint for `LoopInGameThreadWithDelay`: no TimeControlError in 9 `game` runs against 3 in 9 `async` runs (the 4 fast-forward runs of each variant had none).
