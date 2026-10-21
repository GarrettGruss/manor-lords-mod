# Proposal: decide and finish the Wagenburg manor reskin

Issue: #233. Legacy source: `openspec/changes/archive/2026-10-18-legacy-32-manor-wagenburg/README.md`. Legacy issue: #233 (awaiting user).

## Why

The spike of spec 32 is done. The manor can be reskinned: wagons for the wall pieces, a tent for the keep. The wall keeps its collision, because the collision is native obstacle data and not the mesh. A pak swap is global (every manor). Part 2 sets the meshes of one manor from Lua (`wagen_apply`), but the reskin is lost when the manor rebuilds.

A separate enemy camp with a real wall is not proven. The recommendation is in `implementation-notes/invasion-recommendation.md`. The owner must decide if the Wagenburg manor becomes part of the mod.

## What Changes

- Owner answers of 2026-10-19: the player's manor must not change (no global pak swap, no per-manor swap of it). The Meshy models are the owner's and may be released. The first real `save_game` call is approved. The change `spike-wagenburg-bandit-camp` (#229) is the fallback.
- Route left: a per-manor Lua reskin of a non-player manor (AI lord, invader or enemy). If task 2.1 finds none, stop and fall back to #229.
- Open checks run: an AI lord manor and wall (first), a closed gate, defenders on the wall, wall damage and fire, several rings, save and load with and without the pak.
- Optional models: gate, outer tower, taller wagon.
- If the owner approves: ship the reskin through the Invasion Mod, with a delta spec.

## Non-goals

- Animation, siege rules, balance.
- New native code.
- Game design text. The owner writes it in `design/`.

## Legacy folders

- `openspec/changes/archive/2026-10-18-legacy-32-manor-wagenburg/` (notes: `replacement-test.md`, `pathing-test.md`, `per-manor-lua-reskin.md`, `invasion-recommendation.md`).
- `openspec/changes/archive/2026-10-18-legacy-33-meshy-materials/`.

## Capabilities

### New Capabilities
- None yet. This change is a spike with a decision (`skip_specs`). A delta spec is written when the owner approves shipping.

### Modified Capabilities
- None.

## Impact

- Paks `s32wall_P.pak`, `s32keep_P.pak`, `s32lua_P.pak` in `mod/HarnessActions/paks/`, module `mod/shared/HarnessWagenburg`, probe `probe_manor_wagenburg.py` (living spec `harness/manor-commands`: "Not checked yet" for `wagen_*`).
