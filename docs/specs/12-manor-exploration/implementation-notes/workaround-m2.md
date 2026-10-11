# Workarounds for the building rule (M2)

Date: 2026-10-11. Status: in progress. Evidence is in `rule-search.md`.

| Idea | Result so far |
|---|---|
| A. Data change by pak | No data rule found in `DT_ConstructionBPs`, `DT_Upgrades`, `DT_BuildingMeshPathData`, `DT_IndependentBuildingPartAssemblies`. Not possible. |
| B. Property switch | `SetActorEnableCollision(false)` and an empty `finalBorder` on the Keep did not let a Dunghill be placed over it. Not found. Not tested on a bailey. |
| C. Hook the check | The checks are not called through reflected functions (9 hooks, 0 events). Not possible. |
| D. More manors per region | A second Keep is refused while a type 57 building exists (C++ count). `Region.manor` is one reference. Only a retype trick passes. Not a clean fix. |
| E. Smaller area | The area comes from committed modules in the planner. No data cap found. Not tested. |

Blocker for all tests of M2: a bailey area needs committed modules in the planner (UI clicks) and the Keep needs 40 builder units. The harness has no way yet to build a bailey.
M2 stays not verified.
