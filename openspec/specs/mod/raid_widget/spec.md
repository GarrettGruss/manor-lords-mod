# mod/raid_widget Specification

## Purpose
The raid_widget feature shows all raid information in one menu that the player opens with a key. The player can pick the difficulty in it. It needs the pak `raidmenu_P.pak`.

## Requirements

### Requirement: F8 opens and closes the raid menu
The mod SHALL open the raid menu when the player presses the key `raid_widget.toggle_key` (default F8) and it is closed, and close it when it is open. The key callback SHALL only set a flag. The scheduler tick on the game thread SHALL do the toggle.

#### Scenario: The player presses F8 twice
- **WHEN** the menu is open and the player presses F8, then presses F8 again
- **THEN** the menu is closed after the first press and open after the second press
- Checked by `mod/InvasionMod/scenarios/invasion/raid_widget.py`.

### Requirement: The menu shows five raid lines in a fixed order
The menu SHALL show five text lines in this order: `Next raid`, `Size estimate`, `Great raid`, `Difficulty` and `Terms`. The lines SHALL equal the current mod state and SHALL refresh on each scheduler tick (`poll_ms`, default 50 ms).

#### Scenario: The menu opens on a new game
- **WHEN** the menu opens and the difficulty is not picked yet
- **THEN** the widget is in the viewport
- **AND** the shown lines equal the wanted lines, in the order of the five names
- **AND** the difficulty line ends with `(not picked yet)`
- Checked by `mod/InvasionMod/scenarios/invasion/raid_widget.py`.

### Requirement: The line texts follow fixed rules
`Next raid` SHALL show `in N days` or `today`, or `not planned yet`. `Size estimate` SHALL show `about R raiders (S squads)` or `not known yet`. `Great raid` SHALL show the days left, `wave W of N`, `final battle`, `won`, or `clock not started`. `Difficulty` SHALL show the value and `(not picked yet)` before a pick. `Terms` SHALL show `not in this game` when the terms feature is off.

#### Scenario: A raid in 12 days with 54 raiders
- **WHEN** the info has 12 days left, 54 raiders and 3 squads
- **THEN** the lines are `Next raid: in 12 days` and `Size estimate: about 54 raiders (3 squads)`
- Checked by `harness/tests/test_fakegame_raid_widget.py`.

#### Scenario: The great raid phases
- **WHEN** the great raid is in wave 2 of 3, in the final battle, or won
- **THEN** the line reads `Great raid: wave 2 of 3`, `Great raid: final battle` or `Great raid: won`
- Checked by `harness/tests/test_fakegame_raid_widget.py`.

#### Scenario: An open offer of terms
- **WHEN** the terms feature has an offer of 200 silver or 60 silver a year
- **THEN** the line reads `Terms: offered, 200 silver or vassalage (60 a year)`
- Checked by `harness/tests/test_fakegame_raid_widget.py`.

### Requirement: A missing pak gives a clear message
If the widget class cannot be loaded, `raid_widget_open` SHALL return `ok = false` with a message that names the pak `raidmenu_P.pak`, and SHALL NOT raise an error.

#### Scenario: The pak is not installed
- **WHEN** a test calls `raid_widget_open` without the pak
- **THEN** the answer has `ok = false` and a non-empty error text
- Checked by `harness/tests/test_fakegame_raid_widget.py`.

### Requirement: Named commands open, close and show the menu
The mod SHALL offer `InvasionMod.raid_widget_open`, `raid_widget_close` and `raid_widget_state`. The state SHALL return whether the menu is open and in the viewport, the shown lines, the wanted lines, the buttons, the pick count and the last error.

#### Scenario: The state before the menu opens
- **WHEN** a test calls `raid_widget_state` with the menu closed
- **THEN** the wanted lines have five entries and the first starts with `Next raid`
- Checked by `harness/tests/test_fakegame_raid_widget.py`.

### Requirement: The raid menu lists the upcoming raids
The raid menu SHALL list the upcoming raids all the time, not only on a banner. For the yearly (plunder) raid and the subjugation raid it SHALL show the type, the target (`you` or `your vassal <name>`), the size estimate and the days left, or `not planned yet`. The line of a raid type that is switched off (the subjugation raid off, or "Great raids" Off) SHALL be empty. The menu SHALL show no difficulty banner text.

#### Scenario: A planned raid is listed
- **WHEN** a subjugation raid is planned and the raid menu is open
- **THEN** its line shows the target, the size and the days left, and it updates when the days pass
- Checked by `harness/tests/test_fakegame_raid_widget.py` and `mod/InvasionMod/scenarios/invasion/raid_widget.py`.

#### Scenario: A switched-off raid type is not listed
- **WHEN** "Great raids" is Off
- **THEN** the great raid line is empty
- Checked by `harness/tests/test_fakegame_scenario_settings.py`.
