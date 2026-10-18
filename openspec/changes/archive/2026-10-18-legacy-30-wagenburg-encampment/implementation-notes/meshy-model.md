# Meshy Wagenburg model (2026-10-18)

Spec 30, issue #229. Method: spec 21 (`genimage.py`, `genmesh.py multi`, headless UE 5.5.4 import).

## Result
A Wagenburg model was made with Meshy on the first try. A key was set and Meshy was reachable. No account or plan was changed.

| Item | Value |
|---|---|
| Reference views | 2 Gemini images: `view1.png` (high three-quarter view), `view2.png` (top-down view). Prompt: ring of 8 war wagons with plank shields, chains, tents and barrels inside, muted brown, floating object, no ground, no text. Both are in git-ignored `runs/genmesh/wagenburg/`. |
| Meshy call | `multi-image-to-3d`, `meshy-6`, 2k texture, PBR, target 6000 triangles. Task `01a14ec9-791f-7020-b8fe-f8539b92fc24`. |
| Credits | 30. Balance 1050 before, 1020 after. The cap was 60 per call. |
| Files | `model.fbx` 17.8 MB, `model.glb` 14.0 MB, 4 maps (base colour, emission, metallic, roughness). All git-ignored. UE read the FBX as data. Nothing was run. |
| UE import | `/Game/HarnessMod/Wagenburg/SM_Wagenburg`, 11354 vertices, size 1455 x 1459 x 250 cm, base at z 0, one material, 5 textures (caps 1024 and 512). |
| Scale | The ring is about 14.6 m across and 2.5 m high. The wagons are about 3 m long. This fits a camp. The bandit camp row has `Bounds` 1200 x 800. |
| Blueprint | `BM_Wagenburg` (parent `StaticMeshActor`), one part `MainBld_900`, scale 1. |
| Pak | `wagen_P.pak`, 3,419,470 bytes, 23 files. Row 100 (bandit camp) points at `BM_Wagenburg_C`. Row 4000 is a clone of the tent row 87 (block 4000 to 4099 for spec 30) with `bVisibleInUi` true. |

## What the model looks like
- The shape is good: a ring of 8 to 10 wagons with side walls and wheels, and a tent cluster in the middle. The yard is open.
- The model is one mesh with one material. The wagons are not separate objects. The centre tents are part of the same mesh.
- In the game (screenshots `runs/s30-2/screenshots/neutral_after_c.png` and `runs/s30-3/screenshots/ai2_after_s.png`) the ring reads as a wagon fort from the normal camera height.
- Problem: the colour is light grey, not brown. The ox shed of spec 21 spike B looked grey too. The base colour map is brown (with light grey tent patches), so the grey comes from the game render. Not solved. Ideas: check the sRGB flag and the wiring of `Material_001`, or reuse a vanilla wood material and keep only the geometry.
- Because the wagons are one mesh, a unit cannot enter through a gap, and one wagon cannot be destroyed alone.

## Not verified
- The license for a public release (open since spec 21).
- Frame time with several rings.
- LOD, and the look at the closest zoom.
