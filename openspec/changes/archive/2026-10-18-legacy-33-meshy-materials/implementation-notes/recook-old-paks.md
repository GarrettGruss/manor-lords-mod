# Re-cook of the older Meshy paks (2026-10-18)

Issue #237, branch `fix/33-recook-meshy-paks`. No new Meshy credits. Game 0.8.111, `--slot auto`, no mouse, no eval, no save call.

## Steps
1. `retarget_material.py` (`MESH_PATH`) on SM_BigOxShed, SM_Wagon, SM_KeepTent and SM_WeaverShed in the UE workspace `mlm-ue`. Each folder now has `MI_Meshy`. SM_Wagenburg already had it.
2. One cook (`-run=cook ... -nopak -skipeditorcontent`).
3. `harness/tools/recook_meshy_pak.py <old pak> <new name> <mesh folder>`: unpack the old pak, delete `Material_001`, `texture_0_emission`, `texture_0_metallic`, copy the cooked `MI_Meshy`, `texture_0`, `texture_0_normal`, `texture_0_roughness`, build with `pakmod.py build`. Data files (buildingStats, merged mesh replacements) are kept from the old pak.
4. No AES key in any pak or in the diff (byte grep, 0 matches).

## Paks (in `mod/HarnessActions/paks/`)
| Pak | Spec | Bytes | Note |
|---|---|---|---|
| `wagen_P.pak` | 30 | 3,065,344 | replaces the grey one. `wagenmat_P.pak` is removed: it was the same fix. |
| `s32wall_P.pak` | 32 | 3,221,811 | wall piece swap |
| `s32keep_P.pak` | 32 | 2,925,705 | keep swap |
| `bigshed_P.pak` | 21 | 2,716,182 | |
| `weavermesh_P.pak` | 31 | 2,615,893 | new in the repo (was only in `modtools/work31/out`). `weaver106` (data + same mesh) is not re-cooked. |

Not re-cooked: `ladder140_P.pak` (spec 21 siege ladder mesh in `Meshes/`), not in the task.

## Runs
| Run | Scenario and pak | Result |
|---|---|---|
| `20261018-143146-ced8` | `probe-wagenburg` + `wagen` | pass. Screenshot `recook-wagen.png`: dark wood with light canvas. |
| `20261018-143353-8775` | `probe-manor-wagenburg` (fixture `manor-closed`) + `s32wall` + `s32keep` | pass. Wall: `recook-wall.png`. The keep was not placed here (mesh option missing). |
| `20261018-143606-e69f` | same, `HARNESS_MESH` with a `.Name` suffix | pass, keep refused (wrong path form). |
| `20261018-143826-94e6` | same, `HARNESS_MESH=/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_Manor_MainTower_Lv1_New`, `HARNESS_KEEP=1` | pass, keep placed. `recook-keep.png`: light canvas tent next to the manor house. |
| `20261018-144236-e178` | `probe-wagenburg` + `bigshed`, `HARNESS_BM=BM_BigOxShed` | pass. `recook-bigshed-new.png`. |
| `20261018-144534-44fa` | same with the old pak (control) | pass. `recook-bigshed-old.png`. |
| `20261018-144829-61b1` | `probe-extension` + `weavermesh` (`HARNESS_PROBE_FOCUS=TailorShed`, ext 6) | pass. `recook-weaver.png`. |

`probe-wagenburg` got an option `HARNESS_BM` (Blueprint asset name in the pak) so it can show another Meshy Blueprint.

## Fresh import
`import_mesh.py` on the existing weaver FBX (`MESH_DEST=/Game/HarnessMod/FreshImport`, scratch folder, deleted after): log `MATERIAL instance .../FreshImport/MI_Meshy parent .../tudorWall01 slots 1`, no `Material_001` left. `import_replace_mesh.py` has the same `meshy_material.make_game_material(mesh, DEST)` call (line 59). It was not run (same call, no new Meshy FBX).

## Honest limits
- The ox shed and weaver textures are themselves grey-brown. The new and old ox shed screenshots look almost the same at this distance, so they show "loads, no crash, textured material", not a clear before and after. The wagons show the clear difference (spec 33 pictures).
- The weaver shed still looks light grey-blue in the game. The base colour map is dark grey-brown. The `spec`/`AO` mapping is still a guess (see `cause-and-fix.md`). Tune by eye later.
- The keep tent is a pale canvas, plausible for its texture.
