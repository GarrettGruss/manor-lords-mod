# Feature breakdown of M00

This file splits the Invasion Mod overview (`M00-invasion-mod/README.md`) into feature specs. It does not change the design. The design is owned by the user.
Each feature has a folder `docs/mod/M<NN>-<feature>/`. The `<feature>` name is a valid Lua module name. It is the same as `Scripts/features/<feature>/` later.
Status of all features: skeleton only (2026-10-16). Only Batch 1 has iteration files. The user decisions of 2026-10-16 are applied (see "User decisions" in M00).

## Batch table
| Batch | M | Folder | Goal (one line) | Depends on | Blocking spikes or open questions | First iteration |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | M01 | `M01-mod_state` | Keep mod values across save and load (Tags of the pawn and region). | none | Tags size limit test (spec 24) | `01-tags-module` |
| 1 | M02 | `M02-invasion` | Raid schedule, difficulty (1 to 3), raid widget, great raid waves and relief army. | M01 | Timer writes above 730 days; difficulty choice; relief army timing and size | `01-first-scheduled-raid` |
| 1 | M03 | `M03-raid_behavior` | Start the native plunder AI. Loot back to a store on death. Carry caps. Native rout. | M01, M02 | Does the AI obey a carry cap; death event hook; "nearest store" rule | `01-native-plunder` |
| 2 | M04 | `M04-bandits` | Low Public Order turns families into bandits each season. Fight or pay coin. | M01, M03 | Buy-back price; chance per family or per region; homeless timer (spike 8) | `01-low-order-bandits` |
| 2 | M05 | `M05-unit_balance` | Armor lethality, Hussite tiers from existing units, counters, veterancy. | none (feeds M03, M04) | Live write of `att` and `armorPierce`; row ids per tier; spawn hook or poll | `01-unarmored-lethality` |
| 3 | M06 | `M06-sack_and_terms` | A lost battle sacks the town. Tribute terms (no hostages). Fallback capital. | M01, M02; M07 for the fallback | Sack size per difficulty; what a lost battle is; loss of the very large battle | `01-sack-after-defeat` |
| 4 | M07 | `M07-vassals` | Vassalize or settle regions. Indirect control by mod-owned policies and orders. | M01; goals = Endless (spec 26) | Vassal model (open decision 5); how vassal regions are shown; effects on a region not owned; lost land | `01-claim-without-victory` |
| 4 | M08 | `M08-tribute` | Vassals send supplies. Failed protection lowers loyalty. | M07, M02 | Production read of a vassal; goods transfer between regions | `01-tribute-payout` |
| 4 | M09 | `M09-refugees` | A lost vassal sends refugees. Unhoused refugees become bandits. | M07, M04 | Wave size over the 5-families-per-call limit; tent slot limit | `01-refugee-wave` |
| 4 | M10 | `M10-finite_resources` | Home deposits run out. Vassals are the permanent source. | M01, M07, M08 | How to stop production on an empty deposit | `01-iron-deposit` |
| 6 | M12 | `M12-tech_tree` | Two exclusive paths, laws, vassal policies, pak UI. | M01, M04, M07, M08 | Path undo; node list; pak UI screen; id block numbering | `01-path-choice` |
| 6 | M13 | `M13-manor_stronghold` | Manor storage and retinue capacity upgrades. | M12, M03 | Retinue size write; real storage capacity effect | `01-manor-storage` |
| 7 | M14 | `M14-plundered_start` | Start in a damaged village. | M01; spec 26 | Shares that stay playable | `01-start-sack` |

Deferred (listed, no spec folder): occupation and rebellion. They are the heaviest layer. M00 build plan step 10 puts them last. Write specs for them after Batch 7 and a user review.

