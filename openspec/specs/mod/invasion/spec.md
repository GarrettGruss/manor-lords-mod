# mod/invasion Specification

## Purpose
The invasion feature owns the raid schedule of the Invasion Mod. It plans the raids, warns the player, spawns the raids, runs the great raid clock and its waves, and keeps the difficulty.

## Requirements

### Requirement: A daily banner counts down to the raid
The mod SHALL NOT show a countdown banner or a warning banner for a minor (yearly) raid, and SHALL NOT show a banner on each game day before any raid. For the subjugation raid and the player raid (see the assumption in the proposal) the mod SHALL show exactly one banner, 30 game days before the raid day, with the target type and the size estimate: `Raid in 30 days: <target>, about S raiders`, where `<target>` is `your vassal <name>` or `you`. If the raid is planned less than 30 days ahead, the banner SHALL show once on the plan day. The mod SHALL NOT show this banner again after a load. The warning time (`warning_days_min`, `warning_days_max`) and the second banner line with the days left to the great raid SHALL be removed. The banner at the spawn of a raid (`Raiders are here`) is not changed by this requirement.

#### Scenario: The countdown
- **WHEN** a minor raid is planned and the game days run from the plan day to the raid day
- **THEN** no banner shows on any of these days
- **AND** the log has no `INVASION banner` event
- Checked by `harness/tests/test_fakegame_invasion.py` and `mod/InvasionMod/scenarios/invasion/first_raid.py`.

#### Scenario: A subjugation raid against a vassal
- **WHEN** a subjugation raid targets the vassal `V` and the game days run from 40 days before the raid day to the raid day
- **THEN** exactly one banner shows, on the day that is 30 days before the raid day
- **AND** it names `your vassal V` and its size estimate equals the size of the spawned raid
- Checked by `harness/tests/test_fakegame_invasion.py` and `mod/InvasionMod/scenarios/invasion/subjugation_raid.py`.

#### Scenario: A raid against the player
- **WHEN** a player raid is planned 60 game days ahead and the game days run to the raid day
- **THEN** exactly one banner shows, 30 days before the raid day, and it names `you` and the size estimate
- **AND** a load after the banner does not show it again
- Checked by `harness/tests/test_fakegame_invasion.py`.

### Requirement: The raid spawns on the planned day
The mod SHALL spawn the planned yearly raid on the raid day, plus or minus 1 game day. The raid size SHALL be the size multiplier of the size class times the Yearly player raid level, in squads. The size class SHALL be picked at random between small, medium and large with the multipliers 1, 2 and 3 (`size_multipliers`), unless the settings menu fixed it. At level 0 the mod SHALL plan and spawn no yearly raid.

#### Scenario: A medium raid at difficulty 2
- **WHEN** the raid day arrives for a medium raid at the yearly level 2
- **THEN** the raid has 4 squads (2 x 2)
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`LevelTests`).

#### Scenario: A forced raid
- **WHEN** a test calls `invasion_force_next` after the plan exists
- **THEN** the raid spawns at the next check, and a second call is refused because the raid was spawned
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: The yearly level is 0
- **WHEN** the yearly level is 0 and a game year passes
- **THEN** no yearly raid is planned or spawned and no banner shows
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`LevelTests`).

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
With `roles.lord_army.enabled` (default on), the mod SHALL spawn a role raid as the army of the AI lord `Hussite Raiders`, at war with the player, with its battlefield at the player manor. The anchor SHALL be the player manor. If the player has no manor, the anchor SHALL be the average location of the buildings in the player home region. The anchor SHALL NOT depend on the camera. If that fails before any army exists, the mod SHALL spawn bandit squads instead. If it fails after some armies exist, the mod SHALL NOT spawn bandit squads on top, and SHALL try again on the next daily step.

#### Scenario: A lord raid
- **WHEN** a role raid spawns
- **THEN** the raid tracker reports `lord_raid = true`
- Checked by `mod/InvasionMod/scenarios/invasion/subjugation_raid.py`.

#### Scenario: A failure after a partial spawn
- **WHEN** the lord raid fails after some armies were spawned
- **THEN** no bandit squads are added
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: The player has a manor
- **WHEN** a role raid spawns and the player has a manor
- **THEN** the anchor is the location of the manor
- Checked by `mod/InvasionMod/scenarios/invasion/raid_anchor_manor.py` and `harness/tests/test_fakegame_harnessbattlefield.py`.

#### Scenario: The player has no manor
- **WHEN** a role raid spawns and the player has no manor
- **THEN** the anchor is the average location of the buildings in the home region
- Checked by `harness/tests/test_fakegame_harnessbattlefield.py`.

#### Scenario: The camera is over another region
- **WHEN** a role raid spawns while the camera is over a region that is not the home region
- **THEN** the anchor is the same as with the camera over the home region
- Checked by `mod/InvasionMod/scenarios/invasion/raid_anchor_manor.py` and `harness/tests/test_fakegame_harnessbattlefield.py`.

