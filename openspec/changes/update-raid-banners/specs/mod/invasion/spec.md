## MODIFIED Requirements
<!-- Issue: #400 -->

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

## ADDED Requirements
<!-- Issue: #400 -->

### Requirement: The event banners show once, 30 days before
The mod SHALL show the great raid wave banner, the relief army banner and the victory banner once each, 30 game days before the event they announce: the start of a wave, the arrival of the relief army, and the final battle. If the event is planned less than 30 days ahead, the banner SHALL show once on the plan day. The mod SHALL NOT show a daily or repeated banner for these events, and SHALL NOT show them again after a load. The banner at the spawn of a raid is not changed.

#### Scenario: A wave is announced once
- **WHEN** a great raid wave is planned 60 game days ahead and the game days run to the wave day
- **THEN** exactly one wave banner shows, 30 days before the wave day
- **AND** a load after the banner does not show it again
- Not checked yet (planned: `harness/tests/test_fakegame_invasion.py`).

#### Scenario: A late plan
- **WHEN** the relief army is planned 10 game days ahead
- **THEN** its banner shows once on the plan day
- Not checked yet (planned: `harness/tests/test_fakegame_invasion.py`).
