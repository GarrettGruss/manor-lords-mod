# mod/invasion Specification

## Purpose
The invasion feature owns the raid schedule of the Invasion Mod. It plans the raids, warns the player, spawns the raids, runs the great raid clock and its waves, and keeps the difficulty.

## Requirements

### Requirement: The first minor raid is planned within a day range
The mod SHALL plan one minor (plunder) raid on its first daily step. The raid day SHALL be a random number of game days after the plan day, between `first_raid_days_min` and `first_raid_days_max` (default 30 to 90). The warning time SHALL be between `warning_days_min` and `warning_days_max` (default 14 to 56 game days), and never longer than the wait. The plan SHALL be kept in ModState and SHALL survive a load.

#### Scenario: The plan after the start
- **WHEN** a game starts and the first daily step runs
- **THEN** the raid day is between 30 and 90 game days after the plan day
- **AND** the warning time is between 14 and 56 game days
- Checked by `mod/InvasionMod/scenarios/invasion/first_raid.py`.

#### Scenario: The plan is stored in the pawn Tags
- **WHEN** the plan exists
- **THEN** the plan keys are entries in the Tags of the player pawn
- Checked by `harness/tests/test_fakegame_invasion.py`.

### Requirement: A daily banner counts down to the raid
From the warning day, the mod SHALL show one banner on each game day, with the days left and the size estimate (`Raid in N days, about S raiders`). The second line of the banner SHALL show the days left to the great raid. The mod SHALL NOT show a banner before the warning day or two banners on one day.

#### Scenario: The countdown
- **WHEN** the game days run from the warning day to the raid day
- **THEN** each day has one banner and its days left equal the raid day minus that day
- **AND** the size estimate in each banner equals the size of the spawned raid
- Checked by `mod/InvasionMod/scenarios/invasion/first_raid.py`.

### Requirement: The raid spawns on the planned day
The mod SHALL spawn the planned raid on the raid day, plus or minus 1 game day. The raid size SHALL be the size multiplier of the size class times the difficulty, in squads. The size class SHALL be picked at random between small, medium and large with the multipliers 1, 2 and 3 (`size_multipliers`). The mod SHALL spawn the first minor raid only once.

#### Scenario: A medium raid at difficulty 2
- **WHEN** the raid day arrives for a medium raid at difficulty 2
- **THEN** the raid has 4 squads (2 x 2)
- **AND** the number of raiders is between 90 and 100 percent of the planned units (some raiders die at once)
- Checked by `mod/InvasionMod/scenarios/invasion/first_raid.py`.

#### Scenario: A forced raid
- **WHEN** a test calls `invasion_force_next` after the plan exists
- **THEN** the raid spawns at the next check, and a second call is refused because the raid was spawned
- Checked by `harness/tests/test_fakegame_invasion.py`.

### Requirement: The mod owns the base game raid timer
The mod SHALL lift the base game raid timer (`daysUntilNextRaid`) to `base_timer_refill` (default 700) whenever it falls below `base_timer_floor` (default 300), so the base game starts no raid of its own.

#### Scenario: 120 game days
- **WHEN** 120 game days pass after the plan
- **THEN** the log has exactly one plunder spawn event
- **AND** the base timer stays at 300 or more
- Checked by `mod/InvasionMod/scenarios/invasion/no_double_raid.py`.

### Requirement: Raid squads follow the Hussite roles
The mod SHALL give each squad of a raid one unit template. About `ranged_share` (default 25 percent) of the squads SHALL be ranged. The melee tier mix and the crossbow share SHALL depend on the difficulty (`roles.melee_tier_weights`, `roles.crossbow_share`): at difficulty 1 there is no tier III melee and no crossbow squad. The mix SHALL be rebuilt from one saved seed. With `roles.enabled = false` the mod SHALL spawn the raid with `spawnRaiders` instead.

#### Scenario: A large raid at difficulty 1
- **WHEN** a large raid spawns at difficulty 1
- **THEN** it has 3 squads, one template for each squad, and the ranged squads are at most 25 percent plus 1 of the squads
- **AND** the unit stats of each squad match its template, and the units are 90 to 100 percent of the template sizes
- Checked by `mod/InvasionMod/scenarios/invasion/raid_composition.py`.

#### Scenario: The role rules
- **WHEN** the role counts are computed for each difficulty
- **THEN** the ranged count is the rounded share and difficulty 3 has heavier melee than difficulty 1
- Checked by `harness/tests/test_invasion_plan_roles.py`.

#### Scenario: All role templates exist
- **WHEN** each template in `invasion.roles.templates` is spawned as a bandit-side squad
- **THEN** every template spawns living units
- Checked by `mod/InvasionMod/scenarios/unit_balance/role_templates.py`.

### Requirement: A role raid is the army of an AI lord
With `roles.lord_army.enabled` (default on), the mod SHALL spawn a role raid as the army of the AI lord `Hussite Raiders`, at war with the player, with its battlefield at the player manor. If that fails before any army exists, the mod SHALL spawn bandit squads instead. If it fails after some armies exist, the mod SHALL NOT spawn bandit squads on top, and SHALL try again on the next daily step.

#### Scenario: A lord raid
- **WHEN** a role raid spawns
- **THEN** the raid tracker reports `lord_raid = true`
- Checked by `mod/InvasionMod/scenarios/invasion/subjugation_raid.py`.

