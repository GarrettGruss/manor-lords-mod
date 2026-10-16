# Mouse-free placement: blueprint route (issue #104)

Date: 2026-10-15. Result: NOT achieved for a normal building. 1 game launch (run `s104b-1`, fixture `base`). No save function was called. `allow_eval` stayed false.

Follows `mousefree-preview-hook.md`. Code: command `HarnessPlace.bp` (file `mod/HarnessPlace/Scripts/blueprint_route.lua`) with the modes `scan`, `extend`, `newmaster`.

## Question
Does the manor route (blueprint StaticMeshActor in `blueprints`, then `convertBlueprintsToBuildings`) build a normal building (hitching post, row 30) without a mouse?

## Facts
- `SMBuildingMaster` is the class of every building, not only the manor. It has `buildings`, `blueprints`, `blueprintGhosts`, `Data.bType`, `Region`, `ownerPawn`, `masterPtr`.
- Reflected functions with the words blueprint, construct, spawn on `SMBuildingMaster`: `convertBlueprintsToBuildings`, `getConstructionProgress`, `setConstructionPaused`, `spawn*` helpers. On `RTSMultiEngineCPP`: `finishSpawningSoloBuildingAsync` and `spawnAsyncContstrBPLazy` (no readable parameters), and the Blueprint functions `setupBuildings` and `SetBuilding`. No reflected function takes a type and a point and makes a site.
- The preview mesh of row 30 is read from `DummyBuilding` after `updatePlacebuildingMesh(30, false, 0)` (`SM_MERGED_BM_SG_HitchingPost_preview`). Other hitching post masters in the game have no loaded mesh with that name.

## Tries
| Try | Result |
|---|---|
| (b) `extend`: blueprint with tag `bType_30` added to the player manor (type 98), then `setPlacedBuilding(0)` and `convertBlueprintsToBuildings(false)` | The manor became `constructed=false`, `buildings` 0, then 22 (one more child). It is a child of the manor, not a hitching post. `getBuildingCount(30)` of the region stayed 0. The manor was left under reconstruction. |
| (a) `newmaster`: spawn a new `SMBuildingMaster` (deferred), set `Data.bType` 30, `constructed` false, `ownerPawn`, `Region`, `masterPtr`, add the blueprint, convert | The master exists in region Nusslohe with `buildings` 1, `constructed` false, `progress` 0.5. After 1 game day at speed 3 nothing changed: no builders, no progress. `getBuildingCount(30)` stayed 0. The screenshot (`runs/s104b-1/screenshots/bp_newmaster1.png`, git-ignored) shows no building at the spot. |

## Verdict
The blueprint route adds parts to an existing master. It does not make a standalone construction site. A hand-made master is not a real site: no queue entry, no builders. The game made the real site in `finishSpawningSoloBuildingAsync` with `BuildingSpawnParams`, which Lua cannot fill.

## Not done
- Row 125 with pak `stable4`, command `place_building_at`, fake tests, skill update: not done, no working route.
- Not tried (5 launches left): hook `finishSpawningSoloBuildingAsync` during an AI lord build to see if the parameters are readable; look for the queue (`getConstructionQueueID` 0) that `RTSMultiEngineCPP` fills; the real or virtual mouse device (user action).
- The test manor was left under reconstruction in that game only. The game was closed and the fixture slot removed.
