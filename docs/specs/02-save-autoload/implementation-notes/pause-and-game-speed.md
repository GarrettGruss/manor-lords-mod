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
