# Burgage plot placement: events seen (2026-10-12)

Live session with the user. New game on Jagged_Cliffs (no fixture, autoboot switched off), player region `immenreuth`.
The user built 10 burgage plots by hand. The agent watched with bridge hooks (`hook_function`) on PawnCPP and RTSMultiEngineCPP.
The user received 20 timber first (`MLCheatManager:GiveItemByID(16, 20)`).

## Calls seen while placing (one row of 10 plots)
| t (s) | Call | Note |
|---|---|---|
| 145.2 | `resetBuildingMode()` | |
| 147.6 | `selectBuildingMode(3, Stat)` | type 3 = `residentialPlot_lv1`: `occupantTypes.Y` 1 (one family), cost 2 timber, `needsRoad`, upgrades 2 and 12 |
| 150 to 163 | `fieldRemovePoint()` x5 | while drawing |
| 167 to 170 | `changePlotOffset(-1)`, `(+1)`, `(-1)` | plot split offset |
| 173.2 | `addCommitFieldRequest()` | one call for all 10 plots, no parameters |
| 174.2 | `fieldRemovePoint()` | after the commit |

## Hooked but never seen
`activateBuildingMode`, `setPlacedBuilding`, `fieldAddPoint`, `commitField`, `setFieldMode`, `addExtensionChangeRequest`,
`constructionComplete`, `finishSpawningSoloBuildingAsync`. These are called from native code (the hooks see only calls through
ProcessEvent), or not used for plots. No event was seen during construction or move in.

## State after construction (read through the bridge)
- `getBuildingCount(3, true)` = 10. `getAvailableLivingSpace` = constructed 4, unconstructed 0 (so 6 families moved in).
- `getBuildingCount(87, false)` = 0: the homeless tents are gone.
- User report: families move in almost at once after a plot is finished. The tents were deleted by the game when 5 people moved into plots.

## Pawn state during a plot placement (snapshot and diff, second row, user save saveGame_30)
Steps: snapshot the pawn, the user draws 2 points, diff; 2 more points (a closed square), diff; commit, diff.
- 2 points: `placeFieldMode` true, `placePlotType` 3, `FieldPoints` +2, `fieldSmoothPoints` and `fieldSmoothPointsClosed`
  (plain Vectors, the corners), `fieldPointsRotated`, `fieldPointsClosed`, `fieldCenter` (Vector), `fieldSplineMeshes`.
- 4 points (closed): `fieldClosed` true, `expectedNumPlots` 4, `maxDivisionsForThisPlot` 4, `fieldWorkersNeeded` 4,
  `extractedPlots` 4 (`ExtractedPlot` structs, one per plot), `extensionTransforms` 4, preview decals 4 each, `fieldPreviewTriangulated` 6.
- Commit (`addCommitFieldRequest()`, no parameters): every field array above is emptied, `fieldClosed` false, `fieldWorkersNeeded` 0,
  and 4 new `SMBuildingMaster` appear in `closeBuildings`. So the commit reads this pawn state.
- `FieldPoint` (56 bytes) and `ExtractedPlot` show no reflected fields through the bridge, like `BuildingSpawnParams`. Lua cannot
  fill them. The plain Vector arrays can be written, but it is not known if the commit reads them or only the structs.

## Delete and commit without a click
- Deleting a plot from its panel fired no hooked function (also not `SMBuildingMaster:demolish` or `cancelOrder`). Only the
  selection (`selectedBld`) and `closeBuildings` changed. Detect deletes by polling counts.
- With a square drawn by the user (not confirmed), the agent called `PawnCPP:addCommitFieldRequest()` through the bridge.
  4 new `SMBuildingMaster` appeared and the outline arrays emptied. The user confirmed the plots in the game. **Commit without a
  click works.** The build tool stayed open (`placeFieldMode` true).
