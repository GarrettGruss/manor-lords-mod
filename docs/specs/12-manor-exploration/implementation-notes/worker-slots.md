# Worker slots on storage buildings (Q7, criterion M1)

Date: 2026-10-11. Branch `feat/34-manor-storage-workers`. Real game, base fixture, run `workers-spike-1` (`--keep-open`, hidden probe scenario, bridge with raw Lua eval).
`allow_eval` was set to true in the deployed `UEBridge/scripts/settings.lua` for the spike and set back to false after it. Game time at 8x. Run 203 of 400.
Names and numbers only. No game asset is in git.

## Answer to Q7
**Yes.** A worker slot with the storehouse role can be created on the Keep from Lua. A family can be assigned, the assignment holds, and that worker carries goods into the Keep.
The base game decides the slots from a loaded DataTable, and a Lua write to one row is enough. Details below.

## Where the slots come from
- The DataTable `/Game/NotStronghold/Data/buildingStats` (row struct `/Script/ManorLords.Stat`, 104 rows) is loaded in memory. The **row name is the building type id** as text ("72" is the Storehouse).
  `table:FindRow("72")` works in Lua. Fields (plain numbers and a Vector4) can be read and written. (Not the soft object fields.)
- Fields that matter:
  - `workerTypes` (a Vector4): the number of worker families is `Y`. Storehouse 3, Granary_Lv1 3, Granary_Lv2 6, Storehouse_Lv2 6, HitchingPost 2, Keep 0. `X`, `Z`, `W` are 0 for these rows.
  - `job` (int, enum `EJobType`): the role of the worker.
  - `isWork` (bool), `buildingFunction` (enum `EBuildingFunction`), `storageLimitGeneric`, `storageLimitPantry`, `storageLimitLarge`.
  - `occupantTypes` (Vector4): residents of a house (BurgagePlot_Lv1 has `Y` = 1). Not used for workers.
- `SMBuildingMaster:getMaxWorkerFamilies()` and `getJobType()` read the row of `Data.bType` **live**. Retyping the Keep (`Data.bType` 57 to 72 and back) changed them at once (0 to 3, 0 to 45). A write to the row changes them too, with no restart.

## Role (job) values (`EJobType`)
| Building | Type id | `job` | Role name | `buildingFunction` | Slots (`workerTypes.Y`) | Storage limit |
|---|---|---|---|---|---|---|
| Storehouse_Lv1 | 72 | 45 | WarehouseWorker | 6 Warehouse | 3 | generic 250 |
| Storehouse_Lv2 | 99 | 45 | WarehouseWorker | 6 | 6 | generic 2500 |
| Granary_Lv1 | 80 | 44 | GranaryWorker | 5 Granary | 3 | pantry 500 |
| Granary_Lv2 | 68 | 44 | GranaryWorker | 5 | 6 | pantry 2500 |
| Keep (Manor_Keep_Lv1) | 57 | 0 | none | 0 Default | 0 | generic 50 |
| Tax office (Manor_TaxOffice) | 58 | 47 | TaxCollector | 0 | 0 (`isWork` false) | generic 50 |
| HitchingPost | 30 | 51 | OxHandler | 11 | 2 | none |
Other roles near these: LarderWorker 43, GranaryWorker 44, WarehouseWorker 45. `EBuildingFunction` Granary 5, Warehouse 6.
Instance reads on real buildings (built in the live game): Storehouse maxWF 3, job 45, `isStorageTypeBuilding` true. Granary maxWF 3, job 44, true. Keep maxWF 0, job 0, false.
The Keep and the tax office are not storage buildings and have no storehouse worker. The tax office has a job (47) but no slots.

## Creating the slot on the Keep
Write to the row "57" of `buildingStats` (in memory only; it is lost when the game ends):
`isWork = true`, `job = 45`, `workerTypes.Y = 3`, `buildingFunction = 6`, `storageLimitGeneric = 250`.
Read back on the Keep instance: `getMaxWorkerFamilies()` 0 to 3, `getJobType()` 0 to 45. The instance copies `buildingFunction` and `storageLimitGeneric` when it is created, so the write to the instance
(`Keep.buildingFunction = 6`) is needed for `isStorageTypeBuilding()` to turn true. (It did: false to true. `HasStorageLimits()` stays false for the Storehouse too.)
Tests of single fields: `workerTypes.Y` = 0 gives maxWF 0 (the slot count). `job` = 0 gives job 0. `isWork` alone changed neither getter. All three stay set in the scenario.
This changes every building of type 57. A region has at most one (spec 12, Q5).

