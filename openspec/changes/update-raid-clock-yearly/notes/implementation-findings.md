# Implementation findings

## Year and season counting
- The mod counts season changes from its own start (`yearly_season_no`), not the calendar `Year`. Reason: the meaning of `Year` (first value) is not known, and a save loaded in any season then starts a quiet year 1 of 4 seasons.
- Game year N is season changes `4(N-1)` to `4N-1`. The roll in year 2 or later uses the season position 1 to 4 of that count. Year 1 is the first 4 seasons after the mod started (the start season counts as the first).
- The saved season is set before the roll (like `mod/bandits`), so a load does not roll again. A fake game test checks this.

## Kind rules (decision for the owner to confirm)
- First yearly raid: plunder. Second: the subjugation raid (once). Later years: plunder again (new plan, new composition seed).
- The design said "existing kind rules". The existing rules had no later raids, so "one raid a year" needs the repeat of plunder from year 4. Not in the proposal text; the delta spec now says it.

## Test helpers
- `invasion_plan_now` (optional `kind`) plans a raid at once. About 15 test scenarios and 2 fake game test files waited for a plan at the start; they now call it.
- `invasion_force_next` plans a plunder raid when none is planned (as before).
- `invasion_yearly_advance_season` (optional `roll`) counts one season change and rolls. A real year takes about 1800 s at speed 3, so the real test scenario `yearly_raid.py` uses it. It proves the real calendar season read, the real spawn and the tracker. The 360-day quiet year and the 3-year run are proven in the fake game with real calendar season changes.

## Real game notes
- Run 20261022-033120-c1ca (harness_error): the planned subjugation day came while the first raid fought, so the raid spawned by itself and `subjugation_force_next` was refused. The scenario now forces only when not spawned.
- Run 20261022-033548-7c30 (crash): UE4SS access violation at 0x70 in `process_simple_actions` during a day step with an active raid. Not repeated in the next run (20261022-033944-5080 passed).
- `first_raid.py` counted raiders in the census of the bandit side. A raid is a lord army, so the count was 0 (run 20261022-034446-2d33). The scenario now reads `initial` from the raid tracker.
