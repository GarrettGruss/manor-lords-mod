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

### Ring test, run `s14-wallblock-1` (2026-10-11)
- New game (0 AI lords, Jagged Cliffs, home Rangbachau). The user drew one closed road ring with the normal road tool: `Road_2147465225`,
  33 spline points (first = last), length 201 m, about 68 x 58 m. `wall_make wall_type=2` gave 32 wooden meshes; the user saw the palisade.
- Bait: `spawn_units side=player template=spearMilitia` at the ring centre (32 units). Bandits: `spawn_units side=bandit template=Brigands`
  about 20 m outside the south wall (18 units, squad 7, 47 m from the centre).
- Track: scratchpad `wall_watch.py` (census `realPos` every 2 s, point-in-polygon against the spline points). Output in `runs/s14-wallblock-1/wall_watch_2.jsonl`.
- Result at 1x: the bandits walked straight north at about 3.5 m/s: 38 m, 31 m, then 23 m from the centre and **inside the ring after 4 s**,
  then 2 to 8 m from the centre for the rest of the minute. No detour, no stop at the wall.
- **Verdict Q3: a free wall made by `wall_make` does not block units.** It is a mesh only; the pathfinding does not know it.
- Side note: in 56 s inside, the player squad lost no units (by_side player stayed 32). The fight was not studied.
- Then `Road:connectCachedToPathfinding()` (no parameters, jmap) was called on the ring, and a new Brigands squad was spawned. The user watched:
  the bandits **still walked through the wall**. Call returned without error; no crash.
- The user also saw that the wall still **acts as a road**: new buildings snap to it during placement.
- **Verdict Q3: the free wall is a road with a wall mesh.** Changing `roadType` and `wallType` and rebuilding the meshes changes only the look.
  The game's wall behavior (blocking, no snapping) must come from somewhere else, for example the planner's own commit path or the castle module.

### Bailey test, run `s14-bailey-block-1` (fixture `manor-bailey`, 2026-10-11)
- The bailey has 2 wall roads that join end to end into one closed ring: `Road_2147470381` (35 points) and `Road_2147470341` (37 points),
  about 60 x 50 m, centre (10800, -51163). Both: roadType 3, wallType 2, **isBlueprint true**, 39 mesh components.
- Bait: `spearMilitia` (squad 23) inside the bailey. Bandits: `Brigands` (squad 24), spawned about 145 m south (the camera had moved, so the offset was larger).
- Track: scratchpad `squad_watch.py` (the `realPos` of each unit of one squad, point-in-polygon of the joined roads). Output `runs/s14-bailey-block-1/squad_watch_1.jsonl`.
  The bandits were 18-22 m from the centre at 53 s, 13 of 18 inside at 57 s, 18 at 62 s.
- The user watched: **the bandits pathed around the wall and came in through the gateway.** They stopped for a moment to loot a pile, then attacked the units.
- **Verdict: the planner bailey wall blocks units. The free wall does not.**
- The look differs too (user): the free wall (`wall_make` type 2) shows large shields; the bailey wall shows stakes or logs driven into the ground.
- What the bailey road holds: its mesh components use `/Game/ManorLords/Engine/wallMarker` (a plan marker), `bCanEverAffectNavigation` false,
  collision enabled 1 (query only), profile Custom. So the road meshes are not the stakes and not the blocker.
- A property diff of the bailey road and a plain road: only `isBlueprint`, `roadType`, `wallType` and `StaticMeshes` differ.
- The manor (`SMBuildingMaster_2147469053`): `walls` array empty, `moduleMasks` empty, `bModuleMaster` false. Its `BorderISM` is `borderMesh`
  (36 instances, no collision). The object that draws the stakes and blocks units was **not found** (the bridge lists at most 500 objects of a class,
  so the mesh component search was cut off).
- **The stakes found** (same run): the camera was moved (pawn `K2_SetActorLocation`) so the screen centre was on the wall point under the user's cursor,
  then the bridge `target` trace (camera centre, distance 300000) on channels 0 to 5. Channels 0 and 1 hit `GhostStaticMeshActor_2147468901`:
  - at (9285, -49493), on the wall line; properties `buildingType` 470 (`WoodenWallPiece`) and `wallType` 2;
  - its `StaticMeshComponent0`: mesh `SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam`, collision enabled 3 (query and physics), profile `BlockAll`,
    `bCanEverAffectNavigation` false.
  - The level has 79 `GhostStaticMeshActor` objects (the bailey ring and its gate, not each one checked).
