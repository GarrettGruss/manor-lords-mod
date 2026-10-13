# A pak changes composite buildings (2026-10-13)

Spec 18, plan steps 3 and 4. Game 0.8.111. Fixture `base`. Probe `probe-composite-pak` (hidden, mouse-free, no unsafe command).
Runs `s18pak-1` and `s18pak-2` (2 game launches, game closed, `~mods` removed). No save function was called. The AES key came only from the environment.

## Method
- Tool `harness/tools/s65_edit_json.py` (new sub-command `blueprint` sets `BlueprintPath` of a row). Row clones use `stats`.
- Row 87 (tent) reads offline: `BlueprintPath` is `/Game/CPP_BP/BuildingMasterAssemble/BM_HomelessTents.BM_HomelessTents_C`. Row 100 (bandit camp) uses the same class.
  So the earlier open point is closed: the tent row points to the `BM_*` class. Rows 87 and 100 have no row in `DT_BuildingMeshPathData` or `DT_ConstructionBPs`, so no extra rows were needed.
- Pak `comp123`: rows 123 (clone of 87) and 124 (clone of 87, `BlueprintPath` set to `BM_HuntingCamp_C`). New names were added to the `NameMap`.
- Pak `comp87hunt`: row 87 itself with `BlueprintPath` set to `BM_HuntingCamp_C` (a reuse of an existing id with another part list).

## Results
| Check | Result |
|---|---|
| `building_stat` 123 and 124 (run 1) | Both rows load and read like row 87 (`homeless_tents`, function 7, `occupantTypes` 0). A pak CAN add a new type id for a composite building. |
| Placement of 123 or 124 | NOT done. The game has no mouse-free call that places a building of a chosen type (spec 15 notes). Only the real mouse places it. A new id is never made by `settle_region`, which makes type 87 only. |
| `master_parts type=123 / 124` | No master (nothing was placed). |
| Tent via `settle_region`, row 87 unchanged (run 1) | 17 parts: `SM_MERGED_C_HuntersTent`, campfire, sitting logs, ... 3 families. |
| Tent via `settle_region`, row 87 with `BM_HuntingCamp_C` (run 2) | 16 parts, a different list: `SM_MERGED_C_SkinningRack`, `table_megascans_LOD5`, HuntersTent, `SM_MERGED_C_TatteredTentA`, campfire, 3 stick fences, 4 sitting logs, rope, tub, 2 rope barrels. The master is type 87, built, `tent` true, 3 families, homeless 3, as in run 1. No crash. |
| Building function | The tent function (housing of homeless families) comes from the row (`buildingFunction` 7) and the type id, not from the part list. It was the same with the new class. |
| Screenshot | Taken (`runs/s18pak-2/screenshots/tent.png`) but the camera did not show the tent, so it shows nothing useful. |

## Answers to the open questions
- Which asset holds the part list? The `BM_*` class named by `BlueprintPath` of the `buildingStats` row. Changing it by pak changes the parts of new masters (proved).
- Can a new type reuse an existing id with another part list? Yes (run 2).
- Does a new id need a new enum value? The row loads with an id that the enum does not name (123 is only a number). Whether placement works is not tested.
- Build menu: not checked. Rows 87, 123 and 124 have `bVisibleInUi` false. The manor planner needs a widget entry (spec 12 note), so a menu card needs a UI pak too.

## Open
- Place a new id (123) in the world. It needs the real mouse (`activateBuildingMode(123)`), or a native spawn call that is not known. A user decision: allow a mouse test.
- Make a visible new part list from new meshes: needs a new cooked `BM_*` Blueprint (not possible with the JSON tools). Reusing an existing `BM_*` class works.
- Screenshot with the camera on the tent.
