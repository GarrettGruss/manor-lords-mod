# Import and pak (task 2.2, 2026-10-19)

- Import: `mod/HarnessActions/ue/import_replace_mesh.py` headless in UE 5.5.4 (project `mlm-ue`). Env: `MESH_NAME=SM_MeshyHouse`, `MESH_DEST=/Game/HarnessMod/MeshyHouse`, `TARGET_CM=700`.
- Replaced vanilla mesh: `/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_Cottage_Lv1_C_UBeam`. It is the mesh of the burgage house blueprint `BM_SG_Cottage_Lv1_C` (`CPP_BP/BuildingMasterAssemble/Residential/`).
- The level 1 cottage has 3 variants. A and B use `SM_MERGED_C_SG_Cottage_Lv1_A_v4_UBeamFoudnations` and `SM_MERGED_C_SG_Cottage_Lv1_B_Ubeam_00`. Only variant C is replaced. The test scenario must build a burgage plot house and check which variant it got, or A and B must be replaced too.
- Result: longest side 700 cm (548 x 628 cm high), scale 7.292, 3210 vertices, 1 material (`MI_Meshy`, an instance of the game master). Textures capped at 1024 and 512.
- WARNING: the import log shows `min_z -314.2`. The mesh pivot is at the centre, not on the ground. The house may sink half into the ground. Check in the screenshots. Fix with a z offset on import if needed.
- Cook: `-run=cook ...` with `+DirectoriesToAlwaysCook=(Path="/Game/ManorLords/Buildings/Merged")`. The cooked files exist.
- Pak: `meshyhouse_P.pak`, 13 files, 2,550,027 bytes. Build folder `modtools/work/meshyhouse/` (not in git). Copies: `mod/HarnessActions/paks/meshyhouse_P.pak` and `modtools/work/out/meshyhouse_P.pak`. `pakmod.py build` verified that the pak lists the same 13 files as the folder.
