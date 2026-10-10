# Step 2: real phases

Date: 2026-10-10. Code: `harness/runlib/{game,environment,phases,scenario}.py`, `harness/run.py`.
Tests: `harness/tests/test_runlib_phases.py` (32 tests, no game). Together with step 1: 80 tests.

## What was added
| File | Job |
|---|---|
| `runlib/game.py` | game paths (`GameInstall`), process find and stop (psutil), game environment, `boot.json` reader, pause call counter, `ensure_game_alive` |
| `runlib/environment.py` | build id, exe size and time, save SHA-256 (read only), mod folder hashes, git commit and dirty flag |
| `runlib/phases.py` | `build_real_phases`: preflight, deploy, launch, boot, scenario, collect, teardown |
| `runlib/scenario.py` | scenario registry (`@register`), bridge client setup, scenario `noop` |

Changes to existing code: `runner.py` got a `notes` list in the shared state (shown in `summary.notes`).
`tools/read_clock.py` got a function `read_clock()` that returns the dict. `main()` prints it as before.
`run.py` got `--scenario` and `--keep-open`. `config.json` records scenario, test save, limits, keep_open.

## Real runs (all with the real game)
| Run | Verdict | Exit | Time | Detail |
|---|---|---|---|---|
| `20261010-050249-a7fc` | pass | 0 | 37 s | boot READY after 32 s, 2 pauseGame calls, clock paused (change 0.0, gameSpeed 0), summary 2.7 KB |
| `20261010-050345-c51b` | pass | 0 | 37 s | game started by hand first (PID 17984). Note: "stale game process PID 17984 was stopped" |
| `20261010-050429-c093` | crash | 2 | 27 s | game killed 25 s after start by a helper script. Boot phase failed with "game process ended during boot (exit code 15)", crash recorded, collect and teardown ran, `summary.json` written |

After every run no game process was left. The run folder of run 1 has `boot.json`, `ready.marker`, `mod.log`, `bridge/`, `UE4SS.log`, `scenario.json`, `config.json`, `summary.json`.

## Decisions
- Crash detection uses the `Popen` handle (`poll()`), so the exit code is known. `ensure_game_alive` does nothing after `game_stop_requested` is set.
- Boot seconds are counted from the start of the launch phase, to match the earlier 31 s cold start numbers.
- Teardown copies `UE4SS.log` a second time after the stop, because the file is buffered. Collect runs before teardown (spec order), so its copy can be short.
- The `noop` scenario returns `asserts: []` as requested. Its pass depends on `clock.paused`.
- The mod hash covers all top-level folders of `mod/`, including `shared`.

## Surprising or open
- A boot deadline (230 s) or a HarnessBoot `FAILED` raise `PhaseFailed`. A boot deadline therefore gives `harness_error`, not `timeout`. Only the runner limit (240 s) gives `timeout`. Decide in a later step if the boot deadline should be a `timeout`.
- `test_seconds_are_recorded` (step 1) failed once in four runs with 0.19 s against 0.2 s. It is a timing rounding issue in an old test, not in this step.
- `harness_git.dirty` was true in the runs because other work (HarnessTelemetry mod, new test) was uncommitted. The mod hashes show what was deployed.
- Crash reports are copied only if the folder time is newer than the run start. A report that appears late (after collect) is not seen. The killed game in run 3 produced none.
- A new crash report does not set the crash verdict by itself. Only a game process that ended without a stop request does.
- Not tested: Steam closed, a timeout of a real phase, `--keep-open` with the real game, an exception inside the scenario with a live game.
