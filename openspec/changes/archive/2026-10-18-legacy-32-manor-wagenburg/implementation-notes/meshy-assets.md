# Meshy assets: one wagon and one large tent (2026-10-18)

Spec 32, issue #233. Method of spec 21 and 31: `genimage.py` (Gemini, 2 views), `genmesh.py multi`, headless UE 5.5.4 import with `mod/HarnessActions/ue/import_replace_mesh.py`, cook, pak.
No account was made and no plan was changed. The Meshy key and the Gemini key were already set.

## Credits
| Item | Credits | Task |
|---|---|---|
| Wagon, `meshy-6`, 2k PBR, target 4000 triangles | 30 | `01a14f2a-c9f4-713d-beb3-498d2ea605f3` |
| Large tent, same settings, target 3000 triangles | 30 | `01a14f2a-c9e8-727b-a727-95a446d583d6` |
| Total | 60 | balance 990 before |
Gemini: 4 images (2 per model). Files (git-ignored): `runs/genmesh/wagon/` and `runs/genmesh/tent/`.
Both calls ran in parallel in the background and finished in about 10 minutes. `genmesh.py` wrote the task id at once.

## Import
| Asset | Replaces (vanilla path) | Size in UE (cm) | Vertices | Notes |
|---|---|---|---|---|
| `/Game/HarnessMod/Wagon/SM_Wagon` | `SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam` | 240 x 119 x 114, base at z 0 | 7218 | long axis on X, like the palisade piece (219 cm). Scale 0.569 from the Meshy size. |
| `/Game/HarnessMod/KeepTent/SM_KeepTent` | `SM_MERGED_C_SG_Manor_MainTower_Lv1_New` | 599 x 700 x 510, base at z 0 | 4819 | the vanilla keep is 740 x 776 x 18 m tall. Scale 1.70. |
Each has one material and 5 textures (caps 1024 and 512).
The script copies the imported mesh to the vanilla asset path. The cook needs the extra argument `-ini:Game:[/Script/UnrealEd.ProjectPackagingSettings]:+DirectoriesToAlwaysCook=(Path="/Game/ManorLords/Buildings/Merged")` (from spec 31). The cook of that folder also holds meshes of other specs (tailor shed, ox shed): copy only the 2 files that this spec replaces.
Cook exit code was 1 as always (unrelated "Content is missing" errors); the files were there.

## Paks
| Pak | Files | Bytes | Content |
|---|---|---|---|
| `s32wall_P.pak` | 21 | 3,575,917 | the cooked palisade mesh replacement and the Wagon material and textures |
| `s32keep_P.pak` | 21 | 3,279,826 | the cooked keep mesh replacement and the KeepTent material and textures |
Copies are in `mod/HarnessActions/paks/`. The AES key came only from the environment; a byte grep of the paks and the diff found no key.

## Look
- Wagons: the shape reads well at the normal camera (a continuous ring of carts with plank sides, wheels and a cover). Colour: light grey, not brown. The same grey as the spec 21, 30 and 31 meshes. Open: the cause (material or texture wiring).
- Tent: a pitched canvas tent, rendered blue-grey and white, a little crumpled. It reads as a tent, not as a keep. The reference was off-white and brown.
- Screenshots (git-ignored, in `runs/<id>/screenshots/`): `s32-9/ring_c.png` (wagon ring), `s32-7/keep_z3000_c.png` (tent keep and wagon wall from 30 m), `s32-7/keep_z1200_c.png` (tent close).