- Correction (runs `s14-path-new-*` below): the ghost pieces are not the visible built wall and not the block. Destroying all of them left both.
- So the planner wall is two parts: the `Road` (plan, `wallMarker` meshes) and a row of `GhostStaticMeshActor` wall pieces (type 470) with blocking collision.
  `wall_make` makes only the first part, with a different mesh (the road's own wall spline mesh), so nothing blocks.
- No reflected function spawns the pieces (jmap search: ghost, wallpiece, spawnWall, buildWall, placeWall, constructWall, generateWall). The C++ makes them
  inside, probably when the planner's wall is committed or built.
- Not known: whether units are stopped by the collision of the pieces or by a mark in the game's own path grid that is set when the pieces are made.

### Spawned pieces, same run (HarnessActions version 19, command `wall_pieces`)
- The user drew a new closed road ring `Road_2147431170` (32 points, 170 m, centre (15093, -46890)) east of the bailey.
- `wall_pieces road=2147431170 step=200` spawned 86 `GhostStaticMeshActor` pieces (`GameplayStatics:BeginDeferredActorSpawnFromClass` +
  `FinishSpawningActor`, then mobility Movable, `SetStaticMesh` palisade, `SetCollisionProfileName BlockAll`, `buildingType` 470, `wallType` 2).
  Read back: mesh `SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam`, collision 3, `BlockAll`. The user: **the pieces look the same as the bailey wall.**
- Test 1 (pieces only): bait `spearMilitia` (squad 25) at the centre, `Brigands` (squad 26) 35 m east. All 18 bandits inside after 12 s. The user saw them
  **phase through** the pieces. Output `runs/s14-bailey-block-1/squad_watch_pieces.jsonl`.
- Test 2 (pieces, plus the ring road set to `roadType` 3, `wallType` 2, `isBlueprint` true like the bailey roads, plus `connectCachedToPathfinding`):
  new bandits (squad 27) inside after 12 s again; the user saw them phase through. Output `squad_watch_blueprint.jsonl`.
- **Verdict: units do not use physics collision, and the road flags do not mark the path grid.** The game moves units on its own simulated
  positions (`realPos`). The bailey block must be a mark that the C++ writes into its own path data when the planner commits or builds the wall,
  for example through the manor (castle module) that owns the wall. Lua cannot reach that step through any reflected function found so far.
- Side effect in this run (a fixture copy, not a user save): `kill_units side=player count=100` also killed 5 player units that were not bait.

### Path data, runs `s14-path-new-1` to `-3` (new games, 0 AI lords, user builds the manor and a planner wall)
- New named command `path_state` (HarnessActions 19): the size of `RTSMultiEngineCPP.SpatialComponent.Obstacles` (one component, on
  `RTSGameManager`; struct `Obstacle2D` has no reflected fields, so only the size is read) and `drawPathfindingDebug`.
- jmap leads: no reflected function adds obstacles or path data. `SMUnit.Path` (struct `PathPoint`, no fields), class `Obstacle` (0 in the world),
  the `SpatialSystem` plugin (avoidance, queries). `drawPathfindingDebug` true showed nothing (user).
- Obstacle count over time (scratchpad `path_watch.py`, log `runs/s14-path-new-3/path_watch.jsonl`):
  start 274; manor placed and built 274 -> 279; wall committed (plan) back to 274; **while builders built the U wall (84 m) 274 -> 316 in small steps**
  (about one entry per 2 m of wall). Run `-1` showed the same pattern (273 -> 282 -> 273 -> 297 for a 37 m wall, manor built in the same time).
- The ghost pieces (`GhostStaticMeshActor`, type 470) are made at the commit: 15 for 37 m, 92 for 84 m. They report `bHidden` true on the actor,
  but their mesh component is visible with collision. The user's view: they are the construction plan for the builders.
- U-wall test (run `-3`): the U is 16 m wide at the opening and 29 m deep. Bait inside, bandits 35 m behind the closed end (spawn position checked
  with scratchpad `squad_pos.py` before unpausing). The bandits stopped 17-19 m from the centre at the back wall, then went around the arms and in
  through the opening (user saw it; 18 of 18 inside after about 35 s). Output `squad_watch_u.jsonl`.
- **Destroying all 92 ghost pieces** (`K2_DestroyActor`): the wall stayed visible (user), the obstacle count stayed 316, and the bandits still
  **pathed around the wall** (user; `squad_watch_u_nopieces.jsonl`). In run `-1`, `removeRoad` on the built wall road also left the wall visible,
  the count unchanged, and the path the same.
- An earlier straight-wall test (run `-1`) did not tell "through" from "around": `spawnArmy` put the bandits about 17-20 m off the target,
  next to the wall end. Check the real start position before a path test.
- **Crash:** after the 92 ghost pieces were destroyed, the user opened the manor planner and the game crashed: access violation reading
  0x0000000000000000 (inside a UE4SS hook frame). The planner most likely still points at the destroyed pieces. Crash report:
  `runs/s14-path-new-3/crash/`. Rule: do not destroy game-made ghost pieces (also in the skill `harness-game-spike`). The earlier run `-1`
  (15 pieces destroyed, wall road removed) did not open the planner afterwards.
- **Verdict:** the block of a built planner wall does not depend on the ghost pieces or on the road. It appears while the builders build, in step
  with new entries in the global obstacle list. The visible built wall is a third object, not found yet (not the road meshes: still `wallMarker`).

### Instant build spike, run `s14-instant-1` (2026-10-11)
- Question (user): can the manor and its wall be made in the final state without builders?
- The game has no instant-build cheat (all `CheatManager` and `MLCheatManager` functions checked in the jmap).
- `MLBlueprintFunctionLibrary:IsWall(t)` is true only for type 50 (`Manor_Walls`). No type-50 building existed after the wall commit.
- The wall is part of the manor's construction: the manor's `blueprintGhosts` list holds the wall's ghost pieces (this is why destroying them crashed
  the planner). The manor's `walls` list (StaticMeshComponents) was empty. A committed wall has no `Construction` actor of its own; only the palace has one.
