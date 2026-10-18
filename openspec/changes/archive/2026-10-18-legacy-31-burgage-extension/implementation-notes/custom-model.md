# Custom model for the extension (2026-10-18)

## Pipeline (all headless, no mouse for the model)
1. Two reference views with `genimage.py` (Gemini): a small weaver's workshop shed, loom, wool basket, plain background (git-ignored `runs/genmesh/weaver/view1.png`, `view2.png`).
2. `genmesh.py multi --polycount 3000`: Meshy task `01a14f0b-19ed-7776-99a6-2b42c0a6bac2`, 30 credits (one call, about 6 minutes). Result `model.fbx` (16 MB) and 5 maps.
3. UE 5.5.4 headless: `mod/HarnessActions/ue/import_replace_mesh.py` imports the FBX, scales it so the longest floor side is 420 cm, caps textures (1024 / 512), and copies the mesh to the asset path of the vanilla tailor shed: `/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_Ext_TailorShed_Ubeam`. Result: 420 x 356 x 318 cm, 5237 vertices, 1 material, 5 textures. In Git Bash set `MSYS_NO_PATHCONV=1`, or `/Game/...` becomes a Windows path and the import fails.
4. Cook: the project cooks only `/Game/HarnessMod` and `BuildingMasterAssemble` on its own. The replaced mesh is cooked with the extra argument `-ini:Game:[/Script/UnrealEd.ProjectPackagingSettings]:+DirectoriesToAlwaysCook=(Path="/Game/ManorLords/Buildings/Merged")`. The project config does not change.
5. Pak `weavermesh` (19 files, 2,970,004 bytes, sha256 starts `9773805b`): the replaced mesh (`.uasset`, `.uexp`) plus the material and textures under `HarnessMod/Weaver`. The pak replaces the vanilla asset by path, so no part blueprint and no table row are needed.

## In the game (runs s31-mesh-1, s31-mesh-2, s31-mesh-3, all pass, no crash)
- The tailor extension (Type 6) shows the new shed in place of the vanilla one. Screenshot (git-ignored): `runs/s31-mesh-3/screenshots/focus_built_z900.0.png`. Zoom without the mouse: write the pawn property `zoomLevel` (cm of camera distance, minimum 350, default 9000) and centre the camera with `centre_camera_on`.
- Look: a pitched-roof open shed of about the right size, next to the vanilla fence and sheds. The surface is flat grey, not the brown thatch and wood of the reference. This matches the ox shed result of spec 21 (grey texture). Not tested: another season, or a material fix.
- The tailor extension keeps the rest of its part list. The new mesh replaces only the shed part.

## What this gives and what it does not
- Gives: a custom model for an existing extension slot, shipped as a plain asset replacement.
- Does not give: a model for a new extension type (Type 17 has no parts, see `new-extension-number.md`). The `workpos` and `res_*` parts stay in the vanilla blueprint, so the worker stands where the vanilla tailor stood and the loom of the model is only a picture.
