# Hidden and unused buildings (static study)

Date: 2026-10-13. Spec 18, issue #69. Static only: no game launch. Sources: the 104 rows of `buildingStats`, `DT_Translation_BuildingNames` and `DT_Translation_BuildingDescriptions`, and the index of all 20 game paks (12788 `.uasset` entries).

## Answer in short

- There is no mercenary camp building in the files. No `buildingStats` row, no Blueprint, no UI card. Mercenaries are only a hire screen (`UI/Mercenary_Hire/*`, `W_HUD_MercenaryPanelV2`) and the table `DT_MercenaryCompanies`.
- There is no asset with "invasion" or "invader" in its name.
- The nearest real finds are two camp rows that the build menu hides:
  - Row 483 `Siege Camp`: a finished-looking class, mesh and UI art. Its text says "Work in Progress". This is the most likely "invasion camp".
  - Row 100 `Bandit Camp`: the bandit settlement. The player cannot build it, but the game spawns it.
- Row 107 `Settlers Camp` is shown in the menu and is Military category. It is a visible camp that players may mistake for something hidden.

## How a type is shown

A row is in the build menu when `bVisibleInUi` is true. The row key is the building type id. The English name is in `DT_Translation_BuildingNames` under `buildingID_<id>`. The description is under `buildingID_<id>_descr`. The class is `BlueprintPath` (or `assemblyBlueprintVariations`). See `building-parts-static.md`.

## Candidates

| id | name | function | category | in menu | class | notes |
|---|---|---|---|---|---|---|
| 483 | Siege Camp | Siege | Military | no | `BM_SiegeCamp_C` (exists) | description starts "Work in Progress", mentions Siege Equipment near friendly units; has `panelImage`, `panelImageV2`, `buildingImage` (card and tooltip art exist); `AIcanBuild` false; cost 0; `maxHp` 100; no `constructionMeshAsset` |
| 100 | Bandit Camp | Siege | Gathering | no | `BM_HomelessTents_C` (the tent class) | description "Tents and supplies where Bandits congregate."; `maxHp` 5; no UI art (spec 15 notes: bandit camp is a tent master of type 100) |
| 107 | Settlers Camp | Default | Military | yes | `BM_HomelessTents_C` | cost 250; mesh `SM_MERGED_C_outpost`; art `settlers_camp_*` |
| 87 | Homeless People's Tents | Temporary | Gathering | no | `BM_HomelessTents_C` | the refugee tent; used by RefugeeWaves |
| 111 | Worker Camp | Residential | Gathering | no | `BM_Work_Camp_C` (exists) | name exists; no art; `maxHp` 50 |
| 88 | Supplies (supply_dump) | Temporary | Gathering | no | `BM_Supplies_C` | war supplies pile |
| 53 | Rally Point | Temporary | Gathering | no | `BM_RallyFlag_C` | `AIcanBuild` true |
| 57, 472 | Garrison Tower, Outer Tower | Default | | no | `BM_SG_Manor_Lv1_Keep_C`, `BM_SG_Manor_Lv1_Tower__C` | manor modules (spec 14), not stand-alone |

Other rows hidden from the menu with a real class (all with `bVisibleInUi` false): 46 `TradepointOLD`, 85 `Roadpost`, 52 deep mine, 58 tax collector, 68 large granary, 77 and 120 stone churches, 97 small stable, 99 large storehouse, 114 stone well, 115 wooden bridge, 116 large tavern, 122 stone lined pit, 91 to 93 stalls, 104 and 106 scenario ruins, 105 `Brewery_idk_lol` (a Brewery class, no UI art), 469 to 484 manor wall, tower, gate, palace and keep pieces.
Many are upgrade or module steps that the game unlocks by other means, so "not visible" does not mean "unused".

### WIP and dead rows

- `bWorkInProgress` is true on rows 102 `firewood_cart`, 103 `food_cart` and 473 `dyers_shop`. All have a class. The dyer's workshop has name text (id 473) and a card image. The carts have card images only.
- Names that mark dead rows: 1 `Road_DEPREC`, 469 `wooden_gatehouse_module_DEPREC`, 46 `TradepointOLD`, 73 `residential_plot_UI_only`.
- Rows with no class (`BlueprintPath` None, no `assemblyBlueprintVariations`): 40 `Archery range` (mesh `SM_MERGED_C_archeryRange` exists), 45 `Training camp`, 62 `Militia training camp` (mesh `SM_MERGED_c_drillSquare` exists), 22 `Small Townhouse`, 50 `wall_tool`, 78 `cart_park`, 109 `pithouse`, 8/60/484 plots, 471, 476, 477, 480 to 482. These look like early military ideas that were cut. They have no name text, so a menu card would show a raw key.

## Pak assets with no `buildingStats` row

- Classes in `CPP_BP/BuildingMasterAssemble/` that no row names: 68 classes. Nearly all are plot parts and extensions (cottage, house, townhouse, `BM_SG_Ext_*` sheds, `PlotClutter`), used through `DT_IndependentBuildingPartAssemblies`. Stand-alone ones worth a note: `BM_Livestock_Barn`, `BM_Outhouse`, `BM_SG_StableLow`, `BM_SG_HerbsGarden`, `BM_SG_BeehivesExt` (id 51 Apiary has a name), `BM_SG_CoopCage`, `BM_SG_CoopRoofed`.
- Construction Blueprints with a mesh but no row of their own: `C_outpost` (mesh `SM_MERGED_C_outpost`, now used by the Settlers Camp), `c_campfire` (also in `DT_ConstructionBPs`), `SM_MERGED_c_miningCampBase_2`.
- Unused wall style: `SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam` with `SMD_PalisadeNarrow` and a path in `DT_BuildingMeshPathData`. There is no palisade row in `buildingStats`. This is a possible hidden palisade.
- Mercenary assets: only UI (hire screen, army cards, banners in `UWG/BannerSystem/RegimentSymbols/MercenaryCompanies`, one `WIP/` banner) and the body mesh `MGGN_body_mercenary_puff`. Audio `Alerts/banditCampSighted_cue` exists. None is a building.

## How to test (not done)

Cheapest first:

1. Pak that sets `bVisibleInUi` true on row 483 (and 100). The row is in `Military`/`Gathering` category, so the card should show in that tab with its art. Use the same pak flow as `composite-pak.md` (`s65_edit_json.py`). Name text exists for both ids, only 483 has a description and card art. Check the place preview and that it does not crash: `BM_SiegeCamp_C` was never seen placed.
2. Lua without a pak: `PawnCPP:activateBuildingMode(483)` then the real-mouse placement (`place_building`, spec 14 notes). Read `building-placement.md` first: the menu flag may still block it, and this was proven only for visible ids. Use single player and never call a save function.
3. Bandit Camp 100: use the existing bandit camp from `settleRegion` (spec 15), not placement. A placed row 100 is a tent master (`maxHp` 5).
4. Siege Camp use (Siege Equipment near friendly units) needs an army. Test after step 1 passes, with the invasion tools of spec 10.
5. For rows with no class (archery range, training camps), a pak could retarget `BlueprintPath` to an existing class (see `composite-pak.md`). The mesh assets exist but have no class, so only a retarget shows something.

## Open questions

- Does the build menu filter on `bVisibleInUi` only, or also on category tab, tier or perks? Test with row 483.
- Does `BM_SiegeCamp_C` need a world setup (an army, an invasion flag) to place?
- Where do Reddit players see a "mercenary camp"? Possibly they mean the Bandit Camp or the hire screen. Not proven.
