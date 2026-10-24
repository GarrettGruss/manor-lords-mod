# Item ids of the large shield and the spear (task 1.1)

Source: `DT_Items` of the game (`modtools/work/DT_Items.vanilla.json`, made with `pakmod tojson`). The row name is the item id.

| Item | Row name (id) | Field `Name` |
|---|---|---|
| Spear | 133 | `spears` |
| Large shield | 271 | `shields_large` |

The ids match the `GetEquippedID` numbers of the unit gallery run (`docs/wiki/concepts/unit-templates.md`: `mercenary_spearmen` carries 133 and 271).
`HarnessManor.MAX_GOOD` is 200, so the manor commands refuse these ids. The shipment code calls `addToInventory` on the manor module itself
and does not use that limit.
