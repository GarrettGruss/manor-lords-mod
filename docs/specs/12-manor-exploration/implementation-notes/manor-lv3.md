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

## Not done (round 1)
- A finished Lv3 module, the garrison limit before and after, the Lv3 palace ghost.
- Launches ran out. Next ideas: (1) make the Lv3 mesh loaded by a data pak (retarget a row that is loaded to the Tower_Lv3 mesh), then `manor_blueprint_add` type 83; (2) find which call the planner Commit button makes and why it is grey (bailey area is 0 m2 in this fixture, a manor with a wall may enable it); (3) use a fixture without the 3 old plans.

## Changes in the game folder
- `Paks\~mods\mmlv3ui_P.pak` and `mmlv3slot_P.pak` were installed by `run.py` and removed after each run; `~mods` is gone. The game is closed.
- Mod `HarnessWalls` command `manor_planner` has a new option `commit`. Pak work folders `mmlv3ui`, `mmlv3slot` in the git-ignored `modtools/work`.

## Round 2 (runs s90b-1 to s90b-5, 2026-10-14)
5 launches. Pak `mmlv3slot`, fixture `manor-bailey`. No save function was called.
- Hover does not move the ghost. The model follows a real click only. The old "orange outline" is the selection outline of a placed module, not an invalid mark. The red tower at the gate is the fixture gatehouse.
- A click on the Lv3 keep card (0.83, 0.449), then a real click in the bailey places a large Lv3 building at the click spot (s90b-2, s90b-3 `lv3_placed.png`, spot 0.40,0.62). The bottom bar still shows Place / Rotate / Cancel: it is the static planner help and does not mean ghost mode.
- Before this, a banner "A New Message" stood in the screen centre. The probe now clicks it away first (`HARNESS_DISMISS=1`). Options: `HARNESS_PLACE=fx,fy`, `HARNESS_CARD_X`, `HARNESS_CLICKCOMMIT=1`, `HARNESS_GRID=1`.
- The Commit button stays grey after placement. Reasons seen: `SMBuildingMaster:canConstructCastle` returns false (the reason list is not readable through the bridge); the planner shows "Bailey Area None (0m2)" and the raw key `castle_level`, although `getBuildingArea` returns 19407492 (about 1940 m2). `walls` is empty. `blueprintGhosts` has the 3 old plans plus ghosts.
- A real click on Commit (palace card 81, run s90b-5) removed the module again. No refusal text was shown (no requiredTech or settlement level message).
- Without the pak the click at the card position hit road mode, so no vanilla control was made.
- Not done: committed and built module, garrison limit, the Lv3 palace placed and committed. Likely blocker: the 3 wooden wall segments do not form a closed, valid bailey. Next: build a fixture with a closed wall ring (or draw the ring in the planner with real clicks) and read `canConstructCastle` again.
- Game folder: `~mods\mmlv3slot_P.pak` was installed and removed by run.py each run. The game is closed.

## Round 3: fixture manor-closed (runs s90c-1 to s90c-6, 2026-10-14)
6 launches. Pak `mmlv3slot`, fixture `manor-closed` (user save, closed palisade ring). No save function was called. Screenshots are in git-ignored `runs/<id>/screenshots/` of the agent worktree.
- The earlier blocker is gone: `canConstructCastle` is TRUE and `getBuildingArea` is 11843194 (1,184 m2) on this fixture (s90c-1).
- Root cause of the grey Commit and of the raw texts: the harness command `manor_planner` opened the planner with `PawnCPP:setPlannerMode(manor)`. That leaves "Bailey Area None (0m2)", `castle_level` and `constr_cost` unset and Commit grey (s90c-2). The real manor button ("Open the Castle Planner" in the manor panel) calls `PawnCPP:openCastlePlannerUI(manor)`. The command has a new option `ui` that calls it.
- With `openCastlePlannerUI` (s90c-4, `lv3_placed.png`): "Castle Level: Large", "Bailey Area Large (1,184m2)", Commit ACTIVE after the Lv3 keep (card 83) was placed by real clicks (card click, then a click on empty ground in the bailey; the banner click needs the game window in the foreground, it failed once in s90c-1).
- The planner showed "Construction Cost: No Construction Cost" for the keep. No requiredTech or settlement level refusal text appeared.
- A real Commit click (s90c-4 `lv3_commit_click.png`) closed the planner and the manor became "Manor (under construction)" with a dashed outline. In s90c-4 the game then CRASHED (EXCEPTION_ACCESS_VIOLATION reading 0x10, same as s90-6) in the follow-up reads (`master_parts` or `mesh_users` on the manor under construction). Commit by command (`manor_planner commit`) crashed too (s90c-3).
- s90c-5 and s90c-6 (no part or mesh reads): no crash. s90c-6 gave materials (rubble 60 and food, timber 40 into the manor store) and ran 54+ game days. The manor read "Manor" again (finished, `day50.png`), but NO Lv3 keep is visible and `getModularGarrisonLimit` stayed 12 before and after. `getModuleTypes` stayed empty. So the commit rebuilt the manor and did not build the Lv3 keep.
- Likely reason (not proven): the pak only gives the slot ID 83. The module has no mesh or blueprint entry, and `manor_blueprint_add` type 83 earlier said "mesh not found". The Lv3 keep needs its data (mesh, tech) to be loaded.
- `canConstructCastle` reason text: not read. The function takes an out array. The bridge cannot read an out array.
- Result: #90 stays open. Placed and committed by real clicks; not built; garrison 12 -> 12. The Lv3 palace (81) and card 123 (#65) were not tried: launches ran out.
- Game folder: `~mods\mmlv3slot_P.pak` was installed and removed by run.py each run. The game is closed.

