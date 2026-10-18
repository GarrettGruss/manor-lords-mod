# Proposal: add carry caps by raid type

Issue: #275. Legacy source: `openspec/changes/archive/2026-10-16-legacy-m03-raid-behavior/README.md` (iteration table row "03 carry-caps", no iteration file).

## Why

The design (M00) gives a carry cap per raider that depends on the raid type: Hussite plunder about 10 grain or 5 iron, bandit plunder about 5 grain. The code has one `carry_cap` (default 10) for every raid. The legacy spec lists the per-type caps as not started.

## What Changes

- The cap depends on the raid type (Hussite plunder, bandit plunder).
- The cap may depend on the good, if the spike shows that the loot value has a good (open question in `design.md`).

## Non-goals

- Store tiers and the ruin rebuild discount (see the change `add-raid-storage-tiers`).
- Raider steering. Raiders cannot be steered from Lua.
- New loot or sack multipliers. M00 decision 8 says loot scales only with raid size.

## Legacy folders

`openspec/changes/archive/2026-10-16-legacy-m03-raid-behavior/` (read-only).

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `mod/raid_behavior`: the requirement "Loot is capped per raider" gets a cap by raid type.

## Impact

- Code: `mod/InvasionMod/Scripts/features/raid_behavior/` (`rules.lua`, `init.lua`, config).
- Tests: `harness/tests/test_fakegame_raid_behavior.py`, a new test scenario.
- Wiki and CHANGELOG.
