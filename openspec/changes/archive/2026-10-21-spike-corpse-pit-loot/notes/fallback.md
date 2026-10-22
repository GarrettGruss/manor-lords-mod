# No pit, no workers, uncollected bodies (task 1.4)

## Observed
- No pit in the region: 9 bodies of the fixture stayed in `Region.corpses` for more than 10 game days (run `corpse-3`, before the pit). Nothing collects them.
- Pit built, no worker assigned: 0 workers after 8 game days while 3 families had no workplace; the bodies stayed (run `corpse-3`). The game does NOT assign workers to a corpse pit by itself in this fixture. A player must assign a family. `getAllWorkers()` returns 0 units then.
- Pit with workers: all bodies of the region are collected, also bodies 22 000 units away (about 4 game days for 9 bodies with 3 families).
- Bodies in another region (raiders that die in a region that has no pit, for example Eichenhau) are never collected: 3 raider bodies with loot 6 stayed there.
- During raider fights the pit workers run to shelter (`task_run_to_shelter`) and go on later.

## Proposed fallback (for the owner)
1. When the raid tracker sees a raider die with loot, check: the death region is the player region, a pit exists there (`getBuildingCount(113) > 0`, constructed), and it has workers (`#getAllWorkers() > 0`).
2. If yes: park the loot by body key and pay it when the body is delivered (pit `Type 233` `amt` rises). Pay it into the pit inventory (`addToInventory`, villagers haul it) or straight into the nearest store as today.
3. If no: keep today's `return_loot` (direct store add) at the moment of death.
4. Timeout for parked loot: if a body is not delivered within N game days (for example 5), pay it by the direct store add. This also covers a pit that loses its workers.
5. If the worker dies in between, the timeout pays the parked loot.

## Not verified
- A body that is destroyed (pit burned, region lost) before delivery.
- A full pit (capacity).
- Save and load while loot is parked (the parked table must live in `ModState`).
