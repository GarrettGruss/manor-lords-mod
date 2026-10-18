# M00 feasibility: raids, plunder, sack and terms

Date: 2026-10-15. Scope: the mechanics of features `invasion`, `raid behavior` and `sack and terms` in `docs/mod/M00-invasion-mod/README.md`, plus difficulty tiers and open questions 1, 5 and 11.
Method: read the evidence notes and Lua modules. No game run. No Python run. No other file changed.

## Rules for the ratings

- PROVEN: a note shows the call or effect in the real game.
- LIKELY: the calls or data exist in real-game notes, but no note shows them combined.
- UNKNOWN: no evidence. A spike is needed.
- BLOCKED: notes show that Lua or pak cannot do it.

Stand-in results do not count as PROVEN. The toy models `RaidStandIn` and `InvasionStandIn` use invented rules. Their rules are mod rules, not game rules.
Note: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/README.md` says the raid stand-in was verified in the real game. Its PENDING section and `raid-standin.md` say the real-game run is still open. This review treats the stand-in as not proven.

## Table

| Mechanic | Feature | Rating | Evidence | Approach | Main risk |
| --- | --- | --- | --- | --- | --- |
| Raid timer: write it, raid spawns when it reaches 0 | invasion | PROVEN | `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-S1.md`: writes hold; raid spawned on the tick; `raid-timer` 3 of 3 | Lua (`TemporalComponent.daysUntilNextRaid`) | The base game timer also spawns raids. After each raid the new value is random (observed 208 and 353 days). The mod must own the timer. |
| Raid announcement and countdown text | invasion, T4 | PROVEN (banner) | `spike-S9.md`: `PawnCPP:playEventMessage(FName, text, text2)` shows "Raid in N days"; `ui-countdown` 3 of 3 | Lua | The banner fades after a few seconds. The mod must call it again each game day. Look is Q4 (human). |
| Full scheduler: announce, arrive, seasons, great raid timer | invasion | LIKELY | Timer and banner work (above). Season rule is not seen in the base game (`spike-S1.md`). Start timer is 730 days (`yearsUntilFirstRaid` 2). Writes above 730 not tried. | Lua | Season and winter rules are mod rules. The 3 to 5 year great raid timer is not tested. |
| Raid size in squads of 18 | invasion | PROVEN | `spike-S2.md`: `spawnRaiders(NumSquads, centre)` adds 18 units per squad; `raid-spawn` 3 of 3 | Lua | Size steps are 18 units. Finer size needs `spawnArmy`. |
| Typed raid (chosen units) | invasion, tiers | LIKELY | `spawnRaiders` has no type. `spawnArmy` takes unit template names and an owner (`spike-S7.md`, `spike-S2.md`). Typed squads were used in real counter tests (`spike-C1.md`). A `spawnArmy` bandit squad was seen to rally and then attack late (`homeless-rebellion.md`). | Lua | Typed raid squads use the AI lord's own behaviour. Their timing is not in our control. |
| Subjugation raid by an AI army (takes a region) | invasion, sack and terms | LIKELY | `baron-model.md`: a new AI lord (`spawnNewAILord`), war, army and `initChallenge` took a region (`Region.ownerPawn`) in the real game. Same tool in `homeless-rebellion.md` part 4 (challenge ended with the loss of the region). | Lua | The AI did not sack buildings or destroy the town in the notes. "Destroy the town" must come from the mod (`HarnessSack`). |
| Great raid: captain and captain death | invasion | UNKNOWN | No captain or leader flag found in the notes. Units have no health (`spike-S3.md`). | Unknown | Needs a leader concept. Without it the "captain dies" rule cannot be built. |
| Plunder loop: loot, burn, leave | raid behavior | PROVEN | `homeless-rebellion.md`: base AI squads burned 3 to 7 buildings and left with "enough looted. Leaving map." (several runs). Raiders loot on their own (`spike-S1.md`: 53 to 69 loot in 2 days). | Native AI, started by Lua | Only the start of the raid is ours. The AI decides the rest. |
| Seek the nearest stockpile (bait) | raid behavior | BLOCKED | Raid target is ignored: `homeless-rebellion.md` part 4 tests 1, 1b, 2b (raiders appear at the x of the target, then walk to the AI waypoint). A move order does nothing (`squad_move`, part 3). A challenge does not hold a squad (part 3, test 4). `unit-steering.md`: AI and bandit squads are not steerable from Lua. | None found | The bait design has no working lever. |
| Carry cap per raider | raid behavior, tiers | UNKNOWN (enforcement) | `spike-S5.md`: `ItemsLooted` can be written and read (7 written, 7 read). Native max 4 to 5 per unit (`spike-S3.md`). The unit (items or silver) is unknown. | Lua (write the value) | Writing a value does not show that the AI stops looting at the cap. |
| Loot drops on death (ground pile) | raid behavior | UNKNOWN | `spike-S5.md`: kill with loot works; loot is cleared on death; no new actor. `spike-R3.md`: no ground loot object in the base game. The pile is a Lua table (`HarnessLoot`) in the stand-in only. | Pak or mod-made object (not tried) | No world object for a pile is known. Peasant pickup is not built. |
| Recover loot (goods back to stock) | raid behavior | PROVEN | `spike-S6.md`: `GiveItemByID` adds goods to a store with space (real game). | Lua | Goods go to any store with space, not to the store the mod picks. |
| Retreat: full loot | raid behavior, retreat | PROVEN | "Enough looted. Leaving map." in `homeless-rebellion.md` (native AI exit). | Native | The loot amount that triggers it is not known. The mod cannot set it. |
| Retreat: timer end, morale break, captain dead | raid behavior, retreat, tiers | UNKNOWN | Morale reads 1.0 for all units (`spike-S3.md`). No timer end or morale break seen in the notes. No captain (see above). | Unknown | The main retreat triggers of the design have no proof. |
| Player ends a raid with a letter (negotiation) | retreat, sack and terms | PROVEN (removal) / LIKELY (families) | `homeless-rebellion.md` part 4: letter `raider_suggestSettle` removes all bandit units and charges 20 silver (clean tries 2a and 2b). Families came back only for `spawnRaiders` squads. `spawnArmy` squads gave none (3 of 3). | Lua (`bandit_letter`) | Why raid squads give families is not known. Two clean tries only. |
| Burn buildings to ruins (mod-caused) | raid behavior, sack | PROVEN | `spike-S6.md`: `StartFire` makes rubble (type 75); goods inside are lost. `sack-village` 3 of 3. | Lua | Fire spread to neighbours is not tested. |
| Ruins and partial rebuild cost | raid behavior, sack | PROVEN | `spike-R8.md`: rebuild charges the full cost; a lower `constructionGoods` amount is charged (4 to 2). `rebuild-cost` 3 of 3. | Lua (write the site cost) | The site must be placed by a real OS mouse in the harness (`spike-R8.md`). A player-side rebuild in the game is not tested. The discount rule is a mod rule. |
| Storage: manor stores goods | storage tiers, manor holds | PROVEN | `criteria.json` M1: goods in the Keep inventory count in the region stock; worker slot works. `manor-storage` and `manor-storage-workers` 3 of 3 each. | Lua (`HarnessManor`) | Keep is a special building. Other stores are not in this result. |
| Storage: capacity grows with the tech tree | storage tiers | LIKELY | `openspec/changes/archive/2026-10-15-legacy-13-mod-inspection/implementation-notes/storage-and-manor-unlock.md`: capacity is a field of the `buildingStats` row; the Keep row write is real (M1). | Lua (row write) | Capacity effect is not measured. Open question 16. |
| Storage: guarded granary and open barn lose different shares | storage tiers | LIKELY | `spike-S6.md` (`sack-store-trip` 3 of 3): stock of each store is read and removed per store (open barn 50% a trip, granary 10%). The loss factor is a mod rule. | Lua | The base game has no guard or lock. The rule is ours. |
| Manor holds when the town falls | manor holds | UNKNOWN | Keep holds goods (above). No raid was run against the Keep. M2 (buildings in manor area) not verified. | Unknown | No evidence that raiders stop or leave at the Keep. |
| Sack: remove a share of buildings, goods and people | sack and terms | PROVEN | `spike-S6.md`: `sack-village` 50% buildings, 49.4% stock (range 45 to 55), 40% families. 3 of 3. | Lua (`HarnessSack`) | Share is rounded per family (5 families). |
| Sack instead of deletion: game continues | sack and terms | LIKELY | `spike-S8.md`: the game ends when the village has population 0 (day 137, not fed). A sack of 40% families did not end the game in `sack-village`. | Lua plus mod rule | Total depopulation ends the game. The sack rule must keep people alive. The "2 sacks in a window" game over is a toy rule only. |
| Vassal fallback: a second region that the player holds | sack and terms, vassals | LIKELY | `spike-S13` part 2 (in `dynamic-lords.md`): a player-settled village grew 4 to 14 buildings. | Lua (`settleRegion`, `claim_region`) | Settling a region is possible. Growth beyond 20 days is not tested. |
| Vassal fallback: move families, grain and units to it | sack and terms | UNKNOWN | Only toy results (`InvasionStandIn` `evacuate`). No real move between regions in the notes. | Unknown | Needs a real move of families and goods. |
| Tribute: one-time payment | sack and terms, liege | LIKELY | Silver is paid by game calls: `spike-P5.md` (hire cost paid exactly). Letter cost 20 silver (`homeless-rebellion.md`). | Lua | The game does not check the cost. The mod must check it. |
| Tribute: hostages and vassal yearly tribute | sack and terms | UNKNOWN | No game concept found. Toy only (`mod-state-contract.md`). | Unknown | Needs mod data and a yearly timer. |
| Occupation: invader holds the town and takes production | sack and terms (later layer) | LIKELY (holding), UNKNOWN (production and revolt) | Owner change works (`baron-model.md`, `Rebel` test in `homeless-rebellion.md`). `Region.ownerPawn` alone gives no construction (`dynamic-lords.md`). No production read under an invader. | Lua | Production share and revolt are not tested. |
| Difficulty tiers: more squads and more often | difficulty | LIKELY | Squad count (PROVEN, above) and timer (PROVEN). Tier values are mod rules. | Lua | Tier results are toy only (`raid-tiers`). |
| Difficulty tiers: smarter targeting | difficulty | BLOCKED | Target ignored (above). | None found | Same as bait. |
| Difficulty tiers: higher carry caps, lower morale break, escaped captain returns | difficulty | UNKNOWN | See carry cap, morale and captain rows. | Unknown | Depends on the three UNKNOWN rows. |

## Answers to open questions 1, 5 and 11

**Q1 (which hooks exist).** Partly answered for raids and sack.
Usable: `TemporalComponent` raid timer; `spawnRaiders`, `spawnArmy`, `spawnNewAILord`; `initChallenge`, `declareWar`; `playEventMessage`; popup close; `StartFire`, `collapseBuilding`, `demolish`; `consumeGoodNoCheck`; `GiveItemByID`; `constructionGoods`; `Region.ownerPawn`; `settleRegion`; `hireMercs`; unit `ItemsLooted` and `just_die`.
Missing: a squad move or target call, a ground loot object, a morale write, a captain or leader flag.

**Q5 (can the game spawn raiders that steal and carry goods, and can base AI be reused).** Yes for spawn and loot. Raiders loot by themselves. The base bandit AI burns buildings and leaves when it has enough loot. Yes for reuse of the AI lord for a subjugation-type attack (a challenge takes a region). No for steering: a chosen target and a move order do not work.

**Q11 (how large a sack should be).** This is a design choice, not a feasibility question. The game can remove any share of buildings, goods and people. The measured removal in `sack-village` matched the requested percent. The size itself must be set by the user and tested by play (criteria Q3 is human).

## Top 3 risks

1. **Raiders cannot be steered.** No move order, no target, and a challenge does not hold a squad. This blocks bait, the plunder goal states, enforcement of carry caps, and the difficulty targeting. It is the main risk for the raid design.
2. **No world object for a loot pile.** Loot on the ground is part of the design. The base game has none, and the only pile is a Lua table. The mod needs a pak or a made object, and no one has tried either.
3. **Retreat and morale cannot be read or forced.** Morale reads 1.0. No captain flag is known. The base game raid timer restarts at random after each raid and can clash with the mod's schedule.

## Spikes needed

- **SP-R1, raider steering (real game, 3 runs each):** try the rally point (`setPlaceRallyingPoint`, `projectHoldSquad`, not called yet per `homeless-rebellion.md`), a player army as bait, and a war target on the bandit lord. Pass: a raid goes to a chosen stockpile. Blocks: bait, plunder goal states, tiers.
- **SP-R2, ground loot (real game):** find a world object that the mod can create for goods (a pak actor, or a Supplies crate placed by the mod). Check that a peasant walks to it and picks the goods up. Also find out if `ItemsLooted` counts items or silver.
- **SP-R3, morale and leader in a real raid (real game):** read morale of a large raid over time. Search for a leader or captain flag on squads. Check whether a raid with no target ends by timer.
- **SP-R4, vassal move and occupation (real game):** move families and goods from one region to another. Read production of a region under an invader.
- **SP-R5, manor capacity and a raid at the Keep (real game):** write the `buildingStats` capacity of the Keep and read the effect. Send a raid at the Keep and read the goods (open question 16).
