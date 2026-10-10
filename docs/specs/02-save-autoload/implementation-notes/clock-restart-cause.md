# Cause of the clock restart after a load

Date: 2026-10-10. Game build 25598558, test save `saveGame_0`. Method: a temporary Lua mod (`probe-clock-hooks.lua` in this folder)
hooked about 60 functions (pre and post) and logged wall time, the clock, `gameSpeed` and the pawn mode at each call.
The probe mod is removed from `mod/` and from the game (`deploy.ps1 -Clean`). The probe scenario is `probe-speed-fallback.py` in this folder.

## Cause (found, 8 boots with the probe, same sequence every time)
After `LoadGame` the game plays an **intro cinematic**. It ends with `PawnCPP:setMainUIMode(Gameplay)`. That call restores 1x
(`gameSpeed` 0 to 1, delegate `OnGameSpeedChanged`). So it undoes any `pauseGame` made while the cinematic plays.

Sequence (seconds after the `LoadGame` call; the numbers repeat within 0.5 s in each run):

| Time | Event |
|---|---|
| +5 | `ReceiveBeginPlay` of the pawn, then `changeGameSpeed(1)` and `setGameSpeed(1.0)` (clock still 0) |
| +5 | `playCinematicSequence` and `setMainUIMode(Cinematics = 1)`. `currentUIMode` = 1, `cinematicMode` = true |
| +8 | The clock starts (while the cinematic plays; the dip-to-black fade opens) |
| +9 | HarnessBoot calls `pauseGame` (old version). Hook: `gameSpeed` 1 to 0 |
| +13 | `setMainUIMode(Gameplay = 0)`: `cinematicMode` false, `OnGameSpeedChanged`, `gameSpeed` 0 to 1. **This is the restart** |
| +13.5 | HarnessBoot calls `pauseGame` again (call 2) and it holds |

Proof that the time is fixed and not related to our pause (delay experiment, first `pauseGame` made later on purpose):
- Pause at +9: restart at +13 (4 runs).
- Pause at about +12.5 (delay 4): restart 0.3 s later, at the same absolute time.
- Pause at about +15 (delay 7) and at +23 (delay 14), both after the end: no restart, no `OnGameSpeedChanged` event.
A pause made after the cinematic ended is never undone.

No other hooked function fired around the restart: `unPauseGame`, `RTSMultiEngineCPP:setGameSpeed`, `increaseGameSpeed`,
`SetGamePaused`, `unpauseAndResetDLSS`, `closeLevel`, `OnSaveLoadMenuClosed_Event`, `OnSaveLoaded_Event` (never fired in 25 s).
`UpdateDateAndSeason` did not matter. The widget set did not change after +5.5 s.
Also seen: `gameSpeedScheduled` = 1, `isGameSpeedScheduled` = false all the time; `gameSpeedBeforePause` = 1 after the first pause, 0 after the second.
`RTSMultiEngineCPP:setGameSpeed` never fired, even when the speed changed (the pawn function writes the field natively).

## Hook notes
- Hooks on Blueprint functions work (`changeGameSpeed`, `decreaseGameSpeed`, `W_HUD_Timer:OnGameSpeedChanged_Event`, `setMainUIMode` is native).
  Blueprint class hooks can only be registered after the class is loaded: the pawn and HUD ones needed about 4 s, `mainMenu_widget_C` ones the menu.
- Hooks on functions that fire every frame (`setDipToBlackOpacity`, `setIsUsingUI`) crashed the game once
  (`EXCEPTION_ACCESS_VIOLATION` in `lua_setiuservalue`, 1 of 1 run with them, about 1 s after READY). Do not hook per-frame functions.
- The post hook of a Blueprint function logs inner calls before outer ones (order seen: `setGameSpeed`, `changeGameSpeed`, `decreaseGameSpeed`).

## Change in HarnessBoot
`PAUSING` does not call `pauseGame` while `player.currentUIMode ~= 0` (cinematic playing). It waits at most `CINEMATIC_WAIT_S` = 25 s
in the state, then pauses anyway. The 8 s hold stays as a safety net (it covers a restart with no sign).
Result: 5 launcher runs of `smoke`, all `pass`, boot 31 to 32 s, **one** `pauseGame` call in each boot (before: two), the log line
"intro cinematic is playing; waiting" in each, `ready.marker` clock 5.0 to 5.4 (before: about 1).
Tests: `harness/tests/boot_state_machine.py` has new modes `cinematic`, `nocinematic`, `silentrestart`, `cinematicstuck` and counts the `pauseGame` calls.
The fake clock (`fakegame/clock.py`) now models the intro (`cinematic=(start, end)`); `late_revert_after` is now off by default.
The old HarnessBoot fails mode `cinematic` (2 `pauseGame` calls instead of 1).

