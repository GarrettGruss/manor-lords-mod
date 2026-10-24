# Where the code read the global difficulty (task 1.1)

State key `difficulty` (ModState `invasion`) is removed. It is replaced by `level_yearly`, `level_great` and `level_vassal` (each 0 to 3). `great_raids` is removed (level 0 of the great raid).

| Place | Used for | Now reads |
|---|---|---|
| `invasion/init.lua` `make_plan`, `replan_size` | squads of the yearly (plunder) raid | `level_yearly` |
| `invasion/init.lua` `make_subjugation_plan`, `replan_size` | squads of the subjugation raid | `level_vassal` |
| `invasion/init.lua` `composition_list` | role mix of a raid | level of the raid kind (at least 1 for the tables) |
| `invasion/init.lua` `great_wave_list`, `spawn_great_wave`, `spawn_relief_and_final`, `great_step`, `command_great_state` | waves, wave roles, relief army | `level_great` |
| `invasion/init.lua` `clock_step`, `clock_subtitle` | clock, banner subtitle | `level_great` (0: no clock, no subtitle) |
| `invasion/init.lua` `minor_raid_step`, `subjugation_step`, `roll_season`, `next_kind` | banner, spawn, yearly roll | `level_yearly`, `level_vassal` (0: nothing) |
| `bandits/init.lua` (Public Order debuff) | debuff size | `invasion.difficulty()` |
| `sack_and_terms/*.lua` (sack share, terms payment and tribute, fallback cost) | amounts | `invasion.difficulty()` |
| `raid_widget/lines.lua` | the lines "Next raid", "Great raid" and the levels line | `levels` of `raid_info` |

`invasion.difficulty()` is the one number for the features that are not tied to one raid type: the highest of the three levels, at least 1. This is an assumption (the proposal does not say). Owner: say if bandits, sack and terms should read one level (for example the great raid level) instead.

## Old saves
A save made before this change has no level keys: the registered start value applies until `scenario_settings` sees `settings_applied`. An old save without settings gets the defaults (2, 2, 2) and the pick stays open. A save with settings from `add-scenario-settings-menu` has `settings_applied = 1` and no level keys, so it reads the start value 2 (the old `difficulty` it saved is not read any more). This save format existed for a few days only (unmerged to a release); no migration is written.

## Overlap with update-raid-banners (#400)
- Both change `invasion/init.lua` (banners, `clock_subtitle`, `great_step`). Expected conflicts: the `great_raids` checks in `clock_subtitle` and `clock_step` (here `level("great") == 0`), and the `show_*` banner functions. Resolution: keep `level("great") == 0` as the "Great raids Off" test.
- Both change `raid_widget/lines.lua` / `raid_info` fields (`great_raids` is gone here; `levels` is new).
