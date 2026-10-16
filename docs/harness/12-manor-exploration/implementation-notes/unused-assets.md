# Unused manor and castle assets (static study)

Date: 2026-10-13. Spec 12, issue #65. Game 0.8.111. Static only: no game launch, no test. Sources: the pak index (12788 `.uasset`), the JSON of `buildingStats`, `DT_Upgrades`, `DT_ConstructionBPs`, `DT_BuildingMeshPathData`, the name tables, and a string scan of the unpacked headers of `CPP_BP`, the data tables and the socket mesh data (git-ignored folder `modtools/work/ua-scan`). Nothing from the game was copied into the repo.

## Short answer

- A level 3 manor exists in the files. It is finished art and a full set of classes. The game has data rows for it. Nothing shows it to the player:
  - row 81 `manor_palace_lv3`, class `BM_SG_Manor_Lv3_Palace_C`, mesh `SM_MERGED_C_SG_Manor_Lv3_Palace`
  - row 82 `manor_gate_lv3`, class `BM_SG_Manor_Lv3_Gatehouse_C`, mesh `SM_MERGED_C_SG_Gatehouse_LV3`
  - row 83 `manor_keep_lv3`, class `BM_SG_Manor_Tower_Lv3_C`, mesh `SM_MERGED_C_SG_Tower_Lv3`, `garrisonLimit` 36, `requiredTech` set
- The level 3 "garrison" is row 83. The vanilla `Garrison Tower` is row 57 (`manor_keep_lv1`, garrison 12). Row 83 holds 36. There is no `Lv3_Keep` class: the Lv3 keep is the `Tower_Lv3` asset.
- Player claim "finished model": supported. The Lv3 palace mesh is the largest manor mesh (32.6 MB geometry, Lv2 palace 7.3 MB, Lv1 palace 5.0 MB). Lv3 tower 17.3 MB (Lv2 main tower 9.4 MB, Lv1 11.5 MB). Lv3 gatehouse 4.2 MB (Lv2 5.3 MB, Lv1 3.1 MB). Sizes are `.uexp` bytes.
- Not finished: rows 81 to 83 and 474 to 479 have no name text (`buildingID_<id>` is missing in `DT_Translation_BuildingNames`), and no card art of their own (they reuse the Lv1 tooltip and card art). A card would show a raw key.
- Not proven: that the game can place and finish them. Not tested.

## Manor level model

- No `castle_level` field exists. A manor module is a `buildingStats` row with `moduleCategory` Manor. The level is only in the name (`_lv1`, `_lv2`, `_lv3`) and the class.
- `DT_Upgrades` row 9 is `manor_lv3` (cost goods type 16 x 25 and more, `descr` "stuff", no icon). It is a placeholder upgrade. There is no `manor_lv2` upgrade. `manor_lv3` is also the `DisplayName` of no building row (the building rows use `manor_palace_lv3`, `manor_gate_lv3`, `manor_keep_lv3`).
- Row 98 `manor_palace_lv1` is the only manor row with `bVisibleInUi` true (the "Manor" card). Row 95 `manor_gate_lv1` has `settlementLevel` 2.
- Planner (`UI/Castle_Planner/castlePlanner`): ten cards with fixed IDs 98, 57, 58, 83, 81, 81, 95, 50, 57, 472. Cards 83 and 81 are `Collapsed` in the asset. So the planner already has cards for Lv3 keep (83) and Lv3 palace (81). The Lv3 gate (82) and all Lv2 rows (474, 475, 478, 479) have no card. Card images are `card_keep_lv1`, `card_sg_Gatehouse`, `card_tower_lv1` and `card_tax_collector`. No `_lv2` or `_lv3` card image exists.

## Manor and castle assets by level