- Tried on the manor site (user committed manor and wall, game paused), each followed by a short tick:
  - `finish_manor_site type=98` (`Data.constructed` + `setRegionsManor`): the manor reads built, `getConstructionStatus` "Finished", but
    `getConstructionProgress` stays 0.5, the user sees a dirt lot, and the obstacle count does not change.
  - `PawnCPP:constructionComplete(manor)` (new spike command `construction_complete`): no crash, no visible change, no obstacle change.
  - `Construction.constructionProgress` = 1 and = 100 plus `updateConstructionLevel`, `updateBoardVisibilityFast`, `updateElementVisibilityCommon`:
    no visible change; the game reset the value to 0 on the next tick.
- Verdict: no instant build found. The real progress is native state that the reflected calls do not reach. Writing `constructed` alone leaves
  the manor in a mixed state (finished flag, dirt lot); do not use that game further.
- Leads not tried: `SMBuildingMaster:convertBlueprintsToBuildings(bOnlyBuildFirstBuilding)`; many builders plus speed 8x; a saved fixture with the
  wall already built (the harness then loads it in under a minute).

### Fixture `wall-u` and the wall mechanism, runs `s14-wall-fixture-1`, `s14-wall-u-load-1`, `s14-piece-1` (2026-10-11)
- Fixture `wall-u` (user save `saveGame_31`, "free-wall-test-10-11-26-v2"): new game, 0 AI lords, a built palace (type 98, no bailey), a built
  planner U wall (91 m; opening 37 m, depth 33 m) and a built straight planner wall (47 m). Both walls are 49-54 m from the manor.
  Built with 300 planks at 8x (scratchpad `build_fast.py`): obstacles 274 at the wall commit, 337 when built. After a load: 337 again, both
  walls present, autosave pushed away. **Built walls and their obstacle entries survive a save and load.**
- Detector (scratchpad `cross_watch.py`): a unit step that intersects a wall segment (wall polyline sampled every 1 m) is a crossing through the
  wall. Sampling must be about 1 s (track at most 8 units), or a step around an arm tip can look like a crossing.
  Baseline on `wall-u`: bandits 35 m behind the U, bait inside: 0 crossings, 7 of 8 reached the bait around the arms (`cross_baseline4.jsonl`).
- `path_obstacles_clear` (spike: `Obstacles:Empty()`, 337 -> 0): the game crashed at the next squad spawn (null read). Native code keeps
  references into the list, so it is live data, but it cannot be edited from Lua safely. Crash report `runs/s14-wall-u-load-1/crash/`.
- `buildingStats` rows (spike command `building_stat`): 470 `WoodenWallPiece`: not in the UI, `moduleCategory` 2 (manor), `isModule` false,
  `maxHp` 15, `needsRoad` true, `placedWithin` 0. 50 `Manor_Walls`: `moduleCategory` 0. `MLBlueprintFunctionLibrary:IsWall` is true only for 50.
- `activateBuildingMode(470)` shows a small round preview ("Construction Cost: 1", "Trees uprooted for construction: 3827"), but a real click
  places nothing (2 tries). The same flow places a Hitching Post (30). The game makes wall pieces only through the manor wall build.
