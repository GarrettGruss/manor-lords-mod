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
