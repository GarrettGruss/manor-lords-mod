# Meshy research (2026-10-14)

Static research from official pages. No account, no API call, no download.
Part of spec 21. Pages differ in places, so check the price before you buy.

## Sources (all read 2026-10-14)

- https://docs.meshy.ai/en (overview, models, formats)
- https://docs.meshy.ai/en/api/text-to-3d
- https://docs.meshy.ai/en/api/image-to-3d
- https://docs.meshy.ai/en/api/multi-image-to-3d
- https://docs.meshy.ai/en/api/remesh
- https://docs.meshy.ai/en/api/pricing (credit table)
- https://docs.meshy.ai/en/api/rate-limits
- https://www.meshy.ai/pricing (plans)
- Search summary of https://docs.meshy.ai/faq and https://intercom.help/meshy/en/articles/16102098-can-i-use-meshy-assets-commercially . Our fetch of the intercom page and of `meshy.ai/terms` returned 404, so the license wording below comes from the search summary only.

## 1. API

Base URL `https://api.meshy.ai`. Auth: `Authorization: Bearer <key>`.

| Job | Endpoint |
|---|---|
| Text to 3D, preview and refine | `POST /openapi/v2/text-to-3d` (`mode` preview or refine) |
| Image to 3D | `POST /openapi/v1/image-to-3d` |
| Multi-image to 3D (1 to 4 images) | `POST /openapi/v1/multi-image-to-3d` |
| Retexture | texturing API (10 credits) |
| Remesh | `POST /openapi/v1/remesh` |
| Rigging, animation | own API sections exist (5 and 3 credits). Not needed here. |

Each family has `GET /:id`, a list `GET`, `DELETE /:id` and `GET /:id/stream` (server-sent events).
Create calls return `{"result": "<task id>"}`. Poll `GET /:id` until `status` is SUCCEEDED, FAILED or CANCELED (also PENDING, IN_PROGRESS; `progress` 0 to 100). The task has `model_urls`, `texture_urls`, `consumed_credits`. Failed tasks cost 0. Deleting a PENDING task refunds it.

Parameters that matter to us:
- `ai_model`: `meshy-6-lite`, `meshy-6`, `meshy-7.1` (= `latest`), `meshy-t2` (smart topology, made for real-time use, triangles only).
- `target_polycount`: 100 to 300000 (smart topology 100 to 15000, default 4000). `topology` triangle or quad. `should_remesh` is off by default on Meshy 6 and 7.
- `enable_pbr`: metallic, roughness, normal maps. `texture_resolution` 2k, 4k, 8k.
- `texture_prompt` or `texture_image_url` to guide the texture.
- `target_formats`: glb, obj, fbx, stl, usdz, 3mf (remesh also blend).
- `auto_size` and `origin_at` (bottom or center) for real height and pivot. Some size options are marked deprecated.

Rate limits (paid tiers): 20 requests per second. Queued tasks: Pro 10, Studio 20, Premium 30, Ultra 100. Over the limit gives 429 (`Retry-After`). Limits are shared with the web app. Errors: 400, 401, 402 (no credits), 404, 429.

Credits per call (api/pricing):

| Call | meshy-7.1 / meshy-6 | meshy-6-lite | meshy-t2 |
|---|---|---|---|
| Text preview (mesh) | 20 | 5 | 5 |
| Text refine (texture) | 10 (2k/4k), 15 (8k) | same | same |
| Image to 3D, mesh only | 20 | 5 | 5 |
| Image to 3D, 2k or 4k texture | 30 | 15 | 15 |
| Image to 3D, 8k texture | 35 | - | 20 |
| Multi-image, 2k or 4k texture | 30 | 15 | not offered |
| Retexture | 10 / 15 | | |
| Remesh | 5 | | |

Meshy 7.1 with `geometry_resolution` 2k or 4k: +5.

Plans (meshy.ai/pricing): Free 0 USD, 100 credits, no API. Pro 20 USD per month (10 first month), 1000 credits, API. Premium 40 USD, 3000. Ultra 100 USD, 8000. Studio 70 USD plus 10 per seat, 5500 shared. Enterprise custom. One textured image-to-3D asset (30 credits) costs about 0.60 USD at Pro.

## 2. License

- Free plan: output is CC BY 4.0. Commercial use is allowed with credit to Meshy.
- Paid plans: the user owns the output (private, no credit needed). The summary says this holds if the model is not published to the Meshy Community. Rights stay after a downgrade.
- Meshy says you own your assets only if your inputs do not infringe copyright. Our Gemini reference images must not copy protected art (for example, game assets).

