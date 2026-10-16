# Manual menu-save check (2026-10-16)

Question: does a PLAYER save from the game menu keep the Tags marker (option A)?

Method (run `s128-menu-save`, `noop --keep-open`, fixture `base`, HarnessSaveProbe deployed):
1. `HarnessSaveProbe.tag_add` wrote `mlmod_menu_save_1` on the pawn (0 to 1 tags) and the region (4 to 5 tags).
2. The user saved from the Esc menu as a new save `tagtest` (slot `saveGame_33`).
3. The user loaded `tagtest` from the menu.
4. `HarnessSaveProbe.tags_read` read both arrays.

Probe log (mod.log), in order:
- `PawnCPP:requestSaveFile` args `[saveGame_33 | tagtest]`, then `SaveToDiskWithThumbnail` (same args), then `MLSaveLoadMenuScreen:OnGameSlotSaved`.
- `mainMenu_widget:LoadGame`, `ReceiveBeginPlay`, `OnSaveLoaded_Event`, all with `savefileToLoad=saveGame_33`. So a real load ran.

Result: both tags came back (pawn `["mlmod_menu_save_1"]`, region the 4 game tags plus `mlmod_menu_save_1`). **Option A holds for player menu saves.**
Bonus: a menu save fires `requestSaveFile` with slot and name, so a post-hook can see player saves (option B).

Cleanup: the user asked to delete `tagtest`; all 8 `saveGame_33*` files were deleted. HarnessSaveProbe was removed from the game Mods folder and `mods.txt`.
Not tested: quick save and autosave (expected the same path).
