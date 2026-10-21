# Goods at the pit and hauling (task 1.3)

## There is no ground goods or pile actor
- A `types` search over the loaded classes for Pile, Stock, Dropped, Goods and Loot found no goods or loot actor class (only `RegionProductionStockEntry`, `TargetStockGood`, `LivestockSettings`). The archived spikes say the same: no ground loot in the base game; `staticMeshGoods` on a unit is a carried-goods mesh only.
- A pile on the ground would need a mod-made `StaticMeshActor` (visual only, not part of the economy) and a second step that adds the goods to a store. Not tried (no pile mesh was searched).

## The pit inventory works as a drop point (tested, run `corpse-4`)
- `pit:addToInventory({Type = 17, amt = 5})` (planks) works on the pit master. Read back: pit `Inventory` = `[233 corpse x N, 17 planks x 5]`, `numStoredGeneric` 5.
- The region stock counts it at once: `Region:getStockOfGood(17, false, false)` went 14 -> 19, and 19 -> 24 for a second add of 5. The player sees the goods in the stock the moment they are added, as with `world.deposit` on a store.
- Villagers move them by themselves. The planks left the pit inventory and the small store of the village (`bType 72`, region Nusslohe) went from 14 to 19 (first add) and 19 to 24 (second add). Time: still at the pit after 120 game seconds (3 game days) and gone after 1 more game day at speed 3. So hauling takes about 3 to 5 game days. The direct add of `return_loot` is instant.
- No visible pile: the picture with 5 planks in the pit inventory (`evidence/pit-with-5-planks-in-inventory.jpg`) shows the plain dirt pit and the "Corpse Pit" label, no goods mesh.
- Compare with `world.deposit` (direct store add): instant, nothing visible. Pit add: instant stock, the physical move comes later by hauling villagers, nothing visible on the ground. Visible at the pit: the carriers that bring the bodies (`evidence/workers-at-pit-delivering-bodies.jpg`).

## Not verified
- Which villager class hauls the goods, and whether a full store blocks it (the store had room).
- Pit inventory capacity (`storageLimit*` of row 113 is 0) and whether the game shows a storage warning.
- Whether goods that the village does not use (equipment trade goods) are hauled like planks.