- Outline written from Lua (test-only command `plot_field_shift`, HarnessActions 28): with a closed square drawn by the user, the
  command moved `fieldSmoothPoints`, `fieldSmoothPointsClosed` (5 points each) and `fieldCenter` by +3000 on X (also back and forth
  once). On screen only the build button moved; the outline stayed. After `addCommitFieldRequest()` the plots were built at the
  **drawn** outline (user check). So the commit reads the `FieldPoint` structs (or `extractedPlots`), not the plain vectors.
  Lua cannot fill those structs, so a fully mouse-free plot needs the outline drawn by a real or OS mouse, or a struct writer.
- **`extractedPlots` decides where plots are built (HarnessActions 30, `plots:true`).** jmap: `FieldPoint` has no reflected
  properties (56 bytes), but `ExtractedPlot` (400 bytes) is fully reflected: `SmoothBorder`, `Corners`, `extensionSmoothBorder`,
  `extensionCorners` (Vector lists), `primaryBuildingTransform`, `secondaryBuildingTransform`, `extensionTransform`, `backFacade`
  (Segment A, B). The command moved every position of the 2 extracted plots by +3000 on X. The preview did not change on screen.
  After `addCommitFieldRequest()` the 2 plots were built at the **moved** place (user check). So a mod can choose where plots go
  by writing `extractedPlots`, as long as a closed field exists (`fieldClosed` true). Bug found: the HarnessActions parser keeps
  only known fields, so `plots` and `commit` are read from the raw request.
- **Plots with no outline drawn (HarnessActions 31, `plot_field_place`).** The user opened the burgage tool and drew nothing.
  The command emptied `extractedPlots`, grew it to 2 elements (UE4SS grows a TArray when Lua writes index n+1, also for a struct
  element written as `{}`), filled every vector list, transform (Scale3D set to 1) and `backFacade` from numbers in the request,
  and set `expectedNumPlots` 2 and `fieldClosed` true. `FieldPoints` stayed empty. After `addCommitFieldRequest()` the 2 plots
  were built (user check). No crash. So the commit needs only `extractedPlots`, `fieldClosed` and the open burgage tool.
- **Fully mouse-free (same session).** Tool closed (`placeFieldMode` false, `placePlotType` 0). The agent set `placePlotType` 3
  and `placeFieldMode` true (bridge `set_property`), sent `plot_field_place` with the stored shapes moved +3000 on X, and called
  `addCommitFieldRequest()`. 2 plots were built (user check). No click, no drawing, no crash.
  Recipe: set `placePlotType` = 3, `placeFieldMode` = true; write `extractedPlots`; set `expectedNumPlots`, `fieldClosed` = true;
  call `addCommitFieldRequest()`.
