# Save and load hooks (spec 24, plan step 1, static)

Date: 2026-10-15. Method: static only. No game run, no game function call, no save file opened.
Sources:
- jmap: `...\Manor Lords\ManorLords\Binaries\Win64\ue4ss\ManorLords-5.5.4-40574608+++UE5+Release-5.5-5e627997.jmap`.
  Checked with a read-only scan script (scratchpad). Each row below names its jmap path.
- Notes: `openspec/changes/archive/2026-10-15-legacy-02-save-autoload/implementation-notes/jmap-findings.md` (section 1, 4), `clock-restart-cause.md`,
  `main-menu-probe.md`, `load-test-saveGame_0.md`; `openspec/changes/archive/2026-10-15-legacy-07-feature-test-kit/implementation-notes/actions-catalog.md` (save_state, lines 172-178);
  `openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/README.md` (lines 19-52); `openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/implementation-notes/autosave.md`;
  `openspec/changes/archive/2026-10-15-legacy-09-asset-mods/implementation-notes/datatable-check.md`; `harness/runlib/actions.py` (line 62), `harness/runlib/saveslots.py`;
  `mod/shared/HarnessAutosave/HarnessAutosave.lua` (line 8, 92).

"Native" = a C++ UFunction (`FUNC_Native`). "BP" = a Blueprint function. "Static" = a class function (call on `Default__...`).
"UFunction" here means it appears in the jmap as a `Function` entry. Whether UE4SS can hook it is marked per row.

## 1. Save functions

| Function (jmap path) | Kind | Parameters | Hookable (UFunction) | Notes |
|---|---|---|---|---|
| `/Script/ManorLords.PawnCPP:requestSaveFile` | Native, BlueprintCallable, Final | `SlotName: Str`, `saveName: Str` -> `bool` | Yes (in jmap). Runtime hook not tested | Caller passes the slot name. Evidence below (Q2). Name shown in the menu is `saveName`. **Never call.** |
| `/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:SaveToDiskWithThumbnail` | BP, BlueprintEvent | `SlotName: Str`, `OverrideSaveName: Str` -> calls `requestSaveFile` | Yes, after the pawn BP class is loaded | Wrapper around `requestSaveFile`. Never call. |
| `/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:Request Autosave` | BP | `WasGamePaused: Bool` | Hook only. Never call | Timer target of the autosave. HarnessBoot moves the timer away (autosave.md). |
| `/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:Set Autosave Timer` | BP | `Time: Double` | Hookable, but do not call | Restarts the autosave timer. |
| `/Script/ManorLords.MLGameInstance:RequestMenuSave` | Native, BlueprintCallable | none | Yes (in jmap) | Menu save entry. Never call. Who calls it in play is not known. |
| `/Script/ManorLords.MLGameInstance:SetAutosavePeriod` | Native | `autosavePeriod: Float` | Yes | Do not call (CLAUDE.md). |
| `/Script/ManorLords.MLGameInstance:SetAutosavePeriodOnPawn` | BP event | `newAutosavePeriod: Float` -> `bool` | Yes | Used by HarnessBoot (one year, autosave.md). Not a save. |
| `/Script/ManorLords.IoHandler:SaveGameToSlot` | Static, Native | `SaveGameObject: Object`, `SlotName: Str`, `ioCategory: Enum` -> `bool` | Yes (in jmap) | Lowest save call found. Writes to the real save folder. Never call. |
| `/Script/ManorLords.IoHandler:SaveDataToSlot` | Static, Native | `InSaveData: Array`, `SlotName: Str`, `ioCategory` -> `bool` | Yes | Raw bytes. Never call. |
| `/Script/ManorLords.IoHandler:IsSaving` | Static, Native | none -> `bool` | Yes | Read only. Safe to call. |
| `/Script/ManorLords.IoHandler:DoesSaveGameExist` | Static, Native | `SlotName: Str` -> `bool` | Yes | Read only. Safe (used by probes). |
| `/Script/ManorLords.IoHandler:DeleteGameInSlot` | Static, Native | `SlotName: Str` -> `bool` | Yes | Deletes a real save. Never call from a harness action without a guard. |
| `/Script/ManorLords.IoHandler:LoadGameFromSlot` | Static, Native | `SlotName: Str` -> `Object` (MLSaveGame) | Yes | Read only in theory. A bridge call returned `<invalid>` (main-menu-probe.md). |
| `/Script/ManorLords.IoHandler:LoadDataFromSlot` | Static, Native | out `Array`, `SlotName: Str` -> `bool` | Yes | Read only. |
| `/Script/ManorLords.MLCheatManager:PrintSaveFiles` | Exec | none | Yes | Logs save slots. Read only. |
| `/Script/ManorLords.MLSaveLoadMenuScreen:OnGameSlotSaved` | Native, BlueprintCallable | `SlotIndex: Int` | Yes | Fires in the menu after a menu save (name only; behavior not tested). Candidate post-save hook. Gives an index, not a name. |
| `/Script/ManorLords.MLSaveLoadMenuScreen:SlotNameFromIndex` | Native, pure | `SlotIndex: Int` -> `Str` | Yes | Maps index to slot name. |
| `/Game/UI/Main_Menu/menu_saveLoadMenu.menu_saveLoadMenu_C:MakeSlotNameFromSlotNumber` | BP, pure | `SlotNumber: Int` -> `SlotName: Str` | Yes | Builds `saveGame_<N>` style names (menu side). |
| `/Game/UI/Main_Menu/saveSlot_widget.saveSlot_widget_C:DoSave` | BP event | `Save: Bool` | Yes (menu) | Menu save confirm. Not tested. |
| `/Script/ManorLords.PawnCPP:playSaveFinishedNotif` | BP event | none | Yes | Named "finished" notice. Candidate post-save hook (play-time). Not tested. |
| `/Script/ManorLords.PawnCPP:updateAnySaveMenu` | BP event | none | Yes | UI refresh. Low value. |

