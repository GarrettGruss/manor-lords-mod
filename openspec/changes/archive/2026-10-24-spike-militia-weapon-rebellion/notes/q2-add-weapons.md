# Q2: add 30 spears and 30 large shields to the storehouse

## Item ids
The gear of `spearMilitia` is `163/133/271/273`, and `mercenary_spearmen` is "large shield, spear, ..." with the same ids (`docs/wiki/concepts/unit-templates.md`). So 133 is the spear and 271 is the large shield. The Invasion Mod arms shipment uses the same ids.

## Method
Building list `region:GetBuildings()`. The storehouse is the building with `Data.bType` 72 (`isStorageTypeBuilding` true, inventory `15:10,216:3,6:8`). Call `building:addToInventory({Type=133, amt=30})`, and the same for 271 (the call `HarnessManor.manor_put` uses on a manor module).

## Result: TRUE
| | Before | After |
|---|---|---|
| Storehouse inventory | `15:10,216:3,6:8` | `133:30,15:10,216:3,271:30,6:8` |
| `region:getStockOfGood(133)` | 0 | 30 |
| `region:getStockOfGood(271)` | 0 | 30 |

Stock rose by exactly 30 each. The village stock count includes goods that are in the houses.
