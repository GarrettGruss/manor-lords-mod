# Storage in the manor (Q3, criterion M1)

Date: 2026-10-11. Real game, bridge eval. The scenario result is added at the end when it is done.

## What the Keep has
- `SMBuildingMaster.Inventory` (array of `Good {Type, amt}`) exists on the Keep. A site holds the goods that were carried to it (15:10, 16:10, 17:15).
- Storage limits: `storageLimitGeneric` 50, `storageLimitLarge` 0, `storageLimitPantry` 0, `HasStorageLimits()` false, `isStorageTypeBuilding()` false.
  So the base game does not treat the Keep as a store. Workers do not carry goods to it (the goods stayed unchanged for 3 game days).
- `SMBuildingMaster:addToInventory(Good)` works with a Lua table `{Type=16, amt=5}`: the Keep inventory rose 4 to 9 and the region stock (`getStockOfGood`) rose 308 to 313.
  `consumeGoodNoCheck(16)` removed one unit from both (9 to 8, 313 to 312).
- 15 units of stone put into the finished Keep were still there after 3 game days (and the region stock too).

## Chosen way (candidate c, with a real building)
A mod-defined store on top of the Keep inventory. Module `mod/shared/HarnessManor` and actions `manor_state`, `finish_manor_site`, `manor_put`, `manor_take`, `manor_stock`.
Capacity 200 units per module is a mod rule. Each change is read back from the module and from the region stock.
Why not the others: (a) the base game does not use the Keep as a store, so there is nothing to read that the game fills by itself; (b) no Granary or Storehouse can be part of the manor:
the planner has only four module cards and the manor module Blueprints have no storage; whether a Granary can be placed inside a bailey is not tested (no bailey).

## What is base game and what is not
- Base game: the Keep, its `Inventory`, `addToInventory`, `consumeGoodNoCheck`, the region stock that includes it.
- Harness shortcut: finishing the Keep (`Data.constructed = true`, `setRegionsManor`), because 5 families cannot build it.
- Mod-defined: put and take commands, the capacity, the rule that goods in the manor stay there.
