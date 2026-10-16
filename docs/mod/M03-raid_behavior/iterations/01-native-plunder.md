# M03 iteration 01: native-plunder

Branch: `feat/M03-raid_behavior-01-native-plunder`. Issue: `Mod M03.01: native-plunder` (not created yet).

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
Result: not started.
