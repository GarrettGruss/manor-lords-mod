## ADDED Requirements
<!-- Issue: #438 -->

### Requirement: The mod reads the game setup and stores a guard result
At new game start, the mod SHALL read the game setup values for bandit camps (initial and maximum), AI opponents and the off-map adversary. It SHALL store the guard result in ModState: one flag for each part that is off. After a load, the mod SHALL use the stored result. When a save has no stored result, the mod SHALL use a live check: a bandit pawn exists (a pawn with isBandit true) for bandit camps, and AI lord pawns exist for AI opponents.

#### Scenario: A new game stores the result
- **WHEN** a new game starts with bandit camps 0 and limit 0
- **THEN** ModState holds "bandit camps off" and no other flag
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed).

#### Scenario: After a load the result stays
- **WHEN** a save with a stored result is loaded
- **THEN** the mod uses the stored result and does not read the game setup again
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed).

#### Scenario: An old save uses the live check
- **WHEN** a save without a stored result is loaded and no bandit pawn exists
- **THEN** the mod marks bandit camps as off
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real run on fixture `playtest-noai` (proposed).

### Requirement: Bandit camps off disables banditry and warns
When the game was started with bandit camps off (initial 0 and limit 0), the mod SHALL disable the banditry timer and the banditry leave. The scenario settings menu SHALL show a warning line, for example "Locked: this game was started with bandit camps off". The mod SHALL show no banner at game start.

#### Scenario: Bandit camps off disables banditry
- **WHEN** the game was started with bandit camps 0 and limit 0 and the menu opens
- **THEN** the menu shows the bandit camps warning line
- **AND** the banditry timer and leave are disabled
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and `mod/InvasionMod/scenarios/scenario_settings/game_settings_guard.py` (proposed).

### Requirement: AI opponents 0 warns that vassals are not enabled
When the game was started with AI opponents 0, the menu SHALL show the warning "vassals are not enabled". The mod SHALL NOT lock a row for it.

#### Scenario: AI opponents 0 warns only
- **WHEN** the game was started with AI opponents 0 and the menu opens
- **THEN** the menu shows "vassals are not enabled" and no row is locked
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real run on fixture `playtest-noai` (proposed).

### Requirement: Off-map adversary absent locks the Hussite raid levels
When the game was started without the off-map adversary, the Yearly player raid, Great raid and Vassal raids levels SHALL be 0 and locked: the player cannot raise them, and a command SHALL refuse a value above 0. The menu SHALL show a warning next to each locked row. Vassal raids are Hussite raids in the code (the subjugation raid is a lord raid of the mod), so they are locked too. A lock SHALL NOT be removed in that game.

#### Scenario: Off-map adversary absent locks the Hussite raid levels
- **WHEN** the game was started without the off-map adversary and the menu opens
- **THEN** Yearly player raid, Great raid and Vassal raids are 0 and locked, each with a warning
- **AND** a command that sets one of them above 0 is refused
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real run on fixture `playtest-noai` (proposed).

### Requirement: Normal game settings lock nothing
When bandit camps, AI opponents and the off-map adversary are on, the menu SHALL lock no row and show no warning.

#### Scenario: Normal settings lock nothing
- **WHEN** the game was started with bandit camps, AI opponents and the off-map adversary on
- **THEN** no row is locked and no warning shows
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real run on fixture `base` (proposed).
