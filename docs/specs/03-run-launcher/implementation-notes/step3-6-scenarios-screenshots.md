# Steps 3 to 6: scenarios, screenshots, five runs, old scripts

Date: 2026-10-10. All run numbers below are from the real game.
Unit tests: 125 in total (`test_runlib*.py`), 45 new. No game is needed for them.

## What was added
| File | Job |
|---|---|
| `runlib/bridge_client.py` | `Bridge`: engine, pawn and calendar lookup, clock measure, `pause()` and `unpause()` with checks |
| `runlib/scenario_context.py` | `ScenarioContext`: bridge helpers, `scenario.log`, assertions (`check`, `check_range`), `result()` |
| `runlib/scenario.py` | registry with limits and hidden flag, loader for `harness/scenarios/*.py`, `configure_bridge_client` |
| `scenarios/` | `noop`, `smoke`, hidden `selftest-fail` and `selftest-timeout`. Each module has `LIMIT_S` |
| `runlib/windows.py`, `runlib/screenshot.py` | window list (ctypes), window choice, clip to screen, PNG with `mss` |
| `runlib/series.py`, `run_series.py` | N launcher runs, table, `runs/series-<time>.json` |
| `run.py` | `--list-scenarios`, `--include-test-scenarios` |

## Decisions
- The bridge client is the `ue4ss_bridge.server` module, imported in the launcher process. The module reads
  `UE4SS_BRIDGE_GAME_DIR` and `UE4SS_BRIDGE_DATA_DIR` at the first call and caches the result (`_GAME`).
  `configure_bridge_client` sets the variables first and then clears `_GAME`. One launcher process serves one run, so this is enough.
- The pawn path changes in each session. `Bridge` looks up engine, pawn and calendar on every call. This costs one round trip each.
- The bridge returns objects as `{"__object": "<Class> <path>", ...}`. `object_path` takes the path from it.
- `pause()` calls `PawnCPP:pauseGame`, waits 0.5 s, then needs the clock to stand still for 3 s. It tries up to 3 times.
  `unpause()` calls `unPauseGame` and waits up to 5 s for the clock to move. Both return a dict with `ok`. The scenario asserts it.
- The scenario phase time limit is the `LIMIT_S` of the scenario (smoke 60 s, noop 30 s). The old fixed 90 s is now the default only.
- Start screenshot: taken at the start of the scenario phase. End screenshot: taken in `collect`, which runs before teardown, so the game is still open.
  This also gives an end screenshot after a failed or timed out scenario.
- A screenshot problem adds a note and never changes the verdict.
- UE4SS crash dumps (`ue4ss\*.dmp` newer than the run start) are copied into `crash/`. A new UE crash folder or dump adds a note. The verdict does not change.
- `launch-series.ps1` was deleted. `game-launch.ps1` and `game-close.ps1` stay, with a header note that they are for manual use.

## Real runs
Five `smoke` runs in a row with `run_series.py` (`runs/series-20261010-051633.json`). All `pass`, exit 0, each in its own folder, no game process afterwards.

| Run id | Verdict | Total | Boot | Scenario phase |
|---|---|---|---|---|
| 20261010-051259-5529 | pass | 42.8 s | 31 s | 9.1 s |
| 20261010-051341-1ae6 | pass | 42.1 s | 30 s | 9.3 s |
| 20261010-051424-573a | pass | 43.3 s | 31 s | 9.1 s |
| 20261010-051507-1614 | pass | 41.9 s | 30 s | 9.1 s |
| 20261010-051549-08fa | pass | 44.5 s | 32 s | 9.5 s |

Smoke asserts 6 things. In the runs: clock change 0.0 after boot, change about 0.7 after `unPauseGame`, calendar day 61, month 3, year 1, clock change 0.0 after `pauseGame`.
The test save hash was the same in all five runs.

Self tests (hidden scenarios):

