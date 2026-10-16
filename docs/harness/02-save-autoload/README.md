# Spec 02: Save auto-load and in-game ready signal

Status: done (PR 2). The acceptance criteria are met. The main path works in the real game (10 of 10 cold starts, see `implementation-notes/launch-series-results.md`). Items below that say "not tested" stay open (they need the game).
Roadmap phase: 4 (deterministic start state).

## Goal
Start every test run from the same saved game, with no human clicks.
A boot mod loads a fixed test save from the main menu and then tells the harness
when the game is ready for the scenario to start.

## Non-goals
- Launching or killing the game process (planned spec 03, run launcher).
- Sampling telemetry during the run (planned spec 04, telemetry).
- Making the simulation deterministic. After load, the simulation can still differ between runs.

## Background
The game has no native "load save from slot" function.
The load is done by the main-menu Blueprint widget.
Details and sources are in `implementation-notes/jmap-findings.md`.
All names below come from the jmap dump. Treat them as unverified until tested.

Key facts:
- Load entry point: `/Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C:LoadGame(SaveGameSlot)`.
  `SaveGameSlot` is a struct with `SlotIndex:Int` and `Descriptor:MLSaveGameDescr`.
- Fallback: `mainMenu_widget_C:continue()` loads the latest save.
- `MLGameInstance.savefileToLoad:Str` holds the pending slot name.
- `IoHandler:DoesSaveGameExist(SlotName)` and `IoHandler:LoadGameFromSlot(SlotName)` read saves without loading them.
- The load needs a live main-menu widget. It only exists in the main-menu level.
- Blueprint classes may not be loaded yet at startup, so hooks on them can fail.

## Design

### Components
- `mod/HarnessBoot/Scripts/main.lua`: the boot mod. It runs the steps below.
- Settings are read from environment variables set by the launcher:
  - `HARNESS_RUN_DIR`: where to write logs and markers.
  - `HARNESS_TEST_SAVE`: the slot name of the test save.
- Output files in `HARNESS_RUN_DIR`:
  - `boot.json`: current boot state and a timestamp for each state change.
  - `ready.marker`: written once, when the game is ready.
  - `mod.log`: the log from `HarnessLog`.

### Boot state machine (as built)
States: `WAITING_FOR_MENU`, `LOADING_SAVE`, `WAITING_FOR_READY`, `PAUSING`, `READY`, `FAILED`.

1. `WAITING_FOR_MENU`: poll (every 500 ms) until `mainMenu_widget_C` exists. Time limit: 120 s.
2. `LOADING_SAVE`:
   1. Check the save exists with `IoHandler:DoesSaveGameExist`.
   2. Open the load screen with `mainMenu_widget_C:SwitchToLoadScreen(false)`.
   3. Poll `W_MainMenu_SaveLoadScreenV2_C.SortedSlotsByDate` until an entry has `Descriptor.saveSlot` equal to the test slot.
      The list fills while the game scans the save folder, so it can be incomplete. Do not fail on an incomplete list.
   4. Call `mainMenu_widget_C:LoadGame(entry)` with that list entry, unchanged.
   Time limit: 30 s. No fallbacks are built. The main path has not failed in the tests.
3. `WAITING_FOR_READY`: wait until all of these are true for 3 polls in a row:
   - `RTSMultiEngineCPP` is valid.
   - Its `playerRef` is valid.
   - `regions` is not empty and at least one `Region.isSettled` is true.
   Time limit: 180 s.
4. `PAUSING`: the flag `PawnCPP.bIsPlayerPaused` is not reliable, so use the game clock (`RTSMultiEngineCPP:getGameTimeAdjusted`):
   1. Wait until the clock has moved once. After a load the game holds the clock at 0 for a few seconds.
   2. Call `PawnCPP:pauseGame`. If the clock moves again, call it again (at most once every 2 s).
   3. The game is paused when the clock stays still for 8 s in a row. The game restarts its clock once after the first pause, in every run so far.
   Time limit: 60 s. See `implementation-notes/pause-and-game-speed.md`.
5. `READY`: write `ready.marker` (slot, time, clock, calendar).
6. `FAILED`: write the reason to `boot.json` and `mod.log`. The harness reads this as a result.

### Rules
- Run all game-object calls on the game thread (`ExecuteInGameThread`).
- Every wait has a time limit. A timeout moves the state to `FAILED`.
- Write `boot.json` and `ready.marker` atomically (`.tmp`, then rename).
- Log every state change with `HarnessLog`.
- Never write to the original test save. (Today the test uses the user's own `saveGame_0` and only reads it. A separate copy is still to do.)
- The mod is off unless `HARNESS_AUTOBOOT=1` or the file `ue4ss\harness\autoboot.enable` exists.

## Plan and status
1. Probe the main menu through the bridge. Done. (`implementation-notes/main-menu-probe.md`)
2. Test `LoadGame` by hand with a key bind. Done. (`HarnessLoadProbe`, `load-test-saveGame_0.md`)
3. Write `HarnessBoot` with the state machine. Done, with mock tests in `harness/tests/`.
4. Run 10 launches in a row. Done: 10 of 10. (`launch-series-results.md`)
5. Make a copy of the test save under its own slot name, and check that the load screen lists it. **To do.**
6. Test with the "still in development" dialog open. **To do.**
7. Find what restarts the game clock after a load. **To do** (optional: a hook on `setGameSpeed`).

## Answers to the open questions
- Slot name format: the file slot name is `Descriptor.saveSlot` (`autosave`, `saveGame_<N>`). `SlotIndex` is only a list position.
- Does `NotifyOnNewObject` see the menu widget? Not needed. Polling with `FindFirstOf` works.
- Does `LoadGame` need the widget visible or focused? It worked after the load screen was opened by `SwitchToLoadScreen`. Not tested with the dialog open.
- Splash or intro? A "still in development" dialog shows at the menu. Its effect on `LoadGame` is not tested.
- Earliest safe "ready" signal: polling for the engine, player and a settled region, then the clock check. `OnSaveLoaded` was not used.
- Is `pauseGame` safe right after load? It works, but the game restarts the clock after it (see above), so the pause must be held and checked.

## Open questions
- What restarts the clock after the first pause, and is 8 s always enough?
- Does the test save need to be a copy, and does the load screen list a slot with a custom name?
- Does the "still in development" dialog block `LoadGame`?

## Acceptance criteria
- From a cold launch, the game reaches `READY` with the test save loaded, and no input from a human. **Met.**
- 10 of 10 launches reach `READY`, or each failure has a clear reason in `boot.json`. **Met** (10 of 10).
- A missing save or a missing menu gives `FAILED` with a reason, and does not hang. **Met in the mock tests.** Not tried in the real game.
- The spec lists the verified function names and the real slot format. **Met** (see the notes).
