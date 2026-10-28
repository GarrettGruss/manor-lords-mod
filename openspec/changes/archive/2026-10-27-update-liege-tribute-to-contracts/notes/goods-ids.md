# Goods ids of the starter contracts (task 1.1 and spike)

Source: `DT_Items` of the game (`modtools/work/DT_Items.vanilla.json`, made with `pakmod tojson`). The row name is the item id and the `Name` field is the game name. Checked 2026-10-28.

| Id | Game name | Use in the starter set |
|---|---|---|
| 14 | Iron Ore | reward of `salt_for_the_garrison` |
| 15 | Rubble | NOT a food good. Was the reward of `feed_the_city` (the mockup shows bread) |
| 16 | Wood | objective of `timber_for_the_walls` |
| 17 | planks | reward of `build_a_storehouse` |
| 30 | Carp | objective of `feed_the_city` |
| 133 | spears | reward of `raise_the_levy` (also the arms shipment) |
| 145 | Salt | objective of `salt_for_the_garrison` |
| 172 | Bread | new reward of `feed_the_city` |

Decision: `feed_the_city` pays 30 bread (id 172) in place of 30 rubble (id 15). Spec impact: none (the spec names no good id).
