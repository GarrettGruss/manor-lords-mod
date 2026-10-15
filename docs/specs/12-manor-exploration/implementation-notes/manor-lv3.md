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


## Round 5 (static, 2026-10-14, issue #90)
No game launch. Files were read with the repo pak tools and the jmap. The AES key came only from the environment. New read-only scripts in `harness/tools/`: `s90_bm_compare.py` (components of a Blueprint), `s90_cbp_compare.py` (construction Blueprint summary), `s90_bytecode_trace.py` (Kismet bytecode of one function), `s90_jmap_find.py` (jmap search), `s90_row_diff.py` (field diff of `buildingStats` rows).

### Short answer
- The module assets of the Lv3 keep are NOT broken. They have the same shape as the working Lv1 modules. No missing `res_` slot or part was found.
- The planner cost text comes from native code (`SMBuildingMaster:getCastleReconstructionCost`). The widget has no other source. The rules of that function are not visible in any asset or in the jmap.
- So the cause is in native code, or in a rule keyed on the type id. A data pak can still help: see "Next round".

### 1. Module Blueprints (`CPP_BP/BuildingMasterAssemble/ManorModules/`)
| Blueprint | components | building part key |
|---|---|---|
| `BM_SG_Manor_Lv1_Keep` (row 57, works) | DefaultSceneRoot, `MainBld_167`, 2 `Dirt`, 3 `Clutter`, 7 `clutter_stones` | 167 |
| `BM_SG_Manor_Lv1_Tower_` (row 472, works) | DefaultSceneRoot, `MainBld_472`, 2 `Dirt`, 4 `Clutter`, `Scene` | 472 |
| `BM_SG_Manor_Lv1_Gatehouse` (row 95, works) | DefaultSceneRoot, `MainBld_95`, `Dirt`, 4 `Clutter`, `Scene` | 95 |
| `BM_SG_Manor_Lv2_Keep` (row 475, no card) | DefaultSceneRoot, `MainBld_498`, 9 `bld_499_*`, 2 `Dirt`, clutter | 498, 499 |
| `BM_SG_Manor_Tower_Lv3` (row 83) | DefaultSceneRoot, `MainBld_421`, `dirt_3_2` | 421 |
| `BM_SG_Manor_Lv3_Palace` (row 81) | DefaultSceneRoot, `MainBld_419` | 419 |
| `BM_SG_Manor_Lv3_Gatehouse` (row 82) | DefaultSceneRoot, `MainBld_420`, 2 `dirt` | 420 |

- The working Lv1 keep, tower and gatehouse have NO `res_`, `gathering`, `workpos` or `Bld_` component either. Only the Lv1 palace (row 98) has `res_*`, `gathering`, `NobleGathering` and `bld_*`. So a missing `res_` slot does not explain the missing cost: the Lv1 keep works without one.
- The Lv3 Blueprints are plain mesh actors: one `MainBld_<key>` mesh and a dirt plane. They have no function and no bytecode. The Lv3 ones only lack the clutter (art).
- `DT_ConstructionBPs` has the keys 419, 420 and 421. They point to `C_SG_Manor_LV3_Palace`, `C_SG_Gatehouse_LV3` and `C_SG_Tower_Lv3`, in the same layout as key 472 (`constructionAsset` soft path, empty `buildingPartName`). The keys are free numbers: no `buildingStats` row 167, 419, 420 or 421 exists. The working keep uses key 167 for row 57 in the same way.

### 2. Construction Blueprints (`CPP_BP/ConstructionBlueprints/`)
| Asset | static mesh components | tags | note |
|---|---|---|---|
| `C_SG_Manor_Tower_Lv1_00` (472, works) | 174 | `foundation` on 1, `final` on 1 | cooked instancing data present |
| `C_SG_Manor_MainTower_Lv1_New` (167, works) | 815 | `final` on 1 | |
| `C_SG_Tower_Lv3` (421) | 192 | none | a component `C_SG_Tower_lv4_DefaultSceneRoot` is left from a copy |
| `C_SG_Manor_LV3_Palace` (419) | 410 | none | |
| `C_SG_Gatehouse_LV3` (420) | 75 | none | |

