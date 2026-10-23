## MODIFIED Requirements
<!-- Issue: #400 -->

### Requirement: A daily banner counts down to the raid
The mod SHALL NOT show a countdown banner or a warning banner for a minor (yearly plunder) raid. The mod SHALL NOT show a banner before the raid spawns, on any game day. The warning time (`warning_days_min`, `warning_days_max`) and the second banner line with the days left to the great raid SHALL be removed for the minor raid. The banner at the spawn of a raid (`Raiders are here`) is not changed by this requirement. The subjugation raid keeps its warning banner (see the open question in the proposal).

#### Scenario: The countdown
- **WHEN** a minor raid is planned and the game days run from the plan day to the raid day
- **THEN** no countdown banner shows on any of these days
- **AND** the log has no `INVASION banner` event
- Checked by `harness/tests/test_fakegame_invasion.py` and `mod/InvasionMod/scenarios/invasion/first_raid.py`.

### Requirement: The player picks the difficulty once
The mod SHALL keep a difficulty from 1 to 3 (default `invasion.difficulty`). The player SHALL choose it only in the scenario start menu of `mod/scenario_settings`, before the game starts. The mod SHALL NOT show any difficulty banner, in any state: the banner `Pick the difficulty: 1, 2 or 3` and the setting `prompt_every_days` SHALL be removed. `invasion_set_difficulty` SHALL set the difficulty at any time and SHALL mark it as chosen. `invasion_pick_difficulty` SHALL stay as a test command: it SHALL set the difficulty once, and it SHALL be refused after the first pick, after the first raid spawned, and for a value outside 1 to 3. A pick SHALL re-plan the squads of an unspawned raid.

#### Scenario: A pick at difficulty 2
- **WHEN** no pick was made and a test picks difficulty 2
- **THEN** `chosen` was false before and is true after, and the difficulty is 2
- **AND** a second pick is refused
- **AND** the relief army has 8 squads and the great raid has 2 waves
- **AND** the planned squads are a multiple of 2 between 1 and 3 times 2
- Checked by `mod/InvasionMod/scenarios/invasion/difficulty_pick.py`.

#### Scenario: No difficulty banner
- **WHEN** a game runs 30 game days with no pick and with no settings applied
- **THEN** no banner about the difficulty shows and the log has no `INVASION difficulty prompt` event
- Checked by `harness/tests/test_fakegame_invasion.py`.

### Requirement: A great raid clock counts the game days
The mod SHALL start the great raid clock on the first daily step. The clock length SHALL be a random whole number of game days between `great_raid.min_days` and `max_days` (default 1095 to 1825, 3 to 5 game years). The end day SHALL be kept in ModState. The mod SHALL show the clock banner at most twice in a game year: once at the start of spring and once at the start of fall (the season values of the game calendar, `TemporalComponent.Season`). It SHALL show at most one clock banner for a season change, SHALL NOT repeat it after a load in the same season, and SHALL NOT show it on the day the clock ends. The setting `banner_every_days` SHALL be removed. The banner text is the days-left text of the great raid clock.

#### Scenario: The clock after the start
- **WHEN** the clock starts and three game days pass
- **THEN** the clock length is between 1095 and 1825 game days
- **AND** the end day does not change and the days left fall by the days that passed
- **AND** each clock banner shows the days left of its day
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_clock.py`.

#### Scenario: Two clock banners a year
- **WHEN** a test moves the fake game calendar through 3 game years of season changes
- **THEN** exactly 6 clock banners show: one at each spring start and one at each fall start
- **AND** no clock banner shows at the summer or winter start
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: A load does not repeat the banner
- **WHEN** the game is loaded in a season whose clock banner was shown
- **THEN** no second clock banner shows in that season
- Checked by `harness/tests/test_fakegame_invasion.py`.
