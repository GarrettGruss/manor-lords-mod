# M03 iteration 01: native-plunder

Branch: `feat/M03-raid_behavior-01-native-plunder`. Issue: #144.

## Goal
A raid that M02 spawns runs the native plunder AI: it loots, burns and leaves. The mod measures the result and adds no steering.

## Changes
- New feature `Scripts/features/raid_behavior/`.
- After a raid spawn, record the raid in `ModState`: id, start day, squad count.
- Each game day, track the raid: living raiders, total `ItemsLooted`, burned buildings, state (active or left).
- Named command `raid_behavior_state`: active raids and their numbers.
- No steering call. No rout call.

## Acceptance criteria
- A1: a raid of 1 squad (18 raiders; small raid, difficulty 1) on the `base` fixture ends within 20 game days (raiders gone or left). The log shows the native leave line.
- A2: total looted goods at the end are more than 0.
- A3: the number of burned buildings is between 0 and 10 (a range, because the AI is not deterministic).
- A4: the village population after the raid is more than 0 (the game does not end).
- A5: the tracker count of living raiders equals the unit count read from the game, with no difference.
- A6: a small raid at difficulty 2 (2 squads) and a medium raid at difficulty 1 (2 squads) loot more than the 1-squad raid on average over 3 runs each. Loot and burned buildings use only native mechanics (no hostages, no captives).

## Scenarios to write
- `scenarios/raid_behavior/native_plunder.py`: spawn a raid through M02 `invasion_force_next`, run 20 days, assert A1 to A5. Run 3 times. Repeat for 2 squads (small at difficulty 2) for A6.

## Result
Result: PASS in the real game (2026-10-17), with deviations. Details and run ids: `../implementation-notes/iteration-01-native-plunder.md`.
- A1: 1 squad ended (native leave line) on game day 14 in 4 of 4 runs (`m03-plunder-2`, suite `20261017-060551-d673` runs 001, 004, 007). Deviation: raiders do not leave the unit list, so "left" is the leave line. Raids of 2 squads took 12 to 19 days; the scenario limit is 30 days for them.
- A2: looted goods 70 to 87 (1 squad). A3: burned 9 to 10. A4: population above 0. A5: tracker living equals the game count in every sample.
- A6: looted_total mean 77 (small, d1, 1 squad), 163 (small, d2, 2 squads; runs 134, 175, 179), 176 (medium, d1, 2 squads). Both are above the 1-squad raid.
- Loot return: `raid-behavior-loot-return` `m03-loot-return-d` pass (72 loot back to a store, stock +72, read back from the building inventory).
- Open: one crash in 9 suite runs (2 squads), see the notes.