- **Manor area (the no-build zone):** the planner closes the open U with a dashed line across its opening. The cursor inside shows "Manor".
  A Hitching Post inside the U is refused with **"Road Access obstructed"**, also right next to a road drawn into the U (screenshots
  `runs/s14-piece-1/inside_preview.png`, `inside_with_road.png`). The same post 35 m behind the U was placed.
- The straight wall: a Hitching Post 5 m from its middle on the far side was placed; on the side toward the village it was refused, and the
  cursor shows "Manor" there (`straight_b.png`). **Each planner wall extends the manor area toward the manor, also a single straight wall.**
- Bandits walk through the dashed opening line of the U: the area line does not block units; only built wall pieces do.

### What exactly causes the wall collision (runs `s14-piece-1`, `s14-demolish-1`, 2026-10-11)
- Spike command `mesh_users mesh=PalisadeWallNarrow` (scans every StaticMesh, ISM, HISM and SplineMesh component in Lua; 7769 scanned) on the
  loaded `wall-u` fixture: 171 users in three groups of 57: `GhostStaticMeshActor` (plan, collision 3), `Road` components (collision 1), and
  **`SMBuilding` actors** (collision 1). `SMBuilding` (super `StaticMeshActor`, fields `buildingMaster`, `controllableGate`) is a built part of a
  building. The wall `SMBuilding` pieces have `buildingMaster` = the manor (`SMBuildingMaster`, type 98, `isManor` true).
  So the manor build turns each ghost piece into a real part of the manor building.
- 57 built pieces and the obstacle list: 274 (baseline) + 6 (the manor) + 57 = 337. The list grew in small steps while builders built the wall.
- Demolish test (`SMBuildingMaster:demolish(false)` on the manor, fixture `wall-u`): obstacles 337 -> 274 at once (-63 = manor + 57 pieces);
  the U wall is gone from the screen (`runs/s14-demolish-1/u_after_demolish.png`). Bandit run on the same spot with bait inside: **8 of 8
  tracked units crossed the old wall line 22-27 m from the nearest end and reached the bait in 12 s** (`cross_demolished.jsonl`). Before the
  demolish the same run had 0 crossings (bandits around the arms, about 19 s).
- A first demolish run crashed inside UE4SS (read 0x10) during a `mesh_users` scan right after the demolish: do not scan components while the
  game destroys actors. The demolish itself did not crash.
- Option tried (user idea): mark the Hitching Post row 30 as a manor module (`building_stat_write`: `isModule` true, `moduleCategory` 2).
  Inside the U the refusal changed from "Road Access obstructed" to **"no_module_connection"**; the same next to the U wall and next to the
  palace. A module needs a module connection (socket) that the post does not have. Row 30 restored.
- **Answer.** The collision is the game's 2D obstacle data, not physics:
  1. A built wall piece is an `SMBuilding` actor (palisade mesh) owned by the manor `SMBuildingMaster`.
  2. When builders finish a piece, native code adds one `Obstacle2D` entry to `RTSMultiEngineCPP.SpatialComponent.Obstacles`
     (`RTSGameManager.SpatialComponent`). Unit path finding uses these entries; units move on simulated positions (`realPos`).
  3. Evidence that it is these entries and nothing else:
     - entries appear one per piece as pieces are built, and the block appears with them;
     - entries and the block survive a save and load;
     - removing the pieces through the game (demolish) removes the entries and the block together;
     - every candidate without entries does not block: a road with wall flags (`wall_make`, `isBlueprint`, `connectCachedToPathfinding`),
       mod-spawned palisade actors with `BlockAll` collision, a committed but unbuilt wall (ghost pieces only);
     - every change that keeps the entries keeps the block: destroying the ghost pieces, removing the wall road.
     - The list is live native data: emptying it crashed the game at the next squad spawn.
- Not reachable from Lua: the native function that adds an entry, and the fields of `Obstacle2D` (no reflected fields). The jmap has no
  reflected function that adds, reads or removes obstacle entries. Static analysis of the game binary would be the next step (needs a
  disassembler; not installed).
- Consequence: a mod cannot create a blocking wall from Lua today. A blocking wall must be a manor-built wall, and each manor wall piece
  belongs to the manor building, so it also extends the manor area ("Manor" label, normal buildings refused).

### Raw obstacle data from game memory, run `s14-mem-1` (2026-10-11)
- Method: Windows `ReadProcessMemory` from Python (`ctypes`, no extra tool; scratchpad `obstacles_mem.py`). Address of the SpatialComponent from
  the bridge (`address` field); `Obstacles` is a TArray at offset 656 (jmap), one `Obstacle2D` is 128 bytes (jmap `properties_size`).
  The header read gave num 337, max 384: the same count as `path_state`.
