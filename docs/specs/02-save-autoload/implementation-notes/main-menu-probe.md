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
