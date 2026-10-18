# M02 iteration 02: great-raid-clock

Branch: `feat/M02-invasion-02-great-raid-clock`. Issue: #171.

## Goal
The mod keeps a countdown to the great raid. It lasts 3 to 5 game years (M00 balance target). The clock is in ModState, so it survives a load. The banner shows it.

## Changes
- New file `Scripts/features/invasion/great_raid.lua` with pure rules (pick the end day, days left, banner text).
- ModState keys `great_raid_day` (absolute game day when the great raid starts, 0 = no clock yet) and `last_clock_banner_day`.
- The clock starts on the first daily step. The length is a random whole number of days between 3 x 365 and 5 x 365 (config `invasion.great_raid`).
- The mod owns the clock. It does not use the base game raid timer (it holds at most 730 days; see M02 open question 1). The game timer stays high (iteration 01).
- Banner: the countdown banner of a minor raid shows the great raid days in its second line. When no minor raid banner shows, a banner for the great raid shows once every `banner_every_days` (30) game days.
- Named commands: `invasion_clock_state`, `invasion_clock_set_days_left` (for tests only).
- The clock only counts and shows. The waves come in iteration 06. Season weights are not part of this iteration (TBD, the clock runs on game days).

## Acceptance criteria
- C1: the clock length is 1095 to 1825 game days after the day it starts.
- C2: the banner for the great raid shows with the right days left (log line `INVASION clock banner`), at most one per game day.
- C3: the clock is kept in the pawn tags and `days_left` falls by 1 each game day.
- C4: after a load of the same game, the clock end day is the same (ModState roundtrip is proven by M01; the scenario checks the key is registered and saved with the tags).

## Scenarios
- Fake game tests in `harness/tests/test_fakegame_invasion.py` (C1 to C3).
- `scenarios/invasion/great_raid_clock.py`: reads the state, checks C1, sets days left to 3, runs 5 game days, checks the banner lines and days left (C2, C3).

## Result
not started
