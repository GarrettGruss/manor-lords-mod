# Cause and fix

## Cause
The UE FBX import makes a plain `Material` (PBR graph, correctly wired in the editor; checked with `MaterialEditingLibrary`). The cook writes its shader code into a shader library file (`ShaderArchive-ManorLords-PCD3D_SM5.ushaderbytecode`), not into the material. A mod pak ships only `.uasset`, `.uexp` and `.ubulk`. The game's own library (`ShaderArchive-ManorLords_Chunk0-*`) has no code for the new material. The game draws a fallback grey. The cooked material is only 8 KB for this reason. Setting `bShareMaterialShaderCode=False` did not change the 8 KB file (tested), so inline code is not an easy route.
The textures themselves were cooked and packed (`.ubulk` present). The Meshy base colour map is itself grey-brown with light patches, so a wrong render looked "grey".

## Fix
Use a material INSTANCE of a game master material. The game already has the shader code for it.
- Master: `/Game/NotStronghold/Buildings/TudorWall/tudorWall01`. Texture parameters `AO`, `d`, `n`, `spec`. Scalars `aoFromGroundFade` 512, `br` 0.5, `dirt tiling` 2, `n str` 0, `R` 1, `spec` 0.2. Static switches `Dirt?` false, `spec map?` true. All read from the game's own instance `tudorWall01_combined`, so the shader permutation exists.
- `mod/HarnessActions/ue/meshy_material.py` makes a stub master at that path in the UE project (never shipped), makes `MI_Meshy` in the asset folder (d = base colour, n = normal, AO = white, spec = roughness), sets sRGB on the colour map and normal-map compression on the normal map, assigns it to the mesh and deletes the imported material.
- `import_mesh.py` and `import_replace_mesh.py` call it. `retarget_material.py` fixes an already imported mesh (`MESH_PATH`).
- Pak: copy only `MI_Meshy`, the mesh, `texture_0`, `texture_0_normal`, `texture_0_roughness` (not emission, metallic, and not the stub master). Pak `mod/HarnessActions/paks/wagenmat_P.pak` (3,065,373 bytes, 17 files; no AES key, byte grep).

## Proof
Probe `probe-wagenburg --pak wagen` (before) run `20261018-141100-8f90`; `--pak wagenmat` (after) run `20261018-141940-2d36`. Screenshots in this folder: `before-grey.png` (far, vanilla-material pak), `after-instance.png` (ring of wagons now dark wood with light canvas patches, matching the texture). Full set is in git-ignored `runs/<id>/screenshots/`.

## Open
- The `spec` and `AO` mapping is a guess (roughness, white). Tune by eye.
- Old paks (ox shed, weaver, wall, keep tent) need a re-import with the new script and a re-cook. Not done here.
- Screenshots copy screen pixels; other game windows can cover them.