## Why this order
1. Batch 1 is the base. M01 is needed by every feature that keeps values. M02 and M03 give the first playable raid: schedule, spawn, loot. They match build plan steps 0, 1 and 2.
2. Batch 2 adds the inner pressure and the combat rules. M04 and M05 do not need vassals. M05 changes the fights that M03 and M04 create, so tune it as soon as raids and bandits exist. This matches build plan steps 3 and 4.
3. Batch 3 gives defeat a result. Sack and terms need the great raid (M02). The sack itself is proven. The fallback capital waits for M07. Build plan step 5.
4. Batch 4 is the outward system. M07 comes first because M08, M09 and M10 need a vassal. Goals = Endless (spec 26) removes the claim victory problem. Build plan step 6.
5. M11 (liege influence) is backlog, TBD (decision 9). It has no batch. Build plan step 7 waits.
6. Batch 6 (M12, M13) needs the systems that the tree changes. The tree is a wide change, so it comes after the systems exist. Build plan step 8.
7. Batch 7 (M14) is optional and last in the plan (step 9). No start setting exists, so it uses the sack tools after the start.

## Decisions status
The user gave decisions on 2026-10-16. They are listed in `M00-invasion-mod/README.md`, section "User decisions (2026-10-16)".
| # | Decision | Status | Applied in |
| --- | --- | --- | --- |
| 1 | Win condition: survive waves until the relief army arrives, then a very large battle with the liege's reinforcements | decided | M02, M06, M07 |
| 2 | Order is the native Public Order; approval stays separate | decided | M04, M02 |
| 3 | Row id blocks: 1000 + 100 times the M number | decided | table below |
| 4 | One custom raid widget for all raid information | decided | M02 |
| 5 | Vassal model | open (being explained) | M07 |
| 6 | Bandit conversion by Public Order thresholds, once per season | decided (values are tunables) | M04 |
| 7 | No handgunners; Hussites use existing tiered units | decided | M05, M02 |
| 8 | No hostages; native sack and loot; difficulty 1 to 3 times a base size multiplier | decided | M02, M03, M06 |
| 9 | Liege is off-screen; only a custom menu | decided; M11 is backlog | M11, M08, M12 |
| 10 | Tech tree node list and M14 | open (being explained) | M12, M14 |

## Open decisions
Only the user can decide these.
1. Vassal model (decision 5, M00 open question 3). Blocks Batch 4.
2. Tech tree node list, path undo and M14 (decision 10, M00 open question 10). Blocks M12 and M14.
3. Tech boon sizes (M12) and the loss of the very large battle (M06). TBD, set in playtests.
Answered on 2026-10-16 (M00 decisions 11 to 15): difficulty chosen by the player at the start; great raid = 1 x difficulty waves, all large; bandit chance once per region per season tick; low approval debuffs Public Order; sack size linear in difficulty for now. Decisions 16 to 19: large army and relief army 15 squads, final battle not scaled by difficulty, random raid size, Public Order debuff = (100 - approval) x difficulty.

## Backlog
- M11 `M11-liege_influence`: status backlog, TBD (decision 9). The liege is off-screen. Only a custom menu represents it for now. The folder stays. The relief army is owned by M02 until M11 starts.
- Occupation and rebellion (deferred, no spec folder, see above).

## Id blocks
Confirmed (decision 3): one block of 100 building ids per feature, rule 1000 + 100 times the M number.
| Feature | Block |
| --- | --- |
| M01 | none (no rows) |
| M02 | 1200 to 1299 |
| M03 | 1300 to 1399 |
| M04 | 1400 to 1499 |
| M05 | 1500 to 1599 |
| M06 | 1600 to 1699 |
| M07 | 1700 to 1799 |
| M08 | 1800 to 1899 |
| M09 | 1900 to 1999 |
| M10 | 2000 to 2099 |
| M11 | 2100 to 2199 (reserved, backlog) |
| M12 | 2200 to 2299 |
| M13 | 2300 to 2399 |
| M14 | 2400 to 2499 |

Upgrade rows use ids 117 to 999 for all features, until a larger id is tested.

## What the user must decide before each batch
- Before Batch 1: nothing is blocking. The raid widget layout can follow in M02 iteration 05.
- Before Batch 2: the buy-back price rule, and bandit chance per family or per region.
- Before Batch 3: sack size per difficulty, what a lost battle is, the relief army and wave rules.
- Before Batch 4: the vassal model (open decision 1). How the player vassalizes a neighbor. What a lost vassal's land becomes.
- Before Batch 6: the node list of version 1 and path undo (open decision 2). Where the pak UI opens.
- Before Batch 7: the shares of a plundered start, or drop the feature (open decision 2).
