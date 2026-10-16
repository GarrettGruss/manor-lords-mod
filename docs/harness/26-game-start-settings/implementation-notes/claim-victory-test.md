# Claim victory test (spec 26, real game, 2026-10-16)

Tool: scenario `probe-claim-victory` (hidden). Env (shell, not `--env`): `GS_GOAL` 0 to 3, `GS_CONSUME`, `GS_REGION`.
New commands in HarnessActions: `game_setup_state` (read), `game_setup_set_goal` (write `gameSetup.currentGameSetup.goals`).
`claim_region` got an option `consume` (layClaim consumeInfluence). HarnessActions version stays 49 (no bump).
Runs are in `runs/gs26-*` (git-ignored). No save call was made.

## 1. Goal setting read (step 1)
Read with `game_setup_state` and the bridge (`get gameSetup` shows the full struct):

| Start | goals | numGenericAILords | victory status | difficulty |
|---|---|---|---|---|
| New game, Jagged Cliffs | 3 (Growth) | 0 | 0 (Ongoing) | 3 |
| Fixture `base` | 3 (Growth) | 3 | 0 | 3 |

Not conquest by default: the default of a new game here is 3. The enum order is Conquest 0, Dominance 1, Endless 2, Growth 3 (as in the jmap).
`MLSaveGame` has no live object in a running game, so the save copy cannot be read. It was not needed.
The bridge cannot read the path `gameSetup.currentGameSetup.goals` in one call. Read the struct `gameSetup`, or use the command.

## 2. Control (new game, goals = 3, claim Eichenhau with 1000 influence)
3 of 3 runs (`gs26-ctl-new1`, `gs26-goal3-new3`, `gs26-g3-b`): `currentGameVictoryStatus` 0 -> 2 right after the claim, and a letterbox cinematic plays
(screenshot `gs26-ctl-new1/screenshots/after-claim-6s.png`).
Hook counts: `layClaim` 1, `finalizeClaim` 1, `createAndPlayVictoryCinematic` 0, `triggerDefeat` 0.
So the cinematic is not started through a hookable Blueprint call (native call). The hook shows no victory, but the status value shows it.
Status 2 is the victory value (the enum order in the jmap note is not the order of the values).

## 3. Change run (goal written before the claim)
| goals written | runs | victory status after | cinematic |
|---|---|---|---|
| 2 Endless | 3 of 3 (`gs26-goal2-new3`, `gs26-g2-a`, `gs26-g2-b`) | 0 | none (screenshot: normal "Claiming" banner) |
| 0 Conquest | 1 (`gs26-g0-a`) | 0 | none |
| 1 Dominance | 1 (`gs26-g1-a`) | 0 | none |
| 3 Growth (control) | 3 of 3 | 2 | yes |

Verdict A2: yes. Writing `goals` on `MLGameInstance` to Endless (also Conquest, Dominance) stops the victory on a claim. 3 of 3.
The claim still works (region owner set, claim banner shown). Step 4 (save copy) is not needed.

## 4. Fixture `base` (3 AI lords, goals 3)
Claim of Eichenhau with and without goals 2: no victory in both (status 0). The Growth goal needs more than one claim there
(or the AI lords change the rule). Not studied. The victory is a Growth goal event of the start without AI lords.

## 5. Plundered start (A3)
`game_setup_state` and `get gameSetup` list every field of `GameSetupParameters`: AI_aggressiveness, adversary_baron, armamentDelivery,
consumptionRate, generateWaterVeins, goals, initialBanditCamps, loyaltyLossRate, maxBanditCamps, numGenericAILords, raidingFrequency,
requirementDiscontentBias, resourcesRandomization, royalTaxMultiplier, spoilage, startingDay, startingLocation(_AI),
startingSuppliesMultiplier, treeGrowthRate, weatherDamage, yearsUntilFirstRaid. No field for ruins, families or population.
Answer: not a start setting. Use Lua after the start (works at run time, spec 10 S6):
1. Boot into a new game or a fixture, wait for READY.
2. `sack_village` with `buildings_pct`, `stock_pct`, `people_pct` and method `fire` (or `collapse`) in the first game days.
3. Scare the people: `sack_people` (kill a share), `family_add` / family commands for the family count.
4. Optional: `startingSuppliesMultiplier` is the only supply setting, and only before the start (not tested).

## Not verified
- The name of the function that starts the cinematic. A hook on `createAndPlayVictoryCinematic` sees 0 calls.
- Whether a user-visible new game menu choice (the goal option) gives the same value; the mod writes after load.
- The Growth rule of the base fixture.
