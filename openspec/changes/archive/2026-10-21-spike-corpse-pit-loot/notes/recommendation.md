# Recommendation (spike-corpse-pit-loot)

Yes. The corpse pit can carry the loot of a Hussite raid. The follow-up change is `add-corpse-pit-loot`.

## Owner decisions (issue #360, 2026-10-21 and 2026-10-22)

- The pit REPLACES the direct store add. The requirement "The loot of a dead raider goes to the nearest store" was removed by change `fix-native-plunder-test` (archived).
- Bodies left on the ground need no mod fallback. The game's own approval mechanic punishes them.
- The player builds the pit. Tests use the fixture `base-corpse-pit`, which holds a built pit.
- Loot give-back is option (a), for Hussite raids only. The plunder tick records the goods it takes per raid (mod state). When a Hussite raider's body reaches the pit, the mod adds that body's share of those goods to the pit with `pit:addToInventory`.
- Native Brigand raids get no give-back. The game loots them and only a count is known. No loot table and no fixed good.

## Requirement ideas for the follow-up change

1. The plunder tick records the goods it takes per Hussite raid, in mod state that survives a load.
2. When a body of a Hussite raider is delivered to the pit, the pit gets that body's share of the raid's goods.
3. Native raids get no give-back. No pit means no give-back.

## Engine facts used

1. Detect a delivery by polling the pit master (about once a second): the `Inventory` entry `Type 233` ("corpse") `amt` rises by 1 per delivered body. No hook fires.
2. The game does not assign workers to the pit. A test needs `building_assign_worker type=113`.
3. `pit:addToInventory({Type=<good>, amt=<n>})` counts in the region stock at once. Villagers haul it to a store in 3 to 5 game days. No goods pile actor exists.
4. The harness cannot place a normal building (`HarnessPlace`), so tests use the fixture with a built pit.

Test plan: a test scenario on `base-corpse-pit`, `building_assign_worker`, `spawn_raid`, `kill_units`, then a poll of the pit `Type 233` `amt` and of the region stock.
