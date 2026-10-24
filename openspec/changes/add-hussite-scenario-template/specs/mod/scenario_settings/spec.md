## ADDED Requirements
<!-- Issue: #451 -->

### Requirement: A sixth scenario template for the mod
The mod pak SHALL add one row to the game table `DT_GameSetupPresets`, so the "Scenario Templates" row of the New Game screen shows a 6th template titled "The Hussites Are Coming". The row SHALL set these game settings: End goal Growth, AI opponents 0, Off map adversary Absent, Raider frequency None, Initial bandit camps 0, Random bandit camp spawn limit 0, Starting season Spring, Starting supplies Standard, Royal tax None, Armament delivery No, Residential requirements Balanced, Food spoilage Standard, Approval Low penalty, Well placement Underground water and Weather Difficult. The five game templates SHALL stay unchanged.

#### Scenario: Six templates are shown
- **WHEN** the New Game screen opens with the mod pak installed
- **THEN** the "Scenario Templates" row shows six templates and the sixth is titled "The Hussites Are Coming"
- Not checked yet.

#### Scenario: Selecting the template applies the settings
- **WHEN** the player clicks the sixth template
- **THEN** the game settings and the settings list on the screen show the values listed above
- Not checked yet.

#### Scenario: A new game from the template opens the mod start menu
- **WHEN** a new game starts from the sixth template
- **THEN** the mod scenario settings menu opens and pauses the game as for any new game
- Not checked yet.

### Requirement: The mod knows when its template was chosen
At new game start the mod SHALL store in ModState whether the game was started from the Hussite template, when the choice can be detected from the game setup. The mod SHALL NOT call a save function to do this.

#### Scenario: The marker follows the template
- **WHEN** a new game starts from the sixth template, and another new game starts from a game template
- **THEN** the stored marker is true in the first game and false in the second
- Not checked yet.
