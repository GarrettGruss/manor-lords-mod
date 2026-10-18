---
type: Workflow
title: Meshy models
description: Pipeline that makes a 3D model for the game - Gemini reference images, Meshy generation, headless UE import, game material instance, cook and pak - with costs, caps and the grey material cause.
tags: [meshy, gemini, mesh, unreal, pak, material]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T15:30:28Z }
sources:
  - resource: repo://harness/tools/genmesh.py
  - resource: repo://harness/tools/genimage.py
  - resource: repo://harness/tools/recook_meshy_pak.py
  - resource: repo://harness/tests/test_genmesh.py
  - resource: repo://mod/HarnessActions/ue/
  - resource: repo://.claude/skills/harness-meshy/SKILL.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-21-mesh-generation/README.md
  - resource: repo://openspec/changes/archive/2026-10-18-legacy-33-meshy-materials/README.md
---

# Meshy models

This workflow makes a new or replacement mesh (building part, wagon, tent, prop) and ships it in a pak. Check first if a vanilla mesh is enough. Specs: [21](../../../openspec/changes/archive/2026-10-15-legacy-21-mesh-generation/README.md), [30](../../../openspec/changes/archive/2026-10-18-legacy-30-wagenburg-encampment/README.md), [31](../../../openspec/changes/archive/2026-10-18-legacy-31-burgage-extension/README.md), [32](../../../openspec/changes/archive/2026-10-18-legacy-32-manor-wagenburg/README.md), [33](../../../openspec/changes/archive/2026-10-18-legacy-33-meshy-materials/README.md).

Approved by the user (2026-10-18): Gemini for reference images, Meshy on the Pro plan. Generated models may be shipped in the mod. Do not redistribute Meshy's own assets. Never create an account, buy credits or change the plan. If a key is missing or credits are out, stop and ask.

## Pipeline
```mermaid
flowchart LR
  A[genimage two views] --> B[genmesh multi]
  B --> C[UE headless import]
  C --> D[meshy_material instance]
  D --> E[cook]
  E --> F[pak build]
  F --> G[run with --pak and screenshot]
```

### 1. Reference images - `harness/tools/genimage.py`
Gemini API (default model `gemini-3.1-flash-image`, `--list-models` shows more). Key from `GEMINI_API_KEY` (environment, else Windows user scope); never printed. At most 4 images per call. Each call goes to `runs/genimage/log.jsonl`. Ask for two views of the object, plain background, floating, no ground, no text. Look at every image. Files go to the git-ignored `runs/genmesh/<name>/`. Review a set with `harness/tools/contact_sheet.py`.

### 2. Mesh - `harness/tools/genmesh.py`
```
uv run python harness/tools/genmesh.py multi --image a.png --image b.png --out runs/genmesh/<name> --polycount 3000
uv run python harness/tools/genmesh.py balance
uv run python harness/tools/genmesh.py resume --task <id> --out <dir>
```
- Key from `MESHY_API_KEY` (never printed or logged). `multi` takes 1 to 4 images, sends a Meshy multi-image-to-3D task (`meshy-6`, PBR, 2k texture, triangle topology, `auto_size`, `origin_at: bottom`, FBX and GLB), polls every 10 s up to 1200 s, and downloads `model.fbx`, `model.glb` and `tex<N>_<map>.png`.
- A call takes 6 to 10 minutes. Run it in the background.
- Cost: about 30 credits for one textured model (`MULTI_IMAGE_TEXTURED_COST`). `check_caps` refuses a call over 60 credits (`MAX_CREDITS_PER_CALL`) or a day over 200 (`MAX_CREDITS_PER_DAY`). The day total comes from `runs/genmesh/log.jsonl`.
- The task id is logged at once when the task is created, before polling, so a timeout after Meshy charged does not lose it. `resume` downloads an existing task and costs nothing.
- Record the task id and credits in the notes of the change (`openspec/changes/<change-name>/notes/`). Legacy example: [meshy-assets.md](../../../openspec/changes/archive/2026-10-18-legacy-32-manor-wagenburg/implementation-notes/meshy-assets.md).

### 3. Import - headless UE 5.5.4
The UE project is a separate workspace (the skill names it `mlm-ue`), outside the repo. Copy the scripts from `mod/HarnessActions/ue/` into it. Run each with `UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=<script> -unattended -nullrhi`. Inputs are environment variables. In Git Bash set `MSYS_NO_PATHCONV=1`, or `/Game/...` becomes a Windows path.

