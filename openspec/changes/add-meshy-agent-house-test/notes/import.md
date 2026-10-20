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

## Texture settings check (2026-10-20)
- Source colour map `texture_0.png` (2048x2048 RGB): mean RGB 100/83/63. Brown wood, cream plaster, black beams. Not pale.
- Cooked `texture_0` (pak) and game `J_Shrine5_baseTexBaked`: same asset properties via `pakmod.py tojson`. Both PF_DXT1, no SRGB or CompressionSettings override (so defaults: sRGB on, TC_Default). Only ImportedSize and LightingGuid differ.
- So the texture import settings are NOT the cause. `fix_texture_settings` already sets sRGB true for the colour map.
- Next ideas (not tried): the mesh has no vertex colours, and the masters may use vertex colour for paint or tint (white or black default); compare with a game mesh that has vertex colours.

## Vertex colour and parameter name check (2026-10-20, run 20261020-170034-d780, probe run 20261020-170327-cce2)
- Vanilla `SM_MERGED_C_SG_Cottage_Lv1_C_UBeam` (cooked uexp): LOD0 has a colour vertex buffer (stride 4, 17065 vertices), the first bytes are `ff ff ff ff` (white). Our Meshy mesh: colour buffer stride 0, 0 vertices (none).
- Parameter names: `d`, `n`, `spec`, `AO` in our MI_Meshy match the game instance `tudorWall01_combined` (names were copied from it). Live: the house component draws `MI_Meshy <- tudorWall01`. So a name mismatch is not the cause.
- The cooked master has no expression graph (UV channel, vertex colour use not readable). Its names include `palette_buildings`, `proceduralPaint`, `TINT`, `stretchAmt`, a height map (`tudorWall01_h`) and POM.
- Live `GetTextureParameterValue` probe failed (the bridge call needs the object path string, not the returned object dict). Not repeated: the 2 run cap was used.
- Vertex colour write on import: not tried.

## Red colour map test (2026-10-20, runs 20261020-173314-97d4 and 20261020-173736-7ee9)
- Test: new env option `ALBEDO_OVERRIDE=<png>` in `import_replace_mesh.py` imports a PNG over `texture_0` (the colour map). It was a solid red 2048x2048 PNG (255,0,0). Master `tudorWall01`, `BASE_TO_GROUND`, 3 variant paths unchanged. Test pak `modtools/work/out/meshyhousered_P.pak` (not in git). The cooked `texture_0.ubulk` starts with DXT1 red blocks (`00f8 00f8`), so the pak holds red.
- Note: the FBX embeds its textures. Replacing `model.fbm/texture_0.png` on disk has no effect (the first run, 20261020-173314-97d4, still showed the original brown map in the pak). Use `ALBEDO_OVERRIDE`.
- Result: the new house is NOT red at all. It is white and grey with black beams, as before. Screenshot (not committed): `.claude/worktrees/agent-a4bbd25a7ce6f0c03/runs/20261020-173736-7ee9/screenshots/house_z600.png`.
- Live binding (same run, bridge `read_property` of `TextureParameterValues` on `MaterialInstanceConstant /Game/HarnessMod/MeshyHouse/MI_Meshy.MI_Meshy`): parameter `D` is bound to `Texture2D /Game/HarnessMod/MeshyHouse/texture_0`. `GetTextureParameterValue` is not callable through the bridge ("attempt to call a TrivialObject value"): it is not a reflected UFunction on the instance.
- Meaning: the colour map is bound in the game, but its colour does not reach the pixel. The `tudorWall01` master does not use `D` as the base colour (or the palette / `proceduralPaint` / `TINT` logic overrides it completely, or `D` is read through another UV channel or only as a mask). It is not a texture import or binding problem. Next: find which master parameter holds the real albedo (compare all texture parameters of a vanilla `tudorWall01` instance), or use a master that is known to show its albedo.

## Plain engine material test (2026-10-20, run 20261020-180539-51d7)
- New env option `MASTER_MATERIAL=basicshape` in `meshy_material.py` (default unchanged). The instance `MI_Meshy` has parent `/Engine/BasicShapes/BasicShapeMaterial` (in the game paks, `pakmod.py find`) and the vector parameter `Color` = red (1,0,0). No textures. Test pak `modtools/work/out/meshyhousebs_P.pak` (10 files, 1,053,540 bytes, not in git).
- Result: the new house IS red (orange-red) in all pictures. Picture (not committed): `runs/20261020-180539-51d7/screenshots/house_z600.png` (also `house_side_a.png`). The old replaced houses in the row are red too.
- Live (component `SMBuilding_2147457199.StaticMeshComponent0`): `GetNumMaterials` 1, `GetMaterial(0)` = `MI_Meshy`, `OverrideMaterials` empty, `StaticMesh` = our replaced `SM_MERGED_C_SG_Cottage_Lv1_A_v4_UBeamFoudnations`. Nothing replaces our material at run time.
- Meaning: a cooked material instance of a game or engine master draws in the game, and the mesh, UVs and binding are fine. The masters `tudorWall01` and `MegascansStandard` do not show our colour map as the base colour. Next step: a game master that draws a plain base colour texture (a master with a texture parameter and no palette or paint logic), or use `Color` from BasicShapeMaterial with a vertex colour or a texture through another engine master.
