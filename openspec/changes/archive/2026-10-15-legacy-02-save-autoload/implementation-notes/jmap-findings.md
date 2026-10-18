# Manor Lords jmap findings (UE 5.5.4, build CL 40574608)

Source: `...\Binaries\Win64\ue4ss\ManorLords-5.5.4-40574608+++UE5+Release-5.5-5e627997.jmap` (101 MB JSON; top keys: metadata, image_base_address, engine_offsets, objects, vtables).
Object type counts: Function 18127, Class 5560, ScriptStruct 5452, Object 6214, Enum 2071, Package 809. Only classes/functions/structs/enums/CDOs are dumped, NOT live instances (no World/Level/actor instances, so no map names).
"(BP)" = Blueprint-generated, "(C++)" = native /Script/ManorLords. Some BP functions have spaces in names (e.g. `Request Autosave`).

## 0. How much is reflected
- Game module: **/Script/ManorLords**. Game-owned plugins: `/Script/SystemCore` (Navi* UI), `/Script/VertexAnimationManager`, `/Script/SpatialSystem`, `/Script/AutoSettings`, `/Script/AutoSettingsInput`, `/Script/AsyncLoadingScreen`.
- /Script/ManorLords: 157 classes, 1672 UFunctions, 242 structs, 105 enums. /Game Blueprints: 514 classes, 3973 functions (mostly UI/UMG, ExecuteUbergraph, anim).
- Non-/Script/Engine classes total 3719, but nearly all are stock engine plugins (MeshModelingToolsExp, Niagara, AIModule, UMG...). Game-specific is about 157 native + 514 BP + ~100 in game-owned plugins.
- Conclusion: the sim is C++ (`RTSMultiEngineCPP`, `Region`, `SMBuildingMaster`, `SMUnit`, `PawnCPP`) but it IS heavily reflected: ~1.7k native UFUNCTIONs, and nearly all sim state is UPROPERTY on those actors. Many are `Native` only (not BlueprintCallable) but UE4SS can still call/read any reflected UFunction/UPROPERTY. NOT reflected: per-frame tick logic, pathfinding, job/AI task execution (SMUnit.Tasks is a property, logic native), Spatial grids.
- Goods are plain ints (`Good.Type` = item id, `Good.amt`); item table is a DataTable (`RTSMultiEngineCPP.itemStats`, struct `Item`). `MLBlueprintFunctionLibrary:TypeToName/TypeToStr(Int)` map ids to names.

## 1. Save / load
Classes: `/Script/ManorLords.MLSaveGame` (full world snapshot: day, Year, daysTotal, monthsTotal, gameTimeAdjusted, savedRegions[Approval, regionalWealth, workerFamilies...], savedLords[treasury, influence], savedBuildings, savedUnits, savedResources, tradeLog, productionLogs, LevelName, saveName, saveSlot), `MLSaveGameDescr` (date, Version, saveVersion, LevelName, saveName, saveSlot, UncompressedSize), `MLMenuSaveGame`, `SaveSettings`.

SAVE (on player pawn `/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C` : `/Script/ManorLords.PawnCPP`):
- `PawnCPP:requestSaveFile(SlotName:Str, saveName:Str) -> bool` (C++, BlueprintCallable)
- `MyPawnCPP_BP3_C:SaveToDiskWithThumbnail(SlotName:Str, OverrideSaveName:Str)` (BP)
- `MyPawnCPP_BP3_C:Request Autosave(WasGamePaused:Bool)`, `Set Autosave Timer(Time:Double)`
- `MLGameInstance:RequestMenuSave()`, `SetAutosavePeriod(Float)`
- Input event `MyPawnCPP_BP3_C:InpActEvt_quicksave_K2Node_InputActionEvent_18(Key)`; there is NO quickload action.
- `MLGameInstance:ExportSaveThumbnailRT / ImportSaveThumbnail / DeleteSaveThumbnail(WorldContextObject, SaveGameName)`
- `MLCheatManager:PrintSaveFiles()` (Exec) logs slots.
- Completion hook: `PawnCPP:playSaveFinishedNotif()` (BP event); `PawnCPP:updateAnySaveMenu`.

