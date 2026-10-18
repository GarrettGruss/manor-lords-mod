# Proposal: Extend mesh pipeline checks

Issue: #102. Legacy source: `docs/harness/21-mesh-generation/README.md` (open questions and acceptance) and `docs/harness/33-meshy-materials/implementation-notes/cause-and-fix.md` ("Open"). Legacy issues: #102 (spec 21), #237 (spec 33).

## Why
Specs 21 and 33 are built: the Meshy tool, the headless import, the game material instance that fixes the grey look, and the recook of old paks. The living spec `harness/mesh-pipeline` describes them. The issues #102 and #237 can close after this check. Some items remain:
- Frame time with a Meshy mesh in view was not measured (spec 21 acceptance box).
- The `spec` and `AO` mapping of the material instance is a guess (roughness, white). The legacy note says: tune by eye.
- Open questions of spec 21: UV and normal map conventions after the FBX import, and collision of a prop part.
- Only `genmesh.py` has a test. `genimage.py`, the UE scripts, `meshy_material.py` and `recook_meshy_pak.py` have none (backfill report H2). Five spec scenarios say "Not checked yet".
- Screenshots copy screen pixels, so another window can cover the game (spec 33 "Open").

## What Changes
- Measure the clock rate or frame time with and without a Meshy mesh.
- Compare the material with the spec and AO maps tuned, by pictures.
- Add fake tests for the Python parts that have none.
- Close issues #102 and #237 with a comment.

## Non-goals
- New Meshy models.
- A shader library for mods.

## Legacy folders
`docs/harness/21-mesh-generation/` and `docs/harness/33-meshy-materials/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None now. The new tests change the "Not checked yet" lines of `harness/mesh-pipeline` when the change is archived.

## Impact
The real game for the frame time and pictures. Meshy credits are not needed. Pictures are required (visual result).
