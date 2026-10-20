# Import and pak (task 2.2, 2026-10-19)

- Import: `mod/HarnessActions/ue/import_replace_mesh.py` headless in UE 5.5.4 (project `mlm-ue`). Env: `MESH_NAME=SM_MeshyHouse`, `MESH_DEST=/Game/HarnessMod/MeshyHouse`, `TARGET_CM=700`.
- Replaced vanilla mesh: `/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_Cottage_Lv1_C_UBeam`. It is the mesh of the burgage house blueprint `BM_SG_Cottage_Lv1_C` (`CPP_BP/BuildingMasterAssemble/Residential/`).
- The level 1 cottage has 3 variants. A and B use `SM_MERGED_C_SG_Cottage_Lv1_A_v4_UBeamFoudnations` and `SM_MERGED_C_SG_Cottage_Lv1_B_Ubeam_00`. Only variant C is replaced. The test scenario must build a burgage plot house and check which variant it got, or A and B must be replaced too.
- Result: longest side 700 cm (548 x 628 cm high), scale 7.292, 3210 vertices, 1 material (`MI_Meshy`, an instance of the game master). Textures capped at 1024 and 512.
- WARNING: the import log shows `min_z -314.2`. The mesh pivot is at the centre, not on the ground. The house may sink half into the ground. Check in the screenshots. Fix with a z offset on import if needed.
- Cook: `-run=cook ...` with `+DirectoriesToAlwaysCook=(Path="/Game/ManorLords/Buildings/Merged")`. The cooked files exist.
- Pak: `meshyhouse_P.pak`, 13 files, 2,550,027 bytes. Build folder `modtools/work/meshyhouse/` (not in git). Copies: `mod/HarnessActions/paks/meshyhouse_P.pak` and `modtools/work/out/meshyhouse_P.pak`. `pakmod.py build` verified that the pak lists the same 13 files as the folder.

## Rework (2026-10-19): ground pivot and all three variants
- Vanilla `SM_MERGED_C_SG_Cottage_Lv1_C_UBeam` bounds (pak, ExtendedBounds): origin (-79, -16, 166), extent (262, 535, 392). So it spans x 523 cm, y 1069 cm (long side along Y), z -226 to 558 (pivot at the ground, foundations below it).
- `import_replace_mesh.py` has new options (defaults unchanged): `BASE_TO_GROUND=1` re-imports with an import translation of `-min_z`; `EXTRA_REPLACE_PATHS` (comma list) copies the mesh to more vanilla paths.
- Result with `BASE_TO_GROUND=1`: min_z 0.0, max_z 628.1, x -352..348, y -277.5..270.4 (700 x 548 cm, long side along X). Before: min_z -314.2.
- The footprint fits inside the vanilla one. The long side is along X, vanilla long side is along Y: the house may be turned 90 degrees against the road. Check in the screenshots.
- Replaced meshes (paths verified in the game paks with `pakmod.py find`): `.../Buildings/Merged/SM_MERGED_C_SG_Cottage_Lv1_C_UBeam`, `..._Lv1_A_v4_UBeamFoudnations`, `..._Lv1_B_Ubeam_00`. All three are now replaced, so the variant does not matter.
- Gotcha: in one run the last copy (B) was not on disk after exit. The script now saves every copy again at the end. Check that all 3 cooked files exist.
- Pak rebuilt: 19 files, 3,338,836 bytes.

## White house (2026-10-20)
- Not the cause: the pak holds `MI_Meshy` with the textures `d`, `n`, `spec` and `AO` (checked in the cooked file, and live in the game: `TextureParameterValues` of the instance list all four). The new house component draws with `MI_Meshy`, parent `tudorWall01`. The FBX import found the base colour (`model.fbm/texture_0.png`: brown, cream and black).
- Cause of the first "white" pictures: they showed the OLD replaced houses (a row that exists at the start). The new house was not visible yet. The component `bVisible` of a new burgage house is false while it is a construction site. The plot counts as built after 1 day, the mesh shows after about 8 more days. The old scenario did not wait, and the camera did not follow the pawn while the game was paused.
- Look in the game: with the master `tudorWall01` the Meshy colours come out pale. Black beams and cream walls show. Brown wood and thatch come out white or grey. These did NOT change it: live material instance (`br` 0 to 2, `R`, `spec`, `TINT`, `proceduralPaint`, `contrast dirt`, `stretchAmt`, `isConstructing`); `spec` = black texture; alpha channel in the colour map; vertex colour override on import (the FBX import ignored it). The master `scanLuv_owidz_thatch` gave a dark, mossy house without the cream plaster. So the master stays `tudorWall01`.
- Open: a faithful colour needs a game master whose colour comes straight from the albedo map. Not found.
- Import fix: `import_replace_mesh.py` deletes the destination folder before it imports. Before, a second import kept the old textures and the old import translation.
- Pak rebuilt: 19 files, 3,338,836 bytes (3 replaced paths kept, `BASE_TO_GROUND`). No AES key in the pak or in the diff.
- Scenario: waits for `bVisible`, keeps the game at speed 1 so the camera follows the pawn, centres on the component location, turns the camera with the pawn yaw. The mod command `mesh_actors` has a new option `materials` (component name, materials with parents).

## Master swap to MegascansStandard (2026-10-20)
Tried the master of `MI_SS_Shrine5`. The colours stay pale. Details and run ids: `swap-shrines.md`. The pak was not replaced. `meshy_material.py` keeps the option `MASTER_MATERIAL=megascans` (default unchanged).
