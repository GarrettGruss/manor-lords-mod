# Spec 02: Save auto-load and in-game ready signal

Status: draft. Nothing here is verified in the running game yet.
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

### Boot state machine
States: `WAITING_FOR_MENU`, `LOADING_SAVE`, `WAITING_FOR_READY`, `READY`, `FAILED`.

1. `WAITING_FOR_MENU`: use `NotifyOnNewObject` to wait for `mainMenu_widget_C`. Time limit: 120 s.
2. `LOADING_SAVE`:
   1. Check the save exists with `IoHandler:DoesSaveGameExist`.
   2. Find the slot descriptor in `menu_saveLoadMenu_C.NamedSlots`, or with `IoHandler:LoadGameFromSlot`.
   3. Build a `SaveGameSlot` and call `LoadGame` on the game thread.
   4. If that fails, try the fallbacks in order: `continue()`, then set `savefileToLoad` and open the map.
3. `WAITING_FOR_READY`: wait until all of these are true:
   - `RTSMultiEngineCPP` is valid.
   - The main-player `PawnCPP` is valid.
   - `regions` is not empty and the player `Region.isSettled` is true.
   - At least one `TemporalComponent` day update was seen, or `OnSaveLoaded` fired.
   Time limit: 180 s.
4. `READY`: write `ready.marker`. Pause the game (`PawnCPP:pauseGame`) so the harness controls when time starts.
5. `FAILED`: write the reason to `boot.json` and `mod.log`. The harness reads this as a result.

### Rules
- Run all game-object calls on the game thread (`ExecuteInGameThread`).
- Every wait has a time limit. A timeout moves the state to `FAILED`.
- Write `boot.json` and `ready.marker` atomically (`.tmp`, then rename).
- Log every state change and every fallback with `HarnessLog`.
- Never write to the original test save. The harness gives the game a copy.

## Plan
1. Write a small probe mod that only logs when `mainMenu_widget_C` appears and lists `NamedSlots`.
   Record the result in `implementation-notes/`. This checks that the names are right.
2. Test `LoadGame` by hand through the probe (key bind). Record the slot name format.
3. Write `HarnessBoot` with the state machine. Test each fallback by forcing the earlier step to fail.
4. Run 10 launches in a row. Record how many reach `READY` and how long each takes.
5. Update this spec with what was learned.

## Open questions
- Does `NotifyOnNewObject` see `mainMenu_widget_C` before the class is fully loaded?
- What is the real slot name format? (`SlotNameFromIndex`, `MakeSlotNameFromSlotNumber`)
- Does `LoadGame` need the widget to be visible, or focused, or only to exist?
- Does the game show a splash or intro that must be skipped first? (`MLCheatManager:ShouldSkipIntro` exists.)
- Which signal is the earliest safe "ready": `OnSaveLoaded` or the polling check?
- Is `pauseGame` safe right after load, or does it break the load UI?

## Acceptance criteria
- From a cold launch, the game reaches `READY` with the test save loaded, and no input from a human.
- 10 of 10 launches reach `READY`, or each failure has a clear reason in `boot.json`.
- A missing save or a missing menu gives `FAILED` with a reason, and does not hang.
- The spec lists the verified function names and the real slot format.
