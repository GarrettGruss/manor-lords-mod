# Access points, animal spots and the 4-oxen stable (static study, 2026-10-14)

Issue #104. Spec 18. Game 0.8.111. Static only: the game was not started. Sources: the pak (unpacked with `pakmod.py` into the git-ignored `modtools/work/`), the jmap, and strings of the game executable. No game asset is copied here. Only names, numbers and transforms are summarized.
Tools (all new, read only): `harness/tools/s104_rows.py` (buildingStats rows), `s104_table.py` (any table, `--grep`), `s104_components.py` (components of a `BM_` class JSON), `s104_sockets.py` (mesh sockets), `s104_jmap.py` (jmap search), `s104_strings.py` (executable strings), `s104_unpack.ps1` (extract and convert). Components were dumped to `modtools/work/s104/*.txt`.

## Short answers

- Capacity of animals is a data field. `buildingStats.stableSpace` (Int) is 1 for the hitching post (row 30), 2 for the small stable (row 97), 2 for the livestock trader (79) and the pack station (112). `pastureSpace` is 0 in every row. The master copies it into `animalSpaceCache` (`AnimalSpace`: `stableCurrent`, `stableMax`, `pastureCurrent`, `pastureMax`). `getMaxOxen` and `Region:getTotalStableSpace` read it.
- The BM class has NO component for each ox. The hitching post and the small stable have only `gathering` (and `workpos` for the post). Where an ox stands is not stored in the BM class. It is not proven how the game picks the spot (see Open).
- The only "hitch" data is in socket mesh data (`SMD_*`, build-time helper assets): `SMD_HitchingPost` has 4 sockets `hitch0..3`, `SMD_OxShed` has 2 (`hitch0`, `hitch1`). The merged and preview meshes have NO sockets. The executable has no string `hitch` (only engine hitch settings). So `hitch*` is not a runtime lookup by name. It looks like a design helper for the construction Blueprint.
- Native name prefixes: the executable keeps one block of component name constants: `construction, Handcart, lazy, Bld, MainBld, FullBld, outhouse, bPart, VAMP, Bench, Dirt, Custom, flat, Shaft, workpos, gate, gathering, NobleGathering, occlusion, exclusion, plant, noAnimZone(A-D), lore, Res_, Anim, Tool, Clutter/clutter`. Tag names near it: `adjustSlope`, `workPos_add`, `workPos_addX`, `workPos_addY`.

## Rows (buildingStats, exported JSON)

| row | DisplayName | buildingFunction | stableSpace | upgrades / from | cost | BM class | visible | text key |
|---|---|---|---|---|---|---|---|---|
| 30 | hitching_post | Stable | 1 | upgrades `[14, 13, 19]` / from 0 | none (`constructionGoods` empty) | `BM_SG_HitchingPost_C` | yes (Logistics) | `buildingID_30` "Hitching Post" |
| 97 | small_stable | Stable | 2 | upgrades `[13, 19]` / from 30 | none; the upgrade 14 costs 4 planks (item 17) | `BM_SG_SmallStable_C` | no (only by upgrade) | `buildingID_97` "Small Stable" |
| 79 | livestock_trader | Default | 2 | none | | `BM_SG_LivestockMerchant_C` | yes | |
| 112 | Pack Station | Default | 2 | `[21]` | | `BM_SupplyDepot_PackStation_C` | yes | |
| 10 | Pasture | Pasture | 0 | none | | none (an area, Bounds 2500 x 1000, affinity Herbage) | yes (Farming) | |
| 31 | sheep_farm | Default | 0 | none | | `BM_SheepFarm_C` | yes | |
| 72 | Storehouse | Warehouse | 0 | `[7]` / from 0; storage generic 250 | | `BM_SG_Storehouse_Lv1_C` | yes | |
| 80 | granary_lv1 | Granary | 0 | `[8]`; pantry 500 | | `BM_SG_Granary_Lv1_C` | yes | |
| 69 | Farmhouse | Default | 0 | `[11]`; snapPoints 2 | | `BM_SG_Farmhouse_C` | yes | |
| 3 | residentialPlot_lv1 | Residential | 0 | | | none (plot, parts by code) | yes | |

