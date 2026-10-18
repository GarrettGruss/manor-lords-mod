# Persistence and hook tests (spec 24, plan steps 3 and 4)

Date: 2026-10-15. All saves came from `ctx.actions.save_game`. Kept slots were loaded with `run.py --save <slot>.sav` (the harness installs a copy as the next free slot).
All test slots (12 slots, 84 files) were deleted at the end. The real folder equals the manual backup (minus the stale `saveGame_47` copy, see `first-save.md`).
Base game for all tests: fixture `base` (Jagged_Cliffs, day 266). Region: Nusslohe. Live fields were read and written through the bridge (`get`, `set`) or the probe mod.

Tools (hidden or spike-only): scenarios `probe-save-first`, `probe-save-marker`, `probe-save-tags`, `probe-save-read`, `probe-save-fields`;
mod `HarnessSaveProbe` (observe-only hooks, plus the test commands `tag_add` and `tags_read`).

## Option A: values written into live fields

| Field (live property) | Saved field | Run (slot) | After save and load |
|---|---|---|---|
| `pawn.Tags` (TArray of FName) | `SavedLord.ActorTags` | tags (65) | **Kept.** `["mlmod_tag_A1"]` came back. |
| `region.Tags` (TArray of FName) | `SavedRegion.Tags` | tags (66) | **Kept.** The 4 game tags and `mlmod_tag_A1` came back. |
| `pawn.lordsName` (Str) | `SavedLord.CustomName` | marker (56, 62, 63) | **Kept.** `MLMOD_LA` and `MLMOD_LB` came back. The player sees the name. |
| `region.regionName` (Str) | `SavedRegion.CustomName` | marker (55, 59) | The value is saved, but the **load crashes** with a made-up name (access violation 0x530, in boot, after "loaded slot confirmed"). Do not write it. |
| `region.retinueName` (Str) | none | marker (60) | Lost (empty after load). Not saved. |
| `building.TownName` (Str) | unclear | marker (56) | Empty after load. The first `SMBuildingMaster` of the list may be another building after a load, so this is not proven. Not used. |
| `pawn.lastQuestDay`, `pawn.numTimesInDebt` (Int) | none | marker (57) | Lost (0 after load). Not saved. |

Control: a harness save without any marker (slot 53) loads normally. So `save_game` saves are valid, and the crash comes from the region name only.

### How the Tags were written (important)
- The bridge `set` of a `Tags` array (list of strings) **crashed the game** (`push_nameproperty`, run `20261016-034223-9e92`). Do not use it.
- A Lua write works: `object.Tags[#object.Tags + 1] = FName("mlmod_tag_A1")`. It grows the array. The read-back gives the new name. (Probe command `HarnessSaveProbe.tag_add`.)
- The bridge `props` read of `Tags` is safe.
- `allow_eval` is false in the game folder. It was not changed. The Tags write goes through a named command.

### A3: two saves, two values
Slots 62 (`lordsName = MLMOD_LA`) and 63 (`MLMOD_LB`) were made from the same game one after the other. Loading each gave its own value. No mixing.
The Tags slots 65 (pawn marker only) and 66 (pawn and region marker) also differ as expected.

### A4: a save made without the mod state
The fixture `base` (a save from before any marker) was loaded in every run with the probe mod present. `pawn.Tags` is empty and `region.Tags` has only the 4 game tags (`strength_SmallGame`, `strength_Salt`, `church_lv1_constructed`, `manor_constructed`).
A mod reads "no marker" and starts with default state. No error was logged.

### Open points for option A
- The Tags of other objects (building `Tags`, `Tags` of AI lords) were not tested. Pawn and region are enough.
- The `tagAdditionDay` map of the pawn (`SavedLord.tagAdditionDay`) was not checked. The game did not complain about a tag without a day.
- Size: not tested beyond one short name. An FName can hold up to 1023 characters, so a few kB need several tags. A limit test is still open.
- Only the harness save path (`requestSaveFile`) was tested. A menu save, quick save or autosave probably builds the same save object from the same live state, but this is not proven (see option B).
- A tag survives only while the game keeps the object. The pawn and the region persist for the whole game, so they are good owners.

## Option B: hooks (observe only, mod `HarnessSaveProbe`)
Evidence: `mod.log` of runs `20261016-034550-4a62` (save) and `20261016-035228-067e` (load).

| Function | Fired on `save_game` | Fired on a load | Arguments readable |
|---|---|---|---|
| `PawnCPP:requestSaveFile` (native) | **Yes**, once per save | no | Yes: `SlotName` = `saveGame_50`, `saveName` = `harness marker-a` |
| `IoHandler:SaveGameToSlot` | No (only for `rtsSettings`, the settings save at start) | no | Yes (slot `rtsSettings`) |
| `IoHandler:SaveDataToSlot`, `RequestMenuSave`, `OnGameSlotSaved`, `playSaveFinishedNotif`, `SaveToDiskWithThumbnail` | No | no | not applicable |
| `IoHandler:LoadGameFromSlot` | no | Only for `rtsSettings`, not for the save | Yes |
| `mainMenu_widget_C:LoadGame` (BP) | no | **Yes**, once | The struct `SaveGameSlot` is not readable with `ToString`. Use `MLGameInstance.savefileToLoad`. |
| `MLGameInstance.savefileToLoad` (read inside any hook) | | **Yes**: holds the slot name (`saveGame_52`) from before the map opens | Yes |
| `MyPawnCPP_BP3_C:ReceiveBeginPlay` | | **Yes**, once per load | `savefileToLoad` gives the slot |
| `W_HUD_LordPanel_V2_C:OnSaveLoaded_Event` | | **Yes** in all load runs, 4 to 6 s after `LoadGame` (an earlier probe did not see it in 25 s) | `savefileToLoad` gives the slot |

Answers:
- Q1 for the harness save: the native `requestSaveFile` pre-hook fires and shows the slot name and the display name. For a PLAYER save (menu, quick, autosave) this is NOT proven: the harness cannot press the menu. One manual check by the user is needed (menu save with the probe mod loaded, then read `mod.log`).
- Q2: yes for load (`savefileToLoad`) and for the harness save (hook arguments).
- The slot in the load hook is the slot name of the copy that the harness installed (`saveGame_52`), not of the kept slot. In real play it is the slot the player chose.
- Option B works on load. On save it works only if the menu path also reaches `requestSaveFile`. Its key is the slot name. A slot name changes when the player copies, renames or deletes a save, or restores one from the cloud. A side file can then get lost or mixed.

## Q4 and Q5
- Q4: the game clock is in the save (`day`, `month`, `year` from the calendar: 266, 9, 1 in every test slot). Two saves of the same game state have the same date, so a date is not a unique key. No game id was found. A mod-made id kept in the pawn Tags (option A) is the key.
- Q5: a crash before a save leaves the last save as it was (the guard restores or fails on damage; no partial slot was seen). A load of an older save of the same game gives the older tags. The state moves with the save, as wanted. Not tested with a real crash during a save.

## Safety facts found
- Writing `region.regionName` with a made-up name and saving makes that save crash on load. It was a harness slot, so no user save was touched.
- Writing a `Tags` array through the bridge crashes the game at once. Use a Lua FName write.
- `save_game(keep=True)` does not register the slot in the ledger. The person who kept a slot must delete it.
