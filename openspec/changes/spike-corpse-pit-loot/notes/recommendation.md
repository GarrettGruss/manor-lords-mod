# Recommendation (spike-corpse-pit-loot)

Yes, the corpse pit can carry the loot, with polling, and with the direct store add kept as fallback.

1. Detect a delivery by polling the pit master once a second: the `Inventory` entry `Type 233` ("corpse") `amt` rises by 1 per delivered body. The delivery is native code: no hook fires.
2. Map body to loot with the raider key (`GetAddress`) that the tracker already has. A dead raider keeps `ItemsLooted`, and the same object sits in `Region.corpses` until a worker picks it up.
3. Put the loot where the owner wants it: `pit:addToInventory({Type=<good>, amt=<n>})`. It counts in the region stock at once, and villagers haul it to a store within about 3 to 5 game days. The game has no goods pile actor and shows no pile. The visible part is the carriers that walk to the pit.
4. Keep `return_loot` as fallback: no pit, a pit with no workers (the game does not assign workers by itself), or a body in a region without a pit. Add a timeout.
5. Cost: the player must place the pit and assign a family. The harness needs the real mouse to place it (`HarnessPlace` cannot place a normal building) and `building_assign_worker type=113` for the family. A fixture that holds a built pit makes tests repeatable.

Owner decisions that follow (tasks 2.1 to 2.3): replace the direct add or keep it as fallback only; loot per body and which good; what happens to loot that nobody hauls.

Test plan for the implementation: a test scenario on a fixture with a built pit, `building_assign_worker`, `spawn_raid`, `set_unit_loot`, `kill_units`, then a poll of the pit `Type 233` `amt` and of the region stock.