Both stable rows share: Bounds 800 x 800 (circular border), `workerTypes` 2 (job 51), `needsRoad` true, `gatheringSpot` (0, 0, -5000) = not set, `maxHp` 50 (post) and 100 (stable), `canRelocate` true. Row 97 has `flammable` true and `AIcanBuild` false. Row 97 reuses the hitching post tooltip and card art. `constructionMeshAsset`: preview meshes (`SM_MERGED_BM_SG_HitchingPost_preview`, `SM_MERGED_BM_SG_SmallStable_PREVIEW`).
Upgrade chain: `DT_Upgrades` row 14 "upg to small stable": cost item 17 x4, `bUseOnlyOnce` true, `upgradesInto` 97. Row 13 "order_oxen" (`regionalWealth` 20) and row 19 "order_horse" (30) are purchases, not buildings.
`DT_ConstructionBPs` and `DT_BuildingMeshPathData` have NO row for 30 or 97. The key in `MainBld_<N>` is a part key: `MainBld_400` -> construction Blueprint `C_SG_OxShed_UBeam` (mesh path row 400 `SM_MERGED_C_SG_OxShed`). Key 541 -> `C_SG_oxShed_B_ubeam` (a second, unused ox shed "B", mesh `SM_MERGED_C_SG_OxShed_B_UBeam`, `SMD_OxShed_B` with 7 `PP` and 30 numbered sockets and no `hitch`). The farmhouse ox shed upgrade is an extension (`ext_animalStableLow`, `C_Ext_AnimalStableLow`) and an `upg_oxShed` mesh tagged `upgSlotA`.

## Components of the BM classes (everything that is not a clutter or dirt mesh)

Frame: each part class is a `StaticMeshActor` Blueprint: root `StaticMeshComponent0` (Movable), a `DefaultSceneRoot`, and SCS nodes. Units are cm. Rotations are Pitch/Yaw/Roll degrees.

`BM_SG_HitchingPost` (6 components)
| component | class | relative transform | note |
|---|---|---|---|
| `gathering` | Scene | loc (-248.5, 31.4, 0) | delivery / gather point |
| `workpos` | Scene | loc (99.0, -113.9, 0), yaw 137.6 | worker position |
| `MainBld_308` | StaticMesh `SM_MERGED_hitchingPost` | loc (-9.9, -83.8, 0), yaw -26.8, tag `adjustSlope` | the visible post |
| `dirt_0_2` | StaticMesh engine Plane | scale (9.6, 8.0, 0.5), yaw 1.4 | ground patch |

`BM_SG_SmallStable` (39 components)
| component | class | relative transform | note |
|---|---|---|---|
| `gathering` | Scene | loc (304.6, -19.4, 0) | only access point |
| `MainBld_400` | StaticMesh `SM_MERGED_C_SG_OxShed_UBeam` | loc (-5.0, 15.3, 0), yaw 0.9 | the shed |
| `dirt_0_2`, `dirt_3_0` | StaticMesh Plane | scale about (9.6, 8.0, 0.5) and (4.7, 6.1, 0.5) | ground |
| `clutter_*` x 34 | StaticMesh | random props around the shed, tags `adjustSlope`, `random` | barrels, hay, grass, bushes, dirt, tools |
No `workpos`, no `res_`, no animal component. (Its `workerTypes` is 2, but no work position is in the class.)

