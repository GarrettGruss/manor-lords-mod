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

---

# Part 2: a dynamic AI village (2026-10-11)

Goal: the player owns a region, a starter settlement exists there, a neutral AI lord takes it, and the lord builds.
Result: **works.** Five real-game runs (`s13-village-1` to `-5`, new game with only the player, HarnessBoot off, Jagged Cliffs map).
Two calls crashed the game (see "Crashes"). The working flow needs no raw eval.

## Findings
| Step | Call | Result |
|---|---|---|
| Who has a construction component | read `Region.CityPlanningComponent` (run 1, 2) | Only owned regions have one: the player's home, the baron's 2 regions. Free regions have none (property invalid). |
| Own a free region at once | `PawnCPP:layClaim(region, false, false)`, then `PawnCPP:finalizeClaim(region, false)` (command `claim_region`) | **Works.** `layClaim` alone only adds a claim (`DaysLeft` 14, `open_claims` 0). `finalizeClaim` sets `ownerPawn` and **creates the CityPlanningComponent** (run 2: `..._2147468463` appeared). The claim entry is removed. Works for the player and for a lord. |
| Starter village | `PawnCPP:settleRegion(region, camp, supply, type, nil)` on an OWNED region (command `settle_region`) | **Works** (run 2, 3, 4, 5, 7 calls, 0 crashes): 0 -> 4 buildings, 0 -> 5 families, `isSettled` true, `settlementType` 1. Camp = `Region:getSettledRegionCenter()`. Camp example: x -40887, y 62950, z 7087. |
| Why settleRegion crashed in part 1 | all 3 crashes used a region with no owner | The 0x34c read is a missing owner or component. With a claimed region it does not crash. |
| Lord claims and settles by itself | `claim_region target=lord` + `settle_region target=lord` (run 2: Hans on Nusslohe; command `lord_found_village`) | **The lord builds.** Construction log from game cycle 2: `AI_build: LoggingCamp`, `HitchingPost`, `Marketplace`, `BurgagePlotTool`, `AI_upgrade: OrderOxen`. Buildings 4 -> 12 in about 16 game days (supply 0). Run 3: Otto, supply 2: 10 build lines in 20 cycles and no "lacks resources" line (supply 0 lords logged "AI_build lacks resources: BurgagePlotTool / Well_Lv1"). Buildings 4 -> 14. |
| Transfer with `Region.ownerPawn = lord` | `lord_take_region` on a village the player settled (run 2 Karl; run 3 Hans on Eichenhau, Karl on immenreuth, 17 game days) | **No construction.** `debugLog_AI_construction` had 0 lines for these lords. The general and tactics AI ran. Settling the region again as the lord (run 3) did not help. A second `finalizeClaim` by the lord on a region it already owned did nothing (the component stayed). |
| Transfer that works | `Region.ownerPawn = nil`, then the lord's `layClaim` + `finalizeClaim` (command `lord_receive_region`) | **The lord builds.** Run 3 (with the component also cleared): Hans 4 -> 16, Karl 4 -> 15 buildings. Run 4: Karl without clearing the component: 4 -> 14; Hans 14; Otto 10 build lines. Run 5 (final 2-step command): Hans on a player-settled Eichenhau, 4 -> 14 buildings in 14 game days (591 game s), first `AI_build` at cycle 2. The old buildings and the 5 families stay. The player's other village was not changed. |
| Cause (inferred, not proved) | compare the working and the failing paths | `finalizeClaim` on a region WITHOUT an owner registers the region for that lord's construction AI. A plain `ownerPawn` write does not. The component itself is not the cause (run 4 Karl kept the old component and built). |

## Command sequence (user flow)
Game started at the menu with HarnessBoot off and `SetNumAILords(0)` (script `new_game.sh`). Region names come from `regions_state`.
1. `spawn_ai_lord name=Hans build=1` (returns `lord` number, here 3).
2. `lord_relations lord=3` (neutral relations).
3. `lord_start_ai lord=3 value=1 build=1`.
4. The player takes a free region: `claim_region target=0 region=Eichenhau finalize=1`.
5. Starter village: `settle_region target=0 region=Eichenhau type=1 supply=0` (supply 1 or 2 gives the AI more resources).
6. Transfer: `lord_receive_region lord=3 region=Eichenhau`.
7. Unpause, 8x speed. The lord builds within 2 cycles. Read `lords_state log=30` (`debugLog_AI_construction`) and `regions_state` (buildings).
Without a player step: `lord_found_village lord=3 region=Eichenhau type=1 supply=2` (claim + settle by the lord).

## Crashes
| Call | Run | Result |
|---|---|---|
| `CityPlanningComponent:ResetAIBuildingOptions()` through the bridge, on the player's region that was just given to the lord, before `startAI` | s13-village-1 | Access violation reading 0x50. |
| The same call on a region a lord held, after `startAI` | s13-village-2 | Access violation reading 0x50 (the same address). |
Both crash reports are in `runs/s13-village-1/crash/` and `runs/s13-village-2/crash/`. The call is not in the mod (2 of 2 crashes). It is not needed.

## Not verified
- Growth beyond about 20 game days, and whether the lord grows to a town level, trades, or runs out of resources (supply 0 logged "lacks resources").
- What the player sees (map color, region panel) for the lord's village. `playerColor` of a spawned lord has alpha 0.
- A save and load with a spawned lord and its village.
- `lord_take_region` is still useful for a quick owner change, but the lord does not build there.
- Other settlement types (2 to 5) and `outpostToRegion` were not run with the working owner flow.
- Whether the same flow works for a region that a lord won by a challenge. Not tried.
- Three runs per variant were not done (spike level): the flow was seen in 4 runs with 6 lords in total.