IO layer `/Script/ManorLords.IoHandler` (all Static BlueprintCallable; call on `/Script/ManorLords.Default__IoHandler`):
- `DoesSaveGameExist(SlotName:Str)->bool`, `DeleteGameInSlot(SlotName)->bool`, `IsSaving()->bool`
- `LoadGameFromSlot(SlotName:Str)->SaveGame` (returns an MLSaveGame object: lets you READ a save's contents as telemetry without loading it)
- `SaveGameToSlot(SaveGameObject, SlotName, ioCategory:EIoFileCategory)->bool`, `LoadDataFromSlot(out Bytes, SlotName)->bool`, `SaveDataToSlot(...)`, `PurgeSaveFileWriteCache()`
- `EIoFileCategory`: None0, MapSave1, ImageLarge2, ImageSmall3, PlayerProfile4, Descriptor5.

LOAD (no native "LoadGame(slot)" UFunction; driven by the main-menu BP):
- `/Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C` (parent `MLMainMenuScreen`):
  - `LoadGame(SaveGameSlot:struct SaveGameSlot{SlotIndex:Int, Descriptor:MLSaveGameDescr})` is the real load entry point
  - `continue()` (Continue button, latest save), `startNewGame()`, `SwitchToLoadScreen(SaveMode:Bool)`, `GoToGameSetup()`, `closeLevel()`, `EnsureStartAchieved()`
  - bound button events: `BndEvt__mainMenu_widget_menuButton_continue_..._OnClicked`, `..._menuButton_loadGame_...`, `..._menuButton_saveGame_...`
- `/Game/UI/Main_Menu/menu_saveLoadMenu.menu_saveLoadMenu_C` (parent `MLSaveLoadMenuScreen`): `Update Save Slots`, `startUpdateSaveSlotsAsync`, `AddAutosaveSlot`, `AddQuicksaveSlot`, `AddSlot(SlotNumber)`, `MakeSlotNameFromSlotNumber(SlotNumber:Int)->SlotName:Str`, `MakeDescriptorNameFromSlotName`, `IsNowLoading`. C++ base: `StartSlotDiscovery`, `GetFreeSlotName`, `SlotNameFromIndex(Int)->Str`, `DeleteSaveSlot`, `RenameSaveSlot`; props `NamedSlots:Array<MLSaveGameDescr>`, `SortedSlotsByDate:Array<SaveGameSlot>`.
- `MLGameInstance.savefileToLoad:Str` (UPROPERTY) is the pending slot name consumed after the level opens.
- Recommended recipe (UNVERIFIED, test at runtime): in the main menu, find `mainMenu_widget_C`; get a descriptor from `menu_saveLoadMenu_C.NamedSlots` (or `IoHandler:LoadGameFromSlot(<descriptor slot name>)`); build a `SaveGameSlot` and call `LoadGame`. Fallback: `continue()`. Fallback 2: set `savefileToLoad` and `open <map>` via console.
- Level names not in dump; at runtime use `MLGameInstance:getCurrentMap()->Name` / `MLSaveGame.LevelName`. Map packages are under `/Game/NotStronghold/Maps/...`.

## 2. Game time / speed
Master actor `/Script/ManorLords.RTSMultiEngineCPP` (BP `/Game/CPP_BP/RTSMultiEngineCPP_BP.MyRTSMultiEngineCPP_BP_C`; obtain via `MLBlueprintFunctionLibrary:GetRtsEngine(WorldContext)` or `FindFirstOf("RTSMultiEngineCPP")`). Owns `TemporalComponent`, `SquadComponent`, `SpatialComponent`, `playerRef:PawnCPP`, `regions:Array<Region>`, `buildingArr`, `roads`, `unitArr`, `relations`, `tradeLog`, `ForeignMarketSupply`, `tradepoints`, `questDirector`.
- Props: `Delta`, `gameSpeed:Float`, `gameSpeedScheduled`, `gameSpeedBeforePause`, `isGameSpeedScheduled`, `deltaDiff`, `locomotionTicksAdjusted`, `isNightAndAffectsGameplay`, `OnSaveLoaded` (multicast delegate).
- Funcs: `setGameSpeed(NewSpeed:Float)`, `setDay(day:Int)`, `getGameTimeAdjusted()->Float`, `getWindTimeAdjusted()->Float`, `getDaysTotal()->Int`, `getMonthsTotal()->Int`, `getCurrentMonth()->Int`, `getDayOfTheYear()->Int`, `getPreviousMonthStartDay/EndDay()`, `resetCoreTimers()`.
- Player pawn (PawnCPP / MyPawnCPP_BP3_C): `getGameSpeed()->Float`, `setGameSpeed(NewSpeed:Float)`, `pauseGame()`, `unPauseGame()`, `toggleTimePause()` (BP event), `setGamePausedInclVamp(bPaused:Bool)`, `changeGameSpeed(newSpeedIndex:Int, playSfx:Bool)`, `increaseGameSpeed(playSfx, AloowWrapAround)`, `decreaseGameSpeed(playSfx)`, `getGameSpeedID()->Speed:Int`, `isPauseMenuVisible()`, `OpenPauseMenu()`, `ClosePauseMenu(ShouldPauseGame)`; prop `bIsPlayerPaused:Bool`; delegate `OnGameSpeedChanged`; UI events `updateGameSpeedUI`, `updateDateUI(day, month, Season)`.
- `/Script/ManorLords.TemporalComponent` (calendar/weather; `RTSMultiEngineCPP.TemporalComponent`, or static `getWeatherMaster(inWorld)`): props `day`, `daysTotal:Int64`, `dayOfTheMonth`, `month`, `monthsTotal`, `Year`, `Season:Byte` (ESeason: Winter0 Spring1 Summer2 Autumn3), `isWinter`, `wind`, `raining`, `snowing`, `snowLevel`, `isDrought`, `droughtLevel`, `fogLevel`, `daysSinceLastRaid`, `daysUntilNextRaid`; delegates `OnUpdateDay`, `OnUpdateMonth`, `OnUpdateSeason`; funcs `getCurrentDayAndMonth()->GameplayDate{dayOfTheMonth, monthOfTheYear, yearsSurvivedTotal}`, `GetSeason()`, `GetSeasonID(DayOfTheYear)`, `getTotalDaysAndHours()->Double`, `getFutureDayAndMonth(InDaysAhead)`, `setWeatherSpeed(Float)`.
- `PawnCPP:getNumYearsSurvived()->Int`, `getDayOfTheMonthFromWeatherMaster()`.
- Day-tick hook: `RegisterHook("/Script/ManorLords.TemporalComponent:UpdateDateAndSeason")` or the `OnUpdateDay` delegate.

## 3. Telemetry (readable state)
Player `PawnCPP` (`RTSMultiEngineCPP.playerRef`, `FindFirstOf("PawnCPP")`; AI lords are also PawnCPP with `isAI`/`isBandit`; `isMainPlayer`): `silver:Int` (treasury), `influence:Int`, `kingsFavour:Int`, `predictedIncome:Int`, `lordsName`, `currentRegion`, `selectedRegion`, `quests`, `claims`, `enemies`, `recruiting`, `availablePolicies`, `InBox/outbox`, `log`, `commandedSquads`. Funcs: `ChangeTreasury(Amount)`, `changeSilver(amt)`, `changeInfluence(Float)`, `getKingsFavour_daysLeft()`, `getNumTotalBuildings(bType, MustBeConstructed)` (BP), `getTradeDeals()->Array<Tradepoint>`, `checkAndTriggerGameOver()`, `gameOver(Type)`. `MLGameInstance.currentGameVictoryStatus:EVictoryStatus` (Ongoing0, Lost1, Victorious2).

`/Script/ManorLords.Region` (a settlement/region; list `RTSMultiEngineCPP.regions`, `PawnCPP.currentRegion`; lookups `findRegionByName/ByID`, `getRegionFromIndex`, `MLGameInstance:getRegionCount()`):
- Props: `regionName`, `isSettled`, `settlementLevel`, `tier`, `ownerPawn`, **`Approval:Int`**, `publicOrder`, **`regionalWealth:Int`**, `supplies_food:Float`, `supplies_wood:Float`, `expenses`, `isUnderAttack`, `bAnyBuildingOnFire`, `residents:Array<SMUnit>`, `workerFamilies:Array<WorkerFamily{familyMembers, assignedTo, familyStall, familyHome, ConsumptionStatus}>`, `problems:Array<Problem>`, `policies`, `taxRates:Map<Name,Int>`, `targetInventory`, `price:Array<Float>`, `tradeRules`, `tradeRouteLevels`, `summedApprovalFactors:Array<ApprovalMemory{Type:EApprovalFactorType,...}>`, `townCenter`, `manor`.
- Population: `getNumTotalPopulation()`, `getNumHumanResidents()`, `getNumHomelessFamilies()`, `getNumUnassignedFamilies()`, `getNumFamiliesOfLv(familyLevel)`, `getPopulationOfRole(EUnitRole)`, `getNumResidentsOfRoleAndLv`, `GetMonthlyPopChange()`, `GetMonthlyPopGrowthModifiersWithValues()`, `getLivingSpace()/getAvailableLivingSpace()->{constructed,unconstructed}`, `getNumBurgagePlots`, `getNumOccupiedPlots(lvl1..4 out)`, `GetTotalNumReassignableFamilies`, `GetTotalLivestockCountOfType(EUnitRole)`.
- Stock: `getStock(includeReserved)->Array<Good{Type,amt}>`, `getStockOfGood(Type, minusReservation, bIncludePredictedCraftingOutput)->Int`, `getStockOfMultipleGoods`, `getRegionalMarketSupply()`, `getMarketPercentageSupplied(EResidentialRequirement, EItemSubcategory)`, `getMarketFoodVarietyData()->Pair`, `getPredictedHarvestForGoodType`, `getPriceOfGood(goodType)`, `getPrices()`, `getProductionLimit`.
- Buildings: `GetBuildings()->Array<SMBuildingMaster>`, `getBuildingCount(bType, constructedOnly)`, `getResidentialBuildings`, `getActiveResidentialBuildings`, `getNumResidentialBuildingsOfLv(Level)`.
- Settlement/dev: `getNextSettlementLvRequirements()`, `getSettlementRequirementFulfillment()->SettlementRequirements`, `getNumDevPointsSpent`, `GetMaxSettlementLevel` (static). Military: `getNumAvailableRecruits`, `getNumRecruitsNeeded`.
- Trade (on RTSMultiEngineCPP): `getPriceOfGood(Region, goodType)`, `getImportPriceRange`, `getAvailableExportPrice`, `getLowestImportPrice`, `getTradeValue(Region, Filter, startDay, endDay)`, `getTradeLogSummedTradedGoods / getTradeLogAllTradedGoods (Region, startDay, endDay)->Array<TradeLogEntry>`, props `tradeLog`, `ForeignMarketSupply:Array<Good>`.
- Approval: `Region.Approval` + per-factor history `summedApprovalFactors`; `ApprovalComponent:GetApprovalData()->Approval` (static data); `RTSMultiEngineCPP:GetDefaultApprovalRateForFactor(EApprovalFactorType)`. 34 factor types (hunger, starvation, cold, homelessness, missingMarket*, taxation, ...).

`/Script/ManorLords.SMBuildingMaster` (list `RTSMultiEngineCPP.buildingArr` or `Region:GetBuildings()`): props `Data:BuildingDataStruct`, `Inventory:Array<Good>`, `numStoredGeneric/Large/Pantry`, `storageLimit*`, `numActiveWorkerFamilies`, `lv`, `onFire`, `fireAmt`, `TownName`, `Region`, `animals`, `yield`, `field_*Perc` (farm progress), `marketDaysLeft`, `waterSupply`, `buildingFunction:EBuildingFunction`. Funcs: `GetStorageSpaceUsed/Left(EStorageType)`, `GetStorageLimit`, `GetTargetStock`, `GetCurrentlyProducedGoodTypes`, `GetTotalProductivityValueInPercents`, `GetCollapseChance`, `GetMissingSupplyCategories`, `GetFuelStock`. Components: `MaintenanceComponent` (`GetMaintenanceStatus`), `ProductionTrackerComponent` (`getGoodsProducedOver(NumDays)->Map<Int,Int>`).
`/Script/ManorLords.SMUnit` (all villagers/animals/soldiers; `RTSMultiEngineCPP.unitArr`): `dead`, `Home`, `workerFamilyID`, `Inventory`, `Tasks`, `morale`, `stamina`, `DisplayName`.
Military: `Squad` via `MLBlueprintFunctionLibrary:GetSquad(WorldContext, SquadHandle, out Squad)`; `SquadComponent`.
Other: `SessionAchievementData` on RTSMultiEngineCPP (numVillagersDied, numConstructionsFinished, numEnemiesKilled); `RTSMultiEngineCPP:getItem(ItemId)->Item`, `getBuildingData(buildingID)->Stat` (static).
Cheats (`/Script/ManorLords.MLCheatManager`, Exec): `ChangeTreasury(Int)`, `GiveItemByName(Str,Int)`, `GiveItemByID`, `GiveRandomAmountOfAllItems`, `SetSettlementLevel`, `RemoveAllFamilies`, `RainNow`, `SpawnBanditSquad`, `SpawnRaidersOfType`, `CollapseAllBuildings`, `MaintainAllBuildings`, `LogAllProductionTrackerEntries`, `ShouldSkipIntro()->bool`. Needs a CheatManager instance (may be disabled in shipping).

## 4. Menu / world-load flow (hookable)
- GameInstance: `/Game/CPP_BP/BP_MLGameInstance.BP_MLGameInstance_C` : `MLGameInstance`; BP event `ReceiveInit`. Props `savefileToLoad`, `scenario`, `gameSetup`, `gameSetupDifficulty`, `currentGameVictoryStatus`, `Version`. Funcs `getCurrentMap()`, `setCurrentMap(Name)`, `setCurrentGameSetup`, `UpdateGameSetupParameters`.
- GameMode: `/Game/NotStronghold/BP/RTSGame.RTSGame_C` : `NotStrongholdCPPGameModeBase` : GameModeBase (only `ReceiveBeginPlay`). No custom GameState.
- PlayerController: `/Game/NotStronghold/BP/MLPlayerController.MLPlayerController_C` (`ReceiveBeginPlay`, `ReceiveTick`).
- Menu pawn: `/Game/CPP_BP/MenuPawn.MenuPawn_C` : `/Script/ManorLords.MenuPawn`. In-game pawn: `/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C`.
- HUD: `/Game/CPP_BP/BP_HudCPP.BP_HudCPP_C`; in-game UI root `/Game/UI/HUD/MainUICPP.MainUICPP_C`; `/Game/UI/HUD/W_HUD_LordPanel_V2.W_HUD_LordPanel_V2_C:OnSaveLoaded_Event()`.
- Menu widgets: `/Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C` (Construct, Tick, continue, LoadGame, startNewGame), `menu_saveLoadMenu_C`, `saveSlot_widget_C`, `menu_settingsWrapper_C`, `/Game/UI/Game_Setup/mainMenu_GameSetup.mainMenu_GameSetup_C`, `W_Splash_C` (`/Script/ManorLords.MLSplashWidget`), `MLGameSetupScreen`, `MLGameStartScreen`, `MainMenu_LoadingThrobber_C`. Interface `MLMainMenuOpenCloseInterface:Open/Close`.
- World init: `MyRTSMultiEngineCPP_BP_C:ReceiveBeginPlay` and `setupBuildings/setupUnits/setupUpgrades/updateRegions` (BP); delegate `RTSMultiEngineCPP.OnSaveLoaded` fires when a save finishes loading.

"In-game ready" signals, most robust first:
1. Polling: `RTSMultiEngineCPP` valid AND `PawnCPP` (isMainPlayer) valid AND `regions` non-empty AND player `Region.isSettled` (or a TemporalComponent day tick observed).
2. Hook `/Game/CPP_BP/RTSMultiEngineCPP_BP.MyRTSMultiEngineCPP_BP_C:ReceiveBeginPlay`, then poll; for loaded saves also `/Game/UI/HUD/W_HUD_LordPanel_V2.W_HUD_LordPanel_V2_C:OnSaveLoaded_Event`.
3. Hook `/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ReceiveBeginPlay` or `/Game/NotStronghold/BP/RTSGame.RTSGame_C:ReceiveBeginPlay`.
4. Main-menu detection: `MenuPawn_C` exists / `mainMenu_widget_C:Construct`.
5. Liveness: `/Script/ManorLords.TemporalComponent:UpdateDateAndSeason` or `MyPawnCPP_BP3_C:ReceiveTick`.

## 5. Caveats / unknowns
- BP-class hooks only resolve after the BP class is loaded; main-menu level may not have loaded gameplay BPs. Use `NotifyOnNewObject` on `/Script/ManorLords.PawnCPP` / `RTSMultiEngineCPP`.
- `mainMenu_widget_C:LoadGame` needs a live menu widget (main-menu level only); slot-name format from `MakeSlotNameFromSlotNumber` / `SlotNameFromIndex`. Not runtime-verified.
- No pause on RTSMultiEngineCPP beyond `gameSpeed`/`gameSpeedBeforePause`; use PawnCPP `pauseGame/unPauseGame/setGameSpeed`. Speed index to float mapping unknown (`getGameSpeedID`, `changeGameSpeed`).
- To re-query: `py -I` + `json.load` on the jmap (~1.5 GB RAM). Do not copy the jmap into the repo. Under Git Bash, set `MSYS_NO_PATHCONV=1` when passing `/Game/...` args.
