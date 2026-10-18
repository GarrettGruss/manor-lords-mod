# Rule search and placement test (Q2, Q4, Q5, Q6)

Date: 2026-10-11. Real game with the bridge and raw Lua eval (experiments only). Names and numbers only.

## Q2: where is the building rule?
Verdict: **in C++, and no reflected function carries it.**
- Data tables (`DT_ConstructionBPs` 186 rows, `DT_Upgrades` 62 rows, `DT_BuildingMeshPathData` 72 rows, `DT_IndependentBuildingPartAssemblies` 73 rows, read with `pakmod.py extract` and `tojson`):
  they hold construction parts (mesh and assembly Blueprint per building id), upgrade rows and mesh paths. No column links a building to the manor, limits a count or marks "manor only".
  Strings with Manor, Castle, Keep or Gatehouse appear only as mesh and construction Blueprint names.
- Blueprints: the `BM_SG_Manor_*` Blueprints are empty mesh actors; the planner widget only calls native functions (see `manor-survey.md`).
- Hooks: UE4SS hooks were set on `RTSMultiEngineCPP:isBuildingTypeValid`, `pointCollidesWithBuildingBorder`, `segmentCollidesWithAnyBuilding`, `isAreaObstructedByUnits`,
  `PawnCPP:updatePlacebuildingMesh`, `updatePlacebuildingMPC`, `UpdateBuildingProximityCache`, `findNearestWallSnapPoint`, `getHitBuilding` while a build preview was open for 1.5 s.
  **Zero events** came in from all nine. A control hook on `PawnCPP:getMouse3d` got 720 events in the same time. So the placement check calls these natives directly in C++
  and never goes through `ProcessEvent`. A hook cannot see or change it (workaround C is not possible).
- The pawn has no property that says "placement valid" or "reason refused". It has only `placeBuilding`, `placeBuilding_isSnapped`, `resourcesInCollisionOfPlacebuilding`,
  `placebuilding_missingTech`, `fieldCollides`. Both lists stayed empty for every refused spot.

## Q4: normal building inside the manor area
Not tested. A manor area (bailey) needs committed modules and walls in the planner. This session could not complete one (see `workaround-m2.md`).
What was tested: a normal building (Dunghill 121) next to and over a finished Keep.
- Over the Keep footprint: refused (the click placed nothing). Reason: the Keep itself overlaps.
- The preview outline is orange for every building in this build, also for valid spots, so the colour is not a refusal sign. Use the building count after the click.
- With the Keep's `finalBorder` emptied (`TArray:Empty()`, 8 points to 0) the click over the Keep still placed nothing.
- With `SetActorEnableCollision(false)` on the Keep the click over the Keep still placed nothing.

## Q5: manors per region
- `Region.manor` is **one** object reference, so the data model holds one manor per region. `RTSMultiEngineCPP:setRegionsManor(manor)` sets it.
- A second Keep (type 57) is **refused while a building of type 57 exists** in the region. Test (Dunghills place at the same spots):
  - First Keep built (by the shortcut): a second Keep click placed nothing at 7 different open spots.
  - `Region.manor` cleared (`reg.manor = CreateInvalidObject()`): still refused. So the check does not read `Region.manor`.
  - The first Keep retyped (`Data.bType = 121`): the second Keep was placed at once (count of type 57: 1). So the check counts buildings of type 57. It is a unique-building rule in C++.
- Workaround D by retyping is not clean: the retyped actor is no longer a Keep. It proves where the limit is. It is not a fix.

## Q6: collision
- Blocking by buildings is not the actor collision (`SetActorEnableCollision(false)` changed nothing) and not the `finalBorder` array alone (emptied, no change).
  The check uses native building data that Lua cannot reach with the properties tried. Not possible from Lua with what was found. The result is "not found", not "proven impossible".

## Not verified
The reported soft-lock itself (normal buildings refused inside a committed bailey), and any message text. The developer statement is not checked.