- `Obstacle2D` layout (from 337 entries; wall pieces matched to the wall positions):
  | Bytes | Content |
  |---|---|
  | 0-31 | bounding box: 4 doubles min X, min Y, max X, max Y (about 10 cm padding) |
  | 32-39 | int 1 (flag) |
  | 40-79 | a second copy of the box and the flag |
  | 80-95 | TArray of segments: pointer, count, capacity. One segment = 4 doubles (x0, y0, x1, y1) = 32 bytes |
  | 96-111 | a second TArray (empty in all entries read) |
  | 112-119 | two int32, both increase with the index (ids, not grid cells) |
  | 120-123 | int32 = the entry's own index |
  | 124-127 | flags (0x20000 for walls, manor and most map entries; 0x10000 for some) |
- Segment counts: 197 entries 0, 57 entries 2 (the wall pieces), map features 3, 4, 8, 17 and 84 segments, the manor 6.
  **A wall piece = 2 segments: the two diagonals of the piece footprint (an X)**, about 2.6 m long.
- Interventions (the visible wall unchanged):
  - The first segment of the 28 middle U pieces set to zero length in the live list: bandits still went around (0 crossings).
  - Then also the bounding boxes of those 28 entries moved far away: still around (3 crossings, all within 1.1 m of an arm tip).
  - So path finding does not read the live list at query time. `AbstractNavData` is the only navigation data (no Recast navmesh):
    the game uses its own path finder.
- Memory scan for one original segment (scratchpad `memscan_pts.py`, 5.5 GB private writable memory, 45 s): the segment exists as doubles in
  several more places (no float copies): the live entry and 4 arrays of consecutive segments, where the piece's two diagonals sit next to
  segments of other pieces and map features (for example at 0x167124e3e40 and 0x167124e7980). These look like per-tile segment buckets of
  the path finder's spatial grid: a segment that overlaps several tiles is copied into each tile.
- **Not done:** flattening every copy of the 56 middle segments (scratchpad `flatten_copies.py`) and repeating the bandit run. The
  permission check denied the memory-wide write. This is the test that would prove the bucket copies are the block.

### Confirmed cause: the live `Obstacle2D` segments, run `s14-tax-1` (2026-10-11)
The user allowed the memory write of `flatten_copies.py` for test games. Scripts of this spike are kept in `implementation-notes/tools/`
(they read and write game memory with Windows `ReadProcessMemory`/`WriteProcessMemory`; test games only, never a user save).
All runs: fixture `wall-u` copy, bait (32 spear militia) inside the U, 18 Brigands spawned 35 m behind the U's closed end (start position
checked each time), tracker `cross_watch.py` (8 units, about 1 s steps, pop-ups closed every 5 s). The 28 middle U pieces (13-78 m along the U)
are the test pieces; each has 2 segments (the two diagonals). "Through" = crossings 12-23 m from the nearest wall end; "around" = crossings
only at the arm tips (<= 1.1 m) or none.

| Live list segments of the 28 pieces | Tile copies (4 per segment) | Result |
|---|---|---|
| original | original | around (baseline, also `wall-u` runs before) |
| first diagonal flattened, boxes moved far away (`s14-mem-1`) | original | around (the second diagonal still blocks) |
| both diagonals flattened | all 224 copies flattened | **through**: 8 of 8, 18-23 m from the ends, bait reached in 14 s (`cross_allcopies2`) |
| both diagonals flattened | restored | **through**: 8 of 8, 13-21 m (`cross_restored`) |
| restored | restored | around: crossings only 0.3 m from the tips, 1 of 8 at the bait in 60 s (`cross_restored_all`) |
| both diagonals flattened | original (scan: 4 of 4 copies intact) | **through**: 7 of 8, 12-20 m (`cross_livegap2`) |

- The visible wall stood in every run (screenshot `runs/s14-tax-1/through_wall.png`: bandits and militia fight inside the standing U).
- An earlier `livegap` run and the first `allcopies` run were invalid: a "Hunger!" pop-up stopped the simulation (the bandits did not move).
- **The cause of the wall collision is the segment data of the live `Obstacle2D` entries in `RTSMultiEngineCPP.SpatialComponent.Obstacles`
  (bytes 80-95 of an entry point to its segments, 4 doubles each).** The game's own path finder reads these segments when it plans a path.
  One built wall piece = one entry with 2 segments (the diagonals of its footprint). Either diagonal alone is enough to block.
  The bounding box (bytes 0-79) is not needed for the block, and the per-tile copies of the segments are not what the path finder reads
  (flattening them alone was not tested; with the live segments original and the copies flattened the result is unknown).
