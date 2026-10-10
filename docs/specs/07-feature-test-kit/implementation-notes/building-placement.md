# Building placement: search and probe

Date: 2026-10-10 (branch feat/12-clock-cause-and-buildings). Result: **no verified action. Not possible through the bridge alone.**
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
