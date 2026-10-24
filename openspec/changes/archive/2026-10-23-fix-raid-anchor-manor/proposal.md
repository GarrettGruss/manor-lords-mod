## Why

Issue: #449. Spike #430 found that a Hussite raid anchors its army and challenge at the region under the camera. The code calls `battlefield_anchor({lord})`, which uses the current region of the player pawn, and that is the camera region. The raid then goes to the wrong village. Owner decision 2026-10-23.

## What Changes

- The raid anchor is the player manor.
- If the player has no manor, the anchor is the average location of the buildings in the player home region.
- The anchor never depends on the camera.
- `battlefield_anchor` gets a request flag `home` that selects this rule. `lord_raid.start_checked` uses it.

## Open questions (with defaults)

- No manor and no buildings: the anchor is the village centre, then the region actor (existing fallback). Default accepted.

## Impact

- Specs: `mod/invasion` (MODIFIED requirement).
- Code: `mod/shared/HarnessBattlefield`, `mod/InvasionMod/Scripts/features/invasion/lord_raid.lua`.
