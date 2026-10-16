# Spike A: a Meshy siege ladder in the game (2026-10-14)

Spec 21, issue #102. Game 0.8.111, fixture `base`, single player. 1 game launch (run `s21a-1`, `noop --keep-open --pak ladder140`).
No save function was called. The game is closed and `~mods` is removed. No key is in any file.
Screenshots are in git-ignored `runs/s21a-1/screenshots/`.

## Result in short
The mesh shows in the game, stands on the ground, and the type is placed and built from a real click. Verdict: **Meshy for the shape and the texture, with a size fix in UE; Blender for exact boxes**. Details below.

## Cost
| Item | Value |
|---|---|
| Balance before (`GET /openapi/v1/balance`) | 1110 credits |
| Meshy multi-image-to-3D, `meshy-6`, 2k texture, PBR, 2000 triangles target | 30 credits (task `01a13d51-e3cf-752c-9fd0-5138d345e7b2`) |
| Total used | 30 credits (cap was 200). One try was enough. |
| Gemini | 2 images (`runs/genmesh/ladder/view1.png`, `view2.png`) |
| Log | `runs/genmesh/log.jsonl` |

Meshy API as called: `POST /openapi/v1/multi-image-to-3d` with `image_urls` as base64 data URIs, `ai_model meshy-6`, `enable_pbr`, `texture_resolution 2k`, `should_remesh`, `topology triangle`, `target_polycount 2000`, `target_formats [fbx, glb]`, `auto_size`, `origin_at bottom`. Poll `GET /:id` until SUCCEEDED. The task finished well within the poll limit.

## Pipeline steps
1. `harness/tools/genmesh.py` (caps 60 per call, 200 per day, 4 fake tests in `harness/tests/test_genmesh.py`).
2. Reference views: view 1 is a ladder leaning on a wall with a stone slab at its foot. View 2 is the ladder lying at an angle. The two views do not show the same angle, and the slab ended up in the mesh (see Look).
3. Download: `model.fbx` 15.9 MB (embedded maps), `model.glb` 11.9 MB, 5 PBR maps (2k). All in git-ignored `runs/genmesh/ladder/`.
4. `mod/HarnessActions/ue/import_mesh.py` in the UE 5.5.4 workspace, headless. UE used the Interchange importer. It made 1 static mesh, 1 material (`Material_001`) and 5 textures.
5. Texture caps: base colour and normal 1024, roughness, metallic and emission 512. This takes the pak from 17.1 MB to 2.97 MB. The cap is set in the import script (`max_texture_size`).
6. `make_bm.py` now takes a part list (`BM_PARTS` JSON). `BM_SiegeLadder` has one part `clutter_900`.
7. Cook (`-run=cook`), copy to the pak work folder, `pakmod.py build ladder140`. Pak `mod/HarnessActions/paks/ladder140_P.pak` (2,968,318 bytes, 23 files).
8. Row 140 = clone of the tent row 87 with `BlueprintPath` `/Game/HarnessMod/BM_SiegeLadder.BM_SiegeLadder_C` and `bVisibleInUi` true (`s65_edit_json.py stats`, `blueprint`, `visible`). Id 140 was free in vanilla (vanilla uses up to 122 near here) and in the earlier paks (123 to 125).

## Mesh numbers (from the UE import log)
| Check | Value |
|---|---|
| Bounds | 231 x 212 x 300 cm (X, Y, Z), `min z` 0.0 (base on the ground) |
| Vertices | 3500. The triangle count is about the 2000 target (not counted directly; UE reports vertices). |
| Expected size | about 400 cm long (research note). The ladder leans, so its length is about 367 cm (sqrt(212^2 + 300^2)). That is within 10 percent of 400. |
| Material count | 1 |
| Textures | 5, capped as above |

## In the game
| Check | Result |
|---|---|
| Type 140 placed with `activateBuildingMode(140)` + real click | YES, at fraction (0.43, 0.27), on open grass at a road bend. The ghost was WHITE there (`runs/s21a-1/screenshots/g6.png`). Six other spots were orange hatched (near houses, fences or plots) and not clicked. |
| Master | `SMBuildingMaster` type 140, region Nusslohe, 1 part (`clutter` prefix works), `buildingFunction` 7 (from the tent row). |
| Built | YES: `constructed` true after 4 game days (17 s wall time at speed 3). No cost. |
| Mesh visible | YES. A grey-brown wooden ladder leans on the ground. Screenshots: `far` = `mid.png`, `mid` = `near2.png`, `near` = `near.png` (zoom by mouse wheel, `harness/tools/s21_view.py`). |
| Next to vanilla tents | Two vanilla camp tents are in `near2.png` (top and right) at the same zoom. The ladder looks about 3 m tall next to the huts, as planned. |
| Missing texture (pink or white) | No. The texture shows (wood grain on the rails). |
| Frame time | Not measured (one ladder, no visible change). Open point. |

## Look
- At near zoom the ladder reads as a ladder with rungs and a worn grey-brown wood. The AI texture is a little brighter than the game's muted wood.
- The foot of the ladder has a light grey-white lump. It is the stone slab from reference view 1. Use a reference without a base next time (ask for "no ground, floating object").
- The tent is shown from the same camera, so the style gap is small at game zoom. It would show more at the closest zoom.

## Problems
- `run.py --keep-open --pak` ends with `harness_error` (`paks-remove` cannot delete the pak in use). This is known (spec 18 notes). The pak was removed after the game closed.
- The wheel zoom is cumulative between helper calls. The helper `s21_view.py` calls the wheel by `mouse_event`.
- The camera centre can drift after a big zoom. Re-centre after the zoom (the helper does).
- Ghost validity is read from the screenshot. Orange hatched means invalid. The vanilla tent (87) ghost was also orange at its first spot (`t87.png`), so the colour tracks the spot, not the type.
- No collision check, no LOD, no build-menu card, no name text. A construction mesh was not made.
- The Meshy FBX is large (15.9 MB) because the maps are embedded. It is not committed.

## Verdict
- Geometry: good enough. Keep Meshy for organic or detailed props (ladder, sacks, carts).
- Texture: acceptable. For a closer match, use the vanilla materials or a muted retexture. Not tested.
- Blender: still useful for exact boxes, planks and fences (no cost, exact scale).
- Both. Meshy cost 30 credits (about 0.60 USD at Pro) for one prop.

## Not verified
- Frame time with many props. LODs. Collision. License wording (still open in the README). A second try with a cleaner reference.

## Changes outside the repo
- UE workspace `mlm-ue\ManorLords`: `import_mesh.py`, `make_bm.py`, assets `Content/HarnessMod/Meshes/*` and `BM_SiegeLadder`.
- `modtools/work`: `ladder140`, `out/ladder140_P.pak`, and `json/.../buildingStats.json.vanilla` (the vanilla JSON was restored after the edit).
- Game folder: `~mods\ladder140_P.pak` installed, then removed.
