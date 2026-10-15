# Spec 12: Manor exploration (the manor system and its building rule)

Status: Lv3 mesh source round 7 (issue #90, static): the finished keep mesh is keyed by the BM part number (MainBld_167 in DT_ConstructionBPs), the ghost by buildingStats constructionMeshAsset, garrison is native; next is pak B on DT_ConstructionBPs row 167, see `implementation-notes/manor-lv3.md`. Before: Lv3 keep round 6 (issue #90, game): pak A (row 57 retargeted to the Lv3 tower) built nothing, and a vanilla tower (472) committed the same way is also not built in 60 days, so the commit flow, not the Lv3 data, is the blocker; see `implementation-notes/manor-lv3.md`. Before: Lv3 keep static study (issue #90, round 5): module Blueprints and construction assets match the working Lv1 ones; the planner cost is native (`getCastleReconstructionCost`); next test is a type id swap pak (row 57 with the Lv3 BM), see `implementation-notes/manor-lv3.md`. Before: Lv3 module (issue #90, round 4 2026-10-14): data pak `mmlv3full` (cost, tech, mesh row) did not help; planner still shows "No Construction Cost", nothing built in 60 days, garrison 12; card 123 test on a drawn slot was not clean; see `implementation-notes/manor-lv3.md`. Earlier: Lv3 module (issue #90, round 3 2026-10-14, fixture manor-closed): planner opened by `openCastlePlannerUI` shows Large 1,184 m2 and Commit is active; the Lv3 keep (83) was placed and committed by real clicks, the manor rebuilt, but no Lv3 keep was built and the garrison limit stayed 12; see `implementation-notes/manor-lv3.md`. Earlier: Lv3 module (issue #90, round 2 2026-10-14): placed in the planner by real clicks, Commit stays grey (`canConstructCastle` false), not built; see `implementation-notes/manor-lv3.md`. Earlier: spike done (2026-10-11, branch `feat/33-manor-spike`). Requirement added 2026-10-11 (branch `feat/34-manor-storage-workers`): M1 also needs a worker slot with the storehouse or granary role (Q7). Done: scenario `manor-storage-workers`, 3 of 3 real runs, M1 method verified again. Notes: `implementation-notes/worker-slots.md`. M1 (storage) method verified, 3 of 3 real runs. M2 (building inside the manor area) NOT verified. Lead from spec 13 (2026-10-11, `../13-mod-inspection/implementation-notes/summary.md`): two community mods lift the one-Keep limit by the `buildingStats` field `maxInRegion`, and the same row has an untested field `placedWithin`; the next M2 spike tests both.

Spec 13 lead (2026-10-14), garrison: MLArmyCampMod does not use the manor garrison system and has no garrison call (only a squad `camp` state); see the garrison section in `../13-mod-inspection/implementation-notes/ml-army-camp.md`.
Spike #65 (2026-10-13, partial): a pak can add a manor module row (type 123) and a mod-planned blueprint of it is committed and supplied by builders; the planner list is fixed widgets in `castlePlanner` (a pak can retarget them). Follow-up 2026-10-14: the planner opens on a finished manor (command `manor_planner`, the panel needs `SetVisibility`). Follow-up 3 (2026-10-14): card 123 is not drawn in the planner even with all other cards collapsed; a finished module is not proven (builders finished 1 of 6 runs; the part listing timed out). Still open. See `implementation-notes/manor-module-pak.md`.
Unused assets (2026-10-13, static): a finished level 3 manor (palace row 81, gatehouse row 82, keep/garrison row 83 with garrison 36) exists in the paks and data but has no name text and no visible card. Notes: `implementation-notes/unused-assets.md`.
Findings are in `implementation-notes/` (`../17-bailey-buildings/implementation-notes/bailey-buildings.md`, `manor-survey.md`, `rule-search.md`, `storage-m1.md`, `workaround-m2.md`).

### Answers (short)
- Q1: no manor class. The manor is `SMBuildingMaster` actors per module (Keep type 57 and others). The `BM_SG_Manor_*` Blueprints are empty mesh actors. The area is the "bailey" polygon of committed planner modules (Keep alone: 49 m2).
- Q2: the rule is in C++. No data column, no Blueprint logic, and 9 hooks on candidate natives got 0 events (a control hook got 720).
- Q3: the Keep has an `Inventory` and `addToInventory` works (region stock follows), but the base game does not use it as a store.
- Q4: not tested inside a bailey (none could be built). Over a Keep footprint a normal building is refused; collision off and an empty `finalBorder` did not change that.
- Q5: `Region.manor` is one reference; a second Keep is refused while a type 57 building exists (C++ count; clearing `Region.manor` did not help).
- Q6: not found from Lua (see `rule-search.md`).
- M1 way: a mod-defined store on the Keep inventory, with a harness shortcut to finish the Keep (5 families cannot build it: 40 builder units).
- Q7: yes. The slots and the role of a building come from its row in the loaded DataTable `buildingStats` (row name = type id; `workerTypes.Y` slots, `job` role). Writing the Keep row (job 45 WarehouseWorker, 3 slots) from Lua gives the Keep the slots of a Storehouse. `Region:assignFamily(index, building)` assigns a family, and that worker carries goods into the Keep (7 to 9 units in 3 game days, none without the worker). A real Storehouse (72) or Granary (80) with a worker also carries goods; a mod can list them as manor members. Roles: Storehouse 45, Granary 44.

## Goal
Understand how the manor (the castle in the UI) works, and find out if it can be changed with the tools of this project (Lua mods, data tables, paks):
1. Learn how the manor is built: modules, levels, the planner, the area, and what may be placed inside it.
2. Learn if the manor can hold supplies, or if granaries and storehouses can be built as part of it.
3. Stretch goal: find a workaround for the soft-lock bug (see below).

## Why
- The Invasion Mode plan uses stockpiles as raid targets and as sack losses (spec 10, criteria R6, R7, S1). A manor that stores supplies, or a manor area that holds storage, is a natural target.
- A mod must not make the soft-lock worse. A big manor can stop the player from building the city.

## The reported bug (user report, not verified)
- The manor has an area. Inside that area, only manor buildings can be placed. At the moment, those are the tax office and the keep or garrison.
- If the manor grows until it covers the whole city, normal buildings (burgage plots, industry) can no longer be built inside the castle area. The player is then locked out of building the city.
- The user remembers that the developers said a source code rule stopped them from fixing it. This is a memory, not a checked fact.
- Open: is the rule in C++ (then Lua can only work around it) or in data or a Blueprint (then a pak may fix it)?

## Non-goals
- Shipping a polished fix. This spec finds out what is possible and records it.
- Changing the base game for the player without a clear, tested switch.
- Editing C++ (not possible here) or repacking the game executable.

## Background (checked on 2026-10-11, names from the game paks only)
The manor is made of modules. The cooked Blueprints are in `ManorLords/Content/CPP_BP/BuildingMasterAssemble/ManorModules/`:
- `BM_SG_Manor_Lv1_Gatehouse`, `Lv2_Gatehouse`, `Lv3_Gatehouse`
- `BM_SG_Manor_Lv1_Keep`, `Lv2_Keep`
- `BM_SG_Manor_Lv1_Palace_Solo`, `Lv2_Palace`, `Lv3_Palace`
- `BM_SG_Manor_Lv1_Tower_`, `Lv2_Tower_`, `Tower_Lv3`
- `BM_SG_Manor_Wall_Lv1`
Other names:
- `ManorLords/Content/UI/Castle_Planner/castlePlanner` (the planner screen) and `ManorLords/Content/CPP_BP/RT_castlePlannerBlob` (data for the planner).
- `ManorLords/Content/ManorLords/UI/Cards/card_keep_lv1` (UI card for the keep), `icon_garrisonSpace` (UI icon).
- No Granary or Storehouse module exists in `ManorModules`. No asset is named `TaxOffice`. The normal buildings are in the folder `BuildingMasterAssemble/` (for example `BM_SG_Church_Lv1`, `BM_Livestock_Barn`, `BM_ConstructionYard`).
- Related data tables that may hold rules: `DT_ConstructionBPs`, `DT_Upgrades`, `DT_BuildingMeshPathData`, `DT_IndependentBuildingPartAssemblies` (all under `NotStronghold/Data/`). Not read yet.
- All game assets are encrypted in the paks. The key is local and never in git (spec 09). Only names are recorded here.

## Questions
Q1. Structure: which classes make up the manor (C++ and Blueprint)? Is the manor one actor with module parts, or several actors? What is the footprint (area), how is it stored, and how does it grow?
Q2. Rule: where is "only manor buildings inside the manor" decided? Candidates: a flag on the building class (for example a placement category), the planner blob, a data table row, a collision or overlap check at placement time, or a C++ check.
Q3. Storage: does the manor have an inventory or storage component? Does the keep hold goods? Can a Lua mod read stock per manor module?
Q4. Reuse: can a normal granary or storehouse be placed inside the manor area today (placement action, spec 07), or does the placement check refuse it?
Q5. Per region: how many manors does a region allow? Where is that limit (a count on the region, a flag on the building type, a unique-building rule)?
Q6. Collision: what does the placement check use for blocking (collision channels, overlap volumes, a "no build" mask, a navmesh or terrain tool)? Can it be switched off for parts of the manor from Lua (a property on the module, a component that can be disabled)?
Q7. Worker slots: the game may need worker slots on storage buildings. Can a worker slot with the role of a storehouse or granary worker be created on the manor storage building (the Keep)? Can a family be assigned, and does that worker carry goods in or out of the store? If not, can a Storehouse or Granary count as part of the manor (mod-defined) and use its normal worker slots?

## Plan
1. **Read-only survey (no game change).** With the bridge: list the manor classes and their functions and properties (`list_types`, `list_functions`, `find_objects`), and read the manor actor and its modules in a save that has a manor (check the fixtures; if none has one, build a fixture, see "Open"). Record the class tree and the footprint. Answers Q1 and Q3.
2. **Rule search.** Read `DT_ConstructionBPs`, `DT_Upgrades`, the mesh and assembly tables, and the planner blob through the pak tools (names and values only; no game asset goes into git). Look for a field that links a building to the manor or limits it ("manor only", "inside manor", category, count). Also read the bytecode of the planner Blueprint with UAssetGUI for strings and calls (read-only). Answers Q2 and Q5.
3. **Placement test.** In a save with a manor, try the placement action for a burgage plot and for a granary inside, at the edge of and outside the manor area. Record the refusal, and any message or function the game calls on refusal. Hook that function with UE4SS to see the check (hook only; no save calls). Answers Q4.
4. **Storage test.** Read the keep and other modules for inventory fields, and try to put goods in with the existing sack and stock actions (`consumeGoodNoCheck` and `GiveItemByID` from spec 10) to see if stock is counted per manor module. Answers Q3.
5. **Workaround spikes (stretch).** Try in this order, and stop at the first that works:
   - A. **Data:** change the rule in a data table through a pak, if step 2 found one (A/B with `--pak`, spec 09).
   - B. **Property switch from Lua:** change the flag or category that blocks normal buildings, or disable the blocking collision or overlap on a manor module (Q6) at run time.
   - C. **Hook the check:** hook the placement validation function and let normal buildings pass inside the manor area (keep the manor rule for other cases). Needs the function to be a reflected UFunction.
   - D. **More than one manor per region:** find the limit (Q5) and raise it by data or property; test if two manors can stand in one region and cover separate parts of the city.
   - E. **Smaller area:** keep the area from covering the city (cap the area, or let modules stay in a ring). Only if the area is data.
6. **Test method.** For every working idea add a scenario with `COVERS` (new criteria, see below) and an A/B run with and without the workaround. The soft-lock test: build a manor that covers a test area, try to place a burgage plot inside, and expect success with the workaround and refusal without. The placement action uses the real mouse (hidden scenario `place-building`), so these scenarios are exclusive (spec 11) and run alone.
7. **Record.** Findings go to `implementation-notes/` (one file per question or spike). Update this spec, spec 10 if criteria R6 or R7 change, and the CHANGELOG.

## Open questions and risks
- Do the test fixtures contain a manor? If not, building one needs the real-mouse placement of several modules and the resources to pay for them (the `give` actions can supply goods). A fixture made from a play-through save of the user would need the user's help (the harness never writes to the user's saves).
- The rule may be in C++ with no reflected function. Then only B, D or E can work, and maybe none.
- Collision tricks may break pathing or building placement elsewhere. Every workaround needs a test that normal outside-the-manor building still works.
- Memory of the developer statement is unverified. If the developers already fixed or changed the rule in a later game version, step 3 shows it.
- Placement works only with a real OS mouse click today (spec 07). Step 6 depends on it. A faster way to place buildings (a direct function) would help.
- The mod is for single-player. Nothing is done for multiplayer.

