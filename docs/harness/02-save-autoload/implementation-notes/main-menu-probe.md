# Main menu probe (read only)

Date: 2026-10-09. Game at the main menu, "still in development" dialog open. No save loaded.
Tool: ue4ss-bridge (patched), called from Python. All calls were reads. Nothing in the game or the saves changed.

## Results

| Question | Result |
|---|---|
| Which world is loaded? | `/Game/NotStronghold/Maps/MainMenu.MainMenu`. Game mode `MenuGameMode_ML_C`. Pawn `MenuPawn_C`. |
| Does `mainMenu_widget_C` exist? | Yes, one instance. Path: `/Engine/Transient.GameEngine_*:BP_MLGameInstance_C_*.mainMenu_widget_C_*`. It is owned by the game instance. The numbers change in each session. |
| Does `menu_saveLoadMenu_C` exist? | No (count 0). It is created later, when the load screen opens. |
| `RTSMultiEngineCPP`, `PawnCPP` | None (count 0). They exist only in a game map. This can be the "not in game" signal. |
| `MLGameInstance` | One instance (`BP_MLGameInstance_C`). It exists at the menu. |
| `mainMenu_widget_C` functions | `LoadGame`, `continue`, `startNewGame`, `SwitchToLoadScreen`, `closeLevel`, `GoToGameSetup`, `EnsureStartAchieved`, `OnSaveLoadMenuClosed_Event`, `Construct`, `Tick` are present. This matches the jmap. |
| `IoHandler` static calls | Work through the CDO ref `/Script/ManorLords.Default__IoHandler`. |
| `DoesSaveGameExist` | `autosave` = true, `saveGame_0` = true, `saveGame_99` = false. |
| `IsSaving` | false. |
| `LoadGameFromSlot("saveGame_0")` | Returned `{"__object": "<invalid>"}`. The bridge cannot use the returned save object. Do not rely on this call to read a save. |

## Meaning for the plan
- "In the main menu" can be detected: world name is `MainMenu`, and `mainMenu_widget_C` exists.
- "In game" can be detected: `RTSMultiEngineCPP` and `PawnCPP` exist and the world is not `MainMenu`.
- `DoesSaveGameExist` is a safe check that the test save is there before any load attempt.
- To read a save descriptor, use the load screen (`menu_saveLoadMenu_C.NamedSlots`). `LoadGameFromSlot` does not work through the bridge.
- The function list shows names only. It does not show the parameters. The `LoadGame` signature (a `SaveGameSlot` struct) comes from the jmap only.

## Next
1. Open the load screen with `SwitchToLoadScreen(false)`. This is a UI change only. Then read `menu_saveLoadMenu_C.NamedSlots`.
2. Test passing a struct argument to `call_function` (needed for `LoadGame`). Compare with calling `continue()`.
3. Load a save. This needs the user to agree, because it loads a real save into the running game.

## Load screen probe (after `SwitchToLoadScreen(false)`)

The call returned `null` (no error). The load screen opened. The user saw it, with the "still in development" dialog drawn over it.

| Question | Result |
|---|---|
| Class of the load screen | `W_MainMenu_SaveLoadScreenV2_C` (child of `MLSaveLoadMenuScreen`). The jmap name `menu_saveLoadMenu_C` is not used. Count of `menu_saveLoadMenu_C` was 0. |
| Path | `...mainMenu_widget_C_*.WidgetTree_*.W_MainMenu_SaveLoadScreenV2_C_*`. Object names at the menu were the same in two game sessions, but do not store them. |
| `NamedSlots` | Array of 29 `MLSaveGameDescr` objects. One entry is an invalid object. |
| `SortedSlotsByDate` | Array of 29 `SaveGameSlot` structs: `{SlotIndex, Descriptor}`. This is the exact type `mainMenu_widget_C:LoadGame` takes. |
| Descriptor fields that read well | `saveSlot` (string), `saveName`, `LevelName`. |

### SlotIndex is a list position, not the slot number
Examples (`SlotIndex`, `saveSlot`, `saveName`, `LevelName`):
- `0, autosave, "Autosave", Jagged_Cliffs`
- `2, saveGame_0, "saveGame_0", Jagged_Cliffs`
- `29, saveGame_27, "saveGame_0", Jagged_Cliffs` (a save named "saveGame_0" that lives in slot `saveGame_27`)
- Old saves have an empty `saveSlot` and names like "Save Game No. 11".

So the file slot name (`saveSlot`) and the display name (`saveName`) are different things. Select by `saveSlot`.

### Why the bridge cannot load a save
`LoadGame` needs a `SaveGameSlot` struct that holds a `Descriptor` object. The bridge cannot pass object references (review finding L7).
The bridge's `eval_lua` could, but it is off, and we keep it off.
A Lua mod can do it: it takes the struct from `SortedSlotsByDate` and passes it to `LoadGame` unchanged.

### Revised plan for the probe
1. A small Lua mod `HarnessLoadProbe` with a key bind. It does these steps and logs each one with `HarnessLog`:
   1. Find `mainMenu_widget_C`. Call `SwitchToLoadScreen(false)`.
   2. Wait until `W_MainMenu_SaveLoadScreenV2_C.SortedSlotsByDate` is not empty.
   3. Find the entry whose `Descriptor.saveSlot` equals the target slot name.
   4. Call `mainMenu_widget_C:LoadGame(entry)`.
2. Use the same logic in `HarnessBoot` later, without the key bind.