| level | piece | row | class | mesh | in data | in planner / menu |
|---|---|---|---|---|---|---|
| 1 | palace | 98 | `BM_SG_Manor_Lv1_Palace_Solo` | `SM_MERGED_C_SG_Manor_Lv1_Palace_Ubeam` | yes | yes (menu) |
| 1 | keep / garrison tower | 57 | `BM_SG_Manor_Lv1_Keep` | `SM_MERGED_C_SG_Manor_MainTower_Lv1_New` | yes | yes |
| 1 | outer tower | 472 | `BM_SG_Manor_Lv1_Tower_` | `SM_MERGED_C_SG_Manor_Tower_Lv1_00` | yes | yes |
| 1 | gatehouse | 95 | `BM_SG_Manor_Lv1_Gatehouse` | `SM_MERGED_C_SG_Gatehouse_Lv1_Ubeam` | yes | yes |
| 1 | wooden wall | 470 | `BM_SG_Manor_Wall_Lv1` | `SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam` | yes | no card |
| 1 | tax office | 58 | `BM_TaxCollector` | `SM_MERGED_C_SG_TaxCollectorProper` | yes | yes |
| 2 | palace | 474 | `BM_SG_Manor_Lv2_Palace` | `SM_MERGED_SG_Manor_Palace_LV2` | yes | no card |
| 2 | keep | 475 | `BM_SG_Manor_Lv2_Keep` | `SM_MERGED_C_SG_Manor_MainTower_Lv2` | yes | no card |
| 2 | gatehouse | 478 | `BM_SG_Manor_Lv2_Gatehouse` | `SM_MERGED_C_SG_Manor_GateHouse_Lv2` | yes | no card |
| 2 | outer tower | 479 | `BM_SG_Manor_Lv2_Tower_` | `SM_MERGED_C_SG_Manor_Tower_Lv2` | yes | no card |
| 3 | palace | 81 | `BM_SG_Manor_Lv3_Palace` | `SM_MERGED_C_SG_Manor_Lv3_Palace` | yes | card 81 collapsed |
| 3 | gatehouse | 82 | `BM_SG_Manor_Lv3_Gatehouse` | `SM_MERGED_C_SG_Gatehouse_LV3` | yes | no card |
| 3 | keep (garrison 36) | 83 | `BM_SG_Manor_Tower_Lv3` | `SM_MERGED_C_SG_Tower_Lv3` | yes | card 83 collapsed |
| 3 | outer tower | none | none | none | no | none |

Paths: classes are in `CPP_BP/BuildingMasterAssemble/ManorModules/`. Lv1/Lv2 meshes are in `ManorLords/Buildings/Merged/`, Lv3 meshes in `NotStronghold/Buildings/Merged/`. The Lv2 and Lv3 module classes are small empty mesh actors (like Lv1, 2 to 4 KB).

Lv3 support assets (all exist, all referenced by the Lv3 construction Blueprints):
- `CPP_BP/ConstructionBlueprints/C_SG_Manor_LV3_Palace`, `C_SG_Tower_Lv3`, `C_SG_Gatehouse_LV3`; all three are in `DT_ConstructionBPs` (palace and tower and gatehouse entries). The construction Blueprints are large (palace 166 KB header, 131 KB data).
- Stone bases: `NotStronghold/Buildings/SG_ConstructionAssets/SG_StoneFoundations/Manor_LV3_StoneBase_A`, `Manor_LV3_Stripe`, `sg_tower_lv3_base`, `sg_gatehouse_lv3_BASE`; roof tiles `SG_Rooftiles/sg_tower_lv3_rooftiles`.
- Lv2 extras with no row: wall-side gate and tower variants `SM_MERGED_C_SG_Manor_GateHouse_Lv2_E/_N/_S/_W/_Common`, `SM_MERGED_C_SG_Manor_Tower_Lv2_E/_N/_S/_W/_Common`, and fractured (collapse) meshes `Base_SG_Manor_Palace_LV2`, `Base_SG_Manor_MainTower_LV2` in `StoneFractures/`.

