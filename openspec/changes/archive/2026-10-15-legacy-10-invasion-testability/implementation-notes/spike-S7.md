# Spike S7: unit data (DT_UnitTemplates)

Date: 2026-10-10. Branch `feat/28-unit-data-combat`. Real game, base fixture. Runs: `s7-explore`, `s7-explore2` (keep-open, raw Lua eval), `s7-a`, series of `unit-data` (3 of 3: `20261011-022828-09c1`, `-022907-c6e2`, `-022946-d987`, 39 s each).
Verdict: **verified.** The unit table can be listed and written at run time, and a changed value changes behavior. Criterion C3 has a verified method.

## Where the data is
There is no `DT_units`. The loaded DataTable is `/Game/NotStronghold/Data/DT_UnitTemplates.DT_UnitTemplates` (row struct `/Script/ManorLords.UnitTemplate`). It is found with `StaticFindObject`, so no engine property is needed. (`DT_UnitTemplates_OLD` and `DT_MercenaryCompanies` are loaded too.)
29 row names, 4 of them separator lines (`-----`). 25 real rows:
`bowMilitia, militiaFoot, spearMilitia, militiaPole, crossbowMilitia, retinue_tier1, retinue_tier3, Brigands, brigandArchers, brigandPolearms, Mercenary_Archers, mercenary_heavy_archers, mercenary_spearmen, mercenary_infantry, mercenary_crossbowmen, militia, basket, sherwoodBow, wrong_unit_type, militiaFoot_testing, spearMilitiaTesting, brigands_old, retinue_tier1_old, reginaldsRetinue, single`.

## Row fields (jmap)
Number fields (read and written through `HarnessDataTable`, table `units`): `cost` (float), `maxSize` (int), `minMeleeTraining`, `minArcheryTraining` (float), `minHouseLv` (int), `combatExperience` (float).
Other fields are not read: strings (`Name`, `descr`), object and soft object fields (icon, card, portrait: reading a soft field through the bridge crashes the game), and int arrays `weapons, armours, shields, helmets, mounts, bonus` (item ids into DT_Items).
There is **no hit point field**. Strength comes from the equipment item ids. No current template has a mount (`mounts` is empty; only `retinue_tier1_old` has `[0,247]`).
Values seen: `maxSize` 32 for the militia rows, 60 for retinue, brigand and mercenary rows, 1 for `single`; `cost` 0 to 100; `combatExperience` 5.0 in every row; `minHouseLv` 0 to 2.

## What was tried
| Try | Result |
|---|---|
| Read all rows and the 6 fields with `table:FindRow(name)` in Lua | works, about 3 ms for 29 rows. Booleans of other rows sometimes fail to read (not needed) |
| Write `maxSize` of `spearMilitia` 32 -> 12 and 10 | the field reads back; the next `spawnArmy` of that template made **12 and 10 units** (it made 32 before). Restoring 32 gives 32 again |
| Write the `combatExperience` of the template 5 -> 20 | read back, but the spawned unit has `combatExperience` 0. The field does **not** set the experience of new units |
| Live write versus a pak | live write works, so no pak was needed for numbers. A pak with `DT_UnitTemplates` was not tried (the pak spike only round-tripped `DT_Items`) |

## Spawn by template (needed to see the effect)
`RTSMultiEngineCPP:spawnArmy(Vector, {FName(template)}, ownerPawn, 0, 0)` works from Lua. It returns one squad id for each name. Unit counts: `spearMilitia`, `militiaFoot`, `bowMilitia`, `militia` 32; `retinue_tier1/3`, `brigandArchers`, `mercenary_*`, `basket`, `sherwoodBow` 36; `Brigands` 18; `single` 1. So the size is the `maxSize` of the row up to a shape limit (60 gave 36 or 18); the scenarios never assume it.
The owner pawn gives the side: the player pawn gives side `player`, the pawn with `isBandit` gives side `bandit`. This also solves the "choose a type" problem of spike S2 (see `spike-C1.md`). Per-unit stats (`att`, `def`, `range`, `block`, `rangedAtt`, `shootingRange`, `charge`) differ by template, for example `retinue_tier3` def 62 block 60, `brigandArchers` rangedAtt 16 shootingRange 12750, `Brigands` charge 5. `unitTemp` of a spawned unit still reads `None`.

## Harness
`mod/shared/HarnessDataTable` (tables `items` and `units`, row names, `read_all`), `HarnessActions` version 9 (`datatable_*` with `"table"`, `datatable_rows`), actions `datatable_info/read/rows/write`, scenario `unit-data` (COVERS C3): lists the rows, checks the six fields on every row, refuses an unknown table, a field that is not listed, an unknown row and a missing value, writes `maxSize` 10, checks the next squad has 10 units, restores, checks 32 again. Tests: `test_fakegame_harnessbattle.py`, `test_fakegame_battle_scenarios.py`, `test_runlib_battle.py`.

## Not verified
Writing strings, arrays or new rows; a pak change of `DT_UnitTemplates`; whether a changed `weapons`/`armours` id changes combat strength (an equipment edit would need an item id map from DT_Items); the effect of `cost` and `minHouseLv` (they are for recruiting in the UI).
