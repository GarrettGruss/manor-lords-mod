# Building placement: search and probe

Date: 2026-10-10 (branch feat/12-clock-cause-and-buildings). Result of the first attempt: no verified action through the bridge alone. **Third attempt (real OS mouse): verified, see the end of this file.**
Probe: hidden scenario `probe-building` (`HARNESS_PROBE_B` = `read`, `mode`, `click`, `scan`). Game paused at start, `saveGame_0`.

## Candidates from the jmap
- `PawnCPP`: `attemptEnterConstructionMenu`, `activateBuildingMode(InBuilding int)`, `selectBuildingMode(InBuilding, InBuildingStat struct)`,
  `setPlacedBuilding(int)`, `resetBuildingMode`, `LMB_BP_pressed/released`, `isInAnyConstructionMode`, `placeFieldDummy`, `commitField`, `commitRoad`.
- `RTSMultiEngineCPP`: `finishSpawningSoloBuildingAsync(params BuildingSpawnParams struct)`, `spawnAsyncContstrBPLazy`, `getBuildingData`, `getBuildingByID`.
- `Region`: `GetBuildings`, `getBuildingCount(bType, constructedOnly)`, `getNumBurgagePlots`. `SMBuildingMaster`: `convertBlueprintsToBuildings`, `demolish`, `cancelOrder`.
- `MLCheatManager`: only collapse, fire, maintain and `AddItemToBuilding`. No cheat that places a building.
- The build menu widgets (`W_HUD_BuildingPanel`, `W_HUD_BuildingCardV2`) call the pawn; placing is the mouse click in the world (`LMB_BP_released`).

## Results
| Probe | Result |
|---|---|
| `GetBuildings` of the player region | 4 buildings; `getBuildingCount` found type 30 once |
| `engine.buildingArr` size | 33, 31, 38 in three runs with no change made: not usable as a count (it changes by itself) |
| `attemptEnterConstructionMenu` | returns, `isInAnyConstructionMode` stays false |
| `activateBuildingMode(1)` | returns, `isInAnyConstructionMode` becomes true; `resetBuildingMode` clears it |
| `LMB_BP_pressed` and `released` after `activateBuildingMode(1)` | return without error; 5 game seconds later the region still has 4 buildings |
| `scan`: types 2, 5, 10, 16, 20, 30, 40, 50 (activate, click, 2 game s) | building count unchanged (14) for every type |
| `PawnCPP.getMouse3d` in building mode | (0, 0, -100000) every time: no ground under the cursor, so the preview has no position |

No crash happened in these probes. `selectBuildingMode` and `finishSpawningSoloBuildingAsync` were not called: their parameters are structs
(`BuildingSpawnParams` has soft class and object fields; reading such structs crashed the game before, see CLAUDE.md).

## What a human or a new tool would need
- A real mouse position over the terrain (OS mouse input to the game window), or a way to set the value that `getMouse3d` returns.
  Moving the real mouse is intrusive and is not done by the harness.
- Or a `HarnessActions` command that builds a `BuildingSpawnParams` in Lua and calls `finishSpawningSoloBuildingAsync`. The struct fields
  were not listed from the jmap in this session and no call was tried, so this is not verified. It was not built (the task said to build only for a verified action).
- The valid building type ids (`bType`) are not known by name. Only type 30 was seen in the region.
- Fallback: a save fixture that already contains the buildings (made by hand).

## Second attempt: fake the mouse and a raw spawn (2026-10-10, branch feat/13-building-placement)
Result: **still not verified. No building was placed in 13 game runs.** No crash. The experiment code was removed from `mod/` and kept as notes:
`building-placement-probe.lua` (helper module) and `building-placement-probe-scenario.py` (probe scenario). They are not deployed.

### Facts from the jmap
- `BuildingSpawnParams` (struct, 152 bytes, `STRUCT_Native`) has **no reflected property** in the jmap (0 fields; `Item` has 53). Lua cannot name its fields.
  `finishSpawningSoloBuildingAsync(params)` takes only this struct. `spawnAsyncContstrBPLazy` has no parameter.
- No other function places a building. Others only read or change one: `activateBuildingMode`, `setPlacedBuilding`, `updatePlacebuildingMesh(buildingID, isSnapped, snapVariationID)`, `commitField`, `commitRoad`.
- `LMB_BP_pressed/released` are Blueprint events (`FUNC_BlueprintEvent`). `getMouse3d`, `getMouse` are native pure functions.
- `EBuildingType` ids (name = id): HitchingPost 30, Well_Lv1 21, Dunghill 121, RallyPoint 53, Forester 86, WoodcuttersLodge 89, Storehouse_Lv1 72, LoggingCamp 4. Full list in the jmap enum `/Script/ManorLords.EBuildingType`.