| Scenario | Verdict | Exit | Wall time | Check |
|---|---|---|---|---|
| `selftest-fail` | fail ("the scenario failed its assertions") | 1 | 36 s | no game left |
| `selftest-timeout` (limit 5 s, sleeps 40 s) | timeout ("phase scenario timeout: exceeded the time limit of 5 s") | 3 | 38 s | no game left. The launcher exited at once after teardown: the sleeping thread is a daemon thread. `scenario.log` has the "sleeping" line and no "woke up" line |
| `smoke`, game killed from outside about 36 s after start | crash ("game process ended during scenario") | 2 | n/a | note "screenshot end failed: no window belongs to the game process", collect and teardown ran |

Summary size: 3533 bytes for smoke (the biggest, with 6 asserts), 2747 for fail, 2599 for timeout.
The smoke summary is close to the 4096 byte limit. The `environment` block and the assert ranges take most of it. Watch this when scenarios get more asserts.
Screenshots: about 7 MB each at 2582x1496 (PNG level 6). Two per run, so about 14 MB per run. Runs are not in git.

## Screenshots: what the pictures show
I looked at `start.png` and `end.png` of a smoke run with the Read tool.
- The picture shows the real game (HUD, "Game Paused", the map). Start and end are the same scene, as expected for a paused game.
- `mss` copies screen pixels. Anything in front of the game window is in the picture. In this test the UE4SS GUI window (the debugger, top left, about 670x565 px) lay over the game and was captured.
  So "the game window is not in front" is NOT safe: the picture then shows what is on top.
- The window rectangle includes the invisible resize border (about 8 px). A strip on the right edge shows other windows behind the game.
- Capture uses the screen, not the window surface. A minimized window cannot be captured. The code detects this and adds a note.
- DPI: the process is set DPI aware before the window list is read. The rectangle matched the picture.

## Answers to the open questions
1. Does `mss` capture the game window when it is not in front, or on another monitor? Is the "A New Message" banner a problem?
   Not in front: no, it captures what is on screen, so a window in front is in the picture (seen with the UE4SS GUI). Another monitor: not tested on real hardware.
   The code uses the virtual screen of all monitors (`monitors[0]`) and clips to it, with unit tests for a negative left edge. Minimized: not tested with the real game, handled by a note (unit tested).
   "A New Message" banner: not seen in any run, so not tested. Because the launcher takes screenshots of the screen, a banner on top would be in the picture.
   Possible fix if it is needed: a UE4SS setting to hide the GUI window, or `PrintWindow`/graphics capture. Not tried.
2. Where does the UE crash reporter write, and how fast? Not answered. The two forced kills (step 2 and this step) wrote no crash folder.
   A terminate is not a crash for UE. `collect` copies folders newer than the run start from `%LOCALAPPDATA%\ManorLords\Saved\Crashes\`. Timing of a real crash is still unknown.
   No UE4SS `.dmp` file was seen in `ue4ss\`.
3. Steam closed: not tested. Asking Steam to exit is not safe for the user's session. The `preflight` phase fails with "Steam is not running. Start Steam first." (checked by a unit test, not by a real run).
4. Test save copy: not tested. The runs only read `saveGame_0`. Its SHA-256 was the same before all five runs. The question stays open (it matters only if a scenario saves).
5. Can a scenario unpause reliably after a load? Yes in 7 of 7 real runs of `smoke` (one first try and the five runs above, plus the crash run until the kill): `unPauseGame` moved the clock within the first 1 s poll, and `pauseGame` stopped it for 3 s.
   The scenario starts after HarnessBoot holds the pause for 8 s, so the late restart by the game (spec 02) did not happen. Limit: only one test save and one scenario.
6. Is a game started with `Popen` killed when the launcher exits? Not tested as a question. The launcher always stops the game in `teardown` (checked in all runs, including the timeout run).
   With `--keep-open` the game is left on purpose. Whether it then survives the launcher exit was not checked with the real game.

## Not verified
- Another monitor, a minimized window, the "A New Message" banner, and a real UE crash report.
- `--keep-open` with the real game. Steam closed.
- A bridge error inside a scenario while the game is alive (unit tested only: it is `harness_error`).
