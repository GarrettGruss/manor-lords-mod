## ADDED Requirements
<!-- Issue: #438 -->

### Requirement: The guard values are mod settings saved in ModState
At new game start, the mod SHALL read the game setup once and SHALL save two mod settings in ModState: `vassals` (true/false: false when AI opponents (`numGenericAILords`) is 0, else true) and `hussites_enabled` (true when the off-map adversary is present). `villager_banditry` is not a guard setting: the mod makes the bandit pawn itself (change `update-banditry-bandit-camp`). The settings SHALL stay over save and load, and the menu SHALL read them.

#### Scenario: A new game stores the settings from the game setup
- **WHEN** a new game starts with AI opponents 2, bandit camps 0 and limit 0, and the off-map adversary present
- **THEN** ModState holds `vassals` true and `hussites_enabled` true
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed).

#### Scenario: AI opponents 0 disables vassals
- **WHEN** a new game starts with AI opponents 0
- **THEN** `vassals` is false
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed).

#### Scenario: The settings stay over a load
- **WHEN** a save with the two settings is loaded
- **THEN** the mod uses the saved values and does not read the game setup again
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real load run (proposed).

### Requirement: An old save without the settings uses the live check
When a loaded save has no guard settings, the mod SHALL use a live check and SHALL store the result in ModState as the two settings. In the live check, `vassals` is false when no AI lord pawn exists. The live check SHALL NOT set `hussites_enabled` to false, unless the real-game spike shows a way to detect it.

#### Scenario: An old save uses the live check and stores it
- **WHEN** a save without the settings is loaded and no AI lord pawn exists
- **THEN** ModState holds `vassals` false
- **AND** the next load uses these stored values
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real run on fixture `playtest-noai` (proposed).

### Requirement: AI opponents 0 warns that vassals are not enabled
When `vassals` is false, the menu SHALL show the warning "vassals are not enabled". The mod SHALL NOT lock a row for it.

#### Scenario: AI opponents 0 warns only
- **WHEN** the game was started with AI opponents 0 and the menu opens
- **THEN** the menu shows "vassals are not enabled" and no row is locked
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real run on fixture `playtest-noai` (proposed).

### Requirement: Off-map adversary absent locks the Hussite raid levels
When `hussites_enabled` is false, the Yearly player raid, Great raid and Vassal raids levels SHALL be 0 and locked: the player cannot raise them, and a command SHALL refuse a value above 0. The menu SHALL show a warning next to each locked row. Vassal raids are Hussite raids in the code (the subjugation raid is a lord raid of the mod), so they are locked too. A lock SHALL NOT be removed in that game.

#### Scenario: Off-map adversary absent locks the Hussite raid levels
- **WHEN** the game was started without the off-map adversary and the menu opens
- **THEN** Yearly player raid, Great raid and Vassal raids are 0 and locked, each with a warning
- **AND** a command that sets one of them above 0 is refused
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real run on fixture `playtest-noai` (proposed).

### Requirement: Normal game settings lock nothing
When AI opponents and the off-map adversary are on, the menu SHALL lock no row and show no warning.

#### Scenario: Normal settings lock nothing
- **WHEN** the game was started with AI opponents and the off-map adversary on
- **THEN** no row is locked and no warning shows
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real run on fixture `base` (proposed).