Caveat for all hooks: UE4SS normally fires a hook only when the function runs through `ProcessEvent`
(Blueprint calls, Lua calls, many UFunction calls). A C++ call from one native function to another does
not fire it. So a hook on `requestSaveFile` may not fire on a menu save that the C++ code makes directly.
This must be checked in the real game (see section 6).

## 2. Load functions and load events

| Function or property (jmap path) | Kind | Parameters | Hookable | Notes |
|---|---|---|---|---|
| `/Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C:LoadGame` | BP event, the real load entry | `SaveGameSlot: Struct(/Script/ManorLords.SaveGameSlot)` = `{SlotIndex: Int, Descriptor: Object(MLSaveGameDescr)}` | Yes (menu class; the probe hooked it) | A pre-hook sees the slot. `Descriptor.saveSlot` is the file name. |
| `/Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C:continue` | BP event | none | Yes | Continue button (latest save). |
| `/Script/ManorLords.MLGameInstance.savefileToLoad` | Property, Str | pending slot name | Read the property | Set before the map opens (fixture-load-bug.md). Read this in a hook to get the slot name after a load. |
| `/Script/ManorLords.RTSMultiEngineCPP.OnSaveLoaded` | Multicast delegate | none | Unclear from Lua. Not tested | Fires when a save finishes loading (jmap-findings.md section 4). Bind is not verified. |
| `/Game/UI/HUD/W_HUD_LordPanel_V2.W_HUD_LordPanel_V2_C:OnSaveLoaded_Event` | BP event | none | Yes, after the HUD class loads | **Did not fire in a 25 s probe** (clock-restart-cause.md). Do not rely on it alone. |
| `/Game/CPP_BP/RTSMultiEngineCPP_BP.MyRTSMultiEngineCPP_BP_C:OnLoaded_F036CE2A...` | BP latent load callback | `Loaded: Object` | Yes | Name suggests an async asset load, not the save load. Not checked. |
| `/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ReceiveBeginPlay` | BP event | none | Yes, after the pawn BP loads | Runs on new game and on load. Use with a check of `savefileToLoad`. |
| `/Script/ManorLords.IoHandler:LoadGameFromSlot` | Static, Native | `SlotName` | Yes | Pre-hook sees the slot name of a load. |

