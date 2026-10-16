# Homeless tents and tent placement (spike, 2026-10-12, run `s15-e`)

Game 0.8.111. Fixture `base` (day 266, region Riesenbuckel), loaded with `run.py --scenario noop --fixture base --keep-open --run-id s15-e`.
Helper scripts (not committed): `runs/s15-tools/q.py`, `b.py`, `fn.py`, `jm.py`, `tent_click.py`, `mdbg.py`. No crash. No save function called. No building or unit was destroyed in this spike.
The user's goal: build a tent (auto place) -> trigger immigration (settle letter) -> a family moves in.
Result: **the tent could not be placed in this session**, so the pipeline was not run.

## Tent facts
Row 87 of `buildingStats` (read offline with `pakmod.py tojson` and in the game with the new command `building_stat type=87`; both agree):
- `DisplayName` `homeless_tents`, blueprint `/Game/CPP_BP/BuildingMasterAssemble/BM_HomelessTents`, `buildingFunction` 7 (Temporary), category Gathering.
- `bVisibleInUi` false (not in the build menu), `constructionCost` 0, `constructionGoods` empty, `needsRoad` false, `collidesWithRoads` false, `canRelocate` false,
  `maxHp` 5, `flammable` false, `bSize` 1.5, bounds 1200 x 800, `AIcanBuild` false, `maxInRegion` 0, no required tech.
- **`occupantTypes` all 0 and `workerTypes` all 0.** A burgage plot (row 3) has `occupantTypes.Y = 1` (one family). So the stats give a tent no family slot.
  A tent is a shelter for homeless families that the game manages itself. I did not verify that it adds no vacant slot (no tent could be placed).
- A tent is an `SMBuildingMaster` (not a subclass). `SMBuildingMaster:isHomelessTent()` tells it. `Region:getBuildingCount(87, ...)` counts it.
- The fixture has **no tent**: `housing_state` lists 0 tents in the player region and 0 in the whole world (145 `SMBuildingMaster` objects). The earlier note that the fixture has a type 87 building was wrong.
- Region numbers at start: families 10, homeless 0, living 11 (+1 unbuilt), vacant 1 (+1 unbuilt). Residential buildings: 9 of type 3 (8 built with 1, 1, 2, 1, 1, 2, 2, 0 families, one unbuilt).
- Who makes tents: not found. These functions exist: `Region:accomodateHomelessFamilies(ignoreBuilding)` (called once with 0 homeless: no change), `getNumHomelessFamilies`, `hasAnyHomelessFamilies`, `SMBuildingMaster:isHomelessTent`.
  No reflected function spawns a tent. The game does it natively. To see it I would have to make families homeless (collapse a house).
  The permission layer denied `ruin_building`, so this was not tested. It stays an open question.

## Placement tries
| Try | Method | Result |
|---|---|---|
| a1 | Search the function lists of `RTSMultiEngineCPP`, `MyPawnCPP_BP3_C`, `PawnCPP_AI`, `Region`, `SMBuildingMaster`, `MLCheatManager` for tent, homeless, camp, shelter, spawnBuilding, placeBuilding, build, construct, house, settle | No function places a building. Only `finishSpawningSoloBuildingAsync(BuildingSpawnParams)` and a lazy spawner exist. `BuildingSpawnParams` has no reflected field (spec 07, building-placement.md), so Lua cannot fill it. The AI lords build natively. No AI build call is exposed. |
| a2 | Spawn the blueprint actor `BM_HomelessTents_C` with `UWorld:SpawnActor` (a temporary command, removed again) | The class is not loaded (`StaticFindObject` fails) and `LoadAsset` did not load it. No actor spawned. A raw actor would also not be a registered building. Dead end. |
| b | Real mouse: `activateBuildingMode(87 or 30)`, cursor to window fractions (0.3, 0.3), (0.35, 0.15), (0.5, 0.5), (0.65, 0.65) | **The real mouse does not work now.** The cursor moves (`GetCursorPos` follows), the game window is in the foreground, one monitor of 3840 x 2160 exists, but `getMouse` stays (10, 10) and `getMouse3d` stays z = -100000, so no preview appears. The control type 30 (HitchingPost, free) fails the same way. Mouse placement worked in earlier sessions (spec 07). Cause not found (guess: the session does not deliver real input to the game window). |

