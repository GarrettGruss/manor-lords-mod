## ADDED Requirements
<!-- Issue: #451 -->

### Requirement: A sixth scenario template for the mod
The mod pak SHALL add one row to the game table `DT_GameSetupPresets`, so the "Scenario Templates" row of the New Game screen shows a 6th template titled "The Hussites Are Coming". The five game templates SHALL stay unchanged.

#### Scenario: Six templates are shown
- **WHEN** the New Game screen opens with the mod pak installed
- **THEN** the "Scenario Templates" row shows six templates and the sixth is titled "The Hussites Are Coming"
- Checked by `mod/InvasionMod/scenarios/scenario_settings/hussite_template.py` (run `hussite-tpl-13`, check T1; pictures `evidence/t2-sixth-selected.jpg`, `t3-sixth-tooltip.jpg`).

#### Scenario: A new game from the template opens the mod start menu
- **WHEN** a new game starts from the sixth template
- **THEN** the mod scenario settings menu opens and pauses the game as for any new game
- Checked by `mod/InvasionMod/scenarios/scenario_settings/hussite_template.py` with `HUSSITE_CONTINUE=1` (run `hussite-tpl-13`, check T3; picture `evidence/t5-mod-start-menu.jpg`).

### Requirement: The template sets the game settings of the mod
Selecting the template SHALL set these game settings: End goal Growth, AI opponents 0, Off map adversary Absent, Raider frequency None, Initial bandit camps 0, Random bandit camp spawn limit 0, Starting season Spring, Starting supplies Standard, Royal tax None, Armament delivery No, Residential requirements Balanced, Food spoilage Standard, Approval Low penalty, Well placement Underground water and Weather Difficult.

#### Scenario: Selecting the template applies the settings
- **WHEN** the player clicks the sixth template
- **THEN** the game settings and the settings list on the screen show the values listed above
- Checked by `mod/InvasionMod/scenarios/scenario_settings/hussite_template.py` (run `hussite-tpl-13`, checks T2; pictures `evidence/t2-sixth-selected.jpg`, `t4-sixth-settings-list.jpg`).

### Requirement: The mod knows when its template was chosen
At new game start the mod SHALL store in ModState whether the game was started from the Hussite template, when the choice can be detected from the game setup. The mod SHALL NOT call a save function to do this.

#### Scenario: The marker follows the template
- **WHEN** a new game starts from the sixth template, and another new game starts from a game template
- **THEN** the stored marker is true in the first game and false in the second
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`HussiteTemplateMarkerTests`) and `mod/InvasionMod/scenarios/scenario_settings/hussite_template.py` (run `hussite-tpl-13`, check T3).

### Requirement: The new game decision is made for each game
The mod SHALL decide again whether a game is new or loaded after each game start or load in the same session, so a new game that follows a loaded game in one session opens the mod start menu.

#### Scenario: A new game after a load in one session
- **WHEN** a save was loaded, and the player goes to the main menu and starts a new game
- **THEN** the mod start menu opens and pauses the game
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`SecondGameInOneSessionTests`) and `mod/InvasionMod/scenarios/scenario_settings/hussite_template.py` with `HUSSITE_CONTINUE=1` (run `hussite-tpl-13`; the run started from a loaded fixture).
