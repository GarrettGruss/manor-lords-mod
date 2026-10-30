# Item ids (task 1.2)

Source: `DT_Items` of the game (`modtools/work/DT_Items.vanilla.json`, made with `pakmod tojson`; 213 rows). The row name is the item id. Checked 2026-10-30 with a script that prints `Name`, `ItemCategory`, `Subcategory`, `EquipmentSlot`, `storageType`, `tradeable` and `Value` of each id.

## The four unknown ids

| Good | Id | Row `Name` | Category | Tradeable | Verdict |
|---|---|---|---|---|---|
| Bows | 205 | `warbows` | Military / RangedWeapons | yes | Confirmed. The other bow row, 21 `huntingBow`, has category None and is not tradeable: it is a tool of hunters, not a good. |
| Cut stone | 283 | `DressedStone` | Construction / Stoneworks | yes | Confirmed. The stone block of the game is "dressed stone"; 27 `RoughStone` is the quarry output (Material / Minerals). |
| Tools | 6 | `Iron tools` | Construction / Maintenance | yes | Confirmed. The other tool rows (20 fellingAxe, 22 Mallet, 24 Saw, 25 Knife, 26 Sickle, 138 Pickaxe, 263 hammer, 328 Chisel) all have category None and are not tradeable: they are worker equipment. |
| Helmets | 273 | `militia_helmets_resource` | Military / Armor | yes | Confirmed. It is the only helmet row that is a tradeable good. The rows 276, 285, 288, 289 and 294 have category None and are not tradeable: they are visual variants of a unit. |

## The other ids

Every other id of Table 1 of `design.md` exists in `DT_Items` with the name that the table gives, and every one is a stored good (`storageType` Generic or Pantry, category not None): 17 planks, 171 Berries, 279 mushrooms, 330 SmallGame, 3 Hides, 15 Rubble, 146 Clay, 337 Carrots, 339 Beetroots, 338 Cabbages, 145 Salt, 30 Carp, 296 apples, 46 Quinces, 45 Pears, 35 Iron ingot / slab, 7 Wooden Parts, 32 Eel, 177 weapons_sidearms, 270 shields_small, 178 weapons_polearms, 133 spears, 271 shields_large, 163 gambesons, 164 mail_armor, 293 armour_retinue_tier3_variations, 206 crossbows, 323 smokedFish, 320 sausage.

## Notes

- Names for the window come from the game names of the table, not from the row names (for example "Metal bars" for 35). `contracts.json` holds them in the `items` map as before (`good:<id>`).
- Hides: id 3. Id 139 is `Hide Washed`.
- Reward goods: the Medium "weapons" pool is 177, 270, 178, 133, 271 and 206 (all Military and tradeable).
- Take source: `world.take_goods` takes from the stores of types 6, 72, 50, 57, 58, 81, 82, 83, 95 and 98 (as `raid_behavior` `store_tiers`). The stock shown on a card is `getStockOfGood` of the player region. If a good lies in a building that is not in that list, the stock number is higher than what the take finds. The call is then refused with the number found and nothing is lost (units taken are put back). Real runs show how often this happens for armour and smoked goods (see `notes/real-runs.md`).