- All are the same kind of asset: only `StaticMeshComponent`s, no function, no variable except `defaultRootComponent` and `stoneStructure`. The Lv1 assets have one or two tagged parts, the Lv3 ones none. The Lv1 keep has only the tag `final`, so a missing tag is not a proven cause. It was not tested.
- None of them carries a cost, a stage list or a `res_` slot. The cost does not live in these assets.

### 3. Data tables
- `buildingStats` row 83 against row 57 (full field diff, vanilla) differs only in `DisplayName`, `purposeIcon`, `garrisonLimit` (36 and 12), `constructionMeshAsset`, `BlueprintPath`, `constructionGoods` (timber 10 only, and 3 goods) and `requiredTech` (ID and tier 123, and empty). Bounds, `maxInRegion`, `moduleCategory`, `snapPoints`, `needsRoad`, `maxHp` and storage are the same.
- The pak `mmlv3full` was unpacked and read back. Row 83 has goods 16, 24, 16 of the types 16, 17, 15 and no `requiredTech`. So the pak edit is right in the file. The planner still showed no cost. Either the planner cost does not depend on the row goods, or the ghost is not read as row 83.
- Placeholder signs: the Lv3 rows 81, 82 and 83 have one or two goods only, row 83 has `requiredTech` 123, and no panel image. The Lv2 rows (474, 475, 478, 479) have richer goods (types 283 and 329, probably stone items). `DT_BuildingMeshPathData` has stale entries (row 475 points to a brewery oven mesh). The Lv3 art is complete, but the rules look unfinished.
- The executable has the names Manor_Keep_Lv3, Manor_Palace_Lv3 and Manor_Gatehouse_Lv3 (enum `EBuildingType`). The game knows the Lv3 type names.

### 4. Where the planner reads the cost (jmap and bytecode of `castlePlanner`)
- `castlePlanner_C:updateConstructionCost` does this: `constrCost = building.getCastleReconstructionCost(false)` (`building` is the manor master). For every `Good` in the array it reads `building.constructionGoods` and `region.getStockOfGood`, and it builds the text `{a} <img id="ItemID_..."/>{amt} ({has})`. If the array is empty it shows the text key `no_construction_cost`. That is the text we saw.
- So "No Construction Cost" means: the native function returned an EMPTY array. The widget has no other source and no filter.
- `updateCanConstruct` calls `canConstructCastle(outReasons)` and `formatReasonWhyCantConstruct`. The Commit button is `btn_commit`.
- Native signatures (jmap): `getCastleReconstructionCost(bOnlyBuildFirstBuilding) -> Good[]`, `canAffordCastleReconstruction() -> bool`, `doesCastleModuleNeedReconstruction(Actor, newModuleBuildingId:int, wallType) -> bool`, `getModuleTypes()`, `hasModuleOfType(int)`, `getModularGarrisonLimit()`. A saved module is `SavedCastleModule{bType, wallType, Transform, meshOverride, CustomPrimitiveData, ActorTags}`. The function bodies are native (`script` is empty).
- For a later disassembly: `getCastleReconstructionCost` is at RVA 0x4ACD960 and `canConstructCastle` at RVA 0x4ACBFE0 (function pointer of the jmap minus image base 0x7ff6db0a0000).
- A card click (`buildingCardWidget`) calls `PawnCPP:setPlacedBuilding(id)` and `setBuildingMesh(getBuildingMeshForID)`. The second reads `DT_BuildingMeshPathData` row `id`. The card also reads the `buildingStats` row (`minSettlementLevel`, `requiredTechs`, category). The cards are the same widget class as the normal build menu. So the ghost for ID 83 is made by the same path as ID 57.

