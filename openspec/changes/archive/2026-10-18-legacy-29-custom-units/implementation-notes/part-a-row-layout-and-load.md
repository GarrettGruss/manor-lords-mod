# Part A: row layout, new rows, load and spawn

Date: 2026-10-18. Game 0.8.111, UE 5.5.4. Issue #178.

## Export
- `pakmod.py extract` then `tojson` works for `DT_UnitTemplates` (29 rows, 544 KB JSON) and `DT_Items` (213 rows, 6.3 MB JSON). No RawExport. The JSON is in `modtools/work/json/` (git-ignored).
- New tool `harness/tools/clone_table_row.py` clones one row, renames it, adds the name to the name map and sets fields (`--set`, `--array`, `--names`). It works on any row table.
- `pakmod.py fromjson --to <name>` writes `items.uasset`, not the full game path. Move the files to `ManorLords/Content/NotStronghold/Data/DT_Items.*` and `DT_UnitTemplates.*` in the work folder before `build`.

## Unit row layout (`UnitTemplate`)
Fields: `Name`, `descr` (null), `Icon` (int), `iconTexture` (int), `IconTextureV2` (soft object, card art), `isMilitia`, `cost`, `armours`, `weapons`, `shields`, `helmets`, `mounts`, `bonus` (int arrays of item ids), `allowedSkills` (enum array), `traits`, `hideHeads`, `card`, `Portrait`, `maxSize`, `audioTags` (name array), `requiredEquipment`, `minMeleeTraining`, `minArcheryTraining`, `minHouseLv`, `hasBannerCarrier`, `concealmentLevel`, `combatExperience`.
- Zero floats are the string "+0" in the JSON (UAssetGUI). `clone_table_row.py` converts by property type.
- Ranged units have an EMPTY `weapons` array. The ranged weapon is in `shields` (item slot `Shield`). `crossbowMilitia`: armours [52], shields [206], helmets [285]. `bowMilitia`: shields [205].
- Range, damage and reload are not in the unit row. They are item fields.

## Item row layout (`Item`) for ranged weapons
Row name is the item id. `crossbows` is row 206: `EquipmentSlot` Shield, `locomotionStance` Crossbow, `rangedAtt` 32, `shootingRange` 11500, `armorPierce` 0, `Speed` 1.0, `VAMP_Variations` [MGGN_Weapon_Crossbow] (the held mesh). `warbows` 205: rangedAtt 16, range 12750. The bolt (item 314, `VAMP_Crossbow_Bolt_Static`) has no stats. The highest item id is 358. Free ids start at 359.

## Experiment
Pak `handcannon` (built from the current 0.8.111 tables, 74 KB, not committed):
- item 359 `handCannonGun`: clone of 206 with rangedAtt 64, armorPierce 8, shootingRange 6000, Speed 0.5.
- unit row `handCannon`: clone of `crossbowMilitia` with shields [359], cost 40.

Pak `warwagon` adds item 360 (clone of 254 `tradingWagon`, def 60, block 60, Speed 0.4) and unit row `warWagon` (clone of `spearMilitia`, shields [360], maxSize 6, cost 60).

## Results
| Question | Result | Run |
|---|---|---|
| New unit row name loads | YES. `datatable_info` units: 30 rows (29 + 1). `datatable_rows` lists `handCannon`. | `20261018-110301-5a1b` |
| New item row id loads | YES. Items: 214 rows. `datatable_read` row 359 `armorPierce` = 8. | same |
| Lua can spawn the new row | YES. `spawn_units template=handCannon` gives 32 units (`maxSize` of the clone). No crash. | same |
| Item stats applied | YES. The fights show a large change from the item. Mean `att` and `def` of the squad are melee values and do not show it. | `part-a-ab-results.md` |
| `warWagon` row loads and spawns | YES. 6 units. Mean def 53.3, block 50 (item 360 is worn). | `20261018-115406-6f39` |
| New arrays in a new row | YES. The new `shields` array works. | same |

Notes:
- `datatable_read` accepts only a fixed field list. `rangedAtt`, `shootingRange` and `Speed` are refused. The pak values are proven only through fight results.
- Soft object fields (`IconTextureV2`) were copied unchanged. The game did not crash on load. They were not read through the bridge (safety rule).
- A `--keep-open` run with `--pak` fails at pak removal (the game holds the file). Stop the game, then run `pakmod.py remove --all`.
- Spike helpers: `harness/tools/s29_command.py` sends named commands to a `--keep-open` run (create `runs/<id>/commands` first).