- Correction: the earlier note "path finding does not read the live list at query time" was wrong. It was based on flattening only the first
  diagonal; the second diagonal kept the block.
- Who creates the entry: native code adds one entry when builders finish a wall piece (`SMBuilding` part of the manor). No reflected function
  does it. Lua cannot write it; the memory write can (test only).
- Consequences for the design:
  - A breach for bandits = make the segments of the broken pieces zero length (or remove the entry); the visible pieces need their own change.
  - A free blocking wall = an `Obstacle2D` entry with wall segments where the mod wants them. Today only by memory writes (not for a shipped mod).
    A shipped mod needs a native way: a C++ UE4SS mod, or a game call that adds an obstacle for a mod actor (not found).

### Tax office (type 58), run `s14-tax-1`
- Row 58: `moduleCategory` 2 like the palace (98), keep (57), gate (95) and tower (472); `isModule` false for all of them; `bVisibleInUi` false;
  `needsRoad` true; `collidesWithRoads` true; `maxInRegion` 1; `job` 47.
- `activateBuildingMode(58)` inside the U (manor area): the preview shows no error, only "Construction Cost: 4" (timber). A real click did not
  make a site, also with 50 timber given (`tax_inside_u2.png`). The same outside the U. In the base game the tax office is placed from the manor
  planner, so the normal build mode probably cannot commit a manor building. Next: place it through the planner (user), then read the new
  building, its `buildingMaster` link and whether its parts add obstacles.

### Tax office through the manor planner, live with the user (2026-10-12, run `s63-tax-live`, fixture `wall-u`, issue #63)
The user opened the manor planner, placed a tax office, committed the plan and let the builders finish. The agent watched with hooks and
pawn diffs (the run has its own bridge folder `runs/s63-tax-live/bridge`; the MCP bridge tools only watch the default folder, so a small
script sent the ops there).
| Step | Calls seen (hooks) | State |
|---|---|---|
| Open planner, pick the tax office | `PawnCPP:setPlannerMode(manor)` (manor = `SMBuildingMaster` type 98), `PawnCPP:setPlacedBuilding(58)` | pawn `inPlanningMode` true, `plannerModeBld` = the manor, `placeBuilding` 58 |
| Click to place the blueprint | none (native) | the manor's `blueprints` list gets a `StaticMeshActor` with mesh `SM_MERGED_C_SG_TaxCollectorProper` (the palace blueprint is the same kind of actor) |
| Commit the plan | `setPlacedBuilding(0)`, **`SMBuildingMaster:convertBlueprintsToBuildings(bOnlyBuildFirstBuilding)` on the manor**, `setPlannerMode(nil)` | `inPlanningMode` false; type 58 count 0 |
| Builders finish | none | game message "manor is finished"; still **no type 58 building** (`getBuildingCount(58)` 0, no new `SMBuildingMaster`) |

- The built tax office is an `SMBuilding` part (`SMBuilding_2147467196`, tax collector mesh) whose `buildingMaster` is the manor (type 98).
  A `GhostStaticMeshActor` with the same mesh was the construction ghost. So the tax office is a module of the manor, built as part of the
  manor's construction, like the planner walls. The manor showed no change in `upgradesDone`, `Extensions`, `moduleMasks`, `lv` (1) or workers.
- This explains `s14-tax-1`: normal build mode cannot commit type 58, because type 58 is never its own building.
- Mouse-free lead: the commit is a reflected call with one bool (`convertBlueprintsToBuildings(bOnlyBuildFirstBuilding)`). The open step is
  the placement click, which adds the blueprint mesh actor to the manor's `blueprints` list in native code. Not tested: spawning that actor
  from Lua and adding it to the list, then calling `convertBlueprintsToBuildings`.
- Not checked yet: whether the tax office part adds path obstacles, and its worker slots (spec 12: job 47, no slots).
- The blueprint actor is identified by its actor tag: `Tags` = ["bType_58"]. No owner, no other link.

### Manor blueprint without the mouse (same session, HarnessActions 36, command `manor_blueprint_add`)
- The command spawns a `StaticMeshActor` (copying the mesh of an existing blueprint of the same type on the manor), sets the tag
  `bType_<type>`, appends it to the manor's `blueprints` list (4 -> 5) and can call `convertBlueprintsToBuildings(false)` on the manor.
- Test: a second tax office (type 58), 15 m east of the first (x 12849, y -52304, z 2517), first without the commit. The user saw the second
  blueprint in the world and the planner, although `maxInRegion` is 1.
