# Load test: slot saveGame_0 (manual, F8)

Date: 2026-10-09. Mod: `HarnessLoadProbe` (commit 2a901f4). Game at the main menu, "still in development" dialog dismissed.

## Result: the load works
The mod log shows every step (times are unix seconds):
1. `F8 pressed; target slot 'saveGame_0'`
2. `step 1: SwitchToLoadScreen(false)`
3. `step 2: slot list ready after 1 polls` (the list was ready within 500 ms)
4. `slot list has 29 entries`; `found 'saveGame_0' at list position 17, SlotIndex 2, level Jagged_Cliffs`
5. `step 4: calling mainMenu_widget_C:LoadGame`, then `LoadGame returned without error`

No Lua error and no crash. About 10 seconds after F8 the bridge showed the game map loaded.

## State after the load (read with the bridge)
| Item | Value |
|---|---|
| World | `/Game/NotStronghold/Maps/NewMapSets/Jagged_Cliffs.Jagged_Cliffs` |
| Game mode, pawn | `RTSGame_C`, `MyPawnCPP_BP3_C` |
| Objects | `RTSMultiEngineCPP` 1, `PawnCPP` 5 (1 player, 4 AI), `Region` 7 |
| Calendar (`RTSMultiEngineCPP.TemporalComponent`) | `day` 61, `month` 3, `Year` 1, `Season` 1 (spring) |
| Paused | `PawnCPP.bIsPlayerPaused` read true, but the game clock was running. **The game does not start paused.** See `pause-and-game-speed.md`. |
| `RTSMultiEngineCPP.gameSpeed` | 0 at first, 1 about 4 seconds later |
| Regions | 7. Settled: Hochweg, Krumme Leite, Riesenbuckel. Not settled: 4 others. All have `Approval` 50. |

## Things that did not read as expected
- `silver`, `influence` and `kingsFavour` on the player pawn read 0. **The user says these start at 0 in this game, so 0 is correct for this save.** They are valid fields. They will change as the game runs.
- `daysTotal` is 0 although `day` is 61. `TemporalComponent.day` looks like the day of the year, and `daysTotal` may count from another point. Do not use `daysTotal` as the clock. Compare against the calendar shown in the game.
- `RTSMultiEngineCPP` has no property named `daysTotal`. The function `getDaysTotal()` exists and returned 0.

## Answers to open questions in the spec
- Does `NotifyOnNewObject` see the menu widget? Not tested. `FindFirstOf("mainMenu_widget_C")` worked when pressed after the menu was up.
- Slot name format: file slot name is `saveSlot` on the descriptor (`autosave`, `saveGame_<N>`). Select by it, not by `SlotIndex`.
- Does `LoadGame` need the widget visible or focused? The load screen was opened by the mod first. The dialog was dismissed. Not tested with the dialog still open.
- Splash or intro to skip? The "still in development" dialog appears at the menu. The mod worked after the user closed it. It is not known whether it blocks `LoadGame`. Test next.
- Earliest safe "ready" signal: not decided. `RTSMultiEngineCPP` exists about 10 s after F8. Test the polling check from the spec.
- Is `pauseGame` safe right after load? The game does not start paused (the first note was wrong). See `pause-and-game-speed.md`.

## Other findings
- `ue4ss/harness/mod.log` is append-only. Entries from earlier game sessions stay in the file. Use `HARNESS_RUN_DIR` per run, or truncate at launch.
- The key bind works. `HarnessLogTest` still runs; disable it in `mods.txt` when it is no longer useful.

## Next
1. Build `HarnessBoot`: the same logic, with no key bind and a state machine with timeouts.
2. Decide what to do with the dialog (try loading with the dialog open).
3. Make a test save copy under a new slot name and check that the load screen lists it.
