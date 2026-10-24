## RENAMED Requirements
<!-- Issue: #404 -->

- FROM: `### Requirement: The menu shows a background text and four settings`
- TO: `### Requirement: The menu shows a background text and the settings`

## MODIFIED Requirements

### Requirement: The menu shows a background text and the settings
The menu SHALL show a background text of the scenario, from a configurable value and not from fixed words in code. It SHALL show three level settings, each 0 (off), 1 (easy), 2 (medium) or 3 (hard): Yearly player raid, Great raid and Vassal raids. It SHALL also show First Hussite raid (after 1, 2 or 3 years) and Raid size (Small, Medium, Large). It SHALL NOT show a global Difficulty setting. It SHALL have the buttons "Use defaults" and "Begin the game". "Use defaults" SHALL set the three levels to 2, the first raid to 2 years and the size to Medium.

#### Scenario: The menu starts with the defaults
- **WHEN** the menu opens
- **THEN** the three levels are 2, the first raid is after 2 years and the size is Medium
- **AND** no Difficulty setting is shown
- Checked by `harness/tests/test_fakegame_scenario_settings.py` and `mod/InvasionMod/scenarios/scenario_settings/new_game_menu.py` (real game run `levels-newgame-1` passed).

#### Scenario: Use defaults resets the choices
- **WHEN** the player changed all settings and clicks "Use defaults"
- **THEN** the choices are the defaults again
- Checked by `harness/tests/test_fakegame_scenario_settings.py` and `mod/InvasionMod/scenarios/scenario_settings/new_game_menu.py` (real game run `levels-newgame-1` passed).

### Requirement: The Great raids setting can turn the great raid off
The Great raid level SHALL be 0 to 3. At level 0 the mod SHALL NOT start the great raid clock, SHALL show no clock banner, and SHALL NOT spawn waves, the relief army or the final army. At level 1 to 3 the great raid runs as in `mod/invasion` with that level as its difficulty. The yearly player raid and the vassal raids SHALL NOT change with this level.

#### Scenario: Great raids Off
- **WHEN** the Great raid level is 0 (Off) and 3 game days pass
- **THEN** no great raid end day exists and no clock banner shows
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (real game run `levels-scenario-settings-great-raids-off-1` passed).

### Requirement: Named commands skip the menu or choose values
The mod SHALL expose named commands for the harness. One command SHALL close the menu and apply all defaults ("skip"). One command SHALL set any of the settings (the three levels, First Hussite raid, Raid size) and apply them without the mouse. A level outside 0 to 3 SHALL be refused. Test scenarios SHALL use these commands. A test scenario MAY open the menu to test it. The harness SHALL still be able to change the levels at any time with `invasion_set_difficulty`, which sets all three levels.

#### Scenario: Skip the menu
- **WHEN** a test scenario calls the skip command in a new game
- **THEN** the menu is not on screen and the settings are the defaults
- Checked by `harness/tests/test_fakegame_scenario_settings.py`.

#### Scenario: Choose values by command
- **WHEN** a test scenario sets the levels 3, 0 and 1 by command
- **THEN** the state reads yearly 3, great 0 and vassal 1
- **AND** level 4 is refused
- Checked by `harness/tests/test_fakegame_scenario_settings.py`.
