# Proposal: add store tiers and raid stealing

Issue: #276. Legacy source: `openspec/changes/archive/2026-10-16-legacy-m03-raid-behavior/README.md` (iteration table row "04 storage-tiers", no iteration file). Updated 2026-10-19 with the answers of the owner.

## Why

The design (M00) says that a guarded store loses less than an open store, and that the manor is the safest store. None of this is built. The raid tracker returns the loot of a dead raider to the nearest store and treats all stores alike. M13 raised the manor storage, but raiders do not treat the manor store differently (`openspec/changes/archive/2026-10-16-legacy-m13-manor-stronghold/iterations/01-manor-storage.md`).

## What Changes

- Two store tiers. Tier 1: storehouse and granary. Tier 2: manor storage (the manor itself is the guarded store).
- Raiders can steal from tier 1. They never steal from tier 2.
- Game raid: the game steers the raiders and manages the stolen goods. The mod does not compute them.
- Baron AI raid: baron units cannot pillage or steal. The mod steals in Lua. A baron unit that is farther from the battle marker than a threshold is "stealing" and takes a set amount of goods per game day from tier 1 stores, until the raid reaches its steal goal.
- Stretch goal: a tech "Manor" in a third, common branch of the tech tree. It unlocks storage under the manor with the capacity and job slots of a level 1 storehouse.

## Owner decisions after the spikes (2026-10-20)

- A game raid robs the manor store (spike: 31 and 39 of 100 stone). Accepted: the game manages game raids, and the mod does not protect or restore the manor store in them. The tier 2 rule applies to the mod steal of baron AI raids only.
- The steal distance threshold is 200 m (owner choice: about 150 to 200 m). The army fights about 140 m from the battle marker, so units outside the fight steal.

## Non-goals

- The ruin rebuild discount. Dropped on 2026-10-19: the game manages ruin rebuild.
- Raider steering, bait or decoy storehouses (raiders cannot be steered from Lua).
- Carry caps by raid type (see the change `add-raid-carry-caps`).
- New manor storage capacity in the base design (built in M13). The stretch tech only unlocks it.

## Legacy folders

`openspec/changes/archive/2026-10-16-legacy-m03-raid-behavior/` and `openspec/changes/archive/2026-10-16-legacy-m13-manor-stronghold/` (read-only).

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `mod/raid_behavior`: store tiers and baron raid stealing (new requirements; the old requirements on loss share per tier and on the ruin discount are removed).

## Impact

- Code: `mod/InvasionMod/Scripts/features/raid_behavior/`; stretch goal: a tech row and a data change (see `design.md`).
- Tests: fake game tests, new test scenarios.
- Wiki and CHANGELOG.