Other level 3 walls and gates (not manor):
- `C_SG_Lv3GateWall_350`, `C_SG_Lv3GateWall_700` (+ meshes `SM_MERGED_C_SG_Lv3GateWall_350/_700/_Big`). They are in `DT_ConstructionBPs` and `DT_BuildingMeshPathData`, but no `buildingStats` row builds them. They look like the stone town wall gate. No row: not buildable.
- Wall and gate rows 471, 476, 477 (`manor_wall_platform_open`, `manor_wall_stone_small`, `manor_wall_stone_large`) have no class (`BlueprintPath` None). The stone wall of the manor has art (`SM_MERGED_sg_wallPlatform`, `SM_MERGED_WallPlatform_*`) but no Blueprint row.
- Palisade: the earlier note (`hidden-buildings.md`) said the narrow palisade mesh has no row. Correction: `BM_SG_Manor_Wall_Lv1` (row 470, wooden manor wall) uses `SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam`. Row 470 has no card in the planner, but the planner has the wall tool (`wall_tool` row 50).
- Tax office has only a Lv1 form. Palisade, tax office and the Lv1 outer tower have no Lv2 or Lv3 form.

## Other notable unused or unreachable assets

Method: a name is "unreferenced" when its name is not found in the unpacked headers and data of `CPP_BP`, `NotStronghold/Data`, `ManorLords/Database`, the socket mesh data and `Translation`. Levels, widgets and C++ can still use it. Treat the list as leads, not proof.

Counts: of the roughly 410 Blueprints in `CPP_BP`, 24 files have no reference; 16 are base or engine glue (`BP_BuildingMaster`, `BP_HudCPP`, `BP_Region`, `BP_ResourceNode`, `battlefield_BP`, `MyDirector`, game modes). Every mesh in `ManorLords/Buildings/Merged` and `NotStronghold/Buildings/Merged` that is a building mesh is referenced, except one tent mesh. Unit parts (`VAMP/SkeletalMeshes`, 535 files) are assembled by code names, so a scan of names gives noise. They are not listed.

### Buildings and construction

| path | what | referenced | note |
|---|---|---|---|
| `CPP_BP/BuildingMasterAssemble/BM_SiegeCamp` + `UI/Cards/BuildingsStylized/ml_building_card_miniature_0000_Siege-Camp` (card art unreferenced), `T_UI_Tooltip_siege_camp` | row 483 Siege Camp | row only | see `hidden-buildings.md` |
| `Merged/SM_MERGED_tentHand_FixedColors` (NotStronghold) | hand made tent mesh | no | tent family; the tent mesh in use is another |
| `CPP_BP/ConstructionBlueprints/C_Stairs_Wooden_100` | wooden stairs | `DT_ConstructionBPs` only, no building class | used by the construction yard mesh |
| `ManorLords/Buildings/WIP/SM_MERGED_C_SG_Townhouse_lv3_A` | WIP townhouse | `DT_BuildingMeshPathData` only | the shipping mesh is `..._Lv3_A_02` |
| `UI/Cards/Old/simpleBloomery`, `UI/Cards/Old/card_livestock_trader` | old card art for a bloomery and a livestock trader | bloomery no; trader in `DT_Upgrades` | old building ideas |
| `UI/Cards/Units/unitCard_polearmMilitia_test` | test unit card | no | |
| `UWG/ui_textures/building_WIP`, `cards/WIP/merc_archer` | WIP art | no | the other `cards/WIP/merc_*` are used by `DT_UnitTemplates` |
| `z_ReferenceBackup/Old_Widgets/CoatOfArms_OLD` | old coat of arms widget | no | `legacyViewWidget` in the same folder is still referenced by the pawn |
| rows with no class: 40 Archery range, 45 Training camp, 62 Militia training camp, 22 Small Townhouse, 109 pithouse, 484 residentialPlot_lv4 | cut buildings | row only | meshes `SM_MERGED_C_archeryRange`, `SM_MERGED_c_drillSquare` exist |

### Resources, items, people and animals

