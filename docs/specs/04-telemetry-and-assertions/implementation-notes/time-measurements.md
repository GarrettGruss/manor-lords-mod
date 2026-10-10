# Time measurements in the real game

Date: 2026-10-10. Game build 25598558, test save `saveGame_0`. Measured with the bridge in a game started by the launcher
(`run.py --scenario noop --keep-open`), and stopped by hand afterwards. `clock` is `RTSMultiEngineCPP:getGameTimeAdjusted()`.

## Speed
`PawnCPP:changeGameSpeed(newSpeedIndex, playSfx)` takes an index. The engine property `gameSpeed` shows the factor.
The clock rate is measured over 4 s of wall time.

| Call | `gameSpeed` | Clock rate (game s per wall s) |
|---|---|---|
| `changeGameSpeed(0, false)` | 0 | 0.0 (stopped, same as pause) |
| `changeGameSpeed(1, false)` | 1 | 0.998 |
| `changeGameSpeed(2, false)` | 4 | 4.003 |
| `changeGameSpeed(3, false)` | 8 | 8.003 |
| `changeGameSpeed(4, false)` | 8 | 7.926 (clamped to the top speed) |

So the in-game "2x" and "3x" are 4x and 8x of the clock. The harness calls them speed 2 and 3.
- `unPauseGame()` restores the speed from before the pause (8 stayed 8). After the boot pause it gave 1x.
- `increaseGameSpeed(false, false)` stays at 8 at the top (no wrap). `decreaseGameSpeed(false)` goes 8, 4, 1.
- `setGameSpeed(2.0)` and `(3.0)` set `gameSpeed` to exactly 2 and 3 while the game runs, but it does not unpause a paused game.
- `getGameSpeed()` works (returns the factor). `getGameSpeedID()` fails through the bridge (out parameter).

### The "player paused" flag drops the speed
After the boot pause, `PawnCPP.bIsPlayerPaused` stays true. If `changeGameSpeed(3)` is called then, `gameSpeed` is 8 for about 3 s and then
falls back to 1 (seen twice). `changeGameSpeed` alone also does not make a paused game run at once (clock rate 0.0 with `gameSpeed` 1 after
`pauseGame` and `changeGameSpeed`). `unPauseGame()` clears the flag.
In the launcher runs the speed was set back to 1x once more, even after `unPauseGame`, about 3 s after the first change (`attempt 2` in 3 of 3
`time-advance` runs; the later `telemetry-sanity` runs at speed 1 had `attempt 1`). A second `changeGameSpeed` held for the whole run.
The cause of the late restart of spec 02 is known now (intro cinematic, `02-save-autoload/implementation-notes/clock-restart-cause.md`), but this fallback is a different event: two `decreaseGameSpeed` calls 1 to 2 s after `changeGameSpeed(3)`, caller unknown (same note). `TimeControl.set_speed` calls `unPauseGame`, then `changeGameSpeed`,
waits 3 s, checks `gameSpeed`, and tries again up to 3 times.

## Calendar (`TemporalComponent`)
- One game day is **40 game seconds** (measured over 29 days: 1179 clock seconds). That is 40 wall s at 1x, 10 s at 2x, 5 s at 3x.
  The first launcher run of 2 days at speed 3 needed 12.6 wall s, including the 3 s settle time and the pause check.
- `day` is the **day of the year**, 1 to 365. It goes on across months (day 91 is the first day of month 4). `dayOfTheMonth` is the day of the month.
- The year has 365 days. Test with `setDay(362)` on the engine: 365 (month 12) is followed by day 1, month 1 and `Year` 2. `Season` changed from 1 to 0 at the same time (winter 0, spring 1).
  `setDay` did not change `daysTotal`.
- `daysTotal` **does change**. It read 0 at load (day 61), and counted 1 for each game day (7 after 7 days, 48 after 48 days). It never wraps. `monthsTotal` counts months in the same way (3 after 3 months).
- `day`, `dayOfTheMonth`, `month`, `Year` and `daysTotal` change at the same game time. A poll loop that reads them one after another (about 0.6 s per loop) can see a mix at the moment of a change.
  `month` and `Year` were seen to change one poll before `day`. Read them while the game is paused, or use `daysTotal`.
- `TimeControl.run_game_days` counts `daysTotal`. `absolute_day()` (`Year * 365 + day`) gives a day number for date asserts.

## Pop-ups pause the game
At 8x for a few minutes the village got a "Hunger!" event window (Hochweg). The game is paused until the player closes it, and the clock stands
still while `gameSpeed` still reads 1. The bridge cannot close it. `unPauseGame` does not help. `TimeControl` raises an error that names this cause
when the clock does not move. A scenario that runs many days can hit it (seen after about 48 days; the 2 day scenario did not).

## Not measured
- 2x as speed 2 from the paused start in a launcher run (only measured by hand with probes).
- The effect of `playSfx = true`.
- Month lengths other than March (31 days), December (31) and January.
