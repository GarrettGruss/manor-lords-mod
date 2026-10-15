# Spec 21: Mesh generation (Meshy and Blender)

Status: Draft: research only. No code, no API call, no account yet.
Notes: `implementation-notes/meshy-research.md`.

## Goal

Find out if we can make new 3D parts for mod buildings with an AI tool (Meshy) or with Blender scripts.
Target: give the Siege Camp (row 483) a finished mesh and a construction mesh, and add props (ladder, crates, fence).

## Non-goals

- No hand-made art pipeline for the whole game.
- No rigged or animated models.
- No release of generated assets before the license check is done (see Open questions).
- No use of Meshy by mods or scenarios at run time. It is an offline tool.

## Findings in short (details in the note)

- Meshy has a REST API (Bearer key). API access needs a paid plan (Pro, 20 USD per month, 1000 credits). The free plan has no API.
- Cost: image-to-3D with a texture is 30 credits (about 0.60 USD at Pro). Text-to-3D is 20 (preview) + 10 (refine). Remesh 5.
- Output: GLB, FBX, OBJ, USDZ, STL, 3MF (and BLEND for remesh). PBR maps on request. Polycount 100 to 300000.
- License: paid plans are private and customer owned (no credit needed). Free plan is CC BY 4.0 (credit needed). A public GitHub mod is allowed with a paid plan, or with credit to Meshy. Verify the live wording before release (open question).
- Fit: good for tents, carts, crates, ladders. Weak for exact scale, collision, LODs and the game's photo-based textures. Expect manual cleanup.

## Plan

1. Spike A (first): one asset, the siege ladder, from a Gemini reference image. See the note, section "First spike proposal".
2. If A works: `harness/tools/genmesh.py` (like `genimage.py`): key from `MESHY_API_KEY` (env or Windows user scope), never printed, credit cap per call and per day, log in `runs/genmesh/log.jsonl`.
3. `mod/HarnessActions/ue/import_mesh.py` (headless UE 5.5.4): `unreal.AssetImportTask` for FBX, scale to cm, import textures and make a material.
4. Extend `make_bm.py` to take parts from a list and name them `MainBld_`, `Bld_`, `clutter_`, `res_`.
5. Cook, pack, test in game with screenshots (as in spec 18).
6. Compare with a Blender script route for simple boxes and planks (no cost, exact scale).

## Open questions

- Exact license text. The `/terms` page was not readable. Read the terms in the account or ask Meshy support before release.
- Does an AI-made PBR texture look right next to the game's photo textures? Maybe reuse vanilla materials and use Meshy for geometry only.
- Is Pro enough? Spike A needs less than 200 credits.
- Are UV and normal conventions right in UE 5.5.4 after FBX import (flip green channel)?
- Does the BM master need collision or only visuals?

## Acceptance criteria

- A note records the real cost and quality of the first spike.
- One generated mesh shows in the game, at the right scale, in a screenshot taken by the harness.
- The license decision for a public release is written down with its source.
- No key in git (grep the diff). Spend is logged and capped.
