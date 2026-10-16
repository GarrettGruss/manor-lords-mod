# Mouse-free placement of a normal building (issues #104, #115)

Date: 2026-10-15. Result: NOT achieved. Hitching post (30) and large stable (125) were not placed. 1 game launch (run `s104m-1`, fixture `base`). No save function was called.

## Functions a normal placement uses (jmap)
- Reflected on `PawnCPP`: `activateBuildingMode(int)`, `selectBuildingMode(int, Stat)`, `setPlacedBuilding(int)`, `updatePlacebuildingMesh(id, isSnapped, snapVariation)`, `LMB_BP_pressed/released` (Blueprint events), `resetBuildingMode`.
- Property `requestBuild` (bool), `placeBuilding` (int), `placeBuilding_isSnapped`, `resourcesInCollisionOfPlacebuilding`, `placebuilding_missingTech`.
- The preview is the native default component `DummyBuilding` of the pawn (not a reflected property; path `<pawn path>.DummyBuilding`).
- No reflected commit function exists for a normal building. `commitField` and `addCommitFieldRequest` are for plots only. `RTSMultiEngineCPP:finishSpawningSoloBuildingAsync` takes `BuildingSpawnParams` (no reflected fields, spec 07 note).

## What was tried this round
| Try | Result |
|---|---|
| Launch arg `-faketouches` (new `HARNESS_GAME_ARGS`), then `SetCursorPos` and `activateBuildingMode(30)` at 3 spots | `getMouse` stays (10, 10), `getMouse3d` stays Z -100000. No effect. |
| `MLPlayerController:SetMouseLocation(1200, 700)` | Runs, `getMouse` unchanged. |
| Read `DummyBuilding` in building mode | `RelativeLocation` (0, 0, -100000): the native tick writes the failed cursor hit into it. |
| `updatePlacebuildingMesh(30, false, 0)` | Works: `DummyBuilding.StaticMesh` becomes `SM_MERGED_BM_SG_HitchingPost_preview`. |
| Write `RelativeLocation` and call `K2_SetWorldLocation` (via bridge) | The write reads back, but the world location stays (0, 0, -100000). No ghost in the screenshot. The native tick overwrites it, or the transform is not updated. Not separated. |

## Findings
- The cursor path is native and needs a Windows mouse device (see `os-mouse-regression.md`). A fake touch flag and `SetMouseLocation` do not bypass it.
- A Blueprint-visible mesh preview can be made without the mouse (`updatePlacebuildingMesh`), but position and validity come from the native tick.

## Next ideas (not tried, 5 launches left)
1. A mod hook (`RegisterHook` post on `PawnCPP:Tick` or `updatePlacebuildingMesh`) that sets the `DummyBuilding` world transform every frame, then `requestBuild` = true, then `LMB_BP_released`. A bridge write is too slow to win against the tick.
2. Capture a real `BuildingSpawnParams` from a call seen by a hook, then replay it. Needs one real placement by an AI or a user.
3. A virtual HID mouse or a real mouse on the PC (user action).

## Added
- `HARNESS_GAME_ARGS` (allow list `-faketouches`, `-windowed`) in `runlib/game.py`, with fake tests.
- Tool `harness/tools/s104_nomouse_probe.py` (reads getMouse and getMouse3d without a mouse check).
- Leftover: slot `saveGame_46*` from an earlier run is still in the real save folder. This run's slot 47 was removed.