| path | what | note |
|---|---|---|
| `CPP_BP/Resources/Resource_Eel`, `Resource_Mushrooms` | resource node Blueprints with no reference | items 32 Eel and 279 mushrooms exist, meshes `ResourcesGatherable/SM_EelStatic`, `M_EelStandard` are used by the fisherman hut and food stall |
| `DT_Items` rows `VirtualRequirementItem_Faith_Lv4`, `VirtualRequirementItem_Tavern_UNUSED`, `vegetables_DEPREC` (230) | dead item rows | the Faith Lv4 row has no church level 4 |
| `CPP_BP/BP_UnitSpawner`, `BP_VillageSpawner`, `BP_SimpleBirdFlock` | spawner Blueprints | no reference found; may be level actors |
| `VAMP/SkeletalMeshes/Human/.../SM_MGGN_body_mercenary_puff`, `helmet_mercenary_iron` | mercenary body and helmet | mercenaries are a hire screen only (`hidden-buildings.md`) |
| `UWG/BannerSystem/RegimentSymbols/MercenaryCompanies/WIP/merc_wayward_sons` | banner | no reference |
| `VAMP/EquipmentStatic/SiegeLadder/VAMP_siege_ladder` | siege ladder | item 322 `siege_ladder` exists; siege ladders are attacker gear, the Siege Camp idea |
| `Portraits/WIP/*`, `Portraits/Placeholder/Bandit_Gen_A/B/C`, `UI/Events/Victory_Domination/dominance_wip_*` | WIP portraits and a domination victory screen | the domination victory is not in the game |
| `CPP_BP/dynamicMusic/BuildingTracks/V1/...` three `*_preview` or `Rough` tracks | music | no reference |

### Not covered

- Maps (`NotStronghold/Maps/NewMapSets`, 62 assets), `Characters/lord_01`, `UI/Lord_Customization`, and audio (about 2000 cues). Their users are levels and widgets that were not unpacked.
- Engine and plugin samples (Megascans, FantasyVillage, KiteDemo, InfinityBladeEffects, ALS mannequin) are third party and mostly unused. Not a game feature.

## How to see them in game (not done)

Cheapest first. Read `manor-module-pak.md` first: it shows the pak flow, the `manor_blueprint_add` command and the planner card steps.

1. Planner cards 81 and 83 already exist. A pak that edits `UI/Castle_Planner/castlePlanner` (script `harness/tools/s65_edit_json.py planner`) and removes `Collapsed` from the two cards shows Lv3 palace and Lv3 keep cards (the Lv1 card art, no name). Needs a finished manor and the module step of the planner. Risk: native code may check `requiredTech` (row 83) or the settlement level.
2. Show Lv3 in an existing slot: a pak that retargets row 472 (outer tower) to `BM_SG_Manor_Tower_Lv3` and mesh `SM_MERGED_C_SG_Tower_Lv3`, or row 98 to `BM_SG_Manor_Lv3_Palace`. This needs only the data table (like `composite-pak.md`). The card art stays the Lv1 tower, the name stays "Outer Tower".
3. Lua without a pak: `manor_blueprint_add` with type 81, 82 or 83 and the Lv3 mesh. Limit from the spike: the game must have loaded the mesh. The Lv3 meshes are not loaded in a normal game, so the call can fail. A pak (step 2) makes the game load the mesh.
4. Lv2 rows 474, 475, 478, 479 have no card. Add a card ID like the 123 test, or retarget row 472/57 to the Lv2 classes (same flow as step 2).
5. Siege Camp 483 and Bandit Camp 100: `hidden-buildings.md` step 1 (set `bVisibleInUi`).
6. Resource nodes and spawners: spawn from Lua in a test game with `StaticFindObject` of the class and `SpawnActor`. Not checked. The Blueprint class must be loaded first (`NotifyOnNewObject` or `LoadAsset`).
7. Static check, no game: open the meshes in a viewer. Unpacked copies of the 13 manor meshes are in git-ignored `modtools/work/ua-mesh` (not in the repo).

## Open questions

- Does native code place a module by row id only, or does it filter by settlement level or tech? Test step 2 first.
- Is the Lv3 keep meant as the garrison of the town (36 garrison, tech gate), not of the manor? Row 83 sets `requiredTech`.
- Why does row 81 appear twice in the planner (cards 4 and 5)? One may be a copy for a Lv2 slot.