| Script | Job | Main inputs |
|---|---|---|
| `import_mesh.py` | Import an FBX as a new static mesh. Logs size in cm, vertices and material. | `MESH_FBX`, `MESH_NAME`, `MESH_DEST`, `MESH_SCALE` |
| `import_replace_mesh.py` | Import, scale so the longest floor side is `TARGET_CM`, copy to the path of a vanilla mesh so the pak replaces it. | `MESH_FBX`, `MESH_NAME`, `MESH_DEST`, `REPLACE_PATH`, `TARGET_CM` |
| `meshy_material.py` | Make the material instance (below). Called by both import scripts. | - |
| `retarget_material.py` | Give an already imported mesh the game material. | `MESH_PATH` |
| `make_bm.py` | Make a `BM_` building Blueprint class from parts. | `BM_NAME`, `BM_PARTS` (JSON list of `[component name, mesh path, [x,y,z], [sx,sy,sz]]`) |

Both import scripts cap textures (1024 for colour and normal, 512 for others) to keep a pak near 3 MB. Meshy size is arbitrary: set the real size on import and base the mesh on the ground (z 0). `make_bm.py` part names must start with `MainBld_`, `Bld_`, `clutter_` or `res_<good>_`, because the game classifies parts by prefix.

### The grey material rule (spec 33)
Always use a material instance of a game master material. A material made by the UE import has its shader code in a shader library file. A mod pak ships none, so the game draws a fallback grey. `meshy_material.py` makes `MI_Meshy`, an instance of the game master `/Game/NotStronghold/Buildings/TudorWall/tudorWall01`. Parameters: `d` base colour, `n` normal, `spec` roughness, `AO` white. It also makes a stub master at the same path so the editor accepts the instance. The stub is never shipped. The `spec` and `AO` mapping is a guess; tune by eye. Cause and fix: [cause-and-fix.md](../../../openspec/changes/archive/2026-10-18-legacy-33-meshy-materials/implementation-notes/cause-and-fix.md).

### 4. Cook
`UnrealEditor-Cmd.exe <uproject> -run=cook -targetplatform=Windows -unversioned -nopak -skipeditorcontent`. Exit code 1 is usual ("Content is missing"): check that the files exist. A replaced vanilla mesh needs `-ini:Game:[/Script/UnrealEd.ProjectPackagingSettings]:+DirectoriesToAlwaysCook=(Path="/Game/ManorLords/Buildings/Merged")`.

### 5. Pak
Copy only the files of this model into the build folder (`modtools/work/<pak>/ManorLords/Content/HarnessMod/...`): `MI_Meshy`, the mesh, `texture_0`, `texture_0_normal`, `texture_0_roughness`. Keep out the stub master, the emission map and the metallic map. For a building, add a `buildingStats` row (`s65_edit_json.py stats`, `blueprint`, `visible`) with a free id. Then `pakmod.py fromjson --to <pak>` and `pakmod.py build <pak>`. See [Pak mods](pak-mods.md). Never write the AES key anywhere.

`harness/tools/recook_meshy_pak.py <old pak> <new name> <mesh folder>` re-cooks an old pak: it unpacks it, removes `Material_001`, `texture_0_emission` and `texture_0_metallic`, copies the cooked `MI_Meshy` and textures from the UE workspace, and builds. The old pak is not changed. Data files in the old pak are kept. Record: [recook-old-paks.md](../../../openspec/changes/archive/2026-10-18-legacy-33-meshy-materials/implementation-notes/recook-old-paks.md). The script has fixed paths for this PC (the config file and the cooked folder).

### 6. Test
`run.py --scenario <probe> --pak <name>` (see [Pak mods](pak-mods.md)). For a keep-open session, drive the game with the `s94_drive.py`, `s21_locate.py` and `s21_view.py` tools, place only on a white ghost, close the game, then `pakmod.py remove --all`. Check the look by eye in a screenshot. Screenshots copy screen pixels, so keep other windows away. Committed sample paks of these specs are in `mod/HarnessActions/paks/` (for example `wagen_P.pak`).

## Known limits
- One mesh has one material. Parts are not separate objects, so a unit cannot pass a gap and one part cannot be destroyed alone.
- Collision is data, not mesh. A replaced manor wall keeps the collision and gate of the vanilla piece (spec 32).
- Frame time with many models, LOD and the closest zoom are not measured.

## Tests
```
uv run python -m unittest discover -s harness/tests -p "test_genmesh.py"
```
It uses fake API calls (success, day cap, failed task, task id logged before polling, resume, image count). The UE scripts and `genimage.py` have no unit test. They are checked in the real editor and game.
