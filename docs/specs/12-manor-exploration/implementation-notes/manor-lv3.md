# Hidden Lv3 manor modules (issue #90)

Date: 2026-10-14. Game 0.8.111. Fixture `manor-bailey`. 6 game launches (runs `s90-1` to `s90-6`), probe `probe-manor-module`.
No save function was called. The AES key came only from the environment. Screenshots are in git-ignored `runs/<id>/screenshots/`.

## Short answer
- The planner does NOT draw a re-enabled original card. It draws a card only in a slot that was already drawn. A card slot with a new ID shows the module.
- With the slot pak, the Lv3 keep (row 83) is selectable in the planner and a big Lv3-looking building ghost follows the mouse and can be placed.
- Commit failed. The module was not built. A Lv3 module was NOT built in a real game. The issue stays open.

## Step 1: un-collapse cards 81 and 83 (pak `mmlv3ui`, runs s90-1)
- Visibility of both cards became 4 (shown), but the planner never drew them. Collapsing cards 57 and 58 left only the 2 cards 50 and 472. Same result as card 123 in #65.
- So card Visibility does not decide what is drawn. The planner puts only some cards into the list by code (guess: by slot or by name).

## Step 2: reuse a drawn slot (pak `mmlv3slot`, runs s90-2 to s90-4)
- The pak sets the ID of the two drawn slots `buildingWidget_9` (was 472) to 83 and `buildingWidget_8` (was 50) to 81. The pak is `mod/HarnessActions/paks/mmlv3slot_P.pak`.
- Result: both slots draw (still with the Lv1 card art; the keep card has a crown icon, the palace card an empty icon). `runs/s90-2/screenshots/planner_card123_stage0.png`.
- A click on the keep card starts the placement bar (Place, Rotate, Cancel). The ghost appears after the first click in the world: a large timber and stone tower with a tile roof, orange outline. Screenshots `runs/s90-4/screenshots/lv3_placed.png` and `lv3_after_move.png` (the building stays when the mouse moves away).
- The ghost was not white as the notes of spec 18 say for a valid ghost. It was shown with its own materials and an orange outline. Valid or not was not decided.

## Step 3: commit (runs s90-3 to s90-6)
- The planner Commit button stayed grey. A click on it removed the module (runs s90-3, s90-4). The manor stayed built (`manor_state`).
- `manor_blueprint_add` type 83 with the mesh `/Game/NotStronghold/Buildings/Merged/SM_MERGED_C_SG_Tower_Lv3` is refused: `mesh not found` (run s90-5). The path exists in the pak. Neither StaticFindObject nor LoadAsset finds it, also after the planner showed the ghost.
- Run s90-6: the new option `commit` of `manor_planner` called `convertBlueprintsToBuildings` after the placement. `blueprints` was 3 before and 3 after: the planner-placed module is not in the manor `blueprints` array (the 3 are old plans of the fixture). The commit made the manor a construction site ("no built manor module"), and the game then CRASHED (EXCEPTION_ACCESS_VIOLATION reading 0x10, crash folder `runs/s90-6/crash/`). A crash is a result. Cause not analysed.
- Not seen: the native refusal for `requiredTech` or settlement level. The ghost could be placed, so no such check ran at that step.

## Not done
- A finished Lv3 module, the garrison limit before and after, the Lv3 palace ghost.
- Launches ran out. Next ideas: (1) make the Lv3 mesh loaded by a data pak (retarget a row that is loaded to the Tower_Lv3 mesh), then `manor_blueprint_add` type 83; (2) find which call the planner Commit button makes and why it is grey (bailey area is 0 m2 in this fixture, a manor with a wall may enable it); (3) use a fixture without the 3 old plans.

## Changes in the game folder
- `Paks\~mods\mmlv3ui_P.pak` and `mmlv3slot_P.pak` were installed by `run.py` and removed after each run; `~mods` is gone. The game is closed.
- Mod `HarnessWalls` command `manor_planner` has a new option `commit`. Pak work folders `mmlv3ui`, `mmlv3slot` in the git-ignored `modtools/work`.
