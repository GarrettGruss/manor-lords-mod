# Spec 21: Mesh generation (Meshy and Blender)

Status: spec written (2026-10-14). Spike A is ready to start when the user has Meshy Pro and `MESHY_API_KEY` is set. Issue: #102.
Branch: `feat/21-mesh-generation`. Research: `implementation-notes/meshy-research.md`.

## Goal

Make new 3D parts for mod buildings with an AI tool (Meshy), and put them in the game through the spec 18 pipeline
(UE 5.5.4 headless import, a `BM_` class, cook, pak).
First target: a siege ladder prop. Later target: a finished mesh and a construction mesh for the Siege Camp (row 483, #94).

## Non-goals

- A hand-made art pipeline for the whole game.
- Rigged or animated models.
- A release of generated assets before the license check (see Open questions).
- Use of Meshy by mods or scenarios at run time. It is an offline tool.

## Known facts (from the research note)

- Meshy has a REST API with a Bearer key. API access needs a paid plan (Pro, 20 USD a month, 1000 credits).
- Cost: image-to-3D with texture 30 credits, text-to-3D 20 + 10, remesh 5.
- Output formats: GLB, FBX, OBJ, USDZ. PBR maps on request. Polycount target 100 to 300000.
- License on paid plans: the output is owned by the customer. Free plan: CC BY 4.0. Verify the live terms.
- A new `BM_` class works in the game when its components are named `MainBld_`, `Bld_`, `clutter_` or `res_` (spec 18, `siege-camp-and-bm.md`).

## Spike A: siege ladder

1. Tool `harness/tools/genmesh.py`, built like `genimage.py`:
   - Key from `MESHY_API_KEY` (environment, else Windows user scope). Never printed or written.
   - Commands: `--image-to-3d` and `--multi-image-to-3d` with a polycount target, PBR on, FBX out; `--status`; `--balance` if the API gives it.
   - Poll the task, download the result to `runs/genmesh/<name>/`.
   - Credit cap per call and per day (constants). Every call is logged in `runs/genmesh/log.jsonl` with credits used.
   - Fake tests with a fake HTTP layer (no network in tests).
2. Reference images: 2 views (front, side) of a medieval wooden siege ladder with `genimage.py`, plain background, no text.
3. Generate: multi-image-to-3D, target about 2000 triangles, PBR 2k, origin at the bottom.
4. Import: `mod/HarnessActions/ue/import_mesh.py` runs headless in UE 5.5.4 (`unreal.AssetImportTask`, FBX, scale to cm, textures and one material) into `/Game/HarnessMod/Meshes/`.
5. Build: extend `make_bm.py` to take a part list; make `BM_SiegeLadder` with one part `clutter_ladder`.
6. Data: clone a small row (for example row 87) as a new type id, point it at `BM_SiegeLadder`, `bVisibleInUi` true.
7. Game: place the new type with build mode and a real click on a white ghost, let it build, take screenshots near, mid and far, next to a vanilla tent for scale.
8. Write the result in `implementation-notes/spike-a-ladder.md`: credits used, triangles, look, scale, problems.

## Spike B (after A): Siege Camp content

Use the same pipeline for a main tent part and a construction mesh for row 483. Test whether the Siege Camp then gets built (#94).

## Open questions

- The exact license text (the terms page was not readable by the agent). The user checks it in the account before any release.
- Does an AI PBR texture look right next to the game's photo textures? Option: reuse a vanilla material and take only the geometry.
- Are the normal map and UV conventions right after FBX import in UE 5.5.4?
- Does a prop part need collision?

## Acceptance criteria

- [ ] `genmesh.py` exists with fake tests, a credit cap and a spend log. No key in git (diff grep run before each commit).
- [ ] One Meshy mesh shows in the game as a building part, at the right scale (within 10 % of the expected size), base on the ground, no missing texture, at most 3000 triangles, in a harness screenshot.
- [ ] The note records credits used, quality and problems, and a verdict (use Meshy, use Blender, or both).
- [ ] The license decision for a public release is written down with its source.