Verdict for a public GitHub mod release: allowed. Generate on a paid plan (no credit needed), or on the free plan credit Meshy in the mod readme. The free plan has no API, so the API route needs a paid plan anyway. The wording came from search summaries. Read the live terms in the account before the first release. Also check that redistributing the model inside a cooked pak is covered.

## 3. Fit for Manor Lords

Estimates from the documented features. Not tested.

- Good: tents, carts, barrels, crates, ladders, fences, stakes, banners, rubble. Compact props with a clear silhouette.
- Weak: the game uses photo-based textures and a muted look. AI textures can carry painted lighting. Keep `remove_lighting` on and use PBR. Retexture, or reuse vanilla materials, to match the style.
- Polycount: the default 30000 triangles is too high for small props. Use smart topology (about 4000) or remesh to 500 to 3000 for props, up to 8000 for a main tent. Check vanilla part counts in UE first, then set the budget.
- LODs: Meshy gives none. Make them in UE (auto LOD) or run remesh at lower counts.
- Collision: none. Add simple collision in UE if the master needs it (open question).
- Scale and pivot: units are not exact. Use `auto_size` and `origin_at: bottom`, then fix scale in the import step (UE units are cm). A pivot at the base is best for building parts.
- Parts: one mesh per call. A camp is several props placed by `make_bm.py`, not one big generation.

## 4. Pipeline design

1. Reference image (optional): `genimage.py` makes a clean view on a plain background. Use it for image-to-3D, or 2 to 4 views for multi-image.
2. `harness/tools/genmesh.py` (new): `--prompt` or `--image`, `--max-credits`. Key from `MESHY_API_KEY` (env, then Windows user scope, as in `genimage.py`). Never print the key. Refuse a call above the cap. Log each task in `runs/genmesh/log.jsonl` (task id, model, credits). Poll with a timeout. Download FBX and textures to `runs/genmesh/<id>/`. Fail loudly on 402 and 429.
3. `mod/HarnessActions/ue/import_mesh.py` (new, run headless in UE 5.5.4): `unreal.AssetImportTask` with `FbxImportUI` (static mesh, import materials and textures, uniform scale to cm). Destination `/Game/HarnessMod/Meshes/`. Flip the normal green channel if the lighting looks wrong.
4. `make_bm.py`: add static mesh components from a list. Names: `MainBld_<n>` main body, `Bld_<n>` parts, `clutter_<n>` props, `res_<good>_<n>` resource slots (see `openspec/changes/archive/2026-10-15-legacy-18-composite-buildings/implementation-notes/siege-camp-and-bm.md`). Offsets in cm.
5. Cook (`-run=cook`), pack (`pakmod.py build`), deploy with `harness\deploy.ps1`, run a scenario with screenshots.

Blender route for simple props (boxes, planks, a ladder from cylinders): `blender --background --python script.py`. Exact size in cm, free, repeatable, no license issue. Blender is not checked as installed. Quality is low without texture work, but enough for ladders and fences. Use Meshy for organic or detailed shapes (tents, carts, sacks).

Gemini can help in three places: reference images for image-to-3D; texture images (`texture_image_url`) in the game's muted style; and detail textures for a Blender prop.

## 5. First spike proposal

Asset: a siege ladder (small, simple, scale is easy to judge, no building logic).

Steps:
1. The user buys one month of Pro (10 USD first month) and sets `MESHY_API_KEY`. We do not sign up for the user.
2. Write `genmesh.py` with a cap of 100 credits per run.
3. `genimage.py`: 2 views of a rough medieval wooden siege ladder on a plain background.
4. Meshy multi-image-to-3D, `meshy-6`, 2k texture, PBR, `target_polycount` 2000, triangle, `auto_size`, `origin_at bottom`, FBX. Cost 30 credits. Allow one retry (60 total). Add one text-to-3D try for comparison (30 credits).
5. Import in UE 5.5.4. Scale to about 400 cm long. Add an LOD.
6. `make_bm.py`: a `BM_` class with one `clutter_1` part (replace the parts of `BM_HarnessCamp`). Cook and pack.
7. Run in game. Take screenshots near, mid and far, next to a vanilla tent.
8. Write the result in a note in this spec folder.

Cost: about 60 to 120 credits (about 1.20 to 2.40 USD of Pro credits). The first Pro month costs 10 USD. Gemini images: small.

Acceptance:
- The mesh shows in game, within 10 percent of the planned size, with its base on the ground.
- No missing texture (no pink or white material).
- At most 3000 triangles. Frame time unchanged within noise.
- Credits and prompts are logged. No key in the repo.
- A written verdict: keep, use for geometry only, or drop.

Second spike (after the first): the Siege Camp main tent and construction mesh, to fix the gaps in `siege-camp-build.md` (no construction mesh, no finished mesh).
