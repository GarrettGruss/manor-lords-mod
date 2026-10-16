# M02 iteration 01: first-scheduled-raid

Branch: `feat/M02-invasion-01-first-scheduled-raid`. Issue: `Mod M02.01: first-scheduled-raid` (not created yet).

## Goal
The mod owns the raid timer. It plans one minor raid, shows a daily countdown banner with a size estimate, and spawns the raid on the planned day.

## Changes
- New feature `Scripts/features/invasion/`. The schedule is kept in `ModState` (M01).
- Each game day: write the base game raid timer so that the base game does not start a raid by itself. Show the banner "Raid in N days, about S raiders".
- On the planned day: `spawnRaiders` with the planned number of squads (multiplier times difficulty). The raid then runs under the native AI (M03).
- Tunables in `config.lua`: first raid day range, warning weeks range, difficulty (1 to 3), base size multiplier (small 1, medium 2, large 3).
- The raid size is the base size multiplier times the difficulty, in squads of 18. This iteration uses a small raid.
- Raid info goes to the banner in this iteration. The custom raid widget (decision 4) comes in a later iteration.
- Named commands: `invasion_state` (planned day, squads, difficulty, days left), `invasion_force_next` (set the planned day to today).

## Acceptance criteria
- A1: the planned day of the first raid is between day 30 and day 90. The warning time is between 14 and 56 game days.
- A2: from the warning start, the banner function is called once per game day with the correct days left (read from the log, every day).
- A3: the raid spawns on the planned day, plus or minus 1 day. The unit count is 18 times the planned squads. The planned squads equal the base size multiplier times the difficulty (for example small at difficulty 2 gives 2 squads).
- A4: the base game timer does not spawn an extra raid in 120 game days (exactly one raid spawn event in the log).
- A5: the shown size estimate equals the real spawned size (exact in this iteration).

## Scenarios to write
- `scenarios/invasion/first_raid.py`: fixture `base`, speed up, assert A1 to A5 from `invasion_state` and the log.
- `scenarios/invasion/no_double_raid.py`: A4 over 120 days.
- Run `first_raid.py` at difficulty 1, 2 and 3 and check the unit count each time.

## Result
Result: not started.
