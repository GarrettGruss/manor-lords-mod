# Master swap: MegascansStandard (task 3, 2026-10-20)

Lead: the base game instance `MI_SS_Shrine5` (`/Game/NotStronghold/Buildings/scanLuv/Jakob/SG_Shrine5/`) has parent `/Game/Megascans/MegascansStandard`. Read with `pakmod.py tojson` on the extracted copy.

## MI_SS_Shrine5 values
- Texture params: `Base` (J_Shrine5_baseTexBaked), `Normal` (J_Shrine5_normals), `AO` (J_Shrine5_occlusion).
- Scalar params: `AO` 0.7, `Roughness` 0.794286, `spec` 0.400952, `RefractionDepthBias` 0.
- Static switches: `Has roughness?` false, `Use AO` true. `Has Normal` is not overridden (master default).
- Base property override: `OpacityMaskClipValue` 0.3333.
- Other names in the master (cooked master has no expression graph, so types and defaults are not readable): `Rough`, `diff mul`, `tint`, `baked ao to vertex?`, `applyWetnessAndSnowFx`, `useVertexForSnow`, `blendSnow`, `proxyFx_snow`, `snowColor`.

## Change
`meshy_material.py` has env `MASTER_MATERIAL=megascans` (default unchanged, `tudorWall01`). It builds a stub of `/Game/Megascans/MegascansStandard` (never shipped), binds `Base`, `Normal`, `AO` (white) and the shrine scalars and switches. `import_replace_mesh.py` calls it; the env passes through.

## Result: still pale
- Run `20261020-162700-401e`: parent confirmed live (`MI_Meshy <- MegascansStandard`). The house is still white and grey, as with `tudorWall01`. Brown wood and brown thatch are not brown.
- Run `20261020-163127-2b75`: same, with `applyWetnessAndSnowFx` false, `useVertexForSnow` false, `blendSnow` 0, `proxyFx_snow` 0 (guess: the mesh has white vertex colour that drives snow). No change.
- So the pale look is not caused by the `tudorWall01` master. Not tested: the cause may be the texture alpha channel, the vertex colour of the mesh, the `tint` / `diff mul` defaults, or the game light and exposure. Next idea: set a dynamic material instance live over the bridge (`CreateDynamicMaterialInstance` on the house component) and vary `diff mul` and `tint`.
- Pak not replaced: `mod/HarnessActions/paks/meshyhouse_P.pak` is the old one (3,338,836 bytes). The Megascans paks are in `modtools/work/out/meshyhouse_P.megascans*.pak` (not in git).
