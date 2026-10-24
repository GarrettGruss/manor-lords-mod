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

### Requirement: A setting that depends on an off game part is locked at 0 with a warning
When a game part is off, each mod setting that depends on it SHALL be 0 (off) and locked: the player cannot raise it in the menu, and a command SHALL refuse a value above 0 for it. Next to the locked value, the menu SHALL show a warning that names the part, for example "Locked: this game was started with bandit camps off". A lock SHALL NOT be removed in that game. The dependency map is in the proposal of this change. Entries marked "to confirm" SHALL follow the result of the spike.

#### Scenario: Bandit camps off warns
- **WHEN** the game was started with bandit camps 0 and limit 0 and the menu opens
- **THEN** the menu shows the warning "Locked: this game was started with bandit camps off"
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and `mod/InvasionMod/scenarios/scenario_settings/game_settings_guard.py` (proposed).

#### Scenario: AI opponents 0 locks the vassal level
- **WHEN** the game was started with AI opponents 0 and the menu opens
- **THEN** Vassal raids is 0 and locked, and a click or a command cannot raise it
- **AND** the warning names AI opponents
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real run on fixture `playtest-noai` (proposed).

#### Scenario: Normal settings lock nothing
- **WHEN** the game was started with bandit camps, AI opponents and the off-map adversary on
- **THEN** no row is locked and no warning shows
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed) and a real run on fixture `base` (proposed).

### Requirement: A banner at game start lists the switched-off parts
When at least one game part is off, the mod SHALL show a banner at game start that lists the switched-off parts. When all parts are on, the mod SHALL NOT show it.

#### Scenario: The banner lists the parts
- **WHEN** a game starts with bandit camps and AI opponents off
- **THEN** the banner names both
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` (proposed).
