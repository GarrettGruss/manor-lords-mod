## MODIFIED Requirements
<!-- Issue: #375 -->

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