## Round 4 (runs s90d-1, s90d-2, 2026-10-14, fixture manor-closed, 2 launches)
No Lv3 module was built. The garrison limit stayed 12. No save function was called. Screenshots are in git-ignored `runs/<id>/screenshots/` of the agent worktree.

### Static comparison (script `harness/tools/s90_row_goods.py`)
| Field | 83 keep Lv3 | 81 palace Lv3 | 57 keep Lv1 (works) | 472 tower Lv1 (works) |
|---|---|---|---|---|
| `constructionGoods` | timber 10 only | timber 10 only | timber 10, planks 15, rubble 10 | timber 4, rubble 8 |
| `constructionMeshAsset` | `SM_MERGED_C_SG_Tower_Lv3` (set) | `SM_MERGED_C_SG_Manor_Lv3_Palace` (set) | set | set |
| `requiredTech` | ID 123, tier 123 | empty | empty | empty |
| `maxInRegion` | 1 | 1 | 1 | 0 |
| `moduleCategory`, `buildingFunction`, `BlueprintPath` | Manor, Default, set | same | same | same |
| row in `DT_BuildingMeshPathData` | none | none | yes | yes |
| row in `DT_ConstructionBPs` | none | none | none | yes (`C_SG_Manor_Tower_Lv1_00`) |
Other differences: bounds, garrisonLimit (83: 36, 81: 24, 57: 12), storage limits, panel images (83 has none). So the Lv3 rows are partly filled: row 83 has some cost and a construction mesh, and a strange `requiredTech` 123.

### Data pak `mmlv3full` (in `mod/HarnessActions/paks/`)
Row 83: goods copied from row 57 x1.6 (timber 16, planks 24, rubble 16), `requiredTech` cleared, mesh path row 83 added, plus the card slot change of `mmlv3slot`. New `s65_edit_json.py` commands `copyfield` and `meshrow`.

### Result (run s90d-1)
- The planner still shows "Construction Cost: No Construction Cost" after the keep is placed (`lv3_placed.png`). So the planner cost does not come from the `buildingStats` goods of the row, or it reads the cost of the placed ghost, which has none.
- Real Commit click: the manor became "Manor (under construction)" (`lv3_commit_click.png`). With timber, rubble, fish and berries given, 60 game days (speed 3) passed. Manor back to "Manor" (`end.png`), manor goods unchanged (timber 40), `getModuleTypes` empty, garrison 12 -> 12. No keep built.
- Conclusion: data in the row (goods, tech, mesh path) is not enough. The module needs something else: probably the module Blueprint `BM_SG_Manor_Tower_Lv3` (parts and cost per part) or a code path for Lv3 that is not finished in 0.8.111.

### Card 123 on a drawn slot (run s90d-2, issue #65)
Pak `mm123slot`: row 123 cloned from 472 plus widget `buildingWidget_9` ID 123. The planner still placed the big Lv3 keep ghost, "No Construction Cost" again, commit and 60 days built nothing (garrison 12 -> 12). The test is NOT clean: the pak used the git-ignored `castlePlanner.json` of the earlier slot pak, so the widget edit may not have reached the card that was clicked. Card 123 is not proven.

### Next
- Read the Blueprint `BM_SG_Manor_Tower_Lv3` JSON (parts, cost) and compare it with `BM_SG_Manor_Lv1_Keep`.
- Repeat the 123 test from a clean `castlePlanner` extract.

### Game folder
`~mods\mmlv3full_P.pak` and `mm123slot_P.pak` were installed and removed by `run.py`. `~mods` is gone. The game is closed.
