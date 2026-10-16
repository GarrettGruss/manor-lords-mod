# Mouse-free placement: AI lord route (issue #104)

Date: 2026-10-15. Result: NOT achieved. No readable function carries an AI lord build, so there is nothing to reuse for the player. 1 game launch (run `s104a-1`, fixture `base`). No save function was called. `allow_eval` stayed false. The row 30 and row 125 placements were not tried, because step 3 has no input.

Follows `mousefree-blueprint-route.md`. Tool: `harness/tools/s104_ai_watch.py` (holds speed 3, then lists hook counts and the first events of each hook).

## Question
When an AI lord builds a normal building, does a reflected (ProcessEvent) function run with a readable type, transform, region or owner? If yes, the player could call the same function.

## Method
- Fixture `base`: 4 AI lords (`PawnCPP_AI`: Endlein, Herman, Mathes and one more). They build on their own. `debugLog_AI_construction` showed `AI_build` lines for LoggingCamp, BurgagePlotTool, HitchingPost, `Manor_Palace_Lv1`, and many `AI_upgrade` lines.
- Game at speed 3, held every 5 s, about 6 game minutes in total (cycle counter 2 to 119 in the AI log).
- Bridge `hook` on 37 functions (3 of the first batch were refused; 34 ran):
  - `RTSMultiEngineCPP`: `finishSpawningSoloBuildingAsync`, `spawnAsyncContstrBPLazy`, `getConstructionBP`, `loadAsyncBP`, `getLoadedConstructionTemplate`, `setupBuildings`, `SetBuilding`, `eraseBuildingReferences`, `getBuildingData`, `getBuildingByID`, `isBuildingTypeValid`, `extractBTypeFromTag`, `getModuleRadiusForBuildingID`, `getNearestBuildingTo`, `segmentCollidesWithAnyBuilding`, `pointCollidesWithBuildingBorder`, `getBuildingPartMeshPath`, `getUpgradeData`, `updateOpenClaims`.
  - `PawnCPP` (the AI pawn inherits them): `constructionComplete`, `playBuildEffects`, `setBuildingMesh`, `UpdateBuildingProximityCache`, `setPlacedBuilding`, `selectBuildingSilent`, `playBuildingSound`, `getHitBuilding`.
  - `PawnCPP_AI`: `RecalculateOptionsDebug`, `PickBestOptionDebug`.
  - `SMBuildingMaster`: `SetupBuilding`, `setConstructionPaused`, `convertBlueprintsToBuildings`, `BeginUpgrade`.
  - `Construction:setData`, `Construction:getData`, `ConstructionBP_C:setupConstruction`, `ConstructionBP_C:ReceiveBeginPlay`.

## Results
| Hook group | Events during AI builds |
|---|---|
| All `RTSMultiEngineCPP`, `PawnCPP`, `PawnCPP_AI`, `SMBuildingMaster` hooks above | 0 |
| `Construction:setData` | 0 |
| `Construction:getData` | 300+ (called every frame by the visuals, no use) |
| `ConstructionBP_C:setupConstruction` and `ReceiveBeginPlay` | 6 each, on new site actors such as `C_SG_Well_C_...`. The arguments are empty. |

## Findings
- The AI lord decides, picks the spot and creates the construction site in native code. It never goes through a reflected function. This is the same as the player placement (a native path with `BuildingSpawnParams`).
- The first reflected call happens only after the site exists: the visual construction actor (`C_<Name>_C`, a `ConstructionBP_C`) runs `setupConstruction` with no arguments. It is the picture of the site, not the site. Calling it for the player would make a model with no master, no queue entry and no builders (compare `mousefree-blueprint-route.md`, `newmaster`).
- The AI debug functions `RecalculateOptionsDebug` and `PickBestOptionDebug` never ran. They are editor helpers.
- The only AI lever that works from Lua is to hand a region to a lord (`lord_receive_region`, spec 10 `dynamic-lords.md`). The lord then builds what its own AI picks (log names such as `AI_build: HitchingPost`). The player cannot choose the row, the spot, or the owner (the lord owns the building).

## Verdict
The AI route gives no input for the player. Reflected hooks cannot see the build. The native spawn needs a real mouse or a native-level tool (for example a code patch, which this project does not do).

## Not done
- Step 3 (call the same function for the player) and step 4 (row 125 with pak `stable4`, command `place_building_at`, fake tests, skill update): no function to call.
- Not tried: hook by native address (not available in UE4SS Lua), `NotifyOnNewObject` for `SMBuildingMaster` to read its `Data` and transform after an AI build (it would show the result of a build, not a way to start one).
- Remaining real options: a real or virtual mouse device on the PC (user action).

## Cleanup
Game closed. Fixture slot `saveGame_47` removed with `harness/tools/fixtures.py uninstall`.
