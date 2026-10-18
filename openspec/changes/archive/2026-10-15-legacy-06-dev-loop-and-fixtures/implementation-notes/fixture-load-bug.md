# Fixture load bug: runs started a new game (found 2026-10-11)

## What was seen
- Fixture `manor-bailey` (the user's `saveGame_28`, day 106, a manor house with a gate and a wooden bailey) was recorded.
  Three runs with `--fixture manor-bailey` reached READY, but the game showed March 2 (day 61) and only the start tents.
- Earlier runs with `base` had a different home region each time (`immenreuth`, `Wilde Wand`, `Hochweg`, `Rangbachau`,
  `Riesenbuckel`). One save loaded twice gives the same village, so these were new games on the Jagged Cliffs map.
- The spec 02 load test (`../../2026-10-15-legacy-02-save-autoload/implementation-notes/load-test-saveGame_0.md`) only checked that a game came up.
  Day 61 of year 1 is also the start of a new game, so it did not catch this.

## Evidence
1. The private copy was not used. In run `manor-fixture-check` the private `saveGame_0.sav` had the hash of the manor save
   (`2f3a...`), but the game showed a fresh start. The load list had 30 entries, the slots of the user's REAL folder.
   The game lists and loads saves only from the real folder (as it also saves there; CLAUDE.md, Safety).
2. Loading by name was not enough. Booting `saveGame_28` by name (run `manor-fixture-check4`): the boot log found the slot
   ("position 2, SlotIndex 30") and called `LoadGame`, and the game still started new. `MLGameInstance.savefileToLoad` read `""`.
3. The real UI path (run `load-spike-2`, the user loaded `saveGame_28` by hand with hooks attached):
   - the load screen calls `MLSaveLoadMenuScreen:SlotNameFromIndex` for the indices 0 to 30;
   - the UI calls `mainMenu_widget_C:LoadGame({SlotIndex = 30, Descriptor = MLSaveGameDescr})`, the same function as the boot;
   - `BP_MLGameInstance_C.savefileToLoad` changes from `""` to `saveGame_28`, and the map loads that save (day 106, manor present);
   - the field still holds `saveGame_28` after the load.
4. The boot passed the list element through `unwrap()` (a `:get()` call on a struct element). In spike S11 the same pattern crashed
   the game. Here it produced an entry without a usable descriptor, so `LoadGame` had no slot name and the game began a new game.

## Fix (built)
- `HarnessBoot` reads the list element directly and writes `savefileToLoad = <slot>` before `LoadGame`.
- After the load it compares `savefileToLoad` with the wanted slot and ends in FAILED when they differ ("it may have started a new game").
- Mock kit: mode `newgame` (LoadGame clears the field) must end in FAILED.
- Real game: run `manor-fixture-check5` booted `saveGame_28`: log `loaded slot confirmed: savefileToLoad = saveGame_28`, day 106,
  `manor_state` shows the region manor (type 98).

## The slot name lives in the descriptor
A copy of `saveGame_28` files named `saveGame_29` was listed as a second `saveGame_28`, and the boot could not find `saveGame_29`
(run `slot-copy-test-1`). `saveGame_28_descr.sav` holds two tagged `StrProperty` values: `saveName` (the name in the load list)
and `saveSlot` (the slot name). Layout of each: name, `StrProperty`, 4 zero bytes, an int32 size (4 + string length), one byte,
then the FString (int32 length with the null, the text, a null). The main `.sav` file does not hold the slot name.
So an install under a new name must rewrite `saveSlot` in the copied `_descr.sav` and fix the size field. The test copy was removed
(each file checked against its source hash first).

## What this means for earlier results
Every real run before this fix played a new game on the Jagged Cliffs map, not the user's `saveGame_0`. The scenarios did not
need a particular save, so their results stay valid as "a fresh start village". The `base` fixture text "copy of saveGame_0" was not true
for those runs.
