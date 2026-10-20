---
name: harness-meshy
description: Make a 3D model for Manor Lords with Gemini reference images and Meshy, import it headless in UE 5.5.4, and ship it in a pak. Use when a mod needs a new or replacement mesh (building part, wagon, tent, prop).
---

# Meshy models (specs 21, 30, 31, 32, 33)

Use this skill when a task needs a new 3D model in the game. Check first if a vanilla mesh is enough.
For Meshy modes that `genmesh.py` lacks (owner-installed CLI), see `harness-meshy-agent`.

## Approved tools (user, 2026-10-18): Gemini is approved for reference images. Meshy is used on the Pro plan.

## IMPORTANT: Meshy Pro account and private ownership (owner, 2026-10-19)
We use a Meshy **Pro** account. Its license for the models we generate:
- Ownership: full private ownership. Commercial use: allowed, with full commercial rights. Attribution: not required.
- Condition: we keep private ownership only if we do NOT publish the models to the Meshy Community page, and our input assets (prompts, reference images) do not violate third-party copyrights.
- So: never publish, share or make public a model on the Meshy Community page. Keep task visibility private. Use only our own or licensed input images.

## Meshy license (Pro plan), quoted from the Meshy terms:

> Meshy hereby grants you a non-exclusive, royalty-free, worldwide license to reproduce, distribute, and otherwise use and display Service Assets solely to the extent incorporated into and necessary for Customer to use and otherwise exploit the Customer Output.
> Meshy hereby grants you a non-exclusive, royalty-free, worldwide license to reproduce, distribute and otherwise use and exploit the Meshy IP solely as necessary to use and access the Service.
> Other than as expressly allowed by us in writing, nothing herein or in the Service may be implied as granting any license, assignment, or right to copy or use Meshy intellectual property without prior authorization.

Plain note: generated models (Customer Output) may be shipped in the mod. Do not redistribute Meshy's own assets or IP outside that use.

## Pipeline
1. Reference: a text prompt, or 2 Gemini images of the object (`harness/tools/genimage.py`): two views, plain background, floating object, no ground, no text. Files go to git-ignored `runs/genmesh/<name>/`.
2. Meshy: `uv run python harness/tools/genmesh.py multi --image a.png --image b.png --out runs/genmesh/<name> --polycount 3000`. A call takes 6 to 10 minutes. Run it in the background. `genmesh.py balance` shows the credits. `resume --task <id> --out <dir>` downloads a task again and costs nothing.
3. Import: headless UE 5.5.4 with `mod/HarnessActions/ue/import_mesh.py` (new asset) or `import_replace_mesh.py` (copy to the path of a vanilla mesh, so the pak replaces it). Both scale the mesh, cap the textures (1024 and 512) and call `meshy_material.py`. In Git Bash set `MSYS_NO_PATHCONV=1`, or `/Game/...` becomes a Windows path.
4. Cook. A replaced vanilla mesh needs the extra argument `-ini:Game:[/Script/UnrealEd.ProjectPackagingSettings]:+DirectoriesToAlwaysCook=(Path="/Game/ManorLords/Buildings/Merged")`. Cook exit code 1 is usual ("Content is missing"); check that the files exist.
5. Pak: copy only the files of this model. Keep out the stub master, the emission map and the metallic map. Build with `pakmod.py` (skill `harness-pak-mod`). Never write the AES key anywhere.
6. Test: `run.py --scenario <probe> --pak <name>`, with screenshots. Look at them by eye.

## Cost
- About 30 credits for one textured model (`meshy-6`, 2k PBR). `genmesh.py` caps a call at 60 and a day at 200 credits and logs each task in `runs/genmesh/log.jsonl`.
- Record the task id and the credits in the notes of the change (`openspec/changes/<change-name>/notes/`; legacy example: `openspec/changes/archive/2026-10-18-legacy-32-manor-wagenburg/implementation-notes/meshy-assets.md`).
- Never create an account. Never buy credits or change the plan. If the key is missing or credits are out, stop and ask the user.

## Grey material rule
Always use a material INSTANCE of a game master material (spec 33). `meshy_material.py` does it: instance `MI_Meshy` of `/Game/NotStronghold/Buildings/TudorWall/tudorWall01`, with `d` = base colour, `n` = normal, `spec` = roughness, `AO` = white.

Why: the UE import makes a plain material. The cook puts its shader code in a shader library file, and a mod pak ships none. The game has no code for it and draws a fallback grey. A material instance of a game master needs no new shader code. Specs 21, 30, 31 and 32 meshes were grey for this reason. Details: `openspec/changes/archive/2026-10-18-legacy-33-meshy-materials/implementation-notes/cause-and-fix.md`. `retarget_material.py` fixes a mesh that was imported earlier.

## Known limits
- Scale: Meshy size is arbitrary. Set the size on import to the real size (for example a wagon 240 cm long, a ring about 14.6 m). Base on the ground (z 0). Check the size in UE after import.
- One mesh has one material. Parts are not separate objects, so a unit cannot pass a gap and one part cannot be destroyed alone.
- Collision is data, not mesh. A replaced manor wall keeps the collision and the gate of the vanilla piece (spec 32).
- The look is checked by eye in a screenshot. Screenshots copy screen pixels, so keep other windows away.
- The `spec` and `AO` mapping is a guess. Tune by eye.
- Frame time with many models, LOD and the closest zoom are not measured.
