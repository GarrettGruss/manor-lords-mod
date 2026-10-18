# Feasibility: vassals, tribute, liege, finite resources, plundered start

Date: 2026-10-15. Reviewer: read-only review of the evidence in `docs/harness/` and `mod/shared/`. No game run. No Python run.
Design source: `design/invasion-mod.md`.

## Rating key
- PROVEN: shown in the real game by a note.
- LIKELY: the calls or data exist. Not yet combined in one test.
- UNKNOWN: no evidence, or the notes disagree. Needs a spike.
- BLOCKED: notes show it cannot be done from Lua or pak.

## Mechanics

| Mechanic | Rating | Evidence (file: key fact) | Approach | Main risk |
| --- | --- | --- | --- | --- |
| Found a vassal with settlers (player claims a free region, settles it, hands it to a lord) | LIKELY | `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/dynamic-lords.md` Part 2: `claim_region` (layClaim + finalizeClaim) and `settle_region` on an owned region work (5 runs). `lord_receive_region` made a lord build 4 to 14 buildings. But `open-items.md` (update 2026-10-13): the rerun on the `base` fixture with other lords present left the lord village at 5 buildings, 0 build lines. | Both (Lua commands in `HarnessLords`, timers in mod) | The lord-build result did not repeat. Calling `settleRegion` on an unowned region crashed 3 of 3 times (`dynamic-lords.md` Part 1). |
| Vassalize a neighbor (player takes or binds a lord's region) | UNKNOWN | `baron-model.md`: `declareWar`, `addPawnRelations` work. A region owner can be changed (`lord_take_region`). The AI took a region from the player by challenge (owner changed, 4 buildings stayed). Not tested: the player winning a region, `lord_declare_peace`, `lord_claim` (`open-items.md`: "not run"). | Both | No peace or vassal state is known. The AI may declare war back. |
| AI-run vassal region (a lord owns and runs a region) | LIKELY | `dynamic-lords.md` Part 2: owner change plus `lord_receive_region` gave construction logs (`AI_build`). The same caveat as the row above applies. | Lua | Same as the first row: unstable on the base fixture. |
| Indirect control: policies on a vassal region | UNKNOWN | `openspec/changes/archive/2026-10-15-legacy-16-policy-edicts/implementation-notes/policy-followups.md` section 3: a real click signs policy 12 on the player region (`setPolicySigned` works). `HarnessPolicies.lua` `context()` uses only the player region (`sack.playerRegion()`). `enactPolicy` returned false in 95 tries (section 2). Signing policy 12 changed no food or approval number (section 1). | Lua (`Region:setPolicySigned`) | No test on a non-player region. A signed policy has no visible effect in the notes. |
| Indirect control: orders to a vassal's squads | BLOCKED (direct orders); steer by inputs instead | `baron-model.md`: no reflected move order for AI squads. `unit-steering.md`: `formALineArmy` does nothing for AI or bandit squads. Works on player squads only with a real right click. Steering by inputs works (war, influence, silver, challenge, army, bait). | Lua (inputs only) | A vassal cannot be ordered by a direct call. The design must act through AI inputs. |
| Loyalty | UNKNOWN | `spike-P3.md`: `loyalty` exists only in the quest `Reward` and `Punishment` structs. `policies.md` row 1 says loyalty falls 1% a day (text only). No region or lord loyalty field in any note. | Mod-owned value (Lua ledger), or a jmap check | A mod ledger is not shown in the game UI. The game may not use it. |
| Tribute payout (silver, wealth, influence) | LIKELY | `actions-catalog.md`: `changeSilver`, `add_regional_wealth` and `changeInfluence` read back correctly (probe-money, verified rows). | Lua (timer in the mod) | The base game has no tribute system (`criteria.json` S5). The amount and timing are the mod's rule. |
| Tribute source (amount from a vassal's production) | UNKNOWN | `jmap-findings.md`: `ProductionTrackerComponent:getGoodsProducedOver` exists. Not called on a lord region in any note. | Lua read | No real production number for a lord region. |
| Tribute in goods (moving goods out of a vassal) | UNKNOWN | `spike-S6.md`: `consumeGoodNoCheck` works on the player village. `storage-m1.md`: `addToInventory` works on the Keep. Neither was run on a lord-owned region. | Lua | A goods transfer across two regions is not tested. |
| Submission: a neglected vassal pays the invader | UNKNOWN | `baron-model.md` shows the AI takes a region by challenge (owner changes). No submit trigger or tribute term found in any note. | Mod rule plus AI challenge | No way to ask an AI lord to accept payment. |
| Liege and influence: gain and spend | LIKELY | `actions-catalog.md`: `changeInfluence` and `set influence` work. `settler-camp.md`: a region claim used all 1000 influence. `baron-model.md`: the AI claim moved influence 2000 to 360. | Lua | No aid, villager or weapon call found for spending influence on the liege. The spend side is a mod rule. |
| Liege as a world entity | UNKNOWN | No liege object found in any note. `kingsFavour` exists (`changeKingsFavour` verified, `getKingsFavour_daysLeft` in `jmap-findings.md`). Not checked as a liege. | Mod (menu or effects only) | Troops of the liege cannot be shown if the game has no entity for them. |
| Finite home resources (iron, salt run out) | UNKNOWN | No deposit or resource-node state in any note. `unused-assets.md` line 102: resource node spawn "Not checked". `BP_ResourceNode` exists (`unused-assets.md` line 59). Mining settlement type exists (`settler-camp.md`). Stock read works (`getStock`). | Mod could cap stock with `consumeGoodNoCheck` (proven on player village), but not stop a mine. | No known way to make a mine stop. The depletion rule is not in the game. |
| Plundered start (Q2) | LIKELY | `spike-S6.md`: sack by fire or collapse makes Rubble (3 of 3 runs, `sack-village`). `fresh-start.md`: a new game reaches READY with no save. | Lua (`HarnessSack` after READY) | No test that the sacked state holds on day 1. No pak start data found. |

## Open questions 2, 3, 4, 6, 8, 9

| Question | Rating | Evidence and answer |
| --- | --- | --- |
| Q2: start in a plundered village | LIKELY | See the last row above. Sack state is made at run time. Start-state hook not tested (`dynamic-lords.md` lists `setStartLocation` as an untested lead). |
| Q3: how vassal regions show | UNKNOWN | An AI lord region is a `Region` with `ownerPawn` set. Map colour of a spawned lord has alpha 0 (`dynamic-lords.md`, "not verified"). What the player sees was not checked. |
| Q4: policies or orders on a region the player does not control | UNKNOWN (policies); BLOCKED (direct orders) | See the two policy and order rows above. |
| Q6: win condition | UNKNOWN | The game has a victory state (`MLGameInstance.currentGameVictoryStatus`, `jmap-findings.md`). In `settler-camp.md` a region claim started a victory cinematic. The mod must block or use this, so the rule is a risk. |
| Q8: land of a lost vassal | LIKELY (options exist) | Owner change works. A bandit lord exists (Outlaws, `baron-model.md`). An empty region can be cleared and claimed (`dynamic-lords.md`). The choice is a design decision. |
| Q9: is the liege a real entity | UNKNOWN | No liege object found. See the liege row above. |

## Top 3 risks
1. **The vassal build result is not stable.** Part 2 of `dynamic-lords.md` shows the lord builds. The 2026-10-13 rerun in `open-items.md` shows no build. The whole vassal line depends on this.
2. **Policies and orders reach only the player region.** `enactPolicy` never worked. `setPolicySigned` has no visible effect so far. AI squads cannot be ordered directly.
3. **Several core values have no field.** Loyalty, a liege entity and a deposit state were not found. Each would be a mod-owned ledger, which the player may not see. The game also has a victory state that a claim can trigger (`settler-camp.md`).

## Spikes needed
1. **Vassal build repeat (fixes risk 1):** 3 runs per variant of `lord_receive_region` and `lord_found_village` on the `base` fixture with the other lords present. Read `AI_build` lines and building counts. Follow `open-items.md` update 2026-10-13.
2. **Policy on a lord region (risk 2):** call `setPolicySigned` on a region owned by a lord. Read `policiesSigned` and the lord's region approval. Check that the call does not crash.
3. **Peace, challenge and submission (vassalize, submit):** run the `probe-lord-diplomacy` probe (`lord_claim`, `lord_declare_peace`, challenge lost) from `open-items.md`. Add a player challenge that the player wins.
4. **Production and goods tribute:** read `getGoodsProducedOver` on a lord region. Move one good from a lord building with `consumeGoodNoCheck` and add it to a player building with `addToInventory`. Read both sides.
5. **Deposit probe:** find `ResourceNode` actors and any stock or yield field on mines. Check whether a mine can be stopped from Lua. Decide if depletion needs a pak.
6. **Liege probe:** search the jmap for liege, king and favour functions. Read `getKingsFavour_daysLeft` over time. Check whether influence can buy anything through a game call.
7. **Plundered start (Q2):** sack a fresh game on day 0 with `HarnessSack`. Run 30 game days. Check that the ruins and the population hold.
