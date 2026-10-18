# Data model of the manor wall and keep (2026-10-18)

Spec 32, issue #233. Game 0.8.111. Sources: the extracted `buildingStats` and `DT_ConstructionBPs` tables, the `BM_SG_Manor_*` Blueprints (UAssetGUI JSON), the cooked mesh headers, and the earlier spec 12 and 14 notes. Run `s32-2` to `s32-11` confirm the wall facts in the real game.

## Pieces
| Part | `buildingStats` row | Module Blueprint (`CPP_BP/BuildingMasterAssemble/ManorModules/`) | Part name | Mesh (all under `/Game/ManorLords/Buildings/Merged/`) | Row in `DT_ConstructionBPs` |
|---|---|---|---|---|---|
| Wall piece (wooden) | 470 `manor_wall_wooden`, `maxHp` 15 | `BM_SG_Manor_Wall_Lv1` | `MainBld_470` | `SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam` | 470: no asset, `buildingPartName` `manor_wall_wooden` |
| Gatehouse | 95 `manor_gate_lv1`, `maxHp` 100 | `BM_SG_Manor_Lv1_Gatehouse` | `MainBld_95` | `SM_MERGED_C_SG_Gatehouse_Lv1_Ubeam` | 95: `C_SG_Manor_Gatehouse_LV1_Ubeam_C` |
| Outer tower | 472 `manor_outertower_lv1` | `BM_SG_Manor_Lv1_Tower_` | `MainBld_472` | `SM_MERGED_C_SG_Manor_Tower_Lv1_00` | 472: `C_SG_Manor_Tower_Lv1_00_C` |
| Keep (garrison tower) | 57 `manor_keep_lv1`, `maxHp` 200, `garrisonLimit` 12 | `BM_SG_Manor_Lv1_Keep` | `MainBld_167` (+ clutter parts) | `SM_MERGED_C_SG_Manor_MainTower_Lv1_New` | 167: `C_SG_Manor_MainTower_Lv1_New_C` |
| Manor house (palace) | 98 | `BM_SG_Manor_Lv1_Palace_Solo` | | not read | |
| Wall tool | 50 `wall_tool` | none | | | |

- Rows 57, 95, 470 and 472 have `moduleCategory` Manor. Row 57 has `maxInRegion` 1. The keep and the construction asset use the same mesh (`constructionMeshAsset` of row 57 is the keep mesh).
- The 3 mesh paths are plain static mesh assets. The module Blueprints hold one `StaticMeshComponent0` for the main part, so a mesh swap by asset path reaches the finished part, the planner ghost and the plan actors at the same time.

## What exists in a built ring (fixture `manor-closed`, run `s32-1`)
`mesh_actors` (new command, HarnessActions 58) lists the owners of the palisade mesh: 168 components in 3 groups of 56:
1. `SMBuilding` actors (the built wall pieces; `buildingMaster` is the manor, collision enabled query only). 56 pieces on a square ring of about 47 m (radius 23 m from the centre), one gap with the gatehouse.
2. `GhostStaticMeshActor` actors (the plan, collision `BlockAll`; the game makes them at the commit, do not destroy them: spec 14).
3. `Road` components (the planner wall road, `wallMarker` meshes in some fixtures, the palisade mesh here).
The gatehouse mesh has 4 components: `SMBuilding`, `GhostStaticMeshActor`, `Road`.

## Where the collision comes from
- Not the mesh. Spec 14 proved it: the block is the 2D obstacle list `RTSMultiEngineCPP.SpatialComponent.Obstacles`. A built wall piece adds one `Obstacle2D` entry with 2 segments (the diagonals of the piece footprint). The game path finder reads these segments. The entries appear when the builders finish a piece and go away on demolish.
- The footprint is fixed data, not the mesh bounds. Test: the same ring with the wagon mesh (119 cm wide, 240 cm long, 114 cm high; the palisade is 17 cm wide, 219 cm long, about 390 cm high) still reads 337 obstacles in `path_state` (runs `s32-8` to `s32-10`; the pak runs read the same count), and the bandits path the same way (`pathing-test.md`).
- The gate is an opening between two pieces. Bandits entered through it in the control and in the wagon runs.
- Consequence: any mesh that replaces the mesh asset by path keeps the block, the gate, the hit points (15 per piece), the garrison and the manor area rule ("Manor" label, no normal buildings inside).
- A wall piece cannot be made outside the manor build: `activateBuildingMode(470)` places nothing, `wall_make` makes a visual only, mod spawned actors do not block (spec 14). So a camp that blocks must be a real manor.

## Why a mesh swap is global
The mesh asset is shared. A pak that replaces `SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam` changes every manor wall piece, the ghost pieces and the planner road drawing. The same holds for the keep mesh. Per-camp looks need another class and another row, which the manor wall tool does not offer (no wall type with its own row).
