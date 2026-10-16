# Feature breakdown of M00

This file splits the Invasion Mod overview (`M00-invasion-mod/README.md`) into feature specs. It does not change the design. The design is owned by the user.
Each feature has a folder `docs/mod/M<NN>-<feature>/`. The `<feature>` name is a valid Lua module name. It is the same as `Scripts/features/<feature>/` later.
Status of all features: skeleton only (2026-10-16). Only Batch 1 has iteration files.

## Batch table
| Batch | M | Folder | Goal (one line) | Depends on | Blocking spikes or open questions | First iteration |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | M01 | `M01-mod_state` | Keep mod values across save and load (Tags of the pawn and region). | none | Tags size limit test (spec 24) | `01-tags-module` |
| 1 | M02 | `M02-invasion` | Raid schedule, countdown banner, size estimate, great raid clock. | M01 | Timer writes above 730 days; how to show the estimate; win condition | `01-first-scheduled-raid` |
| 1 | M03 | `M03-raid_behavior` | Start the native plunder AI. Loot back to a store on death. Carry caps. Native rout. | M01, M02 | Does the AI obey a carry cap; death event hook; "nearest store" rule | `01-native-plunder` |
| 2 | M04 | `M04-bandits` | Low approval or low regional wealth turns families into bandits. Fight or pay coin. | M01, M03 | Buy-back price; approval threshold and homeless timer (spike 8) | `01-low-approval-bandits` |
| 2 | M05 | `M05-unit_balance` | Armor lethality, Hussite roles, counters, veterancy. | none (feeds M03, M04) | Live write of `att` and `armorPierce`; handgunner row; spawn hook or poll | `01-unarmored-lethality` |
| 3 | M06 | `M06-sack_and_terms` | A lost battle sacks the town. Tribute terms. Fallback capital. | M01, M02; M07 for the fallback | Sack size; what a lost battle is; hostage meaning; win condition | `01-sack-after-defeat` |
| 4 | M07 | `M07-vassals` | Vassalize or settle regions. Indirect control by mod-owned policies and orders. | M01; goals = Endless (spec 26) | How vassal regions are shown; effects on a region not owned; lost land | `01-claim-without-victory` |
| 4 | M08 | `M08-tribute` | Vassals send supplies. Failed protection lowers loyalty. | M07, M02 | Production read of a vassal; goods transfer between regions | `01-tribute-payout` |
| 4 | M09 | `M09-refugees` | A lost vassal sends refugees. Unhoused refugees become bandits. | M07, M04 | Wave size over the 5-families-per-call limit; tent slot limit | `01-refugee-wave` |
| 4 | M10 | `M10-finite_resources` | Home deposits run out. Vassals are the permanent source. | M01, M07, M08 | How to stop production on an empty deposit | `01-iron-deposit` |
| 5 | M11 | `M11-liege_influence` | Tribute to the liege gives influence. Influence buys aid. | M08 | Is the liege a real entity | `01-influence-balance` |
| 6 | M12 | `M12-tech_tree` | Two exclusive paths, laws, vassal policies, pak UI. | M01, M04, M07, M08, M11 | Path undo; node list; pak UI screen; id block numbering | `01-path-choice` |
| 6 | M13 | `M13-manor_stronghold` | Manor storage and retinue capacity upgrades. | M12, M03 | Retinue size write; real storage capacity effect | `01-manor-storage` |
| 7 | M14 | `M14-plundered_start` | Start in a damaged village. | M01; spec 26 | Shares that stay playable | `01-start-sack` |

Deferred (listed, no spec folder): occupation and rebellion. They are the heaviest layer. M00 build plan step 10 puts them last. Write specs for them after Batch 7 and a user review.

## Why this order
1. Batch 1 is the base. M01 is needed by every feature that keeps values. M02 and M03 give the first playable raid: schedule, spawn, loot. They match build plan steps 0, 1 and 2.
2. Batch 2 adds the inner pressure and the combat rules. M04 and M05 do not need vassals. M05 changes the fights that M03 and M04 create, so tune it as soon as raids and bandits exist. This matches build plan steps 3 and 4.
3. Batch 3 gives defeat a result. Sack and terms need the great raid (M02). The sack itself is proven. The fallback capital waits for M07. Build plan step 5.
4. Batch 4 is the outward system. M07 comes first because M08, M09 and M10 need a vassal. Goals = Endless (spec 26) removes the claim victory problem. Build plan step 6.
5. Batch 5 (M11) needs tribute. Build plan step 7.
6. Batch 6 (M12, M13) needs the systems that the tree changes. The tree is a wide change, so it comes after the systems exist. Build plan step 8.
7. Batch 7 (M14) is optional and last in the plan (step 9). No start setting exists, so it uses the sack tools after the start.

## Cross-cutting open questions from M00
These questions block more than one feature. Only the user can decide them.
1. Win condition (M00 open question 6). Blocks the end of M02 (great raid), M06 (what ends the game) and M07 (goals = Endless removes the game's own win). Needed before Batch 3 at the latest.
2. How "order" is measured and shown (M00 open question 7). Pillar 1 says every system feeds order. No score is defined. Needed before Batch 2 if order drives bandits, and before Batch 6 for the path effects.
3. How vassal regions exist in the world (M00 open question 3). Blocks Batch 4.
4. Is the liege a real entity? (M00 open question 9.) Blocks Batch 5.
5. Is the path choice final? (M00 open question 10.) Blocks M12.
6. Sack size that feels fair (M00 open question 11). Blocks the tuning of M06. A first value can be tuned by play.
7. Row id blocks. Spec 23 sets the block start as 1000 + 100 times the feature number. The M numbers differ from the harness spec numbers. This file proposes 1000 + 100 times the M number. The user must confirm.

Proposed id blocks (one block of 100 building ids per feature, rule: 1000 + 100 times the M number). Confirm before any pak work.
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
| M11 | 2100 to 2199 |
| M12 | 2200 to 2299 |
| M13 | 2300 to 2399 |
| M14 | 2400 to 2499 |

Upgrade rows use ids 117 to 999 for all features, until a larger id is tested.

## What the user must decide before each batch
- Before Batch 1: confirm the id block rule above. Confirm that M01 is a core module with no design. Decide how the size estimate is shown (banner line or widget).
- Before Batch 2: define "order" for the bandit rules, or accept raw approval and regional wealth. Give the buy-back price rule. Choose which foot rows are Hussite roles.
- Before Batch 3: win condition. What a lost battle is. Whether hostages stay as a term.
- Before Batch 4: how vassal regions are shown. How the player vassalizes a neighbor. What a lost vassal's land becomes.
- Before Batch 5: is the liege a real entity or a menu.
- Before Batch 6: the node list of version 1. Path undo. Where the pak UI opens.
- Before Batch 7: the shares of a plundered start, or drop the feature.
