# Proposal: find a route for a blocking wall outside the manor

Issue: #52. Legacy source: `openspec/changes/archive/2026-10-15-legacy-14-free-walls/README.md`. Legacy issue: #52 (status: blocked, awaiting user).

## Why

The player and the mod need walls that stop units, without a large manor bailey. The spike of spec 14 found this:
- A free wall made by `wall_make` is a look only. It does not block units.
- A built planner wall blocks units, because native code adds obstacle entries for each built piece.
- Fire or collapse of the manor removes the whole wall. The owner decided on 2026-10-12 that losing the manor is too severe for a breach.

No route is chosen for a wall that blocks units and can be opened in part. The owner must pick one. The last acceptance criterion of spec 14 is still open: builders finish a free wall and units are blocked by it.

## What Changes

- Answer the open questions of spec 14 with small spikes (design.md lists them and who decides).
- If a route works: add a named command, a read command and a test scenario for it. A delta spec is written when the route is chosen.
- Keep the findings in `notes/`.

## Non-goals

- New wall meshes or assets.
- Fixing the "Road Access obstructed" rule inside the bailey (that is the change `spike-bailey-buildings`).
- Calling a save function outside the guarded action `save_game`.
- Changing the unsafe commands. They stay behind the explicit game setting (living spec `harness/building-commands`).

## Legacy folders

- `openspec/changes/archive/2026-10-15-legacy-14-free-walls/` (notes: `implementation-notes/free-walls.md`, `os-mouse-regression.md`).

## Capabilities

### New Capabilities
- None. This is a spike (`skip_specs`). A follow-up delta spec is written for `harness/building-commands` when a route is chosen.

### Modified Capabilities
- None.

## Impact

- Spike commands and probe scenarios in `mod/shared/HarnessWalls` and `harness/scenarios/`.
- Notes in this change folder. No code change before the owner picks a route.
