# Free walls: spike results (Q1 to Q5)

Date: 2026-10-11. Game 0.8.111, real game, 2 sessions (`s14-walls-1` fixture `base`, `s14-walls-2` fixture `manor-bailey`).
Raw Lua eval was off. All work used the bridge (`get`, `set`, `call`), named commands and the real mouse.
Screenshots (kept in the session scratchpad, not in git): `w1_*.png` (session 1), `w2_*.png` (session 2).
No save function was called. The installed fixture slots were removed (`fixtures.py remove`, `fixtures.py uninstall`).

## Short answer
A wall outside the manor is possible. The planner is not needed.
1. Turn the road tool on (`PawnCPP:setRoadMode(true, {X=0,Y=0,Z=0}, false)`).
2. Click 2 or more road points with the real mouse.
3. `PawnCPP:commitRoad()` returns a new plain `Road` (roadType 0, wallType 0, no meshes).
4. Write `road.roadType = 3` (Wall) and `road.wallType = 2` (Wooden), then call `road:cleanSplineMeshes()` and `road:spawnRoadMeshes()`.
5. The road shows palisade meshes at once. It needs no manor, no goods and no builders.

Not shown: that the wall blocks units (Q3), and that it survives a save (Q6).

## Facts about the data
- Wall type enum: `EWallType` None 0, Fence 1, Wooden 2, StoneLow 3, StoneHigh 4. Road type enum: `ERoadType` Regular 0, Dummy 1, Border 2, Wall 3, Stream 4.
  `EPlatformLevel`: None, Open, Hoarding, Closed.
- The 2 planner walls of `manor-bailey` (ids 2147470397 and 2147470357) are `Road` actors with roadType 3, wallType 2, `isBlueprint` true, length about 7900 cm,
  39 static mesh components that all use the mesh `wallMarker` (a marker, not a palisade). `SplineMeshComponents` is empty. No `SMBuildingMaster` of type 50, 470, 471, 476 or 477 exists
  (`building_sites type=...` gave 0 for all five). The manor has one module, type 98 (id 2147469067), the region manor.
  So the visible palisade ring of the bailey in the screenshot is not made of building actors that this harness can list. What makes it was not found.
- `Road` has the functions `cleanSplineMeshes`, `spawnRoadMeshes`, `clearRoad`, `connectCachedToPathfinding`, `getConstructionCost` (returns Good[]), `setCommit`.
- `PawnCPP.dummyRoad` is not the road under the cursor (it pointed at an old road).

## Q1: wall mode outside the planner
- `switchWallMode(OUT NewMode)` needs 1 argument (pass `false`). It runs without error but `wallMode` stays false. The HUD hints stay the road hints
  (`Place Road Point`, `Cancel`, `Adjust Curvature`). Tried 2 times (run 1).
- Writing `wallMode = true` (bridge `set`) changed nothing on screen and the next committed road was plain (roadType 0, wallType 0). So the pawn flag does not make a wall by itself.
- A road drawn with the mouse in road mode is a plain road. Result: wall mode is not a switch you can flip from outside. The wall comes from the road data (steps above).
- Run 2, first test: committed road `Road_2147464916`. Before: roadType 0, wallType 0, 0 meshes. After `set roadType 3`, `set wallType 2`, `cleanSplineMeshes`, `spawnRoadMeshes`:
  roadType 3, wallType 2, `isBlueprint` false, 7 static meshes of `SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam`, length 1726 cm, 8 spline points, centre (16105, -51839, 2543).
  The screenshot `w2_wall.png` shows a dark palisade on the grass. Run 1 did the same with only wallType (roadType stayed 0): no mesh change (`w1_wt2.png`). So `roadType 3` is the key.
- Other wall types, same call: wallType 3 and 4 give 14 meshes of `sg_stoneWall_piece_bottom`; wallType 1 (Fence) gives 0 meshes (fences are made another way).
- Verdict Q1: possible. A wall `Road` can be made with no manor, by a data write after the road tool.

