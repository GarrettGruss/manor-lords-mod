# Direct launch with environment variables

Date: 2026-10-09. Question: can the harness start the game with its own environment variables,
so that each run writes to its own folder? A launch through Steam (`steam://rungameid/...`) cannot pass them.

## Test
1. Closed the game.
2. In PowerShell: `$env:HARNESS_RUN_DIR = <repo>\runs\direct-launch-test` and `$env:HARNESS_AUTOBOOT = '1'`.
3. `Start-Process ManorLords-Win64-Shipping.exe -WorkingDirectory <Win64 folder>`. Steam was running.

## Result: it works
- The game started (the process was up) and stayed up. Steam did not restart it.
- HarnessBoot saw the variables. It reached `READY` and wrote its files in the run folder:
  `boot.json`, `ready.marker`, `mod.log`, and the folder `bridge\`. The old default folder `ue4ss\harness\` was not updated.
- HarnessBoot was on because of `HARNESS_AUTOBOOT=1`. The switch file `autoboot.enable` also existed, so this test does not prove that
  the variable alone is enough. (The code in `HarnessBoot` checks the variable first.)
- UEBridge used `<run folder>\bridge` (patch P1 works).
- The Python side found it with `UE4SS_BRIDGE_DATA_DIR=<run folder>\bridge`. `hello` and `read_clock.py` worked.
  The game was paused (`clock` 0.717, `change` 0.0).
- `game-close.ps1` killed the game after the close request, as before.

## What this means
- The run launcher can start the game directly, with `HARNESS_RUN_DIR`, `HARNESS_AUTOBOOT` and `HARNESS_TEST_SAVE`. No switch file is needed.
- Each run has its own `bridge\` folder. A stale `request.json` from an old run cannot reach a new run.
- The `autoboot.enable` file is then only for manual starts through Steam. Remove it when the launcher is the normal way to start (the uninstall script already does).
- Steam must be running. Not tested: Steam closed. The game may refuse to start, or ask Steam to start it.

## Not tested
- Direct launch with Steam closed.
- Whether any Steam overlay or Steam feature is lost with a direct launch (the user does not need them for tests).
- The folder `runs\direct-launch-test` is a test result and stays out of git (`runs/` is ignored).

## Steam closed: not tested, on purpose (2026-10-10)
The test needs Steam to be shut down (`steam.exe -shutdown`) and started again. A test script was written (shut down Steam, start the game directly with the
harness environment, record whether it stays alive and whether `HarnessBoot` writes `boot.json`, stop the game, start Steam again with `-silent`).
It was NOT run: the permission system refused the action, because it interferes with the user's running Steam session. The refusal was respected.

What the harness does today: `preflight` checks that `steam.exe` is running and fails with a clear message if not (unit tested), so a run never
starts the game without Steam. Whether the game itself would start without Steam (it may call Steam to restart itself, or exit) is unknown.
To test it, the user can close Steam by hand and run: `.venv\Scripts\python.exe harness\run.py --scenario noop --skip-steam-check` (this option does not exist yet:
add it only if the answer matters), or start the game executable directly with `HARNESS_RUN_DIR` set and look at `boot.json`.

## Steam closed: tested (2026-10-10, the user closed Steam and said "steam should be closed")
The section above says the test was not run. It was run later, after the user answered "Yes, test it" and closed Steam. This script did NOT shut Steam down or start it again.

Direct launch without Steam (`ManorLords-Win64-Shipping.exe` started with `HARNESS_RUN_DIR`, `HARNESS_AUTOBOOT=1`, `HARNESS_TEST_SAVE`):
- The game started and stayed alive. `HarnessBoot` reached `READY` after 32 s (the same as with Steam). `boot.json`, `ready.marker`, `mod.log`, `telemetry.jsonl` and `bridge/` were written.
- The game did NOT start Steam by itself (no `steam.exe` or `steamwebhelper.exe` afterwards).
- A full launcher run (`run.py --scenario smoke`) with Steam closed: verdict pass, boot READY (31 s, 1 `pauseGame` call), private appdata removed, user saves unchanged.

Decision: Steam is not required. The preflight no longer fails when Steam is not running. It adds the note "Steam was not running; the game was started directly without it" to the summary
(2 tests). `harness/game-launch.ps1` (Steam URL launch) still needs Steam, and it is for manual use only.
Not tested: Steam features such as cloud saves or achievements (not needed for tests).
