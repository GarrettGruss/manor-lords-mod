## ADDED Requirements
<!-- Issue: #375 -->

### Requirement: The settings menu opens when a new game starts
When a new game starts, the mod SHALL open the scenario settings menu and SHALL keep the game paused until the player clicks "Begin the game". The mod SHALL NOT use, change or read the game's own new game menus or its Raider Frequency. The menu SHALL NOT open for a game loaded from a save.

#### Scenario: A new game opens the menu
- **WHEN** a new game has started and the intro is done
- **THEN** the menu is on screen and the game is paused
- **AND** after "Begin the game" the menu is closed and the game runs
- Not checked yet (planned: `mod/InvasionMod/scenarios/scenario_settings/new_game_menu.py`, with picture evidence).

#### Scenario: A loaded game does not open the menu
- **WHEN** a save loads that holds the settings
- **THEN** the menu does not open and the mod does not pause the game
- Not checked yet (planned: `mod/InvasionMod/scenarios/scenario_settings/load_keeps_settings.py`).

### Requirement: The menu shows a background text and four settings
The menu SHALL show a background text of the scenario, from a configurable value and not from fixed words in code. It SHALL show four settings: Difficulty (Easy, Normal, Hard), First Hussite raid (after 1, 2 or 3 years), Raid size (Small, Medium, Large) and Great raids (On, Off). It SHALL have the buttons "Use defaults" and "Begin the game". "Use defaults" SHALL set all four settings to their defaults: Normal, 2 years, Medium and On.

#### Scenario: The menu starts with the defaults
- **WHEN** the menu opens
- **THEN** the choices are Normal, 2 years, Medium and On
- **AND** the background text equals the configured text
- Not checked yet (planned: `harness/tests/test_fakegame_scenario_settings.py`).

#### Scenario: Use defaults resets the choices
- **WHEN** the player changed all four settings and clicks "Use defaults"
- **THEN** the choices are Normal, 2 years, Medium and On again
- Not checked yet (planned: `harness/tests/test_fakegame_scenario_settings.py`).

### Requirement: The menu follows the approved look
The menu SHALL follow the approved mockup (illuminated manuscript style, as the raid menu of #340). It MAY load PNG images at run time. If the images or the widget class cannot be loaded, the mod SHALL log a clear message, SHALL NOT raise an error, and SHALL apply the defaults so the game does not stay paused.

#### Scenario: The look matches the mockup
- **WHEN** the menu is on screen
- **THEN** a screenshot shows the title, the background text, the four settings and the two buttons in the mockup style
- Checked by review of the picture evidence (`ctx.screenshot`).

#### Scenario: A missing asset
- **WHEN** the widget class cannot be loaded
- **THEN** a log line names the missing asset, the defaults apply and the game runs
- Not checked yet (planned: `harness/tests/test_fakegame_scenario_settings.py`).

### Requirement: The settings are kept with the save
"Begin the game" SHALL store the four settings in the mod state, so they are saved with the game. When a save loads, the mod SHALL apply the stored settings again. A save without stored settings (made before this feature) SHALL get the defaults and SHALL NOT open the menu.

#### Scenario: A save keeps the settings
- **WHEN** a game began with Hard, 3 years, Large and Off, was saved with the guarded `save_game`, and loads in a new run
- **THEN** the difficulty is 3, the first raid delay is 3 years, the size class is Large and Great raids is Off
- **AND** the menu did not open
- Not checked yet (planned: `mod/InvasionMod/scenarios/scenario_settings/load_keeps_settings.py`, one save slot).

#### Scenario: An old save gets the defaults
- **WHEN** a save with no settings entries loads
- **THEN** the settings are the defaults and the menu does not open
- Not checked yet (planned: `harness/tests/test_fakegame_scenario_settings.py`).

### Requirement: A new game is told from a loaded save
The mod SHALL treat a game as new only when no save file was loaded and the mod state holds no "settings applied" entry. The mod SHALL decide this once, after the player pawn exists.

#### Scenario: The two cases
- **WHEN** the mod starts with an empty save file name and no entry
- **THEN** the game is new
- **AND** with a save file name, or with the entry, the game is loaded
- Not checked yet (planned: `harness/tests/test_fakegame_scenario_settings.py`).

### Requirement: The First Hussite raid setting sets the first raid day
The setting "First Hussite raid" (1, 2 or 3 years) SHALL set the first raid day to that many game years after the plan day, plus or minus a spread set in config (default 10 percent of the delay). This option is new. It replaces the fixed range `first_raid_days_min` and `first_raid_days_max` of `mod/invasion`. The warning time SHALL stay between `warning_days_min` and `warning_days_max` and never be longer than the wait.

#### Scenario: A delay of 2 years
- **WHEN** the setting is 2 years and the first daily step runs
- **THEN** the raid day is between 650 and 810 game days after the plan day
- **AND** the warning time is between 14 and 56 game days
- Not checked yet (planned: `mod/InvasionMod/scenarios/scenario_settings/first_raid_delay.py`; the game year length and the range are confirmed in the implementation change).

### Requirement: The raid size setting fixes the size class
The setting "Raid size" SHALL fix the size class of the first minor raid to Small, Medium or Large (multipliers 1, 2, 3 as today). The mod SHALL NOT pick the class at random after the player chose it.

#### Scenario: A fixed size class
- **WHEN** the setting is Large and the first raid is planned
- **THEN** the size class is Large in every run and the squads equal 3 times the difficulty
- Not checked yet (planned: `harness/tests/test_fakegame_scenario_settings.py`).

### Requirement: The Great raids setting can turn the great raid off
When "Great raids" is Off, the mod SHALL NOT start the great raid clock, SHALL show no clock banner, and SHALL NOT spawn waves, the relief army or the final army. The minor and subjugation raids SHALL NOT change. When it is On, the great raid runs as in `mod/invasion`.

#### Scenario: Great raids Off
- **WHEN** the setting is Off and 3 game days pass
- **THEN** no great raid end day exists and no clock banner shows
- Not checked yet (planned: `mod/InvasionMod/scenarios/scenario_settings/great_raids_off.py`).

### Requirement: Named commands skip the menu or choose values
The mod SHALL expose named commands for the harness. One command SHALL close the menu and apply all defaults ("skip"). One command SHALL set any of the four settings and apply them without the mouse. Test scenarios SHALL use these commands. A test scenario MAY open the menu to test it. The harness SHALL still be able to change the difficulty at any time with `invasion_set_difficulty`.

#### Scenario: Skip the menu
- **WHEN** a test scenario calls the skip command in a new game
- **THEN** the menu is not on screen and the settings are the defaults
- Not checked yet (planned: `harness/tests/test_fakegame_scenario_settings.py`).

#### Scenario: Choose values by command
- **WHEN** a test scenario sets Hard, 1 year, Small and Off by command
- **THEN** the state reads 3, 1 year, Small and Off
- Not checked yet (planned: `harness/tests/test_fakegame_scenario_settings.py`).
