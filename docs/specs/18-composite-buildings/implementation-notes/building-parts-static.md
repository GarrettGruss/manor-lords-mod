# What defines the parts of a building type (static read, 2026-10-13)

Sources: the jmap of the game (`ue4ss/ManorLords-5.5.4-...jmap`) and the exported tables in the git-ignored `modtools/work/json`
(from the pak, spec 09). No game asset is stored in git. The AES key is not available in this session, so nothing was extracted again.

## Classes and structs (jmap)
- `SMBuilding` (native class): only `buildingMaster` (back pointer to the master) and `controllableGate`. It is a plain actor. The
  mesh sits in a `StaticMeshComponent0` that a spawned part carries from its blueprint.
- `SMBuildingMaster` (native class): `buildings` (Array of SMBuilding = the parts), `Extensions` (Array of `Extension`: `Type`, `transf`,
  `buildings`, `dirtPlanes`), `UpgradesReplacingVisuals` (`UpgradeMeshReplacement`: one `building` pointer), `blueprints` and
  `blueprintGhosts` (manor planner actors), `moduleMasks`, `upgradesDone`, `Data` (`BuildingDataStruct`: `bType` is an Int), `buildingFunction`
  (`EBuildingFunction`, 23 values, 7 = Temporary = tent). Functions seen: `SetupBuilding`, `ChangeExtension`, `BeginUpgrade`,
  `spawnModuleMask`, `spawnPlotDressing`, `spawnRandomClutter`, `convertBlueprintsToBuildings`, `getModuleTypes`. None adds a part by a call with
  plain arguments.
- `Stat` (row of `buildingStats`): `BlueprintPath` (SoftClassPath), `assemblyBlueprintVariations` (Array of SoftClassPath),
  `constructionMeshAsset`, `buildingFunction`, `occupantTypes`, `isModule`, `moduleCategory`, `placedWithin`, `upgrades`, `bVisibleInUi`,
  `BuildingCategory`, `maxInRegion`. So the row names the blueprint class that makes the master's parts.
- `EBuildingType` (enum): only 100 names are reflected (3 BurgagePlot_Lv1, 57, 58, 87 HomelessTents, 100 BanditCamp, 472, ...), but table keys
  go up to 543 and `bType` is a plain Int. The enum looks like a name list only. Not tested: whether a row with a new number works.

## Data tables (exported JSON)
- `DT_BuildingMeshPathData` (row key = `bType`, 72 rows, struct `PathData`): a soft path to the merged mesh of the building (for
  example 58 -> `SM_MERGED_C_SG_TaxCollectorProper`, 57 and 472 -> tower meshes). No row for 3, 87 or 100.
- `DT_ConstructionBPs` (row key = `bType`, 186 rows, struct `ConstructionBP`: `constructionAsset` soft class, `buildingPartName`): the
  construction blueprint of a type (58 -> `C_SG_TaxCollectorProper_C`, 472 -> `C_SG_Manor_Tower_Lv1_00_C`). No row for 3, 87 or 100.
- `DT_IndependentBuildingPartAssemblies` (row key = a name like `outhouse`, `smallShedPlanked`, 73 rows, `ClassPathData`): classes
  under `/Game/CPP_BP/BuildingMasterAssemble/...` (`BM_Outhouse_C`, `BM_sg_smallShedPlanked_C`). These are the yard props of plots.
- `BM_*` assembly blueprints (example `BM_SG_Manor_Wall_Lv1`, exported): a Blueprint class (StaticMeshActor based) whose
  construction script holds a `StaticMeshComponent` per piece (here `MainBld_470` with one merged mesh) plus a dev text. This is the
  asset that holds the part list and the mesh choice of one type.
- Tent (87) and burgage plot (3) are not in the exported tables. Their `buildingStats` row is not exported either, and reading a Stat row
  with soft fields through the bridge crashes the game. So the `BlueprintPath` of 87 and 3 is NOT read. It is expected to be a
  `BM_*` class (the live tent shows the mesh `SM_MERGED_C_HuntersTent`, class name `BM_HomelessTents_C` in spec 15 notes).

## Answer to "which asset holds the part list" (partly open)
Per type: the `buildingStats` row (`BlueprintPath`, `assemblyBlueprintVariations`) -> a `BM_*` Blueprint class with the mesh components.
Extra tables: mesh path and construction blueprint by `bType`. Plots add random props (`spawnPlotDressing`, `spawnRandomClutter`,
the part assemblies table). Evidence is the jmap plus the exported tables above. Not confirmed in the game: the link row -> class for 87 and 3.

## What a pak would have to change for a new composite type (plan, not tested)
1. A new `BM_<name>` Blueprint class (StaticMeshActor with the part meshes). Needs new or reused meshes, cooked.
2. A new `buildingStats` row (new int key) with `BlueprintPath` to that class, `buildingFunction`, cost, `bVisibleInUi`, category.
3. Rows in `DT_BuildingMeshPathData` and `DT_ConstructionBPs` with the same key (for types that use them).
4. Text rows (name) in the string table.
Open: does the build menu read the list from `buildingStats` only, and does native code have a fixed id switch? That needs a pak test.
All four steps need the AES key to extract and repack (blocked).
