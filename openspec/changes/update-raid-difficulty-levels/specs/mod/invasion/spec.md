## MODIFIED Requirements
<!-- Issue: #404 -->

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

### Requirement: The player picks the difficulty once
The mod SHALL keep three levels from 0 to 3, one for each raid type: yearly, great and vassal (default 2 each, `invasion.levels`). The player SHALL choose them in the scenario start menu of `mod/scenario_settings`. There is no global difficulty. `invasion_set_difficulty` SHALL set all three levels to one value from 0 to 3 at any time, and a new command SHALL set one level. `invasion_pick_difficulty` SHALL stay as a test command that sets the levels once. It SHALL be refused after the first pick, after the first raid spawned, and for a value outside 0 to 3. A change SHALL re-plan the squads of an unspawned raid of that type.

#### Scenario: A pick at difficulty 2
- **WHEN** no pick was made and a test picks the level 2 for all three types, and later sets yearly 1, great 3 and vassal 0
- **THEN** the yearly raid has the squads of level 1, the great raid has 3 waves, and no vassal raid is planned
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`LevelTests`); real game run of `mod/InvasionMod/scenarios/invasion/difficulty_pick.py` still open.

#### Scenario: A bad level
- **WHEN** a test sets a level to 4
- **THEN** the command is refused and the levels do not change
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`DifficultyTests`).

#### Scenario: The settings menu sets the difficulty
- **WHEN** the player begins the game with yearly 3, great 0 and vassal 1 in the settings menu
- **THEN** the three levels are 3, 0 and 1 and chosen is true, and no pick banner shows
- **AND** `invasion_set_difficulty` 1 afterwards sets all three levels to 1
- Checked by `harness/tests/test_fakegame_scenario_settings.py`; real game run of `mod/InvasionMod/scenarios/scenario_settings/new_game_menu.py` still open.

### Requirement: A subjugation raid is large and does not plunder
A subjugation (major) raid SHALL be large: 3 x the Vassal raids level in squads. It SHALL be a lord raid that does not plunder and does not leave. The yearly roll SHALL pick the kind of the raid by the kind rules: the first yearly raid is a plunder raid, the second is the subjugation raid (once), and every later yearly raid is a plunder raid. At the Vassal raids level 0 the mod SHALL plan no subjugation raid and show no banner for it, and the kind rules give a plunder raid instead. It SHALL spawn once for each plan.

#### Scenario: The subjugation raid at difficulty 1
- **WHEN** the vassal level is 1 and the subjugation raid spawns
- **THEN** it has 3 squads
- **AND** the tracker shows `kind = subjugation`, no plunder and no leave reason within 12 game days
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`LevelTests`); real game run of `mod/InvasionMod/scenarios/invasion/subjugation_raid.py` still open.

#### Scenario: Vassal level 0
- **WHEN** the vassal level is 0 and the first raid has ended
- **THEN** no subjugation raid is planned
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`LevelTests`).

### Requirement: The great raid starts with waves
When the clock ends, the mod SHALL spawn one wave for each Great raid level point. Each wave SHALL have `wave_squads` (default 15) squads. Waves SHALL be `wave_gap_days` (default 10) game days apart. The mod SHALL NOT spawn a wave twice. At level 0 the mod SHALL NOT start the clock or spawn waves.

#### Scenario: The first wave at difficulty 1
- **WHEN** a test forces the clock to end at the great level 1
- **THEN** wave 1 has 15 squads and exactly 1 wave spawns
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py` (it uses difficulty 1 today and will read the great level).

### Requirement: A relief army and a final battle end the great raid
`relief_delay_days` (default 10) game days after the last wave, the mod SHALL spawn the relief army on the player side (15, 8 or 0 squads at the Great raid level 1, 2 or 3) and a hostile final army of `final_squads` (default 25) squads, not scaled by the level. When the final army is dead, the phase SHALL become `won`.

#### Scenario: The relief army and the final army at difficulty 1
- **WHEN** the wait after the last wave is over at the great level 1
- **THEN** the relief army has 15 squads and the final army has 25 squads
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py` (it uses difficulty 1 today).

#### Scenario: The win
- **WHEN** the final army has no living unit
- **THEN** the phase is `won`
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.