So no tent was placed. Tent count and `vacant_slots` stay as before (tents 0; vacant 1 constructed, 1 unbuilt). Whether builders must build it is unknown.
The bridge eval is off (`allow_eval = false`). I did not change it.

## Auto placement (code)
Mouse-free part (works, run in the real game):
- `tent_find_spot` (module `mod/shared/HarnessHousing`, `HarnessActions` version 23, Python `actions.tent_find_spot()`): rings of points (700 units apart, 8 rings, 12 angles) around `Region:getSettledRegionCenter()`
  (or the centroid of the buildings). A point is kept when `RTSMultiEngineCPP:pointCollidesWithBuildingBorder(point)` is false (the game's own check) and it is at least 900 units from every building of the region.
  A failed check call is not treated as free. The command returns up to 5 spots (`x`, `y`, `z`, `gap`, `ring`). Real answer on `s15-e`: 5 spots on ring 1, gaps 920 to 1362, centre (-37165, -51659).
  The game check was tried by hand: true on a building and 120 units from it, false at a chosen spot and far away.
  Not checked: water, steep ground, roads, the manor area. The preview of the game checks these when the click comes.
- Read commands: `building_stat type=N`, `housing_state` (slots, tents, residential buildings, tents of the world), `accommodate_homeless` (the game call; no effect with 0 homeless).

Mouse part (**test step only, not run in the real game**, because the mouse does not reach the game now):
- `actions.tent_auto_place()`: `tent_find_spot`, then `Bridge.centre_camera_on(x, y)` (moves the pawn, as `place_at.py` did), then `place_building(87, 0.5, 0.5)` with the real mouse, checked by the tent count (+1).
  Fake tests cover the order and the checks (`test_runlib_osinput.py`, `test_fakegame_harnesshousing.py`).
- **The final mod still has no mouse-free way to place a tent.**

## Pipeline
Not run. It needs a tent first. The s15-c fact still holds: the letter gives +1 family per squad when a vacant constructed slot exists.
Because the tent row has no occupant slot, a tent probably does not create a vacant slot. The test must read `vacant_slots` after a tent exists.

## Family slots on the manor (offline read of `buildingStats`, 2026-10-12)
`occupantTypes` is a Vector4; `Y` is the family count (burgage plot row 3: Y 1). Rows with manor category:
- The modular manor rows in use (57, 58, 98) and the walls (50) have no `occupantTypes`. Wall and platform rows (470 to 482) have only `W` 1.
- Hidden rows `manor_palace_lv2` (474, Y 2) and `manor_palace_lv3` (81, Y 5, Z 12) have family slots. Both have `bVisibleInUi` false and
  `maxInRegion` 1. They are probably manor levels the current game does not use. Not checked in the game: whether they can be built, and
  whether their slots count in `getAvailableLivingSpace`.
- So the current manor gives no family slot. Options: a pak mod row that gives a manor module or the tent row (87) `occupantTypes.Y` > 0,
  or a new residential row that acts as a tent. Placement of such a building still needs the build mode (the player) or a mouse-free call.
Tracking: issue #54 (needs the user to show the tent and how it appears).

## Open questions
- Why does the real mouse not reach the game now (it worked in spec 07 and 14)? Retry with a person at the PC.
- Does a tent count in `getAvailableLivingSpace`? Does a settled family move into it?
- Who spawns tents and when (homeless families)? Test: collapse one house with a family in a test copy and watch `housing_state`.
- A mouse-free place call: the only candidate is `finishSpawningSoloBuildingAsync` with a `BuildingSpawnParams` that Lua cannot build.

## Live identification of the tent (2026-10-12, new game, user hovered the tents)
`PawnCPP:getHitBuilding()` with the mouse over the tents returned `SMBuildingMaster_2147470051` (class `SMBuildingMaster`, not a
Blueprint class; region `waldbrand`).
- `Data`: `bType` 87, `constructed` true, `maxHp` 5, `hp` 0. `buildingFunction` 7. `lv` 1. `buildPriority` 4.
- `buildings`: 17 `SMBuilding` children (the tents and props). `ambiences`: "fireplace" and "flag".
- `occupantFamilyIDs` = [0, 1, 2, 3, 4]: **the tent holds the 5 start families**, although the buildingStats row has no
  `occupantTypes`. So a tent is a home for homeless families by its own rule, not by a slot count.
- Footprint: `FieldPoints` (here a plain Vector array on the building master) and `finalBorder` are a closed outline of 13 points,
  about 12 m x 8 m (`fieldBorderPoints` has the 4 corners). `collidesWithRoads` false. No road position.

## Tent through the plot commit (2026-10-12): no
`placePlotType` is `EPlotType` (None 0, Field 1, Pasture 2, Residential 3, Market 4, Bailey 5); there is no tent plot type. The
building type is a separate int, `placeBuilding`. Test: `placePlotType` 3, `placeBuilding` 87, `placeFieldMode` true, one plot
written with `plot_field_place` at the mouse point (`getMouse3d`), then `addCommitFieldRequest()`. Result: a burgage plot (type 3
count 0 -> 1, type 87 count stayed 1; user check). The residential commit ignores `placeBuilding`.
Mouse point: `PawnCPP:getMouse3d()` gives the ground point under the real mouse (works when the mouse is over the game).

## Bandit camp compared with the homeless tent (2026-10-12, user hovered a bandit camp)
`getHitBuilding()` gave `SMBuildingMaster_2147468852`. Same build as the tent: class `SMBuildingMaster`, 17 `SMBuilding` children,
ambiences "fireplace" and "flag", `maxHp` 5, constructed, a 12 m x 8 m axis-aligned footprint (`fieldBorderPoints`).
Differences: `Data.bType` **100** (tent 87), `buildingFunction` **17** (tent 7), `Region` none (tent: the player region),
`ownerPawn` a `PawnCPP_AI` (tent: the player pawn), `occupantFamilyIDs` empty (tent: 5 families). Position about (-37000, -37200).
So a bandit camp is the tent model with another building type and an AI owner, outside any region.
- Camp brigands (same session, new game, before any player unit moved): the user hovered the brigands by the camp. Pawn
  `hoverUnit` = `VAMP_DefaultUnit_C_2147468884`, `hoverSquadID` 5, `bHoversEnemy` true. The unit has no `Owner` and no `Home`.
  `bandit_state`: the bandit lord is `PawnCPP_AI_2147468992` (the camp's `ownerPawn`), with 18 units at game start, status
  `at_war`. Homeless families in the tent: 5 (the region reports them as homeless, vacant slots -5).
- The 17 `SMBuilding` children are prop actors: each has only `buildingMaster` (back link) and `controllableGate` (empty), and one
  `StaticMeshComponent0` as root. Meshes seen (5 of the tent, 1 of the camp): `SM_MERGED_C_HuntersTent` (tent, also in the camp),
  `SM_MERGED_c_campfire`, `SM_MERGED_sittingLog`, `StickFencePost` (Megascans). They hold no game state.

## Deleting the tent (2026-10-12, fresh game)
The UI has no demolish for the tent. `SMBuildingMaster:demolish(refund=false)` (one Bool parameter, jmap) on the tent through the
bridge removed it: tents 1 -> 0, the master object stayed with `built` false, 0 families, position (0, 0). Families 5, homeless 5,
residents 10 did not change. After about 20 s of game time the families wandered (user) and the game did not put up a new tent
(`world_tents` empty). So the game spawns tents at events (start, immigration), not to fix homelessness at once.

## How the game makes a tent (2026-10-12, part 9)
`PawnCPP:settleRegion` on the settled player region made a new tent (type 87) at once per call, with 3 to 5 families in it (runs `s15-surge1`). See `immigration-surge.md`.