Others for comparison:
- `BM_SG_Storehouse_Lv1`: Scene `Generic` (origin) and 14 goods folders (`Clay`, `planks`, `Firewood`, `Tools`, ...), `MainBld_411`, `Bld_306`, 2 `Handcart*`, 147 `res_<good>_<n>` meshes (e.g. `res_35_*` 18, `res_13_*` 17). Tags on `res_` slots: `adjustSlope`, `alignSlope`, `addRefHeight`, `construction`, `process`, and `workPos_addX_<n>` / `workPos_addY_<n>` (offset of the worker position from the slot, values -100, 25, 50, 100).
- `BM_SG_Granary_Lv1`: Scene `gathering` loc (-277.5, 145.1, 0), Scene `Beer` loc (659.9, -15.2, 0), `Meat`, 75 `res_*`, 2 `handcart_*`, `MainBld`, `Bld`, 4 `Dirt`.
- `BM_SG_Farmhouse`: 8 `workpos_0..` (loc from (-919, 21) to (-778, 481), yaw -165 to 43), folders `Benches`, `Blenders`, `BuildingParts`, `clutters`, `DirtPlanes`, `GameplayLocations`, `Resources`, `MainBld_402/403`, 30 `Res_*` (flax piles), `upg_oxShed` (tag `upgSlotA`), `Preview_CobbledFloor`.
- `BM_SG_Cottage_Lv1_A` (a house): Scene `gathering` at the origin, folders `GameplayLocations`, `Resources`, `BuildingParts`, `Dirts`, `clutter`, `MainBld`, `fullBld`, 2 `res_`. No door component. The visible door is a mesh socket `doorPoor` (with `stairsWooden`) in `SMD_Farm_core`, i.e. art only.
- `BM_SheepFarm`: 3 `workpos_0..2` loc (0,-260), (60,-440), (380,-340); no `gathering`.
- `BM_SG_LivestockMerchant` (stableSpace 2): `gathering` loc (303.8, -334.9, 0), `Scene` loc (-115.3, -89.4, 0) yaw -451.2, 14 `Bld_`, `MainBld`.
- `BM_SupplyDepot_PackStation` (stableSpace 2): `Scene` loc (-321.2, 180.6, 0) yaw -451.2, 3 `Bld_`, `FullBld`, 2 `dirt`.
- `BM_SG_Ext_AnimalFeeder` (extension): `Scene` loc (-3.5, 166.1, 0) yaw -270, `workpos` (-117.6, -156.7) and `workpos1` (5.2, -113.7), both yaw 186.2.

## Meaning of the prefixes (evidence level)

| name | meaning | evidence |
|---|---|---|
| `MainBld_<key>`, `Bld_<key>`, `FullBld`, `fullBld`, `lazyBld_` | building parts. `<key>` is a `DT_ConstructionBPs` key. The master spawns an `SMBuilding` per part. | spike #69 (3 parts), executable constants |
| `res_<good>_<n>`, `Res_` | resource slot n of good `<good>` (DT_Items key). Shown when stock exists. Tags `construction`, `process` mark the construction and crafting use. | spike #94 (`res_16_*` = timber), storehouse data |
| `workpos`, `workpos_<n>`, `workpos<n>` | worker standing positions (jmap property type `SceneComponent` on the BM class; the master has `additionalWorkPositions`) | jmap, executable constants, comp lists |
| `workPos_addX_<v>`, `workPos_addY_<v>` (tag) | offset of the worker position of a resource slot. This is where a carrier stands to put or take that good. | tags on 70+ slots, executable `workPos_add*` |
| `gathering` | the gather and delivery point of the whole building. Row field `gatheringSpot` (0,0,-5000) is the unset default. | present on granary, stables, merchant, houses; jmap; executable |
| `NobleGathering`, `gate`, `exclusion`, `occlusion`, `noAnimZone*`, `Anim`, `plant`, `Shaft`, `Tool`, `Custom`, `flat`, `lore`, `outhouse`, `bPart`, `Bench`, `Handcart`, `Dirt`, `VAMP` | other native prefixes. `noAnimZone*` and `exclusion` look like zones where animated people or props are kept out. Not tested. | executable only |
| `clutter_*`, `Clutter` | random dressing (`spawnRandomClutter`). Tag `random`, `adjustSlope`. | spike #69 |
| `upg_*` + tag `upgSlotA` | mesh of an upgrade or extension slot | farmhouse |
| `Scene` (default name) | unknown. It sits on both stableSpace-2 rows (merchant, pack station) and the feeder. Candidate for an animal spot. | comp lists only |

There is NO component named `entrance`, `door`, `exit` or `stall` in any class read. Entry is the `gathering` point plus the road (`roadPos`, `needsRoad`, snap to road). Delivery and pickup stand at `gathering` (building) or at `res_` slot plus `workPos_add*` (storage goods).

## jmap findings (fields and functions)

