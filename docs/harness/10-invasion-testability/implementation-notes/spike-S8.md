# Spike S8: pop-ups and stalls

Date: 2026-10-10. Game: real game, base fixture, 8x speed. Tools: bridge calls through a watcher script and the scenario `soak-days` (runs `soak-1` to `soak-3`).
Verdict: **solved by closing, and avoided by feeding.** A pop-up can be closed through the bridge. A fed village does not get the hunger pop-up.

## What appears
- Two kinds of pop-up were seen: `messageType` = `hunger` (the "Hunger!" window of the village) and `cold` (once, in the first winter at about day 320, in the long run `soak-long3`; it was closed by `close_popups` too). `hunger` appeared at about game day 91 of the base fixture in every long run
  (watch runs: day 91 and day 117 after a restart of the clock; soak runs `soak-1`, `soak-2`, `soak-3`: once each, after about 7.5 wall minutes at 8x).
  Other types exist in the game data (`DT_Popups`).
- It is a Blueprint widget `popupMessageWidget_C` (path `Game/UI/Elements/popupMessageWidget`), one instance under `BP_MLGameInstance_C`.
  Properties: `messageType` (Name), `Region`, `closing` (bool), `Button_Accept`, `messageTxt`, `title_txt`.
  Screenshot: a dimmed screen with a CLOSE button at the bottom.

## Does it pause or stall the game
- Yes. The game pauses itself: `gameSpeed` goes from 8 to **0**, and the clock stands still (3640.04 for as long as it was watched).
  The player pause flag `bIsPlayerPaused` does not show it (it read true while the game ran, and false during one stall). `queuedPopups`, `eventMsgQueue` and `MessageWidgets` of the player pawn stayed empty: they are not the source.
- `unPauseGame` does not help (spec 04). A stall does not end by itself.

## What closes it
- Calling the Blueprint event of the Accept button on the widget closes it:
  `popupMessageWidget_C:BndEvt__popupMessageWidget_Button_Accept_K2Node_ComponentBoundEvent_0_OnButtonReleasedEvent__DelegateSignature()`.
  Result in the real game (twice by hand, then in all three soak runs): `closing` becomes true, `gameSpeed` goes back to **8** (the old speed), and the clock runs again within 3 s.
- How to see that a pop-up is open: `closing == false` on a live widget. Do not use `IsInViewport` or `GetIsVisible`: both read false for an open pop-up. `Visibility` was 4 in both states.
  After a close the widget can stay in memory with `closing == true`, and it is later removed (`no live instance` is then a normal answer).
- The command `close_popups` of `HarnessActions` (version 6) presses Accept only on widgets with `closing == false`, so it cannot unpause a game that the scenario paused on purpose.
  `popup_state` reads the same state. A call with no pop-up open answers `count 0`.
- In a scenario: `ctx.popups()` as `on_poll` of `ctx.run_until`, with the stall detector as the second line (`stall_s`, `on_stall=ctx.popups`).
  In the soak runs the pop-up was closed at the next poll (2 s): `stalled_polls` was 0 and the clock rate stayed 7.9.

## What was not found
- **Prevention by feeding.** The hunger pop-up comes from the start village running out of food. With `GiveItemByID(30, 100)` (100 Fish) every 10 game days the soak run `soak-feed` (200 days) had **no pop-up at all**.
  Closing is still the safety net. Function-level prevention (`playPopupMessageIfNotPlayedRecently`, `playQueuedPopups`, `DT_Popups`) was not tried.
- **The village is defeated at about day 137 if it is not fed.** The scenario run `soak-long2` stalled at clock 5498 (day 137, `daysTotal` 137). The screenshot shows "You have been defeated." (days passed 137, dead villagers 4); the player region had population 0.
  `BP_MLGameInstance_C.currentGameVictoryStatus` is the status (0 while playing). This explains the stall without a widget, and probably the earlier game that vanished at day 135 (the game can be left from that screen; not proven).
  `soak-days` feeds the village and checks the status at each poll (`GameOver` with a clear message). Feeding is not enough for 2 years: see `soak-results.md` (defeat at about day 350, in the first winter).
- **A game ended from outside.** In run `soak-long` the game process ended 25 s into the scenario with exit code 15 (the code that `psutil` terminate gives on Windows). No crash report, no pop-up, nothing in the logs. Not repeated in the 8 runs that followed; cause not found.
- Other pop-up types: not seen in about 1500 game days of runs.

## Harness changes from this spike
- `HarnessActions` commands `popup_state` and `close_popups`, actions `ctx.actions.close_popups()` and `popup_state()`, helper `ctx.popups`, `runlib/popups.py`.
- Stall detector in `ctx.run_until` (spec 10, U3). A stall is a failed scenario with a message that names pop-ups.