## Acceptance criteria
These are part of the Invasion Mode goal (spec 10, criteria M1 and M2). The current castle design does not allow a real defense. Meet at least one of the two scenarios; both is better.

**Scenario 1 (M1): storage in the manor.** Goods can be stored within the manor.
- [x] A scenario (COVERS M1, `manor-storage`, runs `manor-storage-1` to `-3`) puts goods into the manor (or a manor module, or a storage building that is part of the manor), reads the stock back, takes some out, and reads the stock after game days. It passes 3 of 3 real-game runs.
- [x] (added 2026-10-11, spec 12 branch `feat/34-manor-storage-workers`) A worker slot with the storehouse or granary role exists on the manor storage building, a family is assigned to it, and that worker moves goods into or out of it within a few game days (ranges, not exact values). Scenario `manor-storage-workers` passes 3 of 3 real-game runs (`manor-storage-workers-v2-1` to `-3`). If the Keep cannot get such a slot, the notes say so, and the alternative (a Storehouse or Granary treated as part of the manor, with its normal slots) is tried. Notes: `implementation-notes/worker-slots.md`.
- [x] The way is named (a Lua store on the Keep inventory; the others failed, see `storage-m1.md`): the manor gets an inventory, or a granary or storehouse can be built as part of the manor, or a Lua storage layer is tied to the manor. The notes say which, and why the others failed.

**Scenario 2 (M2): normal buildings inside the manor.** The player can wall in the city.
- [ ] A scenario (COVERS M2, exclusive, real mouse) builds a manor that covers a test area, then places a burgage plot and an industry building inside it. With the workaround the placement succeeds; without it, it is refused (A/B). It passes 3 of 3 real-game runs.
- [ ] The workaround is named: a data change, a property switch (collision off on manor parts), a hooked placement check, several manors per region, or a smaller area. The notes say which, and show that normal building outside the manor still works.

**Survey and hygiene**
- [x] Notes answer Q1 to Q6, each with evidence (class names, property names, values) or a clear "not possible, because".
- [x] A class tree of the manor and its modules is recorded (names only, no assets in git).
- [ ] (partly: over the Keep only; no bailey) The placement test shows if normal buildings are refused inside the manor area, and the refusing check is named if it can be found.
- [ ] If neither scenario is possible, the notes explain why with evidence, and criteria M1 and M2 are marked blocked with that reason.
- [x] No game asset, key or copy of game data is in git.
