# Proposal: update-raid-banners

Issue: #400

## Why
Owner requirement (2026-10-22): "The great raid notification shall play no more than 2 times per game year, once in the spring, and once in the fall. The yearly smaller raids shall have no notification banner. The difficulty selected shall not have a notification and shall be managed through the scenario start menu."

## What changes
- The great raid clock banner shows at most twice a game year: at the start of spring and at the start of fall. `banner_every_days` (30) is removed.
- A minor (yearly) raid has no countdown banner and no warning banner. The great raid line under the countdown goes away with it, because it has no other home.
- The difficulty has no banner. `prompt_every_days` and the `Pick the difficulty` banner are removed. The scenario start menu is the only way for the player to choose. `invasion_pick_difficulty` stays as a test command.
- Not changed: the banner at the spawn of a raid, the wave, relief and victory banners, and the subjugation raid warning banner.

## Impact
- Spec `mod/invasion`: MODIFIED "A daily banner counts down to the raid", "The player picks the difficulty once", "A great raid clock counts the game days".
- Code: `mod/InvasionMod/Scripts/features/invasion/init.lua` (`show_countdown`, `prompt_step`, `clock_step`), `mod/InvasionMod/Scripts/config.lua`, the banner and warning rules in `plan.lua`.
- Tests: `harness/tests/test_fakegame_invasion.py`, the test scenarios `first_raid.py`, `difficulty_pick.py`, `great_raid_clock.py`.
- Overlap: the open changes `add-scenario-settings-menu` and `update-raid-clock-yearly` also change these requirements (the second removes the warning time of the first raid). This change is written against the text on `main`. Whichever change is archived last must rebase its delta on the earlier ones.
- Season values: the code reads `TemporalComponent.Season` (`current_season` in `init.lua`). Which values are spring and fall is not confirmed yet (task 1.1). The yearly roll counts seasons from the mod start, not the calendar, so it cannot be reused for this.

## Open questions for the owner
1. Does the subjugation raid keep its warning banner? (It is kept now.)
2. Should the great raid waves themselves (when the clock ends) still announce (`Great raid: wave N of M`, relief army, victory)? They are kept now.
3. When "Great raids" is Off in the settings menu, no clock banner shows (as now). Is that right?
4. Is the start of the season the right moment, or the first day after a load in that season?