### 5. Conclusion
- A proven missing data or asset: none. The module Blueprint, the construction Blueprint, the `DT_ConstructionBPs` keys and the `buildingStats` row are complete and have the same shape as the working Lv1 pieces. Row goods and `requiredTech` were tried in round 4.
- So the block is in native code: `getCastleReconstructionCost` (and the commit path `convertBlueprintsToBuildings`) gives nothing for type 83. Likely reasons, none proven: (a) a switch on the type id that handles 57, 58, 95, 98, 472 and others but not 81 to 83; (b) the ghost is not counted in the `blueprints` array (round 1 saw 3 before and after); (c) a level or tech check inside the native function.
- A pak cannot change native code. A UE-made BM (spec 18) does not help: the Lv3 BM exists and the data is not the problem.
- The type id is the lever. If the native code keys on the type id, a data pak can give a WORKING type id the Lv3 look: retarget row 57 (keep, garrison 12) to `BM_SG_Manor_Tower_Lv3` and mesh `SM_MERGED_C_SG_Tower_Lv3`, set `garrisonLimit` 36, and set the mesh path row 57. This needs no new card (the planner has card 57) and no native change. It is the most promising route to a built Lv3 keep. Not tested.

### Next round (needs the game)
1. Control without a pak. Open the planner on `manor-closed` with `openCastlePlannerUI`. Place the vanilla outer tower (card 472) by real clicks and read the cost text. Then call `getCastleReconstructionCost(false)` on the manor through the bridge (the result is a `Good` array without soft objects) and `doesCastleModuleNeedReconstruction(nil, id, 0)` for id 472, 57, 83 and 81. If 83 and 81 give false and 57 and 472 give true, a native switch on the type id is confirmed.
2. A/B with data paks (`s65_edit_json.py` has `copyfield` and `meshrow`):
   - Pak A: row 57 gets the `BlueprintPath` of `BM_SG_Manor_Tower_Lv3`, `constructionMeshAsset` Tower_Lv3, `garrisonLimit` 36 and the mesh path row 57 to the Lv3 mesh. Place card 57, commit, run 60 game days, read `getModularGarrisonLimit` and `getModuleTypes`. A built Lv3 tower with garrison 36 closes #90 for the keep.
   - Pak B (control for the type id): row 83 gets the paths of the Lv1 keep. If the cost is still empty, type 83 itself is blocked in code, and pak A is the only route.
3. Lv3 palace: retarget row 98 (palace Lv1) to `BM_SG_Manor_Lv3_Palace`. The Lv1 palace BM has `res_` and `gathering` parts and the Lv3 palace BM has none, so storage and servants may not work. Test the keep first.
4. If pak A fails too: disassemble `getCastleReconstructionCost` (RVA 0x4ACD960) in the shipping executable to read the rule. Treat any downloaded tool as untrusted.

## Round 6 (runs s90e-1 to s90e-5, 2026-10-14, fixture manor-closed, 5 launches)
No Lv3 module was built. Garrison stayed 12. No save function was called. Screenshots are in git-ignored `runs/<id>/screenshots/` of the agent worktree (`.claude/worktrees/agent-ade33fb887f1d1a89/runs/`).

### Result in one line
The control failed too: a vanilla outer tower (card 472) placed and committed by real clicks is also NOT built in 60 game days. So the missing Lv3 keep is not caused by the Lv3 data. The commit flow of the harness builds no module at all.

### 1. Control (runs s90e-1 to s90e-3, no pak)
- The native `getCastleReconstructionCost(false)` returns an empty array before and after placing the vanilla tower (472) and keep (57). The planner shows "No Construction Cost" for vanilla modules too (`s90e-3/screenshots/control_57_placed.png`). So an empty cost is NOT a sign of a blocked Lv3 type. Round 4 and 5 read it wrongly.
- `canAffordCastleReconstruction` is true.
- `doesCastleModuleNeedReconstruction(Actor, id, wallType)` cannot be called through the bridge: a nil Actor argument is dropped ("UFunction expected 3 parameters, received 2"). A named mod command would be needed. Not done.
- `PawnCPP:setPlacedBuilding(id)` by the bridge gives only a flat white grid, not a module ghost. Real card clicks are needed.
- Card layout of the vanilla planner (fractions of the window, y 0.449): 0.785 keep (57), 0.83 gatehouse (95), 0.875 outer tower (472), 0.92 hall (58). The probe collapsed 57 and 58 by default (`HIDE_STAGES`); the new option `HARNESS_NOHIDE=1` keeps them. Run s90e-2 clicked collapsed slots and hit the wrong cards.