## 3. Q2 and Q4: slot names, file names and folder

Folder: `%LOCALAPPDATA%\ManorLords\Saved\SaveGames` (the real one, the user's). Names only, nothing opened.
Names seen (listed 2026-10-15; the folder itself was not changed):
- 90 files ending in `.sav`, and 43 `saveGame_<N>_descr.sav` files.
- Slot names: `autosave` (with `autosave.sav`, `autosave_descr.sav`, `autosave_coat_0..5.png`), and `saveGame_0` to `saveGame_47`
  (with gaps; for example 33, 34, 35, 42, 44 are missing). Each slot has `<slot>.sav`, `<slot>_descr.sav`, `<slot>.png`, and `<slot>_coat_<k>.png`.
- Other files: `menu.sav` (probably the menu save class `MLMenuSaveGame`, not checked), `rtsSettings.sav`, `steam_autocloud.vdf`.
- Other folders next to it: `SaveGames-backup` and `SaveGames-overwritten-by-probe-20261010`. The second one is from the `saveGame_9` overwrite (section 4).

Naming rule (evidence):
- The game writes `<SlotName>.sav` where `SlotName` is the string given to the save call (for example `saveGame_9.sav`).
- The menu builds slot names as `saveGame_<N>` (`MakeSlotNameFromSlotNumber`). `autosave` and `menu` are fixed names.
- The save also has a descriptor file `<SlotName>_descr.sav`. It holds `saveSlot` (the slot name), `saveName` (the name in the list), `LevelName`, `date`, `Version`, `saveVersion`, `UncompressedSize`.
- The load list shows only `autosave` and `saveGame_<N>` (06 README lines 19 and 37). A slot named `harness_<name>` is not listed.
  This affects plan step 2: `save_game` must not rely on the menu list for a `harness_` slot. The existing runlib install uses `saveGame_<max+1>` for this reason (06 README line 52).

Answers:
- **Q2 (slot or path from a hook):** Yes, by the call arguments. A pre- or post-hook on `requestSaveFile` or
  `IoHandler:SaveGameToSlot` sees `SlotName`. A load hook sees `SaveGameSlot.Descriptor` (and `saveSlot`), or
  `MLGameInstance.savefileToLoad`. The file path is the real folder plus `<SlotName>.sav`.
- **Q4 (file names, id):** Files are named by slot. The saved data has a real-clock `date` (DateTime), a game clock
  (`day`, `Year`, `daysTotal`, `monthsTotal`, `gameTimeAdjusted`, `gameTicksAdjusted`), and `UserIndex`.
  No save id or unique game id was found. `gameTicksAdjusted` (UInt64) and `date` are the closest things. Neither is proven unique.

### Does `requestSaveFile` let the caller choose the file?
**Yes.** Evidence:
- The jmap signature takes `SlotName` as the first input (section 1).
- `actions-catalog.md` lines 172-177: `requestSaveFile("saveGame_9", "probe-save")` returned true. It wrote `saveGame_9.sav`, `saveGame_9_descr.sav`
  and new coat files in the REAL folder. The file `saveGame_9` was an old 2024 save, and it was overwritten.
- `IoHandler:DoesSaveGameExist("saveGame_9")` was true before the call. So the game did not pick the slot itself.
- Conclusion for plan step 2: a new name is safe only if it does not exist yet. The guard must check `DoesSaveGameExist(name)` is false BEFORE the call, and refuse otherwise.
  It must not depend on the game to pick a new name.

## 4. Real-folder risk (why the guard matters)

- `IoHandler` reads and writes the REAL folder, even when a run has a private `LOCALAPPDATA` (actions-catalog.md line 175-176).
  The private folder only got its own `saveGame_0` files. So a harness save made through the game lands in the user's folder.
- The overwritten `saveGame_9` was restored from `SaveGames-backup` (actions-catalog.md line 177). The folder `SaveGames-overwritten-by-probe-20261010` is kept for review. Do not delete it without asking the user.
- A harness save writes into the real folder. Its cleanup (`DeleteGameInSlot`) also acts on the real folder. Plan step 2 must cover both.

## 5. Q3: fields that a save keeps and that Lua could write

The save class is `/Script/ManorLords.MLSaveGame`. It is a snapshot. The game fills it from live actors at save time. The live fields are not all saved.
So a Lua write to a live field only survives a save if the game copies that field into `MLSaveGame`. This is not verified for any field.

### 5a. Fields in `MLSaveGame` (top level, jmap `/Script/ManorLords.MLSaveGame`)
| Field | Type | Possible use | Risk |
|---|---|---|---|
| `day`, `Year`, `daysTotal`, `monthsTotal`, `gameTimeAdjusted`, `gameTicksAdjusted` | Int, UInt64, Float | game date (Q4) | Game-owned. Do not write. |
| `daysUntilNextRaid`, `daysSinceLastRaid` | Int | the great raid countdown (game-owned) | Game-owned. Do not write. |
| `lastBanditCampSpawnedDay`, `kingsFavour_daysLeft`, `scenario_nextActionDay` | Int | game state | Game-owned. Do not write. |
| `startedVersion`, `saveVersion` | Str, Int | version of the save | Game-owned. |
| `relationshipTags` (`SavedRelationsTag`: `pawnA_setupIndex`, `pawnB_setupIndex`, `Tag: Name`) | Array | a Name-typed tag per pair | Game uses it for relations. A harness tag would need an FName (crash note: plain strings crash). |
| `issuedStoryQuests`, `tutorialsLeftToShow` | untyped Array | a list of names | Game-owned. Untyped (element type not in the jmap). |
| `UserIndex` | UInt32 | engine | Do not write. |

### 5b. Sub-structs with spare or free-looking fields (jmap `ScriptStruct` entries)
| Struct | Field | Type | Possible use | Risk |
|---|---|---|---|---|
| `SavedRegion` | `Tags` | Array (untyped) | a marker per region | Element type unknown. Not known if the game reads it. |
| `SavedRegion` | `regionTags` | Array (untyped) | a marker per region | Probably game-used (region rules). Check. |
| `SavedRegion` | `forbidGlobalTradeGoodTypes`, `tradeRouteMerchantLocations` | Array | none | Game-owned. |
| `SavedLord` | `ActorTags` | Array (untyped) | a marker per pawn (lord) | Element type unknown. |
| `SavedLord` | `tagAdditionDay` | Map | a day per tag | Game uses it for tags. Check. |
| `SavedBuilding` | `buildingTags` | Array (untyped) | a marker per building | Element type unknown. Game uses buildings tags for rules. Check. |
| `SavedBuilding` | `CustomName` | Str | a name | Shown to the player. Not a good marker. |
| `SavedRegion` | `CustomName` | Str | a name | Shown to the player. Not a good marker. |
| `SavedLord` | `CustomName` | Str | a name | Shown to the player. |

No field is clearly free. The safest markers are the untyped Arrays, and only after a real-game test shows that the game keeps them.
Numeric markers would be better, but the jmap shows no free `Int` on the live pawn or region.

### 5c. Lua-writable live fields
- Data tables: a Lua write to `DT_Items` numbers works in memory (datatable-check.md). The check did NOT test whether a change survives a save and load.
  The note says so. Treat this as **not verified** for save persistence.
- Live properties on `Region`, `PawnCPP`, `SMBuildingMaster` (jmap-findings.md section 3). The jmap does not say which are copied into `MLSaveGame`.

## 6. What the real-game step must check

These are not known from static data:

1. **Hook fire test (A1):** For each candidate in sections 1 and 2, register a hook. Do one harness save (`save_game`, plan step 2) and one load. Record which hooks fired and what arguments they got.
   Also do one menu save and one menu load by hand, with the same hooks, to check that the menu path fires the same hooks (C++ calls may not fire).
2. **Native hook support:** Confirm that UE4SS hooks on the native `PawnCPP:requestSaveFile` and `IoHandler:SaveGameToSlot` fire (not only on a BP wrapper).
3. **Slot name in the hook (Q2):** Read `SlotName` in the pre-hook of `IoHandler:SaveGameToSlot`. Read `SaveGameSlot.Descriptor.saveSlot` in the `LoadGame` pre-hook. Confirm the values.
4. **Marker survival (A2):** Write a marker into one or two candidate fields (5b, untyped arrays first). Save with `save_game`. Load that slot in a new run. Read the field back. Also check a numeric marker in a region value that the game does not change.
5. **Two saves, two values (A3):** Two different harness slots, two different markers. Load each and check no mixing.
6. **Old save (A4):** Load an existing save made before any mod (for example `saveGame_0` fixture) with the marker mod loaded. The mod must start with default state and log no error.
7. **Game date as key:** Check that `day`, `Year`, `gameTicksAdjusted` change between two saves of the same game. Check whether two saves of one game share `gameTicksAdjusted`.
8. **Real folder guard:** Before each real save, hash the user's folder (CLAUDE.md). After the save, exactly one new `.sav` (and `_descr.sav`, `.png`, `_coat_*.png`) may appear. Restore from `SaveGames-backup` on any change.
9. **Load list:** Confirm whether a `harness_` slot is listed by the load screen. The notes say it is not (06 README line 37). If it is not listed, `LoadGame` must use the descriptor from `NamedSlots` or `IoHandler:LoadGameFromSlot`, or the harness must copy the slot to `saveGame_<N>` first (runlib install).
10. **Q5 (crash before save, older save):** Not answered by static data. Test with a run that ends without a save, then load an older save.

## 7. Summary of answers

- **Q1 (which functions fire on player save or load, can Lua hook them):** Candidates are in sections 1 and 2. The jmap shows all of them as reflected UFunctions. None is confirmed to fire during a play save or load. The most likely save hooks are `PawnCPP:requestSaveFile` and `IoHandler:SaveGameToSlot`. The most likely load hook is `mainMenu_widget_C:LoadGame`. The post-load event `W_HUD_LordPanel_V2_C:OnSaveLoaded_Event` did not fire in one probe.
- **Q2 (slot name or path in a hook):** Yes, from the arguments (section 3).
- **Q3 (fields to write):** No free field is proven. The candidates are untyped Arrays and tags (section 5). Persistence over a load is not verified.
- **Q4 (file names, game id):** Files are `<SlotName>.sav` in the real folder. A game clock exists (`day`, `Year`, `gameTicksAdjusted`). No unique id was found.
- **Q5:** Not answered statically.

## 8. Changes to the plan (for the spec README)

- Plan step 2 must check `DoesSaveGameExist(slot) == false` before `requestSaveFile`. The game does not pick a free name.
- Plan step 2 must handle that the real folder is always used. Cleanup (`DeleteGameInSlot`) is also a real-folder write. Keep the `SaveGames-overwritten-by-probe-20261010` folder.
- A `harness_` name may not show in the load list. Consider a `saveGame_<max+1>` name plus the runlib install (already built), or prove the list first (section 6, step 9).
- Option A (write into the save) needs one more check: a live field must map to a saved field. Choose markers only from `MLSaveGame` or the saved sub-structs (section 5).
