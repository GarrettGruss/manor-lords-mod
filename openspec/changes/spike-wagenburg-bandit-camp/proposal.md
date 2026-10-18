# Proposal: decide and ship the Wagenburg encampment look

Issue: #229. Legacy source: `docs/harness/30-wagenburg-encampment/README.md`. Legacy issue: #229 (awaiting user).

## Why

The spike of spec 30 is done. A Meshy ring of war wagons shows in the game in two ways: as the bandit camp (row 100 retargeted by a pak, host a) and as an actor that Lua spawns in neutral or AI regions (host c). Host b, a camp the player builds with a new row, loads but was never placed (needs the real mouse). The recommendation is in `implementation-notes/invasion-recommendation.md`.

The Invasion Mod design (decision 7) left war wagons out because "the game cannot show them". The spike changes that fact. The owner must decide if the Wagenburg camp becomes part of the mod.

## What Changes

- The owner decides which hosts ship, and whether the Meshy license allows a public release.
- Open checks from the spike are done: host b placement with the real mouse, bandits stuck in the ring, a mix of tents and wagon camps, and a respawn on load for host c.
- If the owner approves: ship the pak and the row 100 patch through the Invasion Mod pack, with a delta spec for the owning feature.

## Non-goals

- Animation, siege rules, garrison logic, balance.
- War wagon units (that is spec 29, closed: stand-in squad only).
- Game design text. The owner writes the design in `docs/mod/M00-invasion-mod/`.

## Legacy folders

- `docs/harness/30-wagenburg-encampment/` (notes: `meshy-model.md`, `host-tests.md`, `invasion-recommendation.md`).
- `docs/harness/33-meshy-materials/` (the grey look is fixed there; check it here).

## Capabilities

### New Capabilities
- None yet. This change is a spike with a decision (`skip_specs`). A delta spec for the Invasion Mod feature that owns bandit camps is written when the owner approves shipping.

### Modified Capabilities
- None.

## Impact

- Pak `mod/HarnessActions/paks/wagen_P.pak`, probe `probe_wagenburg.py`, commands `encampment_*` (living spec `harness/encampment-commands`).
- If shipped: a data patch for row 100 in `mod/InvasionMod/data/`, and a Lua spawn with a respawn on load.