- `SMBuildingMaster`: `oxen` (units), `maxOxen`, `activeOxen`, `animals`, `animalsOnPasture`, `animalSpaceCache` (`AnimalSpace`), `additionalWorkPositions` (struct array), `freeStallTransforms` (market stalls only), `Resources` (the `res_` actors), `Extensions` (`Extension`: `Type`, `transf`, `buildings`, `dirtPlanes`), `Carts`.
- Functions: `getMaxOxen`, `spawnAnimal(animalRole)`, `orderLivestock(Type)`, `changeActiveLivestockWorkers(amt)`, `RecomodateAnimalsOfType(AnimalType)`, `getAnimals`, `getAnimalsCurrentlyOnPasture`, `getLivestockWorkerRole`, `ChangeExtension(Slot)`, `BeginUpgrade`, `getAllPossibleUpgrades`.
- `Region`: `getTotalStableSpace`, `getTotalLivestockCount`, `GetTotalLivestockCountOfType`, `getNumUnassignedLivestockOfType`, `hasAnyUnassignedOxen`, `getLivestockPrice`, `accomodateHomelessLivestock`, `recomodatePastureLivestock`. `PawnCPP:getPlayersOxen`.
- Class `VAMP_Ox_C` (super `SMUnit`). `BM_SG_HitchingPost_C` has the properties `gathering` and `workpos` (type SceneComponent). `BM_SG_SmallStable_C` is not in the jmap (class not loaded when it was made).
- Stable total is village wide: `Inventory_C:WillNotRemoveLastOxSlot` calls `getTotalStableSpace`. So the stable row gives capacity to the region. The master then assigns oxen to the building.
- No jmap field for a per-animal spot, rest spot, `AnimalSlots`, `entrance` or `waypoint`.

## Open (needs the game)

1. Where do the oxen of a hitching post and a small stable stand? Read `master.oxen` positions against the master actor transform in a village with both buildings. Compare to the hitch socket positions (small stable, world, about (75, 208) and (75, -143) before the master transform) and to `gathering`.
2. Does a change of `stableSpace` alone raise `stableMax` and `getMaxOxen`, and does the extra ox get a spot?
3. Are 3 and 4 oxen on a 2-socket shed placed on the same spot (overlap) or around `gathering`?

## Plan: large stable (4 oxen), game round

Spec first: add it as a section to spec 18, or a new spec if the user wants a feature. Branch from the spec 18 branch or `main`.

### Pak `stable4` (data)
1. Extract `buildingStats` (existing flow: `pakmod.py extract`, `tojson`, as in `siege-camp-and-bm.md`).
2. `s65_edit_json.py stats <json> 97 125` clones row 97 to a new row 125 (ids up to 124 are in use by earlier tests, 125 is free in the table; check again).
3. New setter needed in `s65_edit_json.py`: `int <json> <row> <field> <value>` (UAssetGUI Int and Float fields; keep `IsZero` rules from the siege note). Set on row 125: `stableSpace` 4, `Bounds` X 800 Y 1500 (two sheds side by side), `maxHp` 150, `bVisibleInUi` true (`visible` command), `upgradedFrom` 97, `DisplayName` stays `small_stable` or becomes `large_stable` (no text row `buildingID_125`, the UI shows a raw key; add a text row only if the card is needed).
4. `s65_edit_json.py blueprint <json> 125 /Game/HarnessMod/BM_HarnessLargeStable BM_HarnessLargeStable_C` points the row to the new class.
5. Optional later: a `DT_Upgrades` row (new id, `upgradesInto` 125, cost 8 planks) and the id appended to the `upgrades` array of row 97. Not needed for the first test (place by `activateBuildingMode(125)`).
6. `fromjson --to stable4`, then `build stable4`. Remove the pak after the run (`pakmod.py remove --all`).