### Requirement: The player picks the difficulty once
The mod SHALL keep three levels from 0 to 3, one for each raid type: yearly, great and vassal (default 2 each, `invasion.levels`). The player SHALL choose them in the scenario start menu of `mod/scenario_settings`. There is no global difficulty. `invasion_set_difficulty` SHALL set all three levels to one value from 0 to 3 at any time, and a new command SHALL set one level. `invasion_pick_difficulty` SHALL stay as a test command that sets the levels once. It SHALL be refused after the first pick, after the first raid spawned, and for a value outside 0 to 3. A change SHALL re-plan the squads of an unspawned raid of that type.

#### Scenario: A pick at difficulty 2
- **WHEN** no pick was made and a test picks the level 2 for all three types, and later sets yearly 1, great 3 and vassal 0
- **THEN** the yearly raid has the squads of level 1, the great raid has 3 waves, and no vassal raid is planned
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`LevelTests`); real game runs `levels-invasion-difficulty-pick-1`, `levels-pick-d1-1` and `levels-pick-d3-1` passed.

#### Scenario: A bad level
- **WHEN** a test sets a level to 4
- **THEN** the command is refused and the levels do not change
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`DifficultyTests`).

#### Scenario: The settings menu sets the difficulty
- **WHEN** the player begins the game with yearly 3, great 0 and vassal 1 in the settings menu
- **THEN** the three levels are 3, 0 and 1 and chosen is true, and no pick banner shows
- **AND** `invasion_set_difficulty` 1 afterwards sets all three levels to 1
- Checked by `harness/tests/test_fakegame_scenario_settings.py`; real game run `levels-newgame-1` passed.

#### Scenario: No difficulty banner
- **WHEN** a game runs 30 game days with no pick and with no settings applied
- **THEN** no banner about the difficulty shows and the log has no `INVASION difficulty prompt` event
- Checked by `harness/tests/test_fakegame_invasion.py`.

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
The mod SHALL start the great raid clock on the first daily step. The clock SHALL end at the first day of game year `great_raid.start_year` (default 10). The settings `min_days`, `max_days` and `banner_every_days` SHALL be removed. The end day SHALL be kept in ModState. The mod SHALL show one clock warning banner on the first day of each of the 3 game years before the start year (default years 7, 8 and 9), with the years left (`Great raid in N years`). It SHALL NOT show a clock banner in any other year, including the start year, SHALL NOT repeat a banner after a load in the same year, and SHALL show none when "Great raids" is Off.

#### Scenario: The clock after the start
- **WHEN** the clock starts and three game days pass
- **THEN** the end day is the first day of game year 10 and does not change
- **AND** the days left fall by the days that passed
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_clock.py`.

#### Scenario: Three warnings
- **WHEN** a test moves the fake game calendar through game years 1 to 10
- **THEN** exactly 3 clock banners show, on the first day of years 7, 8 and 9, with 3, 2 and 1 years left
- **AND** no clock banner shows in years 1 to 6 or in year 10
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: A load does not repeat the banner
- **WHEN** the game is loaded in a year whose clock banner was shown
- **THEN** no second clock banner shows in that year
- Checked by `harness/tests/test_fakegame_invasion.py`.

### Requirement: The great raid starts with waves
When the clock ends, the mod SHALL spawn one wave for each Great raid level point. Each wave SHALL have `wave_squads` (default 15) squads. Waves SHALL be `wave_gap_days` (default 10) game days apart. The mod SHALL NOT spawn a wave twice. At level 0 the mod SHALL NOT start the clock or spawn waves.

#### Scenario: The first wave at difficulty 1
- **WHEN** a test forces the clock to end at the great level 1
- **THEN** wave 1 has 15 squads and exactly 1 wave spawns
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py` (real game run `levels-great-raid-waves-4` passed, INVASION_DIFFICULTY=1).

### Requirement: A relief army and a final battle end the great raid
`relief_delay_days` (default 10) game days after the last wave, the mod SHALL spawn the relief army on the player side (15, 8 or 0 squads at the Great raid level 1, 2 or 3) and a hostile final army of `final_squads` (default 25) squads, not scaled by the level. When the final army is dead, the phase SHALL become `won`.

#### Scenario: The relief army and the final army at difficulty 1
- **WHEN** the wait after the last wave is over at the great level 1
- **THEN** the relief army has 15 squads and the final army has 25 squads
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py` (real game run `levels-great-raid-waves-4` passed, INVASION_DIFFICULTY=1).

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
A subjugation (major) raid SHALL be large: 3 x the Vassal raids level in squads. It SHALL be a lord raid that does not plunder and does not leave. The yearly roll SHALL pick the kind of the raid by the kind rules: the first yearly raid is a plunder raid, the second is the subjugation raid (once), and every later yearly raid is a plunder raid. At the Vassal raids level 0 the mod SHALL plan no subjugation raid and show no banner for it, and the kind rules give a plunder raid instead. It SHALL spawn once for each plan.

#### Scenario: The subjugation raid at difficulty 1
- **WHEN** the vassal level is 1 and the subjugation raid spawns
- **THEN** it has 3 squads
- **AND** the tracker shows `kind = subjugation`, no plunder and no leave reason within 12 game days
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`LevelTests`); real game run `levels-invasion-subjugation-raid-3` passed.

#### Scenario: Vassal level 0
- **WHEN** the vassal level is 0 and the first raid has ended
- **THEN** no subjugation raid is planned
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`LevelTests`).