## Q2: goods, builders, cost
- The wall road came out with `isBlueprint` false and no construction site: `building_sites` shows no new wall piece, and the road had full meshes at once.
- No goods and no builders were used (nothing to read: no site exists). The wood stock was not measured as a difference (other things changed it in 1 month of game time).
- `Road:getConstructionCost` exists but was not called. Not measured: what the planner charges for its wall, because the planner was not used.
- Verdict Q2: the mod gives an instant free wall. This is a harness shortcut, not a base game action.

## Q3: blocks units, gate
- Not verified. Tried:
  - `RTSMultiEngineCPP:getPathPrice(A, B)`: answers small whole numbers (1, 3, 5, 7, 14, 27) that do not depend on the wall (same value across and beside the wall). Not usable.
  - A raider group (`spawn_raiders`) at 8x: the squad centre read is the first unit, so it jumps. No clean track near the wall. The wall was only 17 m long, so a path around it is short.
- Not tried: `Road:connectCachedToPathfinding`, a longer wall, a unit test with a player squad order. No gate was tried.

## Q4: buildings next to and inside walls
- Real mouse `place_building` of type 30 (Hitching Post) with the cursor over the wall (`getMouse3d` = (16163, -51851), wall at x 16105): a new site was made (id 2147461492, `built` false).
  So the free wall did not refuse a placement on top of it. A ring of walls was not made, so "inside" was not tested.
- Verdict Q4: the road-wall is not an obstacle for the placement check (one small building, one try).

## Q5: offering the tool to the player
- The road tool is already open to the player. A mod could convert a committed road into a wall when the player holds a key (hook `commitRoad`, or poll `wall_state`). Not built.
- The `WoodenWallPiece` row (470) is a building row. No `WoodenWallPiece` actors exist, and the Road wall does not use it. Not tested as a category entry.
- No tested menu entry or key.

## Q6: save and load
- Not tested. A save needs the user (safety rule). `isBlueprint` false and roadType 3 are the state to check after a load.

## Removal
- `PawnCPP:removeRoad(road)` empties the wall road: spline length 0, 0 meshes, the screenshot shows the wall gone (`w2_rm2.png`). The empty actor stays in `FindAllOf("Road")`; `wall_state` skips it.
- `K2_DestroyActor` on a wall road also removed it from sight. It is not in the mod.

## Named commands (HarnessActions version 18, module `mod/shared/HarnessWalls`)
- `wall_state`: every wall road with id, wall_name, blueprint, meshes, length, middle (read only).
- `road_mode on=1|0`, `road_commit`, `wall_make road=<id> wall_type=2|3|4`, `wall_remove road=<id>`.
- The shared request parser of HarnessActions knows fixed fields only. The wall commands read `road`, `wall_type` and `on` from the raw request text.
- Python wrappers in `harness/runlib/actions.py`: `wall_state`, `road_mode`, `road_commit`, `wall_make`, `wall_remove`.
- Fake tests: `harness/tests/test_fakegame_harnesswalls.py` (12 tests).
- The clicks for the road points are not a command. A scratchpad script (`mclick.py`) used `focus_game`, `move_cursor` and `left_click` from `harness/runlib/osinput.py`
  at window fractions such as (0.12, 0.40), (0.20, 0.34), (0.30, 0.30). Run 2 made a full flow: `road_mode on=1`, 3 clicks, `road_commit`, `wall_make` (wooden, 3 meshes), `wall_remove`.
- The game must not show a pop-up while clicking ("Hunger!" blocked the mouse once; use `close_popups`).

## Not verified
- Blocking of units (Q3), a gate, a ring and inside placement (Q4), a save and load (Q6), the pathfinding link of the wall (`connectCachedToPathfinding`), a key or menu (Q5).
- What object makes the visible palisade of the planner bailey.