### Blueprint `BM_HarnessLargeStable` (UE 5.5.4, copy `make_bm.py` to `make_bm_stable.py`)
Parent `StaticMeshActor`, path `/Game/HarnessMod`. Components (names matter, see prefixes):
| name | class | relative transform | note |
|---|---|---|---|
| `MainBld_900` | StaticMesh `/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_OxShed_UBeam` | loc (-5.0, 15.3, 0), yaw 0.9 | shed A (copy of the small stable part) |
| `MainBld_901` | same mesh | loc (-5.0, 665.3, 0), yaw 0.9 | shed B. The shed pivot is near its centre; its length along Y is about 550 to 650. Adjust the offset after the first screenshot (gap or overlap) |
| `gathering` | Scene | loc (304.6, 340.0, 0) | in front of the pair, centre between A and B (small stable: (304.6, -19.4) in front of its single shed) |
| `dirt_0_0` | StaticMesh `/Engine/BasicShapes/Plane` | loc (44, 340, 0), scale (5, 14, 0.5) | optional ground patch |
Extra probe components (harmless if unused; test hypothesis "Scene = animal spot"): `Scene_0..3` as Scene components at the four hitch positions: (74.7, 208.3), (75.1, -142.9), (74.7, 858.3), (75.1, 507.1), yaw about 180. Add them only in a second pak (`stable4b`) so the first result is clean.
Use the mesh by reference path (no copy). The engine loads it from the base paks. If the cook step needs the asset, add `+DirectoriesToAlwaysCook` for `/Game/ManorLords/Buildings/Merged` (or use an engine mesh stand-in and swap in the pak: `stable4` can also retarget the part with the construction key 400 route).

### Test scenario (round 2)
Fixture `base` or a fixture with a village. No save call. Steps:
1. Baseline (no pak): place a hitching post (row 30), upgrade to the small stable (upgrade 14, 4 planks), order 2 oxen (`orderLivestock` or upgrade 13). Bridge reads: master transform, `oxen` array (each location), `animalSpaceCache`, `getMaxOxen`, `Region:getTotalStableSpace`, parts via `master_parts`. Screenshot with the oxen. Do not read soft-object structs (`getItem`, `RowStruct`).
2. With pak `stable4`: `activateBuildingMode(125)`, real click on open ground next to a road (white ghost), build (4 game days at speed 3 as the tent test). Read `stableMax` (expect 4), parts (expect 2 `MainBld_*` parts).
3. Get 4 oxen: `orderLivestock(<ox type>)` four times, or the `order_oxen` upgrade, or `spawnAnimal`. The ox type id and price: `Region:getLivestockPrice`. Give the settlement wealth first (`regionalWealth` 20 per ox).
4. Wait until the oxen are assigned. Read `oxen` positions against the master and screenshot (camera over the building with `K2_TeleportTo` on the pawn, see siege notes). Expected: 4 oxen near the stable, not stacked on one point.
5. Accept: `stableMax` 4, 4 oxen listed in `oxen`, 4 distinct positions (pairwise distance over 50 cm), screenshot shows 4 oxen at or near the stable. Fail case: spots stack. Then run `stable4b` with the `Scene_*` probe components and compare positions.
Note the traps from the siege notes: `bVisibleInUi` needs `IsZero` false; the `MAX_TYPE` limit is 600; the command channel needs `reload_mods`; remove the pak after the game is closed.

## Changes outside the repo
- `modtools/work/` (git-ignored): extracted and JSON files of the classes listed above, `modtools/work/s104/*.txt`. No game file, no save, no setting was changed. The game was not started.

## Game round (2026-10-15, issue #104, runs s104g-1 to s104g-3, 3 launches, fixture `base`)
No save function was called. The AES key came only from the environment. The game is closed and `~mods` is removed. Screenshots are git-ignored: `runs/s104g-N/screenshots/` (worktree `agent-a0e941f6393cf399b`): `stable97_a.png` (baseline), `stable97_pak.png` (two sheds), `stable4_4oxen.png` (HUD shows 4 oxen).
New tools: `s104_stable.py` (master, oxen, `animalSpaceCache`), `s104_order.py` (struct call, does NOT work), `s104_mouse_probe.py`, `s104_window_probe.py`, `s104_window_fit.py`, `s104_cursor_probe.py`.

### Baseline (run s104g-1, no pak)
- `base` already has a small stable (row 97) for the player (region Nusslohe) and hitching posts (row 30) for AI regions. So no hitching post was placed. The mouse blocker (below) made a new placement impossible.
- Player stable: `animals` holds 2 `VAMP_Ox_C`, `oxen` is empty, `animalSpaceCache` `stableCurrent` 2, `stableMax` 2. `getMaxOxen` returns 0 (not the stable size). `Region:getTotalStableSpace` 2. Hitching posts: `stableMax` 1 and one animal each (ox or horse).
- The animals are not standing at the building. They were 3.6 k to 9 k units away (field work). A kept-open run is paused, so nothing moves to a rest spot.
- Real data: `master.animals` is the list of housed animals (not `oxen`). The building owns no per-ox spot.

