# Pause and game speed

Date: 2026-10-09. Measured in the running game with the bridge and with HarnessBoot.

## The game does not start paused after a load
An earlier note said the game starts paused. That was wrong. The user saw time running after the load.
Measurements 40 s after the load (the clock is `RTSMultiEngineCPP:getGameTimeAdjusted()`):

| Step | `bIsPlayerPaused` | `gameSpeed` | clock change in 3 s |
|---|---|---|---|
| Baseline after the load | true | 1 | 3.1 (running) |
| After `PawnCPP:pauseGame()` | true | 0 | 0.0 (stopped) |
| After `PawnCPP:setGameSpeed(0)` | true | 0 | 0.8 (still moving a little) |
| After `unPauseGame()` and `setGameSpeed(1)` | false | 1 | 1.3 (starting to run) |

Findings:
- `PawnCPP.bIsPlayerPaused` is **not reliable**. It read true while time ran. It only changes after `pauseGame` or `unPauseGame` calls.
- `pauseGame()` does stop the clock. It is the right call.
- `setGameSpeed(0)` does not stop the clock completely. Do not use it to pause.
- Right after a load, `gameSpeed` is 0 for a few seconds, then the game sets it to 1.
  So a `pauseGame` call that comes too early can be undone by the game.
- The only safe test for "paused" is to read the clock twice and see that it did not move.

## Game speed settings (from the user)
The game has four speed settings: pause, 1x, 2x and 3x.
`gameSpeed` read 1 at 1x. The values for 2x and 3x are not measured yet.
Functions from the jmap: `PawnCPP:getGameSpeedID`, `changeGameSpeed(newSpeedIndex, playSfx)`, `increaseGameSpeed`, `decreaseGameSpeed`.
`getGameSpeedID` has an out parameter and fails through the bridge ("expected 1 parameters, received 0").

## What HarnessBoot does now
New state `PAUSING` between `WAITING_FOR_READY` and `READY`:
1. Read the clock every 500 ms.
2. If the clock moves, call `pauseGame` (at most once every 2 s).
3. When the clock does not move for 3 polls in a row, write `ready.marker` and go to `READY`.
4. If this does not work in 30 s, the state is `FAILED`.

`ready.marker` now has a `clock` field. `"paused":true` means the clock was measured as stopped.

## Slot list fills while it loads
The first HarnessBoot run found `saveGame_0` in a list of 10 entries. The earlier probe saw 29 entries.
The game scans the save folder in the background, so a list that is not empty can still be incomplete.
HarnessBoot now polls until the wanted slot is in the list. It fails only when the 30 s limit ends.
Before this fix, a slot that was not yet listed gave a false failure.

## Open
- Values of `gameSpeed` at 2x and 3x.
- Whether `pauseGame` works at once after the clock first moves, or needs the game to settle. The retry handles both.

## Second fix: the clock stands at 0 right after the load
The first version of `PAUSING` (commit f1903e6) still failed in the real game. The log showed
`calling pauseGame (call 1)` and `READY` in the same second, and `ready.marker` had `"clock":0.0`.
The user saw the game running at 1x.

Cause: for several seconds after `LoadGame` the game itself holds the speed at 0, so the clock stands at 0.
The check read "clock did not move" three times and called that "paused". Then the game set the speed to 1x and undid the pause.

Fix: `PAUSING` now waits until the clock has moved at least once (`sawRunning`). Only then does it call `pauseGame`
and count the polls where the clock stands still. If the clock never moves, the state is `FAILED` with "the clock never started".
The time limit for this state is 60 s.

Test: the fake game in `harness/tests/boot_state_machine.py` now holds the clock at 0 for 12 ticks after the load, longer than the ready check.
After `READY` the test lets 10 more seconds pass and checks that the clock did not move.
The version from f1903e6 fails this test ("the clock moved after READY (0.0 -> 8.0)"). The new version passes.

## Open: one launch where the slot list never appeared
In the same log, an earlier launch ended with `FAILED: slot 'saveGame_0' did not appear in the save list in 30 s`.
The load screen was opened, but the list never had the slot. The next launch (about 100 s later) worked: the list had 29 entries within 1 s.
Possible causes: the "still in development" banner on top, or the first `SwitchToLoadScreen` call coming before the menu was ready.
Not known. If it happens again, try calling `SwitchToLoadScreen` again after 10 s.

## Third fix: the game restarts the clock after our pause
Run with the second fix (commit 1578d7c), 2026-10-09 23:03. `boot.json` said `READY`. `ready.marker` had `"clock":0.433`,
so the pause worked at that moment: the clock had started, `pauseGame` was called, and the clock stood still.
About 2 s after `READY` the clock ran again. The user saw 1x. The bridge confirmed: the clock changed by 3.08 per 3 s, `gameSpeed` 1.

Measurements afterwards, with `PawnCPP:pauseGame()` called by hand in the middle of the game:

| Time after `pauseGame` | clock change in 2 s | `gameSpeed` |
|---|---|---|
| 2 s to 14 s (7 readings) | 0.0 each time | 0 |

So `pauseGame` holds when it is called later. Something undoes the pause only in the first seconds after a load.
Other values read at the time: `gameSpeedScheduled` = 1, `isGameSpeedScheduled` = false, `gameSpeedBeforePause` = 0.

The cause is not known. A candidate: the main menu closes about 10 s after `LoadGame`, and `mainMenu_widget_C` has a function named
`unpauseAndResetDLSS`. This is a guess. It was not tested. The game might also apply the scheduled speed `gameSpeedScheduled`.

Fix: `PAUSING` now needs the clock to stand still for 8 seconds in a row (`CLOCK_STOPPED_SECONDS`).
If the clock moves again, it calls `pauseGame` again and starts to count from zero.
The test now includes a late restart of the clock (the fake game undoes the pause once, 17 ticks after the load).
The previous version fails it ("the clock moved after READY (1.0 -> 11.0)"). The new version passes.

The 8 s window is a guess based on one run (the clock restarted about 4 s after the pause).
If a run still shows a late restart, find the cause first. A hook on `RTSMultiEngineCPP:setGameSpeed` would show who sets the speed.

## Open
- RESOLVED (2026-10-10): the intro cinematic ends and restores 1x. See `clock-restart-cause.md`.
- (old) Which game code restarts the clock after the load? Not confirmed.
- Is 8 s long enough in every launch? Check the next runs. Look at `boot.json` and at `mod.log` for a second `pauseGame` call.

## Result of the third fix (run at 23:07, build with the 8 s hold)
The game stays paused.

`mod.log`:
- `state -> PAUSING` at +8 s after the load call.
- `game clock is moving; calling pauseGame (call 1)` at the same time.
- `game clock is moving; calling pauseGame (call 2)` 5 s later. **The game did restart the clock after our first pause.** The hold caught it.
- `state -> READY` 8 s after the second pause. `ready.marker`: `"clock":1.0835`, `seconds_since_start` 24.

Checked with the bridge after `READY`, 8 readings over 24 s: the clock stayed at 1.084 (change 0.0 each time) and `gameSpeed` stayed 0.
The user also saw the game paused.

So the late restart is real. It happened again, about 5 s after the first pause. The 8 s hold is enough in this run (one run).
The cause is still not known. Collect more runs before the window is trusted.

## Launch log
`mod.log` also shows a launch at 1791605143 with no end state (`WAITING_FOR_MENU` and then nothing). The game was probably closed before the menu appeared.
