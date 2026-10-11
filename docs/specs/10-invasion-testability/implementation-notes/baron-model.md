# Spike S11: the baron and the AI lords as the invader model

Date: 2026-10-11. Real game, runs `s11-baron-1` (crashed, see "Crash") and `s11-baron-2` (map Jagged Cliffs, fixture `base`).
Tools: the jmap (signatures), the bridge read ops, and the new mod module `HarnessLords` (named commands, no eval).

## Question
Can invaders reuse the base game's hostile AI lord (the baron) instead of a custom raid AI? What can a mod steer?

## Answer
Yes, mostly. The AI lords run a C++ AI that a mod can steer through reflected calls and fields. The AI hires an army, marches it,
fights and takes a region on its own. A mod can also create a new AI lord (an invader faction) and steer it the same way.
A mod cannot give a squad a move order directly (no reflected order call was found). It steers the AI by its inputs:
war state, influence, silver, a challenge, an army, and bait.

## What the game has
- Five pawns: the player (`MyPawnCPP_BP3_C`) and four `PawnCPP_AI`. Lord 1 is the baron "Hildebolt von Berenreute"
  (traits `illegitimate`, `cant_build`, `off_map_lord`, `villain`; no army at start). Two neighbor lords (random names, for example
  Hanns, Sewolt, Herman) with a small squad each. "Outlaws" (`isBandit`, trait `bandit`) owns the bandit camp squad.
- `PawnCPP_AI` adds timers `AICommandHandle`, `AIGeneralStrategyHandle`, `AILetterwritingHandle` and `AI_general_cycles` (5),
  `AI_tactics_cycles` (1). Function `startAI(Speed, canBuild)`.
- `RTSMultiEngineCPP` holds `relations` (pawnA, pawnB, `Tags` such as `at_war` and `acquainted`, `friendship`, `status`),
  `challenges`, `openClaims`, `AI_buildingTypes`, flags `spawnAIPlayers`, `declareWarInstant`, `AI_canBuild`.
- **AI decision logs:** `RTSMultiEngineCPP.debugLog_AI_general`, `debugLog_AI_tactics`, `debugLog_AI_construction` (string arrays,
  about 50 lines, newest last). Each line names the lord and a cycle number. This makes the AI observable for tests.
  Examples: `claimRegions: not enough influence`, `can't afford more mercenaries`, `Comparing army strength proportion ... 13.2`,
  `Army - targetEnemyArmy found`, `Army - move to enemy army`, `I am participating in a battle challenge`,
  `Army - moving army to the challenge area`, `AI tactic - archers_bait`, `Army in battle`, `overpowered, disbanding mercenaries`,
  `general_AI (not landed lord): Army - leaving map.`
- Squad struct `/Script/ManorLords.Squad` has `TargetLocation`, `targetRegion`, `targetSquad`, `Control` (ESquadControl: Full,
  Engaged, Partial, Fleeing, Encamped), `behaviourStance` (Neutral, Aggressive, Defensive), `pushStance`, `camp`, `arrivesIn`.
  Squads live in native storage. `getSquadByID` returns a copy, so these fields cannot be written from Lua.

## Steering levers (all seen in the real game)
| Lever | Call | Result |
|---|---|---|
| War | `PawnCPP:declareWar(target)` (command `lord_declare_war`) | relation tag `at_war`; the target joins `enemies` |
| Influence | write `PawnCPP.influence` (`lord_set_influence`) | the baron stopped "not enough influence" and claimed region `immenreuth` (influence 2000 -> 1000 -> 360) |
| Silver | `PawnCPP:changeSilver(amt)` (bridge call, scalar) | the baron hired mercenaries by itself: 3 squads of 36 for 90 silver, later 4 more |
| Army | `RTSMultiEngineCPP:spawnArmy(pos, templates, lord, 0, 0)` (`lord_spawn_army`) | the lord commands the squads; its AI moves them |
| Challenge | `RTSMultiEngineCPP:initChallenge(target, lord, region)` (`lord_challenge`) | 90 days; AI: "moving army to the challenge area"; the army marched about 110 000 units and held a position about 10 000 units from the player |
| Bait | a player army near the lord's army (`spawn_units side=player`) | AI tactic `archers_bait`, then a battle; 64 player militia died; challenge status 2 (Combat) |
| Win | the challenge ends | the region owner (`Region.ownerPawn`) became the baron; the player commanded 0 regions; the `at_war` tag ended; the village stayed (4 buildings, 10 people), no game over screen |
| New lord | `RTSMultiEngineCPP:spawnNewAILord(name, false, nil, false)` (`spawn_ai_lord`) | lord "Norse Warlord" was made; with war, an army, a challenge and `startAI(1, false)` its AI marched 3 retinue squads (108 units) to the challenge area |
| Target enemy army | an enemy army on the map | the baron's army hunted the Outlaws army (strength ratio 13), destroyed it, then "grab camp" |

Without a challenge or an enemy army, the baron did not attack the village: "no enemy army or not baited (weaker?)",
then "(not landed lord): Army - leaving map". The baron and the AI do not sack buildings by themselves in what was seen.

## Speed (user note, 2026-10-11)
When an army is spotted, the game sets the speed to 1x. An army that walks through forest is hidden and seen again quickly,
so the speed drops to 1x again and again. A test must set the speed again every second while armies march
(seen: 7 resets in 8 s, 19 resets in 110 s). `increaseGameSpeed` on the engine cannot be called through the bridge.
The harness now does this: `ctx.time.run_game_seconds` and `run_game_days` check the speed about once a second and set it again
(`speed_resets` in the record). Not handled: `set_speed` alone checks the speed once after 3 s and fails after 3 tries if armies
drop it each time; start the run before armies are near, or call it again.

## Crash
The first `lords_state` crashed the game (EXCEPTION_ACCESS_VIOLATION in `UE4SS!RC::LuaType::UStruct::setup_member_functions`).
The module called `:get()` on struct elements of property arrays (`relations`, `challenges`, `commandedSquads`) and read the struct copy
of `getSquadByID`. A pcall cannot catch it. Rule: read property array elements directly; call `:get()` only on function return values;
do not read struct values returned by value. Unit positions: `SMUnit.realPos` moves; the actor location of a unit did not.

## What is not verified
- The 3 of 3 scenario runs. This spike ran each lever once (the challenge flow and the new lord twice in total).
- `lord_claim` (`layClaim` on the player region) and `lord_declare_peace` were not run. `addPawnRelations` for a new lord (it had no relation row) was not tried.
- What a new lord with `canBuild` true does, a portrait, the new lord in a saved game, and whether a new lord survives a load.
- The outcome when the player contests the challenge (with its own army in the area all the time), and the "challenge lost" path.
- Whether the AI ever sacks buildings. Sacking stays with the mod (`HarnessSack`), as before.
- Mercenaries hired by the AI appear at the map edge and walk in; their arrival time was not measured.

## Consequences for the plan
- S4 (steering) is answered for the lord AI: steer by war, influence, silver, a challenge, an army, and bait. No direct move order.
- The invasion engine can be thin: create an invader lord (`spawnNewAILord`), give it an army and a challenge on the player region,
  and let the C++ AI march and fight. The mod adds what the base game lacks: the announcement, the sacking, the loot.
- A test can read the AI's decisions from the debug logs and the squad positions (`realPos`) and targets (`getTargetPos`).