### What was tried (each in the real game, game at 1x or paused)
| Step | Result |
|---|---|
| `RegisterHook` post hook on `PawnCPP:getMouse3d` that does `retval:set({X,Y,Z})` | Works. The game calls it about 500 times per second and every result was replaced. `getMouse3d` then returned the chosen point (next to an existing building, same z). No crash. |
| Same for `getMouse` (Vector2D): without a mouse it is (10, 10), over the HUD. Replaced with (1200, 700) | Works, no crash. |
| `activateBuildingMode(30)`, wait 2 s, `LMB_BP_pressed`, 1 s, `LMB_BP_released`, wait 3 s | Building count of the player region unchanged. `placeBuilding` = 30, `isInAnyConstructionMode` true, screenshot shows the build hints (Place, Rotate, Cancel) but **no preview building**. |
| Same with the game running during the whole sequence (not paused) | Unchanged. |
| Hook on `getLMBPressedB` returning true, plus `updatePlacebuildingMesh(30, false, 0)` | `getLMBPressedB` true, count unchanged. |
| Set `requestBuild` = true on the pawn | The game reset it to false at once (it reads it), count unchanged. |
| `finishSpawningSoloBuildingAsync({})` (zeroed struct) | Returns without error and without crash. Player region unchanged (4 to 4). |

State while armed: `isUsingUI` false, `bFullscreenUIActive` false, `currentUIMode` 0, `placebuilding_missingTech` empty, `resourcesInCollisionOfPlacebuilding` empty, `previewBuildingDecals` empty, `buildingPreviewPlane` is a plain engine Plane.

### Bugs and traps found
- Counts of an AI region grow by themselves during a run (one region went 5 to 6 and 6 to 7 within seconds). The first raw spawn run looked like a success (5 to 6); the next run showed that it was an AI region. Always count the player's region, and compare with a control run.
- The world coordinates differ from run to run (the player settlement was at different x, y in each run, and region names change). Use the pawn position and a building of the nearest region, never fixed numbers.
- `GetBuildings()` of `PawnCPP.currentRegion` can be an AI region (4 or 14 buildings in different runs).
- A TArray from a Lua call has no `ForEach`; use `#array` and `array[i]`.
- A vararg `...` inside a nested closure is a Lua syntax error (the mod then does not load and every command times out).

### Remaining gap
The preview never appears, so the placement code path stops before the click: the Blueprint tick probably needs a real viewport hit (a ray from the real mouse), not only `getMouse3d`.
`BuildingSpawnParams` cannot be filled from Lua. Open options: OS mouse input over the ground (intrusive, not done), a save fixture that already has the buildings, or reading the Blueprint script of the pawn to find the check that fails.

## Third attempt: real OS mouse (2026-10-10, branch feat/14-os-mouse-placement)
Result: **verified. A building is placed with a real left click.** Probe runs and 10 runs of the scenario `place-building`.

Steps that work (code: `harness/runlib/osinput.py`, action `place_building`):
1. The game is paused after boot. Bring the game window (class `UnrealWindow`) to the front (`AttachThreadInput`, `BringWindowToTop`, `SetForegroundWindow`). Check that it is the foreground window. Else send no input.
2. `PawnCPP:activateBuildingMode(id)` through the bridge.
3. `SetCursorPos` to a point of the window (fraction 0.65, 0.65), then 1 pixel right and back, so the game sees a mouse move.
   Now `getMouse` is the window position (for example (1280, 1002)) and `getMouse3d` is a real ground point (z about 3000 to 5700, not -100000). The **preview appears** (screenshot).
4. Unpause, wait 2 s, left click (mouse_event down, 150 ms, up), wait 3 s, pause.
5. `getBuildingCount(30, False)` of the player region grows by 1 (3 to 4, 5 to 6, 14 to 15). The new building shows as a construction site (screenshot).
6. `resetBuildingMode`, `ClipCursor(NULL)`, and the cursor goes back (measured: 0 px difference in 3 runs).

### Facts
- The earlier blocker was right: the preview needs a real cursor over terrain. A faked `getMouse3d` was not enough.
- Dunghill (121) with 0 timber: the preview shows "Not enough goods!" and the click places nothing. Use `give_item` first. HitchingPost (30) is free.
- **A click on a spot that overlaps another building site places nothing** (the preview is orange, not white). At window fraction (0.5, 0.7) the spot overlaps the log pile of the start camp in some starts (2 of 4 probe runs placed nothing there). At (0.65, 0.65) 8 of 8 runs placed the building.
- The start save gives a different map spot per run (region names change), but the camera shows the same camp layout, so a fixed window fraction works.
- Count the buildings of the chosen type in the player region (`getBuildingCount(type, False)`), not the length of `GetBuildings`. `props` on an `SMBuildingMaster` returns no type property.
- Cursor: before the fix the cursor came back 8 pixels away (the game clips the cursor to its window). `ClipCursor(NULL)` before the restore fixes it.
- No crash. No save was called. The user's cursor and focus are taken during the action (about 6 s).

### Not verified
- Other building types than HitchingPost 30 (Dunghill needs goods; not tried with goods).
- Other window sizes, other monitors or DPI scales (tested once: window 2582x1496 at 100 % scale).
- Whether the game accepts the click when the window is only partly visible or when another program steals the focus during the click.