### 2. Pak A (run s90e-4)
- Pak `s90pakA` (`mod/HarnessActions/paks/s90pakA_P.pak`), built from a clean extract of `buildingStats` and `DT_BuildingMeshPathData`: row 57 got `BlueprintPath` (`BM_SG_Manor_Tower_Lv3`), `constructionMeshAsset` and `garrisonLimit` 36 copied from row 83, and the mesh path row 57 now points to `SM_MERGED_C_SG_Tower_Lv3`. New `s65_edit_json.py meshpath`.
- Card 57 placed by a real click: only a faint pillar ghost appeared (`s90e-4/screenshots/lv3_placed.png`), not a tower. `canConstructCastle` true, cost empty. Commit click worked (`lv3_commit_click.png`). 60 game days (`day50.png`): no keep, garrison 12 -> 12, `getModuleTypes` empty.

### 3. Control commit (run s90e-5, no pak)
- Vanilla outer tower (472) placed by real clicks: a large tower with an orange outline (`s90e-5/screenshots/lv3_placed.png`). Same steps as pak A: Commit click, timber, rubble, fish and berries given, 60 days at top speed.
- Result: the manor was rebuilt, no tower exists (`end.png`, `day60.png`), garrison 12 -> 12, `getModuleTypes` empty. So the vanilla module is dropped as well.

### Conclusions
- The block is in the commit/build flow, for every module type, not in a Lv3 rule. Round 5's native-switch-on-type theory is not supported: a vanilla type behaves the same.
- Open for the next round (fixture manor-closed): (a) read `blueprints` and `blueprintGhosts` after the Commit click to see if the ghost became a blueprint (many `GhostStaticMeshActor` objects exist after placing, `blueprints` stayed old); (b) find what a real player needs: builders on the manor site, and a cost that is not empty. An empty cost with a placed vanilla tower suggests the placement is not registered as a module; try a second click or the planner Place button; (c) pak B (row 83 with Lv1 paths) and the palace via row 98 were NOT run: they mean nothing until a vanilla module can be built.
- Launch 6 was not used.

### Changes
- `probe-manor-module`: mode `control`, options `HARNESS_NOHIDE`, `HARNESS_CARD_Y`; function `read_costs`. `s65_edit_json.py`: command `meshpath`.
- Game folder: `~mods\s90pakA_P.pak` was installed and removed by `run.py` (`pakmod.py list`: none installed). The game is closed. Work folder `modtools/work/s90pakA` (git-ignored).

## Round 7 (static): mesh and garrison source
Date: 2026-10-15. No game launch. Sources: `getBuildingMeshForID` bytecode, `DT_ConstructionBPs`, `DT_BuildingMeshPathData`, pak A JSON, run `live-lv3a`.

### What is proven
- Pak A was installed in live test 2 (`runs/live-lv3a/config.json` lists `s90pakA`). Its JSON is right: row 57 has the Lv3 `BlueprintPath`, `constructionMeshAsset` Tower_Lv3 and `garrisonLimit` 36. The mesh path row 57 is Tower_Lv3 too.
- `MyPawnCPP_BP3:getBuildingMeshForID(id)` (also `buildingCardWidget`, `RTSWidgetFunctions:commonGetBuildingMeshByID`) reads `buildingStats` row `<id>`, field `constructionMeshAsset`. A card click calls it, then `setBuildingMesh`. So the card ghost SHOULD show Tower_Lv3 after pak A. It showed the Lv1 keep.
- `RTSMultiEngineCPP_BP:getConstructionBP(key)` reads `DT_ConstructionBPs` row `<key>`, field `constructionAsset`. The key is NOT the type id. It is the number in the module part name `MainBld_<key>` of the BM Blueprint: Lv1 keep `MainBld_167` -> `C_SG_Manor_MainTower_Lv1_New`; Lv3 tower `MainBld_421` -> `C_SG_Tower_Lv3`. `DT_BuildingMeshPathData` has no rows 167, 419, 420, 421, 81, 83.
- `getModularGarrisonLimit` is native. Facts: 12 with no keep, 24 with one keep, 24 with two keeps (spec 14), 24 after pak A. It is not the sum of `garrisonLimit` fields.

