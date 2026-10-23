# mod/invasion Specification

## Purpose
The invasion feature owns the raid schedule of the Invasion Mod. It plans the raids, warns the player, spawns the raids, runs the great raid clock and its waves, and keeps the difficulty.

## Requirements

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
The mod SHALL keep a difficulty from 1 to 3 (default `invasion.difficulty`). The player SHALL choose it in the scenario settings menu of `mod/scenario_settings` before the game starts. The mod SHALL NOT show the banner `Pick the difficulty: 1, 2 or 3` after the settings were applied. `invasion_set_difficulty` SHALL set the difficulty at any time and SHALL mark it as chosen. `invasion_pick_difficulty` SHALL set the difficulty once. It SHALL be refused after the first pick, after the first raid spawned, and for a value outside 1 to 3. A pick SHALL re-plan the squads of an unspawned raid.

#### Scenario: A pick at difficulty 2
- **WHEN** no pick was made and a test picks difficulty 2
- **THEN** `chosen` was false before and is true after, and the difficulty is 2
- **AND** a second pick is refused
- **AND** the relief army has 8 squads and the great raid has 2 waves
- **AND** the planned squads are a multiple of 2 between 1 and 3 times 2
- Checked by `mod/InvasionMod/scenarios/invasion/difficulty_pick.py`.

#### Scenario: The settings menu sets the difficulty
- **WHEN** the player begins the game with Hard in the settings menu
- **THEN** the difficulty is 3 and chosen is true, and no pick banner shows
- **AND** `invasion_set_difficulty` 1 afterwards sets the difficulty to 1
- Checked by `mod/InvasionMod/scenarios/scenario_settings/new_game_menu.py` (run 20261022-045227-57f0) and `harness/tests/test_fakegame_scenario_settings.py`.

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

### Requirement: No raid comes in the first game year
The mod SHALL NOT plan or spawn a raid in the first game year after the game start. Base game raids stay lifted (see "The mod owns the base game raid timer").

#### Scenario: The first year is quiet
- **WHEN** the 3 season changes of the first game year pass (a fake game test moves the calendar by real season changes; the real game test scenario runs the first days and counts the other changes with a test command)
- **THEN** no raid is planned and the log has no raid spawn event
- Checked by `harness/tests/test_fakegame_invasion.py` and `mod/InvasionMod/scenarios/invasion/yearly_raid.py`.

### Requirement: One raid comes in each later game year, by a season roll
From the second game year, the mod SHALL roll at each season change while no raid was done in the current game year. The chance of the roll SHALL be `yearly.chance_by_season` (default 25, 33, 50 and 100 percent for the first to the fourth season). A successful roll SHALL plan one raid in that season. The mod SHALL spawn at most one raid in a game year. The year, the roll state and the planned raid SHALL be kept in ModState and SHALL survive a load. A season SHALL NOT be rolled twice.

#### Scenario: Chances by season
- **WHEN** a test runs the season roll with the roll value 0.2 in the first season of year 2
- **THEN** a raid is planned
- **AND** with the roll value 0.9 no raid is planned and the second season rolls next
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: The last season always raids
- **WHEN** no raid was planned in the first three seasons of year 2
- **THEN** a raid is planned in the fourth season, whatever the roll value is
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: One raid a year
- **WHEN** 3 game years pass in a test scenario
- **THEN** exactly 2 raids spawn (years 2 and 3), at most one in each year
- Checked by `harness/tests/test_fakegame_invasion.py` (3 years of real season changes) and `mod/InvasionMod/scenarios/invasion/yearly_raid.py` (season changes counted by a test command).

#### Scenario: A load does not repeat a roll
- **WHEN** the game is loaded in a season that was already rolled
- **THEN** no new roll runs in that season
- Checked by `harness/tests/test_fakegame_invasion.py`.

### Requirement: A subjugation raid is large and does not plunder
A subjugation (major) raid SHALL be large: 3 x difficulty squads. It SHALL be a lord raid that does not plunder and does not leave. The yearly roll SHALL pick the kind of the raid by the kind rules: the first yearly raid is a plunder raid, the second is the subjugation raid (once), and every later yearly raid is a plunder raid.

#### Scenario: The subjugation raid at difficulty 1
- **WHEN** a subjugation raid spawns
- **THEN** it has 3 squads x difficulty
- **AND** the tracker shows `kind = subjugation`, no plunder and no leave reason within 12 game days
- Checked by `mod/InvasionMod/scenarios/invasion/subjugation_raid.py`.
