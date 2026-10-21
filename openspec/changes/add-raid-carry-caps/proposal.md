# Proposal: add carry caps by raid type

Issue: #275. Legacy source: `openspec/changes/archive/2026-10-16-legacy-m03-raid-behavior/README.md` (iteration table row "03 carry-caps", no iteration file).

## Why

The design (M00) gives a carry cap per raider that depends on the raid type: Hussite plunder about 10 grain or 5 iron, bandit plunder about 5 grain. The code has one `carry_cap` (default 10) for every raid. The legacy spec lists the per-type caps as not started.

## What Changes

- Owner decision (2026-10-20, after spike 1.1): the mod manages plundered quantities only for Hussite raids. The Hussite AI has raiding disabled, so the game does not manage the raid natively.
- The plundered goods of a Hussite raid stop at `carry_cap` (default 10) for each raider at the start.
- The mod no longer writes `ItemsLooted` of native raids. The game caps them at about 5 per raider by itself (`notes/loot-cap-spike.md`).
- No cap by good: the loot has no good type (spike finding 3).
- Owner choice (2026-10-20): the carry cap is also the loot goal of a Hussite raid. It leaves by loot at `carry_cap` per raider, not at `leave.loot_per_raider` (4). Other role raids keep `leave.loot_per_raider`.

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
- `mod/raid_behavior`: the requirement "Loot is capped per raider" applies to Hussite raids only. The requirement "A role raid leaves for loot, losses or time" uses `carry_cap` as the loot goal of a Hussite raid.

## Impact

- Code: `mod/InvasionMod/Scripts/features/raid_behavior/` (`rules.lua`, `init.lua`, config).
- Tests: `harness/tests/test_fakegame_raid_behavior.py`, a new test scenario.
- Wiki and CHANGELOG.