## The 1x fallback after `changeGameSpeed` (not explained)
Not the cinematic: it happens about 26 s after the `LoadGame` call, after READY. Hook sequence (6 runs: 4 `time-advance`, 2 `probe-speed-fallback`):
`changeGameSpeed(3)` sets `gameSpeed` 8. 0.9 to 1.9 s later, in one instant, `decreaseGameSpeed` runs twice (8 to 4 to 1), giving
`changeGameSpeed(2)`, `setGameSpeed(4.0)`, `changeGameSpeed(1)`, `setGameSpeed(1.0)`. A second `changeGameSpeed(3)` holds.
It happened in 6 of 6 runs where `changeGameSpeed(3)` came 27.0 to 28.0 s after the mod loaded (decrease at 28.5 to 29.4 s), and in 0 of 4
runs where it came at 26.3 to 26.5 s (the speed held for 9 s and a second call too). So a one-time event at about 28.5 s mod time seems to
slow the game down, but it did not act in the runs with the earlier change, which contradicts a simple timer.
The caller of `decreaseGameSpeed` is **not known**. It was not `InpActEvt_slowSpeed`/`fastSpeed`/`pause`, `W_HUD_Timer`, `MainUICPP`,
`playPopupMessageGUI`, `playEventMessage`, `playAlert`, `playMessage`, `addLog`, `triggerTutorialIfNeeded`, `OnWindowFocusChanged` (all hooked, none fired).
Not verified: a tutorial timer (`Start Tutorials if Enabled` sets a timer at +5 s). `TimeControl.set_speed` retries and handles it. Keep the retry.

## Not verified
- Behavior with the intro switched off in the game settings (no run). HarnessBoot then pauses at once (tested only in the fake game).
- Other saves or maps. All runs used `saveGame_0`.

## The 1x fallback: more tests (2026-10-10, probe scenario `probe-tutorial-speed`)
The hidden scenario `harness/scenarios/probe_tutorial_speed.py` unpauses, calls `changeGameSpeed(3)` and samples `gameSpeed` and the clock every
0.25 to 0.9 s for 10 s. It was run in the real game with the private save folder (no hook mod).

- The game has a tutorial system. The engine actor holds `tutorialsLeftToShow` (32 names, starting with `tutorial_beginnings`, `tutorial_growth`,
  `tutorial_gameSpeed`). The player has `tutorialsShown`, `TutorialMessages` and `tutorialTimerHandle`. The settings `useTutorials` and `showTutorials` exist
  in the jmap but were not found on the game instance, the player or the engine.
- **Hypothesis 1, rejected: the tutorial queue.** With `engine.tutorialsLeftToShow` set to an empty list (the write worked), the speed still fell from 8 to 1
  about 1.5 to 1.9 s after the change, at a game clock of about 20 to 22.
- **Hypothesis 2, rejected: a letter arrival.** `PawnCPP.InBox` and `TutorialMessages` stayed at length 0 during the samples, also in runs with a drop.
- **The fallback is intermittent.** Six controlled trials (3 with extra reads of `InBox` and `TutorialMessages` in the samples, 3 without): the speed fell back to 1x in 2 of 6
  trials (one with the reads, one without). When it fell, it was at a game clock of about 17 to 22 s (1.5 to 1.9 s after the change). In the other 4 trials the speed held at 8
  for the full 10 s. Earlier runs that used `time-advance` saw it in 6 of 6 runs when the change came 27 to 28 s after the load, so the rate also depends on the situation.
- So the cause is not known. It is not the tutorial queue, not a new letter, and not the probe's own reads. It looks like a game event around game clock 17 to 22 s that
  lowers the speed one time (two `decreaseGameSpeed` calls in one instant, caller unknown, see above). `TimeControl.set_speed` retries and holds on the second call.
- Decision: close the question as "intermittent, handled by the retry". A scenario must not assume that the first `changeGameSpeed` holds. If a later feature needs the
  cause, hook `decreaseGameSpeed` with a stack or caller identification (UE4SS hooks give no stack): try a native hook on the speed UI function, or watch the HUD speed widget.