## Assigning a family
- `Region:assignFamily(familyID, workplace)` (parameters: int, object). The family id is the zero-based index in `Region.workerFamilies`. `Region:unassignFamily(familyID)` undoes it.
- After `assignFamily(0, storehouse)`: `family.assignedTo` is the storehouse, `Region:getNumUnassignedFamilies()` 5 to 4, `building.assignedFamilyIDs` length 0 to 1,
  `getAssignedFamiliesUI()` 1 entry, `getAllWorkers()` 2 (the two members of the family).
- `getNumActiveWorkerFamilies()` and `numActiveWorkerFamilies` stay 0 after an assignment. They are the "active" toggle of the UI: `addActiveWorkerFamily()` gives 1, `removeActiveWorkerFamily()` back to 0.
  Hauling happened with the toggle at 0. So an assignment is what counts. Use `assignedFamilyIDs` for tests, not the active count.
- The assignment held for all of the runs below (at least 1100 game seconds, 27 game days) until `unassignFamily`.

## Does the worker carry goods? (positive and negative controls)
Village: base fixture, a built Storehouse (72), Granary (80), Keep (57, finished with the shortcut). Two Supplies crates (type 88) hold the goods. Counts are inventories per building. 8x speed, 80 game seconds (2 game days) per step.
1. All three have a worker (families 0, 1, 2): in 2 steps the Storehouse gets rubble 0 to 50 (crates 95 to 45), the Granary gets food (172: 18), the Keep gets 216: 5 then 6, food 6: 6, and rubble.
2. All families unassigned (`unassignFamily` 0 to 4), 2 steps (160 game s): **no change** in any building (rubble 50, 18, ... the same). Totals rose only by the village production of good 6 (8 to 10).
3. **Only the Keep has a worker** (family 2): the Storehouse stays at 15:50, the Keep gets rubble 4, 10, 15 and food 216 6 to 9 over 3 steps, the crate falls by the same amount. 2 more steps: rubble 16, 20, then 25. About 5 units of rubble per 2 game days.
4. The Keep worker with `buildingFunction` set back to 0 (`isStorageTypeBuilding` false): it still carries (216: 15 to 20 and rubble 15 to 16 in 2 steps). So the worker slot and the assignment are what matter, not the function flag.
Goods that did not move in any step: wood 16, planks 17, stone 27 and 78 in crate 1 (100 each, put there by `give_item`), also with `storageLimitLarge` 250 on the Keep. Rubble (15) and food (216, 6, 172) moved.
The reason is not known (it may be a rule of the worker for which goods count). In a later run the Keep worker did carry planks (17). The scenario counts all goods that arrive without a harness put.

## Scenario result (`manor-storage-workers`)
Mod: `HarnessManor` (`worker_slot`, `assign_worker`, `unassign_workers`, `worker_state`), `HarnessActions` version 13. Hidden scenario, real mouse, about 90 s.
Steps: place a Keep and finish it (shortcut), check slots 0 and job 0, write the slots (3, job 45), wait 2 game days (the builders' last deliveries), control 2 game days with the slot and no worker (total goods unchanged),
assign a family, wait 3 game days, check that 4 or more units arrived with no harness put, the family is still assigned, the region stock of the counted goods is unchanged, and take one unit of a carried good out.
- First real run `manor-storage-workers-1`: failed the control (4 rubble arrived in the first 2 game days). A second probe (`workers-spike-2`) showed why: rubble 3 then 6 arrived with no slot (builders), then nothing for 6 more game days.
  With the worker, planks (17) rose 1, 4, 7, 9, 12 and rubble stayed at 6. So the worker picks the good (planks here, rubble in the first spike). The test counts all goods and waits first.
- 3 of 3 passed: `manor-storage-workers-v2-1` (7 units hauled), `-2` (7), `-3` (8). The control total stayed the same each time.
Runs used by this work: 6 (2 probe runs, 1 failed scenario run, 3 passing runs; the counter went from 202 to 208).

## The other idea: a Storehouse or Granary as part of the manor
A real Storehouse with a worker carries goods by the base rules (point 1: rubble 50, built and assigned with `assignFamily`). It needs no change. Membership in the manor is mod-defined (`HarnessManor`: a Storehouse or Granary
listed as a member is read by `manor_state`, `manor_put` and `manor_take` like a module). The base game has no such link; the area rule (Q2, Q4) is not involved.
Both ways work. The Keep slot is the closer reading of "worker slot on the manor storage building".

## What was not tried
- Which goods the worker carries and why (wood, planks and stone stayed in the crate).
- Carrying goods **out** of the Keep (to a builder or a market). Only "in" was seen.
- A Keep that the game finished by itself (the shortcut was used). Other manor modules (Gatehouse, Palace).
- A save and reload with the changed row (never save). The row is in memory only, so a mod must write it at every start.
- Whether a second storehouse worker role (LarderWorker 43) can be used.
- The tax office slots (`job` 47 exists, `workerTypes` is 0). Not tried.
