# M03: raid-behavior

Feature folder: `raid_behavior`. Batch 1.

## Goal
Start the native plunder AI for a raid. Loot of a killed raider goes back to a store. Carry caps apply. Routing stays native.

## Player rules (from M00)
- Raiders loot stores, kill villagers and burn buildings. The base AI picks the targets and leaves when it has looted enough.
- Carry cap per raider: Hussite plunder about 10 grain or 5 iron. Bandit plunder about 5 grain.
- When a looter is killed, the goods it carried go back to the nearest storehouse. There is no ground pile.
- Storage tiers: a guarded granary loses less per trip than an open barn. The manor is the safest store. Manor capacity grows with the tech tree (M12, M13).
- Burned buildings become ruins. Ruins rebuild at partial cost.
- Units rout on their own. A mod mass rout is added only if playtests show the game is too punishing.
- Hostages are dropped (decision 8). Loot and sack use the native game mechanics. Raid size comes from M02: base size multiplier times difficulty (1 to 3).

## Current state
Iteration 01 done (2026-10-17): feature `raid_behavior` tracks the raid, cuts loot to a cap and returns the loot of a dead raider to the nearest store. Command `raid_behavior_state`. Notes: `implementation-notes/iteration-01-native-plunder.md`. One rare game crash remains in raids of 2 squads.

## Proven building blocks
- The base AI loots, burns 3 to 7 buildings and leaves with "enough looted": `openspec/changes/archive/2026-10-15-legacy-15-bandit-settlement/implementation-notes/homeless-rebellion.md`, `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-S1.md`.
- Raiders cannot be steered: `homeless-rebellion.md` part 4, `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/unit-steering.md`.
- `ItemsLooted` can be read and written. Native max is 4 to 5 per unit: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-S5.md`, `spike-S3.md`.
- Goods back to a store with `GiveItemByID`: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-S6.md`.
- Loss share per store, sack, fire to ruins, partial rebuild cost: `spike-S6.md`, `spike-R8.md`.
- Manor store: `openspec/changes/archive/2026-10-15-legacy-12-manor-exploration/implementation-notes/storage-m1.md`.
- Review: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-raids.md`.
- Mod state: M01. Raid start: M02.
- Row ids: `openspec/changes/archive/2026-10-15-legacy-23-row-id-range/README.md`. Confirmed block (decision 3): building ids 1300 to 1399.

## Tunables (M00 values, first guesses)
- Carry cap per raider (Hussite grain 10, iron 5. Bandit grain 5).
- Loss share per trip by store tier. M00 gives no numbers. The spike used open barn 50% and granary 10%.
- Rebuild discount for ruins.
- Loot and sack scale with raid size, which is multiplier times difficulty (M02). No separate loot multiplier is added (decision 8).

## Dependencies
- M02 invasion (starts the raid).
- M01 mod-state.
- Storage tiers use M12 and M13 later.

## Open questions
1. Does the native AI stop looting at a written `ItemsLooted` cap? Writing the value does not prove it (spike-S5). The unit of the value (items or silver) is unknown.
2. Which store gets the goods of a killed looter? `GiveItemByID` fills any store with space. A rule for "nearest" is needed.
3. Which unit death event can the mod hook to read the carried goods before they are cleared?
4. Does the squad type matter (`spawnRaiders` against `spawnArmy`)? A `spawnArmy` squad attacked late in one test.
5. What is the ruin rebuild discount? M00 says "partial cost" and gives no number.
6. Which building types are guarded and which are open? M00 gives no list.
7. Does the native loot per raider stay in range when the raid has 1 to 9 squads (multiplier 1 to 3 times difficulty 1 to 3)? Test in iteration 01.

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | native-plunder | Start the native plunder AI and measure the loot. | done, A1 to A6 pass (see the iteration file) |
| 02 | role-raid-leave | Role raids leave after loot, losses or time. | done, lord army raid with plunder tick (see the iteration file) |
| 02b | loot-back-to-store | Loot of a killed raider returns to a store. | not started |
| 03 | carry-caps | Carry caps by raid type. | not started |
| 04 | storage-tiers | Loss per trip by store tier. Ruin rebuild discount. | not started |
