# Per-manor reskin from Lua (2026-10-18, part 2)

Spec 32, issue #233. Question (user): can a normal manor become a Wagenburg manor without changing the player's other manors?
Answer: YES for one manor, selected by its master id. The pak adds the wagon and tent as NEW assets. Lua sets the static mesh. The wall keeps its collision and gate.

## Method
- Pak `s32lua_P.pak` (26 files, 5,359,928 bytes): `/Game/HarnessMod/WagonM/SM_Wagon` and `/Game/HarnessMod/TentM/SM_KeepTent`, each with a material instance `MI_Meshy` (spec 33: instance of the game master `tudorWall01`; textures `texture_0`, `_normal`, `_roughness`). No vanilla path is replaced. Same Meshy models as part 1 (no new credits). Imported with `import_mesh.py` (scale 0.569 and 1.6994), cooked without the extra `DirectoriesToAlwaysCook` argument. No AES key in the pak (byte grep).
- New module `mod/shared/HarnessWagenburg` (commands in HarnessActions 59): `wagen_state` (parts of each manor by mesh), `wagen_apply {manor, wall_mesh, keep_mesh}`, `wagen_revert`.
  - Pak meshes load with the asset registry call (`AssetRegistryHelpers:GetAsset`, class StaticMesh) and are rooted. `LoadAsset` alone does not load pak assets (first try `s32b-1`: "mesh not found").
  - Wall: the `SMBuilding` actors whose `buildingMaster` is the chosen manor and whose mesh is the palisade piece. `SetMobility(Movable)` then `SetStaticMesh`.
  - Keep: the keep is a module with its own master, so it is found by distance (6000 cm) to the manor. Three actor kinds show the keep mesh and all three must change: `SMBuilding` (built), `StaticMeshActor` (the blueprint actor from `manor_blueprint_add`) and `GhostStaticMeshActor`. With only the `SMBuilding` changed (`s32b-4`, `s32b-6`) the vanilla tower stayed visible and the tent stood inside it.

## Runs (fixture `manor-closed`, no mouse, no eval, no save call, `--slot auto`)
| Run | What | Result |
|---|---|---|
| `s32b-own-base`, `s32b-own-manor-closed` | list manors (type 98) | one manor in each save. No AI-owned manor exists in these fixtures. |
| `s32b-1` | Lua wall, first try | mesh not found (asset registry needed) |
| `s32b-2` | Lua wall, path test | 56 of 56 wall pieces changed. Wagons on the ring (`screenshots/ring_c.png`). Obstacles 337. 0 wall crossings, first bandit inside at sample 27, 1.2 m from the gate, 18 of 18 inside (`s32_track_report.py`). |
| `s32b-3` | same, with a WRONG manor id (1) | `changed` 0 and 0. The ring keeps the palisade (`screenshots/ring_c.png`). The pak alone changes nothing. (Run ended `harness_error`, a Windows file lock on the bridge file in teardown, after the screenshots.) |
| `s32b-4`, `s32b-6` | keep mode (mouse-free keep, then apply) | the wall pieces were palisade again after the keep build (see below). Keep: only the `SMBuilding` changed, old tower still visible. |
| `s32b-7` | keep mode, apply wall and keep after the build | 56 wall pieces and 6 keep actors changed. Wagon ring and tent keep, vanilla tower gone (`screenshots/keep_z3000_c.png`). No crash. |

## Findings
1. The manor commit (adding the keep) rebuilds the manor parts. The wall pieces went back to the palisade mesh (`wagen_state` counted 56 palisade again in `s32b-4`). So the Lua reskin is not permanent. The mod must apply it again after every manor commit. A save load builds the parts again too, so it must also run after a load. Not tested: no save call is allowed here, so a real load was not run. Expect the same reset.
2. Collision and path are native obstacle data, so they did not change (337 obstacles, same entry by the gate).
3. Per-manor selection works by master id. It was tested on the only manor of the fixture. A second manor (player or AI) was not available, so "the player's other manor keeps the palisade" is shown only by the wrong-id run (`s32b-3`).
4. Looks: the wagons render dark grey with a lighter cover, a little darker than part 1. The tent is still blue-grey. The spec 33 material instance made little visible difference at this zoom. Tuning of `spec` and `AO` (spec 33 open point) is not done.
5. Option 2 (new building rows cloning the wall and keep rows): not tested. A new row needs a new Blueprint and the wall tool has no card for a new wall type (spec 14 and part 1), so Lua mesh swap is the practical per-manor route.

## What a mod needs
- Pak with the two meshes. A hook or a timer that runs `wagen_apply` for the chosen manor after a load and after each manor commit (for example when `manor_state` or the part count changes). About 60 lines of Lua are in `HarnessWagenburg`; the hook is not written.
- Pick the manor by id each time (ids change between loads: `2147469792`, `2147469808`, `2147469862` in three loads of the same fixture). Use the region manor (`is_region_manor`) or a stored region name.
