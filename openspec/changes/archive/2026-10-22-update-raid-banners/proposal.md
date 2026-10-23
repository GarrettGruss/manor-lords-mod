# Proposal: update-raid-banners

Issue: #400

## Why
Owner requirement (2026-10-22): "The great raid notification shall play no more than 2 times per game year, once in the spring, and once in the fall. The yearly smaller raids shall have no notification banner. The difficulty selected shall not have a notification and shall be managed through the scenario start menu."

Owner decisions (2026-10-22), which replace the spring and fall rule: "Subjugation raid and player raid should show just once, 30 days before occurring. It should show type (attacking vassal or player), and size. The great wave should occur on year 10 default, and there should be a warning once a year about the great wave, starting t-3 years before the great wave will start."

## What changes
- A minor (yearly) raid has no banner of any kind: no countdown and no warning. This is unchanged from the first draft.
- The subjugation raid and the player raid show exactly one banner each, 30 game days before the raid day. The banner shows the target type (`your vassal <name>` or `you`) and the size estimate. There is no daily countdown.
- The great raid clock has a fixed length: it ends at the start of game year `great_raid.start_year` (default 10). The random range `min_days`/`max_days` (1095 to 1825) is removed.
- The great raid warning banner shows once a game year, at the start of years 7, 8 and 9 (3, 2 and 1 years before the start). Year 10 itself shows no clock banner: the wave banners announce it. `banner_every_days` (30) is removed. There is no spring or fall rule.
- The difficulty has no banner. `prompt_every_days` and the `Pick the difficulty` banner are removed. The scenario start menu is the only way for the player to choose. `invasion_pick_difficulty` stays as a test command.
- Not changed: the banner at the spawn of a raid, and the wave, relief and victory banners.

## Assumptions
- "Player raid" means the plunder raid, the raid whose target is the player home region (spec "A subjugation raid targets a vassal region": a plunder raid always targets the home region). In the yearly raid rule of `update-raid-clock-yearly` this is the yearly minor raid, which would then have a banner. This conflicts with the earlier rule "yearly smaller raids have no banner". This draft resolves it this way: a minor raid whose target is the player gets the one 30 day banner only when it is a large (major) raid, and the small yearly plunder raid gets none. This must be confirmed (see open question 1).
- The target type of a subjugation raid is a vassal when a vassal region exists, else the player (stand-in home region).
- Year 1 is the first game year; "start of year 10" is the first day of game year 10. The year length is the one the yearly raid rule uses.
- A 30 day banner is not shown if the raid is planned less than 30 days ahead (the banner shows once on the plan day).

## Impact
- Spec `mod/invasion`: MODIFIED "A daily banner counts down to the raid", "The player picks the difficulty once", "A great raid clock counts the game days".
- Code: `mod/InvasionMod/Scripts/features/invasion/init.lua` (`show_countdown`, `prompt_step`, `clock_step`), `mod/InvasionMod/Scripts/config.lua`, the banner and warning rules in `plan.lua`.
- Tests: `harness/tests/test_fakegame_invasion.py`, the test scenarios `first_raid.py`, `subjugation_raid.py`, `difficulty_pick.py`, `great_raid_clock.py`.
- Overlap: the open changes `add-scenario-settings-menu` and `update-raid-clock-yearly` also change these requirements. The settings menu keeps "Great raids" On or Off; the start year is a config value and is not a menu setting. Whichever change is archived last must rebase its delta on the earlier ones.

## Open questions for the owner
1. Is the "player raid" the large yearly raid only, or every yearly raid that targets the player? (Assumed: large only; small yearly raids have no banner.)
2. Should the great raid waves themselves (`Great raid: wave N of M`, relief army, victory) still announce? They are kept now.
3. When "Great raids" is Off in the settings menu, no clock banner shows (as now). Is that right?
4. After a load, should a missed warning (for example a load in year 8 after the year 8 start) show once, or be skipped? (Assumed: skipped; a shown year is kept in ModState.)

## Answered
- Subjugation raid warning: kept, but as one banner 30 days before (owner, 2026-10-22).
- Season trigger: dropped; the great raid warning is yearly (owner, 2026-10-22).
