# Proposal: add store tiers and the ruin rebuild discount

Issue: #276. Legacy source: `docs/mod/M03-raid_behavior/README.md` (iteration table row "04 storage-tiers", no iteration file).

## Why

The design (M00) says that a guarded granary loses less per trip than an open barn, that the manor is the safest store, and that burned buildings become ruins that rebuild at partial cost. None of this is built. The raid tracker returns the loot of a dead raider to the nearest store and treats all stores alike. M13 raised the manor storage, but raiders do not treat the manor store differently (`docs/mod/M13-manor_stronghold/iterations/01-manor-storage.md`).

## What Changes

- Each store type has a tier. The share of goods that a raider takes per trip depends on the tier.
- The manor store is the safest tier.
- A ruin from a raid rebuilds at a partial cost.

## Non-goals

- Carry caps by raid type (see the change `add-raid-carry-caps`).
- Bait, decoy storehouses or raider steering (dropped in M00, section "No raider steering"; raiders cannot be steered from Lua).
- New manor storage capacity (built in M13).

## Legacy folders

`docs/mod/M03-raid_behavior/` and `docs/mod/M13-manor_stronghold/` (read-only).

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `mod/raid_behavior`: store tiers and the ruin rebuild discount (new requirements).

## Impact

- Code: `mod/InvasionMod/Scripts/features/raid_behavior/`; maybe a pak row change for the rebuild cost (see `design.md`).
- Tests: fake game tests, new test scenarios.
- Wiki, skills for pak mods if a pak is used, and CHANGELOG.
