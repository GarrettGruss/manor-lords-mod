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