### Most likely source of each value (not proven)
1. Planner ghost mesh: `buildingStats.constructionMeshAsset` by card ID (proven path above). That pak A did not change it means the retargeted row was not the row read. Open: the planner may read the mesh from a type switch in native code, or a cached row. A cheap check: bridge `building_stat type=57` in a pak A run. If it shows garrison 36, the table is loaded and the ghost source is native. If it shows 12, the pak did not take for row 57.
2. Finished module mesh: `DT_ConstructionBPs` row from the BM `MainBld_<key>` (167 for the keep), not the row 57 `BlueprintPath`. Pak A changed the BM class but the built module stayed Lv1, so the module is likely rebuilt from the saved module data (`SavedCastleModule`: bType, mesh override, tags), where the mesh is the blueprint actor mesh taken from the ghost.
3. Garrison: native. 12 per manor plus 12 once a keep exists; not read from row 57 `garrisonLimit`.

### Next pak (pak B), cheapest first
1. In the same game run, read `building_stat type=57` (confirms the row is loaded).
2. Pak B, `DT_ConstructionBPs`: set row 167 `constructionAsset` to the value of row 421 (`C_SG_Tower_Lv3_C`). Keep pak A rows. This changes the finished Lv1 keep at its real source key. Tool: copy a field with `s65_edit_json.py` (add a `copyfield`-style edit if missing).
3. Ghost: if the ghost is still Lv1, put the module through the mod command `manor_blueprint_add` with a loaded mesh, or set `meshOverride` through a saved module. The Lv3 mesh must be loaded first (`mesh not found` in round 1: load it with a pak asset reference or `LoadAsset` after a load order trick).
4. Garrison 36: a Lua post-hook on `SMBuildingMaster:getModularGarrisonLimit` that adds 24 when the Lv3 module exists. Native code cannot be changed by a pak.