### Pak `stable4` (`mod/HarnessActions/paks/stable4_P.pak`, paths start with `ManorLords/Content/`)
- Row 125 = clone of row 97: `stableSpace` 4 (a Byte field), `Bounds` 800 x 1500, `maxHp` 150, `bVisibleInUi` true, class `/Game/HarnessMod/BM_HarnessLargeStable`. Row 97 got the same changes (stableSpace, Bounds, maxHp, class). This lets a built stable of the save become the large stable without a mouse placement.
- Blueprint `BM_HarnessLargeStable` (`mod/HarnessActions/ue/make_bm_stable.py`, UE 5.5.4): parts `MainBld_900`, `MainBld_901` (mesh `/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_OxShed_UBeam`, 650 units apart in Y) and Scene `gathering`. The game mesh is not in the UE project. A stand-in copy of the engine Cube was made at the same path, and only the `BM_` files were packed. The cooked Blueprint then points at the real game mesh.
- Load check: `building_stat kind=125` reads `bVisibleInUi` true and `maxHp` 150 (vanilla has no row 125). Row 97 reads `maxHp` 150.
- Result: the player stable now has 2 parts (two real ox sheds side by side, `stable97_pak.png`) and `stableMax` 4. `Region:getTotalStableSpace` 4. So a data change of `stableSpace` alone raises the capacity at once, and the new class gives the two-shed look. A stable of an AI region (row 97) also reads `stableMax` 4.
- Placing row 125 with the build mode: NOT done (blocker below).

### 4 oxen (run s104g-3)
- Command `plot_upgrade` now takes `type` (HarnessHousing): it sends `addUpgradeRequest` for the first own master of that type, no mouse. `upgrade=13` (order oxen) added ONE ox: `stableCurrent` 2 to 3 after about 3 game days (the ox walks in from the map edge, 100 k units, about 14 game days at speed 3). Three more orders (also after the ox arrived) added nothing. `orderLivestock(0)` returned true and added nothing. Reason not found (`regionalWealth` 85, price 1).
- The 4th animal was added with `SMBuildingMaster:spawnAnimal(12)` (EUnitRole 12 = Ox). It is a harness spawn, not a purchase. `spawnAnimal(0)` spawned a `VAMP_DefaultUnit` (wrong role, a stray that stays in `animals`; it is not counted in `stableCurrent`).
- End state: `stableCurrent` 4, `stableMax` 4, 4 `VAMP_Ox_C` in `animals`, HUD oxen counter 4 (`stable4_4oxen.png`). A new ox stands at the master origin (offset about (-15, +10) from the master location), the arrived bought ox at about (-10, -20) to (-35, -230). Others were away working. Positions are therefore not fixed spots: they come from the work AI. No evidence for per-ox stable slots; with 4 oxen at the stable, they did not stack in one point (distinct realPos, more than 50 units apart).

### Blocker: the mouse does not reach the world (third round in a row)
- `getMouse3d` returns Z -100000 in build mode (hitching post 30 and row 125) with the game unpaused, window moved to (0,0) 2000 x 1200 (it was partly off the 2560 x 1440 screen), a click on the window first, `SetCursorPos` plus relative `mouse_event` wiggles, the game in the foreground, the cursor over the game window. The build mode hints show, but no ghost. Probes `s104_mouse_probe.py`, `s104_window_probe.py`. Not solved. So no new building was placed, and "place with a real click on a white ghost" is open.
- Workaround used: the pak overrides row 97, so the existing stable of the save becomes the large stable.

### Verdict
- Capacity and look: proven (stableMax 4, two sheds, 4 oxen housed, HUD 4).
- New placeable card (row 125 by the mouse): not proven (mouse blocker).
- Open: why repeated `order_oxen` adds nothing; where oxen rest when idle (run unpaused longer, at night).
