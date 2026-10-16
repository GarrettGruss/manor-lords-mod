# Spike: a large ox shed from Meshy (2026-10-15)

Spec 21, issue #102. Branch checked out: `main` (nothing committed). No save function was called. No key is in any file.

## Cost
| Item | Value |
|---|---|
| Balance before | 1080 credits |
| Balance after | 1050 credits |
| Meshy multi-image-to-3d, `meshy-6`, 2k PBR, target 3000 triangles | 30 credits (task `01a141f4-38ac-74b0-91a5-4c9b2532cc4a`) |
| Total | 30 credits (cap 150 for this task, 60 per call) |
| Gemini | 2 reference views (`runs/genmesh/oxshed/view1.png` front, `view2.png` three-quarter) |

Problem: the first `genmesh.py multi` call hit my 110 s shell timeout. The task had already started and was paid, but the log line is written only at the end. I did not call again. I read the task id with `GET /multi-image-to-3d`, waited, downloaded, and wrote the log line by hand (`note: recovered after client timeout`). Fix to do: write the log line when the task is created, and let `genmesh.py` resume a task id.

## Mesh
- Files: `runs/genmesh/oxshed/model.fbx` (17.2 MB), `model.glb`, 5 maps (git-ignored).
- UE import (headless, UE 5.5.4): `/Game/HarnessMod/OxShed/SM_BigOxShed`, 5196 vertices, size 817 x 314 x 300 cm, base at z 0, centred on x and y. One material, 5 textures (1024 / 512 caps).
- Blueprint `BM_BigOxShed`: one part `MainBld_900`, scale (0.75, 1.6, 1.0). Footprint about 613 x 503 cm. The scale is not uniform, so the planks look stretched in Y.
- Pak `bigshed` (23 files, 3,070,293 bytes): `modtools/work/out/bigshed_P.pak`, copy at `mod/HarnessActions/paks/bigshed_P.pak` (not committed). Row 125 = clone of row 97: `stableSpace` 4, Bounds 700 x 700, `maxHp` 150, visible, class `BM_BigOxShed_C`. The AES key came only from the environment. The diff has no key.
- Note: the pak buildingStats name map still holds one unused string with a bad path from my first (Git Bash mangled) edit. It is not used by the row. Set `MSYS_NO_PATHCONV=1` and use Windows paths for the JSON argument.

## In the game (run `s21b-1`, `noop --keep-open --pak bigshed`)
- Ghost of row 125 at (0.35, 0.3): white. Real click placed it. Built after 14 game days at speed 3.
- Mesh shows: a long open-fronted shed with a pitched roof, posts and stall walls. Screenshots (git-ignored) `runs/s21b-1/screenshots/shed_near.png`, `shed_mid.png`, `ghost125.png`.
- Look: the texture is grey and flat, not the brown thatch and wood of the reference. The game was in winter (Dec 8, snow), so snow tint may play a part. Not proven. The roof has faceted dents (low poly). Open: compare in summer.
- Verdict: the geometry and scale work. The texture needs a check in summer.