- **Plot count in a drawn field.** The count is `maxDivisionsForThisPlot` + `numPlotOffset` (pawn properties). With a closed field
  of 4 plots, the agent called `PawnCPP:changePlotOffset(-1)` (the same call as the user's plot count keys). `numPlotOffset` became
  -1, the preview showed 3 plots (user check), and the commit built 3 plots. `expectedNumPlots` still read 4 after the change: it
  is not the live count. Read the count as `extractedPlots` length.
- Open: the plot data came from a drawn field. A mod must compute corners, borders, the house and extension transforms and the back
  facade itself (or keep stored shapes and move them). Not checked: what the commit does with a bad spot (overlap, water, slope,
  no road), timber cost and builder flow for these plots, and whether the build tool state needs a reset after the commit.

## Leads
- The plot outline is pawn state. `addCommitFieldRequest` reads it. If Lua can fill the field points (the pawn properties used by
  `projectField`, `getFieldCenter`), a plot row may be placed without the mouse. Not tested. Next step: snapshot the pawn during a placement.
- Homeless tents are removed by the game when homes are free. A mod that wants homeless people must keep free homes at 0.
</content>
</invoke>

## How a built burgage plot is made up (2026-10-12, run `s65-burgage-inspect`, fixture `base`)
The user hovered the house of a level 1 plot; `PawnCPP:getHitBuilding()` gave `SMBuildingMaster_2147466692`: `Data.bType` 3,
constructed, `lv` 1, `buildingFunction` 1, `occupantFamilyIDs` [3] (one family). It is built like the homeless tent: one
`SMBuildingMaster` with plain `SMBuilding` prop parts, each with one `StaticMeshComponent0`.
- `buildings`: 35 parts. The house is ONE part, `SM_MERGED_C_SG_Cottage_Lv1_A_v4_UBeamFoudnations`. The others are props: a shed
  (`SM_MERGED_C_SG_J_ShedA`), an outhouse, a gate, fence segments, stairs, a chest, a bag, a rope, barrels, a sitting log, stick heaps,
  stone packs, 8 `GroundBlenderA` (ground blend meshes) and 3 grass clumps (`clump_short_2_wallMask`).
- `Extensions`: 1 entry (`Extension` struct, `Type` 0 = the back garden). It has its own list of 33 parts (log walls, filler boards,
  sitting logs, tools: hoe, hammer, shovel, 2 axes, a wagon wheel, a tub, fences, stones, stick heaps) and its own `dirtPlanes` mesh
  components on the master.
- So a plot is a building master + house mesh part + prop parts, and the garden extension is a second part list inside the same master.
  The game picks the props. Not checked: whether plots placed with `plot_field_place` get the same parts.
- A larger plot with a vegetable garden (`SMBuildingMaster_2147467363`, user hover): still `Data.bType` 3 and `lv` 1, but
  `upgradesDone` = [12, 108] and `occupantFamilyIDs` = [4, 5] (two families). The house is two parts (`SM_MERGED_C_SG_Cottage_Lv1_C_UBeam`
  and `SM_MERGED_C_SG_Cottage_LV1_BPart_C_UBeam`, the second family's part); 35 parts in all. The extension has `Type` 8 (vegetable
  garden, 18 parts: 6 cabbages, beet bundles, carrot piles, baskets, a narrow shed). So plot upgrades do not change the building type:
  they are listed in `upgradesDone` (12 is in row 3's `upgrades` list [2, 12]; 108 is likely the garden) and change the part lists and the
  extension type. Lead: `PawnCPP:addUpgradeRequest` and `addExtensionChangeRequest` could add these without the mouse (not tested).

## Garden upgrade through the panel (same session, user upgraded the small plot `SMBuildingMaster_2147466692`)
- Hook: `PawnCPP:addExtensionChangeRequest(UpgradeRequest)` fired once (the panel call is reflected and hookable).
  `UpgradeRequest` (16 bytes, jmap) is fully reflected: `buildingMaster` (SMBuildingMaster), `upgradeID` (int), `Slot` (int).
  `PawnCPP:addUpgradeRequest` takes the same struct.
- Plot diff: `upgradesDone` [] -> [108] (108 = vegetable garden), `Extensions[1].Type` 0 -> 8, `Data.constructed` true -> false,
  `isBeingUpgraded` true, `constructionGoods` = 2 planks (item 17), the old yard parts removed (28 house-list parts, 14 extension parts),
  18 `Resources` entries added, a field decal, `forceHarvest` true. Builders must finish the upgrade.
- Lead (not tested): a mod calls `addExtensionChangeRequest({buildingMaster = plot, upgradeID = 108, Slot = 0})` for a garden, and
  `addUpgradeRequest` with `upgradeID` 12 for the second family (row 3 `upgrades` [2, 12]).
- Builders finished the garden (`Data.constructed` true, `isBeingUpgraded` false). Buying carrot seeds in the panel fired
  `PawnCPP:addUpgradeRequest({buildingMaster = the plot, upgradeID = 30, Slot = 0})` (args read by the hook). `upgradesDone` became
  [108, 30] (30 = carrot seeds). Regional wealth went 591 -> 559 over the same minutes (the seed price is part of it; not isolated).
- **Upgrade without the mouse (HarnessActions 37, command `plot_upgrade`):** with the user's mouse over a plain plot
  (`SMBuildingMaster_2147466768`, type 3, `upgradesDone` []), the command called `PawnCPP:addUpgradeRequest({buildingMaster = getHitBuilding(),
  upgradeID = 12, Slot = 0})` from Lua (the hook saw it). A moment later: `upgradesDone` [12], `isBeingUpgraded` true, `Data.constructed`
  false, `constructionGoods` 2 timber (item 16), families still [2]. So a Lua table with an object field is accepted as the struct.
- **Upgrade ids** (engine `RTSMultiEngineCPP.upgrades`, 63 `Upgrade` structs: Name, cost, regionalWealth, upgradesInto, ...; also
  `DT_Upgrades`): normal upgrade id = list position + 1 (WRONG, see the correction below), extension id = 100 + extension number. Checked against the panel:
  12 = `BPart` (cost 2 timber: the second-family house part, user saw "2 logs"), 30 = `PlantCarrots` (32 regional wealth; the user bought
  carrot seeds), 108 = `extension8` (2 planks, the vegetable garden, extension `Type` 8). Others: 2 peasant house, 3 townhouse,
  28 to 33 the crops (beetroots, carrots, cabbages, quinces, apples, pears), 14 herbs_garden. `buildingStats` rows with the same numbers
  are unrelated (row 108 is clay_furnace).
- After `plot_upgrade upgrade=12` the plot showed "awaiting an extension" (user): the upgrade is under construction like the garden.
- Result: after the builders finished the BPart upgrade (id 12) placed by `plot_upgrade`, the plot holds **2 families** (user). The user
  says this plot is too small for the second-family upgrade in normal play; the panel does not offer it there. So the plot size check is
  only in the UI: `addUpgradeRequest` from Lua does not enforce it (like `convertBlueprintsToBuildings` ignoring `maxInRegion`).
  For refugee waves this gives a mouse-free way to add family slots to existing plots (2 timber each).
- **Extensions take the plain extension number.** A first try sent `addExtensionChangeRequest` with `upgradeID` 108: the extension
  `Type` became 108, `upgradesDone` got a 0, no build started, and the panel showed `upgradeID_208` (invalid). The panel's delete button
  sent `addExtensionChangeRequest(upgradeID 0)` (hook): `Type` back to 0, the bad entry removed. Then `plot_upgrade upgrade=8
  extension=true`: `Type` 8, `upgradesDone` [12, 108], `isBeingUpgraded` true, cost 2 planks. So the request uses the extension number
  (0 = plain yard, 8 = vegetable garden) and the game stores number + 100 in `upgradesDone`.
- Seeds without the mouse: after the garden was built (`constructed` true), `plot_upgrade upgrade=30` (`addUpgradeRequest`) gave
  `upgradesDone` [12, 108, 30]; regional wealth 559 -> 527 (exactly 32, the `PlantCarrots` price). The user confirmed it in the panel.
  Full mouse-free plot chain on one plot: wing (12, 2 timber) -> garden (extension 8, 2 planks) -> carrot seeds (30, 32 wealth).
- **Correction: the id rule "list position + 1" is wrong.** Level 2: `plot_upgrade upgrade=3` (twice, the second time after the food
  need was met) only added a stray 3 to `upgradesDone`; nothing was built. The user then clicked the level 2 upgrade in the panel: the hook
  saw `addUpgradeRequest(upgradeID 2)`; the plot became `bType` 8 (peasant house), under construction, `upgradesDone` [12, 108, 30, 3, 2].
  The stray 3 did not block it. So ids are not list positions in `RTSMultiEngineCPP.upgrades`; they are most likely the row keys of
  `DT_Upgrades`. Ids confirmed from panel calls or effects: 2 = level 2 (peasant house, plot type 3 -> 8), 12 = second-family wing,
  30 = carrot seeds (32 wealth), extension 8 = vegetable garden. Read `DT_Upgrades` row keys before using any other id.
- A level-up needs the family's needs met first (the panel said "requirements not met": foraged goods, vegetables, grains or fruits);
  after 50 each of berries (171), vegetables (230), wheat bread (172) and apples (296) and some game time, it was met.
- Level 2 finished: `Data.bType` 8, constructed, `lv` 2, families [2, 10] (two), `upgradesDone` [12, 108, 30, 3, 2].
