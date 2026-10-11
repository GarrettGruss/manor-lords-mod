# Spike S13: dynamic lords (2026-10-11)

## Question (user request)
Can the world start with only the player, and can the player "claim" a region by spawning a neutral AI lord into it at run time?

## Method
Four real-game runs (`s13-lords-1` to `-3`, plus the S11 runs). Each new game was started from the main menu with HarnessBoot off:
`MLGameInstance:SetNumAILords(0)`, then `mainMenu_widget_C:startNewGame()` (no arguments; the game starts at once with the intro cinematic).
Commands: `HarnessLords` (`spawn_ai_lord`, `lord_relations`, `lord_take_region`, `lord_start_ai`, `regions_state`, `lords_state`).

## Results
| Step | Call | Result |
|---|---|---|
| World with only the player | `SetNumAILords(0)` before `startNewGame` (`getMaxAILords` = 3) | **Works.** Pawns: the player, the baron (off-map, no army, cannot build, owns 2 border regions) and the Outlaws. No neighbor lords. 7 regions: 1 settled (the player's, random each new game), 2 the baron's, 4 free and empty. |
| Spawn a lord at run time | `spawnNewAILord(name, false, nil, canBuild true)` | **Works** (also S11). |
| Neutral relations | `RTSMultiEngineCPP:addPawnRelations(lord)` | **Works.** Relation rows 3 -> 6. With the player: no tags (not at war), friendship 0. |
| Give the lord a region | write `Region.ownerPawn = lord` | **Works** for a settled region: the owner changes and the village (4 buildings, 5 families) stays. In run `s13-lords-2` this was by mistake the player's start region, so the player was left with no region. |
| Lord runs the region | `startAI(1, canBuild true)`, 10 game days at 8x | **Partly.** The general and tactics AI run ("claimRegions: not enough influence", "banditCampsToLoot = 1"). **No construction:** `debugLog_AI_construction` stayed empty. Lords made at game start placed their first building by day 2 in other runs. |
| Found a settlement in an empty region | `PawnCPP:settleRegion(region, campTransform, supply, ESettlementType, outpostToRegion)` | **Crashes the game, 3 of 3**: access violation reading 0x34c, the same address each time: called on the new lord with no outpost region, on the player pawn, and on the new lord with an outpost region. The command was removed. Crash reports: `runs/s13-lords-*/crash/`. |

## Answer
- A world with only the player: yes (a new game with `numGenericAILords` 0).
- Spawning a neutral lord at run time and handing it an existing settlement: yes.
- Spawning a lord into an EMPTY region so that it founds and grows a village: not from Lua today. `settleRegion` crashes, and a spawned lord does
  not run construction even when it owns a village.

## Options for the design
1. Start with AI lords present (up to 3, the game's own setup) and make "claiming" a change of allegiance (relations, friendship, a mod-defined
   support level), not a spawn. The game's lords build and grow on their own.
2. Pre-built neutral villages as a fixture: build or grow villages in empty regions (the player builds them, or lords of a setup game), save,
   then hand each to a spawned neutral lord at run time with `ownerPawn`. Their growth would then come from the mod, unless the construction AI
   can be started (next lead).
3. Leads not yet tested: `CityPlanningComponent:ResetAIBuildingOptions` (may set up the construction AI of a lord), the engine flag
   `spawnAIPlayers` and `AI_buildingTypes`, a `settleRegion` call with a camp transform taken from a real settlement (the 0x34c read may come
   from a missing object that the game creates for a start location), and `MLGameInstance:setStartLocation`.

## Not verified
- What the player sees (map, region panel, letters) for a spawned lord.
- Whether a spawned lord and its region survive a save and load.
- Construction AI with any of the leads in option 3.
