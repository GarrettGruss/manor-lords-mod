# Engine facts that the end-game concepts need

Issue: #521. Desk research only (2026-10-28). No game run. Game build of the extract: the tables in `modtools/work/json/` (not in git). Where a fact comes from a table extract, check it again with a pak build before you rely on it.

Rating words used in all notes:
- **Proven**: a real game run in this repo showed it. The source is named.
- **Data**: the extracted table has the column. Not tested in the game.
- **Unknown**: no evidence. This is a spike question.

## 1. New buildings

| Need | State | Evidence |
|---|---|---|
| A new `buildingStats` row (new id) from a pak | Proven | Rows 123, 124 and 125 were added by pak, placed with `activateBuildingMode(id)` and a real click, and built. Archive `2026-10-15-legacy-18-composite-buildings/implementation-notes/siege-camp-and-bm.md`, `real-mouse-placement-proof.md`. The pak patch op `add` clones a row (`harness/tools/modpak.py`; wiki `workflows/pak-mods.md`). |
| A new model for it (Blueprint with new meshes) | Proven | `BM_HarnessCamp` made headless in UE 5.5.4. Components must be named `MainBld_*` or `Bld_*`, or the master has 0 parts. A Meshy house model shipped too (wiki `workflows/meshy-models.md`). |
| Reuse a vanilla model instead | Proven | A new row can point at a vanilla `BM_*` class (row 123 at `BM_HuntingCamp` gave 16 parts). |
| A build menu card for a new id | Unknown | The Siege Camp (vanilla row 483) got a card in the Military tab by setting `bVisibleInUi`. A new id got no card in the Military tab (tent category). Other tabs were not tried. The spike `spike-composite-building-gaps` was closed without build on 2026-10-19. |
| Start placement without a card | Proven | `activateBuildingMode(id)` then a real click. A mod menu button can call it (not tried by a player; inferred). |
| Unlock tier ("town") | Data | Row columns `settlementLevel`, `requiredPerks`, `requiredTech`, `maxInRegion`, `placedWithin`, `isModule`, `moduleCategory`. The card reads `minSettlementLevel` and `requiredTechs`. `Region.settlementLevel` is readable (tech_tree feature) and the cheat `SetSettlementLevel` works in test scenarios (levels 2 and 3). A refusal for a too low level was never seen (legacy-12 notes: ghost was placeable). Unknown for a new id. |
| Live write of a row field | Proven for numbers | `HarnessHousing.STAT_FIELDS` reads and writes `maxInRegion`, `settlementLevel`, `bVisibleInUi`, `constructionCost`. A write affects new placements, not existing buildings. A write of `bVisibleInUi` at run time to show or hide a card was not tried. |
| Raise a "one per region" limit | Data | A community mod lifts `maxInRegion` to 99 on manor rows. Not tested here. |
| A new `buildingFunction` | Not possible | `EBuildingFunction` is a native enum (23 values). The function (Trader, Tavern, Church, Manor, Construction, Stable...) selects native behavior. A row can only pick an existing one. |
| A new `job` (worker type) | Not possible as new; reuse is Unknown | `job` is an int into native job behavior (names in `DT_Translation_Jobs`). The wiki records that a new extension type cannot be added (`pak-mods.md`, "Limit: no new backyard extension type"). A stand-alone building row with an existing job id is the route the repo chose. |
| Place a building where there is no road | Data | `needsRoad`, `collidesWithRoads` columns. |
| Water placement rule (river or lake edge) | Unknown | No column for it. Placement checks are native C++ (the bailey rule is native, `engine-limits.md`). `fishingPond` (row 39) and `woodenBridge` (115) have function `Landscape`; wells have `WaterSource`. |
| Buildings count by id | Proven | `Region:getBuildingCount(bType, constructedOnly)`, `Region:GetBuildings()`. Used by the harness. |
| Remove a building from Lua | Partly proven | `SMBuildingMaster:demolish(true)` removed a bandit camp (wiki `engine-limits.md`, #489). Not tried on a player building. `collapseBuilding()` makes rubble (#341). |

Vanilla assets that are in the files but not shown to the player (string scan of the unpacked headers in `modtools/work/ua-scan`, and the `buildingStats` extract):
- `buildingStats` row 59 "Fisherman's Hut" (job 66, `averageProduction` items 30 and 32, `bVisibleInUi` true), class `BM_SG_FishermansHut`, and `Resource_Fish`. The fish items 30 and 32 (category Food, subcategory Fishes) name a recipe input item 319 and tool item 315. Neither row exists in the `DT_Items` extract. So the game has half-finished fishing data. Whether row 59 can be placed, or works, is Unknown.
- `BM_SG_HerbsGarden` and `DT_Upgrades` row 15 `herbs_garden` (an upgrade of the Forager, row 36). An item named "Herbs" exists in the item texts.
- Level 2 and 3 manor rows 474 to 483 (unfinished; see `2026-10-15-legacy-12-manor-exploration/implementation-notes/unused-assets.md`).
- Not found in the files: cobblestone, fountain, sewer, bath-house, town hall (Rathaus), astronomical clock, tournament, dock, boat. Any of these needs a new model.

## 2. Goods and recipes

- `DT_Items` rows hold the recipe: `Resources` (inputs), `craftingOutput`, `craftingTool` (an item id), `upgradesRequiredToCraft`, `techsRequiredToCraft`, `ExpertiseOnCraft`, `requirementLevel`, `tradeable`, `isMajorTrade`, `Value` (price), `ItemCategory`, `Subcategory`. 213 rows in the extract.
- New rows in `DT_Items` and `DT_UnitTemplates`: Proven (spec 29, wiki `pak-mods.md`).
- `ItemCategory` and `Subcategory` are native enums. A new item uses an existing category.
- Which building produces a recipe: not a column of the item. The link is the building `job` plus `craftingTool` (data) and native code. Unknown: can a new building row with an existing job id make a new item from a new recipe row? This is the key question for the apothecary, the boatwright and guild crafts.
- A mod can set a job and a recipe on a slot at run time (burgage tailor extension, wiki `pak-mods.md`).
- Plate: the retinue tier 3 template uses plate armor (wiki `unit-templates.md`). Item 293 (category Military, subcategory Armor, price 8, needs 6 of item 35, `craftingTool` 0) has no tool, so no building makes it. Its identity is not checked.
- Region stock can be read (`getStockOfGood`) and changed with `addToInventory` on a building (proven, #482, #360). A building can remove one item with `consumeGoodNoCheck`.
- Production can be read: `ProductionTrackerComponent:getGoodsProducedOver(days)` (jmap).

## 3. Effect hooks

| Effect | State | Evidence |
|---|---|---|
| Silver (treasury) | Proven | `PawnCPP:changeSilver(n)` and `ChangeTreasury(n)` add. Used by tribute and liege_influence. `predictedIncome` is readable. |
| Influence | Proven | `PawnCPP:changeInfluence(n)`. Mod-owned influence balance in `liege_influence`. |
| `Region.regionalWealth` | Proven for the write; effect Unknown | A set of 200 held for 3 game days in 3 of 3 runs (legacy-07 `actions-catalog.md`). Whether wealth changes income was not tested. The policy text says a small land tax is paid from regional wealth. |
| `Region.Approval` (happiness) | Single write does not hold | The game recalculates it in 1 to 3 game days (legacy-07). A per-tick write is not tested. The 34 factor types are a native enum; a pak cannot add one; weights come only from config (spike #403). |
| `Region.publicOrder` | Proven | A per-tick write holds (spike #403, owner route A). The game did not change families or approval in 10 days, so its native effect looks weak. |
| Approval factor rows shown to the player | Proven for display | Custom rows in the public order tooltip (feature `order_tooltip`). An appended `ApprovalMemory` shows, but `publicOrderMemory` entries have no effect. Expect the same for approval; Unknown. |
| Merchant visit rate, trade speed | Unknown | The merchants are native squads (`ESquadType` Merchants). `RTSMultiEngineCPP` has `tradepoints`, `ForeignMarketSupply`, `tradeLog`, `getTradeValue`. `TradeSettings` CDO has `importFee`, which a community Lua mod writes. A visit interval field was not looked for. The trading post upgrades are `DT_Upgrades` 10, 19, 21 (trade_wagon, order_horse, order_mule). |
| Experience of units | Proven | `SMUnit.combatExperience` rises in fights and can be written (`set_squad_experience`, spike C2). Its effect on strength was not measured. |
| Create a unit type | Proven | New `DT_UnitTemplates` rows (spec 29). Max squad size is a column (`maxSize`). `PawnCPP:addMilitiaSquad(region, FName)` registers a militia squad by template name (#482); a new template name there is Unknown. |
| Equipment of a unit | Limited | `SMUnit:equip` is cosmetic for villagers. Gear of a new squad comes from the template and from stock in the homes (spear and shield stock proven, #482). |
| Retinue size | Limited | The native hire adds no man above the native limit (12 per manor module; spec `mod/manor_stronghold`). A guild unit must not be a retinue. |
| New metric (Health) | Mod-owned only | The engine has no health metric. `ModState` stores mod values in the save (feature `mod_state`). Display: tooltip rows, mod menu, `HarnessUi` banners. |
| Mod menu and actions | Proven | Bottom bar button, mod menu, pak widgets (`native-ui-elements.md`, `building-mod-ui.md`). |
| Per-day or per-tick mod work | Proven | `LoopInGameThreadWithDelay`, the mod scheduler, `OnUpdateDay` hook. |

## 4. Roads

Roads are a native system (`RTSMultiEngineCPP.roads`, the road tool, row 1 `Road_DEPREC`). No data column or enum for a road surface type was found. A new road type (cobblestone) therefore needs native code. See `buildings.md`.

## 5. Known limits that apply to all concepts

- A hook cannot cancel a native action. A mod cannot refuse a placement. It can hide a card (if `bVisibleInUi` writes work) or remove the building after the placement.
- No native code (owner decision, `native-modding.md`).
- The simulation is not deterministic. Tests use ranges.
- Do not read `Squad` structs. Do not call `K2_DestroyActor` on an `SMUnit`.