- Commit through the bridge (`convertBlueprintsToBuildings(false)` on the manor; the hook saw the call): tax collector mesh users went from
  1 to 2 `GhostStaticMeshActor` (construction ghost) and 1 to 2 `SMBuilding` parts of the manor. So a mod can plan manor modules without the
  mouse, and the commit does not enforce `maxInRegion`. User check: the scaffold appeared and families began the construction.
- Garrison (keep, type 57) through the planner, same session: `setPlannerMode(manor)`, `setPlacedBuilding(57)`, the blueprint
  `StaticMeshActor` with tag `bType_57` and mesh `SM_MERGED_C_SG_Manor_MainTower_Lv1_New`, commit `convertBlueprintsToBuildings` on the manor.
  Cost: 5 rubble stone (item 15, `EItemType::Rubble`; rough stone is 27). After the builders finished: no type 57 building and no new
  `SMBuildingMaster`; the garrison is a manor part like the tax office. `SMBuildingMaster:getModularGarrisonLimit()` on the manor returns 24
  (not read before the garrison, so the change is not known). The game UI shows the garrison as 5/24 (user), so the limit read by
  `getModularGarrisonLimit` is the garrison capacity shown to the player.
- Second garrison without the mouse (`manor_blueprint_add type=57`, 18 m east of the first, commit in the same call): blueprints 6 -> 7,
  the builders built it (user). `getModularGarrisonLimit()` stayed 24 and the UI stayed at 24 (user). So extra garrison modules do not add
  capacity: the limit is not a sum over garrison parts (it may come from the first garrison, the manor level or the palace).
- Guard tower through the planner (user): `setPlacedBuilding(472)`, blueprint tag `bType_472`, mesh `SM_MERGED_C_SG_Manor_Tower_Lv1_00`,
  commit `convertBlueprintsToBuildings` on the manor; cost included rubble stone. After the builders finished: type 472 count 0, no new
  `SMBuildingMaster`, `getModularGarrisonLimit()` still 24. So the tower is a manor part too and does not change the reported garrison limit.
  Civilian garrison test (same session): 150 fish given (the village was starving), then one Brigands squad (squad 19, 18 units,
  `bandit_spawn_at`) 30 m west of the tower at (7937, -50456). The village had 3 families (all homeless) and 5 retinue units.
  For 2 minutes of play (polled every 10 s) bandit units stayed 36, player units 5, families 3; the user saw no civilian go into the tower.
  Caveat: `spawnArmy` bandit squads wait at the AI waypoint for about 480 game seconds before they attack (spec 15 part 3), so no raid
  alarm happened. A fair test needs a real raid (`spawn_raid`) or an alarm, and housed families. `hasModuleOfType(57)`, `(58)`, `(95)`, `(98)`, `(472)` all return false: that
  call does not use building type numbers.
- Limits: the mesh path of a module type with no blueprint on the manor is not known by the command (it copies from an existing blueprint).
  The ground check, the manor area check and the cost were not checked for a mod-made blueprint.

### How walls are removed (for a future "bandits destroy walls" feature)
- `SMBuildingMaster:demolish(false)` on the manor removes the whole manor with all wall pieces and their obstacle entries at once
  (337 -> 274). Too coarse for one breach.
- A wall piece is an `SMBuilding` part of the manor; there is no reflected call to remove one part. Do not `K2_DestroyActor` game parts
  (the planner keeps pointers; a crash followed for ghost pieces).
- Data that hints at damage: `WoodenWallPiece` (470) has `maxHp` 15, `Manor_Walls` (50) `maxHp` 100; `BuildingDataStruct` has `hp`/`maxHp`;
  `SMBuildingMaster` has `collapseBuilding`, `StartFire`; `Construction` has `reverseConstruction`, `isCollapsing`, `setOnFire`;
  `MLCheatManager` has `CollapseNumBuildings`, `SetFireToNumBuildings`. None of these was tested on walls.
- The planner can delete a wall plan (`PawnCPP:destroySelectedCastleBlueprint` after `selectCastleBlueprint`, object arguments; not tested).
- Leads for a breach: (1) the planner path (select one wall segment, delete it) and check that the obstacle entries of that segment go;
  (2) fire or collapse on the manor and check whether wall pieces lose entries one by one; (3) the path-finder segment buckets (needs the
  denied memory write).

