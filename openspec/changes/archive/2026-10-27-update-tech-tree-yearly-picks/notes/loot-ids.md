# Loot ids for Strip the Dead (owner values, 2026-10-28)

Check of the good ids against the game data. Source: `modtools/work/DT_Items.vanilla.json` (the extracted vanilla `DT_Items`, 213 rows, row name = good id; field `Name`).

| Id | `Name` in DT_Items | Use in `raid_behavior.body_loot.bandit` |
|---|---|---|
| 177 | `weapons_sidearms` | the sword (the owner's "sword" is the sidearm good) |
| 270 | `shields_small` | the small shield |
| 273 | `militia_helmets_resource` | the helmet (the basic militia helmet) |

Related ids seen in the same table: 133 `spears`, 271 `shields_large`, 163 `gambesons`, 288 `mercenary_helmet_poor`.

Result: all three ids exist and match the names the owner used. The only assumption is "sword = sidearm": DT_Items has no separate "sword" good, and the rebellion design (`update-banditry-rebellion-raid`) also lists 177 as "sidearms".

Variants (equal weight): `{177, 270}` and `{177, 270, 273}`. The mod draws one variant for each looted body (`rules.pick_variant`, `math.random`).

The soldier kind has no values (the owner gave none): `body_loot.soldier = {}`.
