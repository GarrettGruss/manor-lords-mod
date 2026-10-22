## Why

Issue #386. Follows spike `spike-corpse-pit-loot` (#360).

Owner decisions (chat, 2026-10-21 and 2026-10-22):

- The corpse pit replaces the direct store add. The old requirement "The loot of a dead raider goes to the nearest store" was removed by change `fix-native-plunder-test`.
- The player builds the pit. Bodies left on the ground need no mod fallback.
- Loot give-back is for Hussite raids only. The plunder tick records the goods it takes per raid. When the body of a Hussite raider reaches the pit, the mod adds that body's share of those goods to the pit.
- Native raids get no give-back. No loot table and no fixed good.

## What Changes

- The plunder tick records the goods it takes, per Hussite raid, in mod state.
- The mod polls the pit inventory (`Type 233`, corpse). For each new body of a Hussite raider it adds the body's share to the pit with `addToInventory`.
- No pit means no give-back. Native raids get none.

## Capabilities

### Modified Capabilities

- `mod/raid_behavior`: three ADDED requirements.

## Impact

- Code later: `mod/InvasionMod/Scripts/features/raid_behavior/` (plunder tick, new pit poll), mod state keys.
- Tests: fake game test and a test scenario on the default fixture `base-corpse-pit`.
- Spike notes: `openspec/changes/archive/*-spike-corpse-pit-loot/notes/`.