### Unsafe commands and tools (off unless allowed)
These commands and scripts change game data outside the normal game flow. They are kept so the spike results can be reproduced, but they
are refused unless the variable `HARNESS_ALLOW_UNSAFE=1` is set. Use them only on test games, never on a user save, never in a shipped mod.
- Spike commands in HarnessWalls (HarnessActions). The game process needs the variable; the launcher passes the shell environment to the game.
  - `path_obstacles_clear`: empties the global obstacle list. The next squad spawn crashed the game (null read).
  - `building_stat_write`: writes one field of a `buildingStats` row in memory, until the game ends.
  - `construction_complete`: calls `PawnCPP:constructionComplete` on one building (no crash, no change on the manor; see above).
  - Without the variable each one answers `ok: false` with the error "... is an unsafe spike command". Fake tests check both cases.
- Memory write scripts in `tools/unsafe/` (Windows `WriteProcessMemory`). The script process needs the variable;
  `obstacles_mem.open_game_rw` refuses without it, so every write path is covered.
  - `obstacle_gap.py`: makes the segments of the middle part of one wall zero length in the live obstacle list (run `s14-tax-1`). Has a restore mode.
  - `flatten_copies.py`: finds every copy of given segments in writable memory and makes them zero length. Has a restore mode.
- Read-only scripts (`obstacles_mem.py dump`, `memscan_pts.py`, `cross_watch.py`, `wall_test.sh`) stay in `tools/` and need no variable.
- Entry layout for all of these: see "Raw obstacle data" and "Confirmed cause" above.

### Fire and damage as a breach
Question: does the game destroy wall pieces through fire or damage, so that a raid can open the path? Fixture `wall-u`. New read command
`building_health building=<id>` (type, hp, maxHp, onFire, fireAmt, rubble, built, collapse chance; fake test added).
Manor id changes with each load (2147470014 in run 2, 2147470012 in runs 3 and 4); read it with `manor_state`.

Data before any change: manor type 98, `Data.hp` 0, `Data.maxHp` 200, not on fire. The 57 wall pieces are `SMBuilding` actors with no health data of their own
(no reflected hp, fire or damage call on them). They are not separate damage targets. Obstacles: 337.

| Run | Call (bridge, on the manor `SMBuildingMaster`) | After 8 to 24 s at speed 3 |
|---|---|---|
| s14-fire-2 | `StartFire()` | manor type 75 (rubble), onFire false, maxHp 100; obstacles 337 -> 274; `mesh_users PalisadeWallNarrow`: SMBuilding pieces 57 -> 0 (Road and Ghost components stay at 57 each, total 171 -> 114); screenshot `fire1.png` |
| s14-fire-3 | `collapseBuilding()` | same: type 75, obstacles 274, total 114 |
| s14-fire-2 | bandit test after the fire (`wall_test.sh`, bait inside) | 4 crossings through the old wall line, bait reached; obstacles 274 |

- Verdict: fire and collapse on the manor remove the whole wall at once (6 manor + 57 piece entries, 63 in all), not piece by piece. The fire did not burn for
  39 s: the manor was already rubble at the first read (8 s). So a manor fire is a complete breach, not a gap.
- Not tested: `SetFireToNumBuildings`, `CollapseNumBuildings`, `GetCollapseChance` (it is 0 on a standing manor), damage to single pieces.
- Raiders (runs 4): Brigands spawned 35 m behind the wall with bait inside: 0 crossings, they went around; with no bait: 1 crossing at 1.1 m from the wall end (a go-around).
  About 20 reads over 100 s at speed 3 each time, with bandits in the village: manor hp 0, onFire false, type 98, obstacles 337 all the time. The bandits killed
  villagers (families 5 -> 3) but did not attack or burn the wall or the manor. No crash.
- Base game: nothing in the notes or in this spike shows raiders setting fires. The `raid-standin` faction table has a `burn` objective, but that is a mod rule, not game code.
- Natural breach method that works today: a mod rule that calls `StartFire` or `collapseBuilding` on the manor when a raid reaches the wall. It removes the whole wall.
  A partial breach needs a call that removes one piece; none is reflected (see "How walls are removed").

### Where this leaves free walls
- Look: solved (`wall_make` gives the shield wall; `wall_pieces` gives the bailey stake wall).
- Block: not solved. Leads not tried: the castle planner functions on the pawn (`splitWallsByCastleModule`, `joinWalls`) with a manor selected;
  reading the path grid itself (`RTSMultiEngineCPP` path or grid properties) before and after the user draws a planner wall; a mod rule that stops or
  slows enemy units at a wall line (polling `realPos`, then an order or a speed change).

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
- Whether a planner bailey wall blocks units (Q3: a free wall does not block, also after `connectCachedToPathfinding`), a gate, a ring and inside placement (Q4), a save and load (Q6), the pathfinding link of the wall (`connectCachedToPathfinding`), a key or menu (Q5).
- What object makes the visible palisade of the planner bailey.
