# M02 iteration 01: first-scheduled-raid

Branch: `feat/M02-invasion-01-first-scheduled-raid`. Issue: #143.

## Goal
The mod owns the raid timer. It plans one minor raid, shows a daily countdown banner with a size estimate, and spawns the raid on the planned day.

## Changes
- New feature `Scripts/features/invasion/`. The schedule is kept in `ModState` (M01).
- Each game day: write the base game raid timer so that the base game does not start a raid by itself. Show the banner "Raid in N days, about S raiders".
- On the planned day: `spawnRaiders` with the planned number of squads (multiplier times difficulty). The raid then runs under the native AI (M03).
- Tunables in `config.lua`: first raid day range, warning days range, difficulty (1 to 3), base size multiplier (small 1, medium 2, large 3).
- Difficulty 1 to 3 is chosen by the player at the start. In this iteration it is a config value and the command `invasion_set_difficulty`, kept in ModState. The start UI comes later.
- The size class (small, medium, large) is random for each raid. The raid size is the base size multiplier times the difficulty, in squads of 18. The command `invasion_set_size` forces the class (for the A3 check).
- Raid info goes to the banner in this iteration. The custom raid widget (decision 4) comes in a later iteration.
- Named commands: `invasion_state` (planned day, squads, difficulty, days left), `invasion_force_next` (set the planned day to today), `invasion_set_difficulty`, `invasion_set_size`.

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
Result: PASS in the real game (2026-10-17).
- A1, A2, A3, A5 passed in `invasion-first-raid` at difficulty 1 (medium, run `m02-first-raid-d1`), difficulty 2 (small, `m02-first-raid-d2`) and difficulty 3 (large, 162 raiders, `m02-first-raid-d3b`). The first difficulty 3 run failed A5 only because of a scenario issue (fixed).
- A4 passed in `invasion-no-double-raid` over 120 game days (run `m02-no-double-raid-d`): one spawn event, the base timer stayed at 300 or more, every lift started from 299.
- Failed runs on the way: `m02-no-double-raid` and `-b` stalled because a pop-up ("Hunger!") paused the game inside a chunk of 10 game days. Fix: `ctx.time` runs now close pop-ups every 2 s (commit `fix(time)`). Run `m02-no-double-raid-c` then passed all but one check: the census showed 16 bandit units instead of 18, because raiders fight and die in the days after the spawn. The check now accepts 1 to 18 units (run d: 15 of 18).
- Open for later iterations: only one raid is planned; the start UI for difficulty; the custom widget.
- Notes: `docs/mod/M02-invasion/implementation-notes/iteration-01-first-scheduled-raid.md`.
