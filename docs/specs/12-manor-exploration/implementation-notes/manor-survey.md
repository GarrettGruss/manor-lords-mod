# Manor survey: classes, area, how it is built (Q1, Q3)

Date: 2026-10-11. Game: real game, base fixture (`saveGame_0`, Jagged_Cliffs), a `--keep-open` run with the bridge and raw Lua eval (experiments only).
Names only. No game asset is in git.

## Fixtures have no manor
The only fixture (`base`) is a new start: 4 or 5 buildings (HitchingPost 30, two Supplies 88, HomelessTents 87), 5 families, 10 people. No manor.
A manor was built in the live game with `place_building` (real mouse).

## Class tree
- There is **no manor class**. The manor is made of ordinary `SMBuildingMaster` actors (C++ class `/Script/ManorLords.SMBuildingMaster`).
  Type names in the enum `EBuildingType`: Manor_Walls 50, Manor_Keep_Lv1 57, Manor_TaxOffice 58, Manor_Palace_Lv3 81, Manor_Gatehouse_Lv3 82, Manor_Keep_Lv3 83,
  Manor_Gate_Lv1 95, Manor_Palace_Lv1 98, Manor_OuterTower_Lv1 472, Manor_Palace_Lv2 474, Manor_Keep_Lv2 475, Manor_Wall_Stone_Small 476, Manor_Wall_Stone_Large 477,
  Manor_Gate_Lv2 478, Manor_OuterTower_Lv2 479 (also WoodenWallPiece 470, WoodenPlatform 471).
- The cooked Blueprints `BM_SG_Manor_*` (pak folder `CPP_BP/BuildingMasterAssemble/ManorModules/`) are **plain StaticMeshActor Blueprints**:
  one `StaticMeshComponent` with a merged mesh and (Keep, Gatehouse) a preview plane. Read with UAssetGUI (Keep, Gatehouse, Wall): no function, no variable, no bytecode.
  They are the preview ghosts of the planner. They carry no rule and no storage.
- The planner screen `UI/Castle_Planner/castlePlanner` (widget Blueprint) only calls native functions: `canConstructCastle(outReasons)`,
  `getBuildingArea`, `getReconstructedCastleArea`, `getCastleLevelFromArea`, `formatReasonWhyCantConstruct` (enum `EReason`).
  Cards: `card_keep_lv1`, `card_sg_Gatehouse`, `card_tax_collector`, `card_tower_lv1`. `RT_castlePlannerBlob` is a render target (8 names, no data).
- Native members that matter:
  - `SMBuildingMaster`: functions `isManor`, `hasModuleOfType(int)`, `getModuleTypes`, `canConstructCastle(outReasons)`, `canAffordCastleReconstruction`,
    `getCastleReconstructionCost`, `getReconstructedCastleArea(smoothBorder, triangulatedBorder)`, `getCastleLevelFromArea(area)`, `getBuildingArea`,
    `getModularGarrisonLimit`, `spawnManorServantsInside(n)`, `spawnModuleMask`, `doesCastleModuleNeedReconstruction`.
    Properties `bModuleMaster`, `moduleMasterPtr`, `masterPtr`, `areaMasterBld`, `moduleMasks`, `walls`, `blueprints`, `blueprintGhosts`, `finalBorder`.
  - `PawnCPP`: `openCastlePlannerUI(building)`, `selectCastleBlueprint(blueprint, followMode)`, `spawnCastleFloater`, `splitWallsByCastleModule(actor)`, `getManors()`,
    `castlePlanningTools`, `destroySelectedCastleBlueprint`.
  - `RTSMultiEngineCPP:setRegionsManor(manor)`. `Region.manor` (one ObjectProperty).
  - Struct `SavedCastleModule` (bType, wallType, Transform, meshOverride, CustomPrimitiveData, ActorTags): the save format of a module.
- The planner modules (Gatehouse, Tower, Palace-or-Residence, Tax collector) are Blueprint ghost actors until the player presses Commit.
  Before a commit `Region:GetBuildings()` lists only the Keep.

## Footprint and growth
- The Keep alone: `getBuildingArea` = 490000 (cm2, 7 m x 7 m), the planner shows "Bailey Area Modest (0 m2) to Modest (49 m2)", "Castle Level: Modest" (`castle_level_small`).
- The area is the "bailey area": the polygon that the modules and walls enclose (`getReconstructedCastleArea` fills two border arrays, `finalBorder` holds the building polygon).
  `getCastleLevelFromArea` maps the area to a level. The level gates garrison, family space, retinue and administration level.
  So the manor area grows when the player commits more modules and walls in the planner. It is not a data table.
- Placing modules needs UI clicks (select a module card, click the ground, Commit). This session did not finish a bailey (see `workaround-m2.md`).

## Building a Keep
- The Keep costs 10 wood (16), 15 planks (17) and 10 rubble (15), read from the build preview and `constructionGoods`.
- The goods are carried to the site (about 4 game days), but the site then stays at `getConstructionStatus` = `not_enough_workers`:
  `getNumBuilders` returns (0, 40): the Keep needs 40 builder units. The 5 families of the test village never finish it (14 and 24 game days tried, with a Construction Yard
  (type 119, workers assigned with `Region:assignFamily`) and two oxen). A Dunghill (needs 5) is built in 3 to 4 game days in the same village.
- Harness shortcut (not base game): writing `site.Data.constructed = true` makes `IsConstructed()` true and the status `Finished`. `RTSMultiEngineCPP:setRegionsManor(site)` then sets `Region.manor`.
  `isManor()` stays false and `PawnCPP:getManors()` stays empty after that: the base game sets more state when it finishes a Keep. The shortcut gives a built Keep, not a full manor.

## Q3: storage
See `storage-m1.md`.