### Card 123 (#65)
- Card slot `buildingWidget_5` (ID 123) is not drawn (round "spike" of #65). Slots that are drawn take a new ID (pak `mmlv3slot` used `_9` and `_8`). So: set ID 123 on `buildingWidget_9` (drawn slot of 472) and keep 472 on a second slot, or retarget the second 57 card `_6`.
- Row 123 is cloned from 472, so its key chain is `MainBld_472` -> `DT_ConstructionBPs` 472 (Lv1 outer tower). Give row 123 its own `constructionMeshAsset`, a `DT_BuildingMeshPathData` row 123 (none exists) and, for a different finished look, a BM with a new `MainBld_<key>` and a `DT_ConstructionBPs` row for that key.
- Same open question as for card 57: confirm with `building_stat type=123` that the ghost mesh follows `constructionMeshAsset`.

## Round 8 (runs s90f-1 to s90f-6, 2026-10-15, fixture manor-closed, 6 launches)
No Lv3 module was built. The harness mouse did not reach the game in these runs, so the working flow (card, place, check `blueprints`, Commit) could not be run. No save function was called. Screenshots are git-ignored: `runs/s90f-N/screenshots/` of the agent worktree `.claude/worktrees/agent-ab05b49097fc30160/`.

### Finding 1: pak A of rounds 6 and 7 never loaded (path bug)
- `s90pakA_P.pak` held its files at the pak ROOT (`buildingStats.uasset`, no `ManorLords/Content/NotStronghold/Data/` prefix). The JSON had been put in `modtools/work/s90json`, not under `modtools/work/json/ManorLords/...`, so `pakmod.py fromjson --to` used the file name only. The game ignored the pak. This explains live test 2 (the keep stayed Lv1, garrison 24) and run s90e-4.
- Fix: edit the JSON in `modtools/work/json/ManorLords/Content/NotStronghold/Data/` (made by `pakmod.py tojson` from a fresh `extract`). Check with `repak list`: every path must start with `ManorLords/Content/`.
- Rebuilt: `s90pakA_P.pak` (row 57: BlueprintPath, constructionMeshAsset, garrisonLimit 36 copied from row 83; mesh path row 57 = Tower_Lv3) and new `s90pakB_P.pak` (the same rows plus `DT_ConstructionBPs` row 167 `constructionAsset` copied from row 421 = `C_SG_Tower_Lv3_C`). Both are in `mod/HarnessActions/paks/`, both from a clean extract, no key in the bytes.
- Task 1 result (run s90f-5): with the fixed pak A, `building_stat kind=57` reads `garrisonLimit` 36 and `maxInRegion` 1. So the row IS loaded now.

### Finding 2: garrison hook works
- New module `HarnessGarrison` (`mod/shared/HarnessGarrison/HarnessGarrison.lua`), installed by HarnessActions only when the game environment has `HARNESS_GARRISON_BONUS` (opt-in; `HARNESS_GARRISON_MODULE_TYPE` chooses the built module type, default 83). It is a post-hook on `SMBuildingMaster:getModularGarrisonLimit` and adds the bonus to the return value.
- Run s90f-5 (bonus 24, module type 98 = the manor itself, only to prove the hook): `getModularGarrisonLimit` through the bridge returned 36; the mod log says `limit 12 -> 36`. A real Lv3 keep test needs a built module (see below). Native C++ callers are not changed, so the UI number may stay at the native value: check on screen when a Lv3 keep exists.

### Finding 3: the mouse did not reach the game (open)
- New probe `probe-manor-flow` (the working flow: open planner by `openCastlePlannerUI`, click card, place, check `blueprints` count and cost, Commit, give goods, wait for `IsConstructed`). Runs s90f-1, 2, 6: the card click opened tooltips (hover works: `s90f-3/screenshots/k2.png`, k3.png) but no ghost appeared, `blueprints` stayed 3, and the scenario stopped before Commit (as designed).
- Card order on `manor-closed` today: x 0.785 Walls and Gates, 0.83 Outer Tower (472), 0.875 Garrison Tower (keep, 57), 0.92 hall; y 0.449. Round 6 notes had another order. Use hover tooltips to check.
- By hand in a kept-open game (s90f-3 with pak, s90f-4 WITHOUT any pak): the cost tag "Construction Cost: 4 8" appears at the screen centre and does not follow the cursor; `PawnCPP:getMouse3d` returns Z -100000 (no ground) for every cursor position, also with no planner and in plain building mode (`s94_drive.py ghost`). The game is in the foreground and the cursor is inside the window. So the synthetic cursor is not seen by the game's world trace today, with or without the pak. The earlier runs (s90e-5) did show a ghost, so something changed in the session (focus, DPI, or a user input device). Needs the user's real mouse or a check of the input setup.
- Not tried: opening the planner with the real manor panel button instead of `openCastlePlannerUI` (the button may also switch the input mode), and a raw-input mouse move.

### Not done
- Pak B ghost and finished module (task 2): pak B is built and installed in run s90f-6, but no module could be placed. The Lv3 look of the finished keep is NOT proven.
- Card 123 (#65, task 4): no launch left.

### Tools added
- `probe-manor-flow` scenario (options `HARNESS_CARD_X/Y`, `HARNESS_SPOTS`, `HARNESS_STOP=planner`, `HARNESS_DAYS`), `s94_drive.py` commands `click`, `hover`, `prop`, `call`, `mouse3d`, `pause`, `unpause`.
- Next run: first prove `getMouse3d` is valid (hover in building mode) before any planner step; then pak B with `HARNESS_CARD_X=0.875`.
