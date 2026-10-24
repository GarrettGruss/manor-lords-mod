## ADDED Requirements
<!-- Issue: #438 -->

### Requirement: The vassals guard value is a mod setting saved in ModState
At new game start, the mod SHALL read the game setup once and SHALL save one mod setting in ModState: `vassals` (true/false: false when AI opponents (`numGenericAILords`) is 0, else true). The setting SHALL stay over save and load, and the menu SHALL read it. The mod SHALL NOT save a setting for the off-map adversary or for bandit camps: the mod makes the bandit pawn itself (change `update-banditry-bandit-camp`) and its Hussite raids are mod-made AI lord armies.

#### Scenario: A new game stores the setting from the game setup
- **WHEN** a new game starts with AI opponents 2
- **THEN** ModState holds `vassals` true
- Checked by `harness/tests/test_fakegame_game_settings_guard.py`.

#### Scenario: AI opponents 0 disables vassals
- **WHEN** a new game starts with AI opponents 0
- **THEN** `vassals` is false
- Checked by `harness/tests/test_fakegame_game_settings_guard.py`.

#### Scenario: The setting stays over a load
- **WHEN** a save with the setting is loaded
- **THEN** the mod uses the saved value and does not read the game setup again
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` and the notes of the change (a real save and load was not run: `save_game` has not run in the real game yet).

### Requirement: An old save without the setting uses the live check
When a loaded save has no `vassals` setting, the mod SHALL use a live check and SHALL store the result in ModState. In the live check, `vassals` is false when no AI lord pawn exists.

#### Scenario: An old save uses the live check and stores it
- **WHEN** a save without the setting is loaded and no AI lord pawn exists
- **THEN** ModState holds `vassals` false
- **AND** the next load uses this stored value
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` and `mod/InvasionMod/scenarios/scenario_settings/game_settings_guard.py` on fixture `playtest-noai`.

### Requirement: AI opponents 0 warns that vassals are not enabled
When `vassals` is false, the menu SHALL show the warning "vassals are not enabled". The mod SHALL NOT lock a row for it.

#### Scenario: AI opponents 0 warns only
- **WHEN** the game was started with AI opponents 0 and the menu opens
- **THEN** the menu shows "vassals are not enabled" and no row is locked
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` and `mod/InvasionMod/scenarios/scenario_settings/game_settings_guard.py` on fixture `playtest-noai`.

### Requirement: Other game settings lock nothing
The mod SHALL NOT lock a menu row or refuse a command because of a game setting. This includes an absent off-map adversary: the Yearly player raid, Great raid and Vassal raids levels stay free.

#### Scenario: Off-map adversary absent locks nothing
- **WHEN** the game was started without the off-map adversary and the menu opens
- **THEN** no row is locked and no warning shows
- **AND** a command that sets Yearly player raid above 0 is accepted
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` and `mod/InvasionMod/scenarios/scenario_settings/game_settings_guard.py` on fixture `playtest-noai`.

#### Scenario: Normal settings lock nothing
- **WHEN** the game was started with AI opponents on
- **THEN** no row is locked and no warning shows
- Checked by `harness/tests/test_fakegame_game_settings_guard.py` and `mod/InvasionMod/scenarios/scenario_settings/game_settings_guard.py` on fixture `base`.