#### Scenario: A failure after a partial spawn
- **WHEN** the lord raid fails after some armies were spawned
- **THEN** no bandit squads are added
- Checked by `harness/tests/test_fakegame_invasion.py`.

### Requirement: The player picks the difficulty once
The mod SHALL keep a difficulty from 1 to 3 (default `invasion.difficulty`). Until the player picks one, the mod SHALL show the banner `Pick the difficulty: 1, 2 or 3` every `prompt_every_days` (default 7) game days. `invasion_pick_difficulty` SHALL set the difficulty once. It SHALL be refused after the first pick, after the first raid spawned, and for a value outside 1 to 3. A pick SHALL re-plan the squads of an unspawned raid.

#### Scenario: A pick at difficulty 2
- **WHEN** no pick was made and a test picks difficulty 2
- **THEN** `chosen` was false before and is true after, and the difficulty is 2
- **AND** a second pick is refused
- **AND** the relief army has 8 squads and the great raid has 2 waves
- **AND** the planned squads are a multiple of 2 between 1 and 3 times 2
- Checked by `mod/InvasionMod/scenarios/invasion/difficulty_pick.py`.

### Requirement: A subjugation raid follows the first raid
After the first raid spawned, the mod SHALL plan one subjugation (major) raid `subjugation.wait_days_min` to `wait_days_max` (default 60 to 120) game days later, with a warning banner like the first raid. The raid SHALL be large: 3 x difficulty squads. It SHALL be a lord raid that does not plunder and does not leave. It SHALL spawn once.

#### Scenario: The subjugation raid at difficulty 1
- **WHEN** the first raid has ended and the subjugation raid spawns
- **THEN** it was planned 60 to 120 game days ahead
- **AND** it has 3 squads x difficulty
- **AND** the tracker shows `kind = subjugation`, no plunder and no leave reason within 12 game days
- Checked by `mod/InvasionMod/scenarios/invasion/subjugation_raid.py`.

### Requirement: A subjugation raid targets a vassal region
The mod SHALL ask the registered vassal provider for target regions when a subjugation raid spawns. If a vassal region exists, the raid SHALL target it with `stand_in = false`. Otherwise the target SHALL be the home region with `stand_in = true`. A plunder raid SHALL always target the home region.

#### Scenario: One vassal exists
- **WHEN** one vassal exists and the subjugation raid spawns
- **THEN** the spawn log names the vassal region and `stand_in=false`
- Checked by `mod/InvasionMod/scenarios/invasion/vassal_targets.py`.

#### Scenario: No vassal exists
- **WHEN** no vassal exists and the subjugation raid spawns
- **THEN** the spawn log names the home region and `stand_in=true`
- Checked by `mod/InvasionMod/scenarios/invasion/subjugation_raid.py`.

### Requirement: A great raid clock counts the game days
The mod SHALL start the great raid clock on the first daily step. The clock length SHALL be a random whole number of game days between `great_raid.min_days` and `max_days` (default 1095 to 1825, 3 to 5 game years). The end day SHALL be kept in ModState. The mod SHALL show a clock banner every `banner_every_days` (default 30) game days when no raid banner shows, at most one per game day.

#### Scenario: The clock after the start
- **WHEN** the clock starts and three game days pass
- **THEN** the clock length is between 1095 and 1825 game days
- **AND** the end day does not change and the days left fall by the days that passed
- **AND** each clock banner shows the days left of its day
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_clock.py`.

### Requirement: The great raid starts with waves
When the clock ends, the mod SHALL spawn one wave for each difficulty point. Each wave SHALL have `wave_squads` (default 15) squads. Waves SHALL be `wave_gap_days` (default 10) game days apart. The mod SHALL NOT spawn a wave twice.

#### Scenario: The first wave at difficulty 1
- **WHEN** a test forces the clock to end at difficulty 1
- **THEN** wave 1 has 15 squads and exactly 1 wave spawns
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py`.

### Requirement: A relief army and a final battle end the great raid
`relief_delay_days` (default 10) game days after the last wave, the mod SHALL spawn the relief army on the player side (15, 8 or 0 squads at difficulty 1, 2 or 3) and a hostile final army of `final_squads` (default 25) squads, not scaled by difficulty. When the final army is dead, the phase SHALL become `won`.

#### Scenario: The relief army and the final army at difficulty 1
- **WHEN** the wait after the last wave is over
- **THEN** the relief army has 15 squads and spawned
- **AND** the final army has 25 squads
- **AND** the game still answers with all squads on the map
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py`.

#### Scenario: The win
- **WHEN** the final army has no living unit
- **THEN** the phase is `won`
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: Named commands expose and drive the schedule
The mod SHALL offer these commands for scenarios: `invasion_state`, `invasion_force_next`, `invasion_set_difficulty`, `invasion_set_size`, `invasion_set_roles`, `invasion_raid_squads`, `invasion_difficulty_state`, `invasion_pick_difficulty`, `invasion_clock_state`, `invasion_clock_set_days_left`, `invasion_great_state`, `invasion_great_force_start`, `invasion_great_skip_wait`, `invasion_subjugation_state` and `invasion_subjugation_force_next`. A difficulty outside 1 to 3 SHALL be refused.

#### Scenario: A bad difficulty
- **WHEN** a test sets the difficulty to a value outside 1 to 3
- **THEN** the command is refused and the difficulty does not change
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: A forced great raid start
- **WHEN** a test calls `invasion_great_force_start` after the great raid started
- **THEN** the command is refused
- Checked by `harness/tests/test_fakegame_invasion.py`.
