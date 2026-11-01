## MODIFIED Requirements
<!-- Issue: #540 -->

### Requirement: The menu follows the approved look
The menu SHALL follow the game-menu style of the mockup `scenario-settings-game-style.html` (in `openspec/changes/update-scenario-settings-window-style/mockups/`; after the archive, in `openspec/specs/mod/scenario_settings/mockups/`). The layout is: a dark full background with a soft centre light, a centred title "The Hussites Are Coming" in spaced small capitals with a thin gold rule, and one dark panel with rough edges in two columns. The left column has a "The Scenario" heading bar and the background text. The right column has a "Settings" heading bar and the five rows (Yearly player raid, Great raid, Vassal raids, First Hussite raid, Raid size) with their options and defaults. Options are plain serif text: the selected option is gold and underlined, the others are grey. The bottom has "Use defaults" and a large "Begin the game". The framework's bottom Close SHALL NOT show on this menu, and the Esc key SHALL NOT close it: "Begin the game" is the only way out. If the images, the font or the widget class cannot be loaded, the mod SHALL log a clear message, SHALL NOT raise an error, and SHALL apply the defaults so the game does not stay paused. The menu SHALL NOT show a warning box about vassals (the mockup shows one; it was removed by the owner on 2026-11-01, because vassals work with AI opponents 0). The behavior of the settings does not change.

#### Scenario: The look matches the mockup
- **WHEN** the menu is on screen
- **THEN** a screenshot shows the dark background, the title with the gold rule, the two columns, the five setting rows and the two buttons in the mockup style
- **AND** the selected option of each row is gold and underlined, the others are grey, and no "> <" markers show
- **AND** no warning box shows, also in a game started with AI opponents 0
- Checked by review of the picture evidence (`ctx.screenshot`) in `mod/InvasionMod/scenarios/scenario_settings/new_game_menu.py`.

#### Scenario: No Close on the start screen
- **WHEN** the menu is open
- **THEN** no framework Close shows, the Esc key does not close the menu, and "Begin the game" closes it
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (the menu is registered without a Close button; Esc does nothing), `mod/InvasionMod/scenarios/scenario_settings/new_game_menu.py` and picture evidence.

#### Scenario: Other menus keep their Close
- **WHEN** another menu (for example the liege window) opens
- **THEN** the framework's bottom Close shows as before
- Checked by the fake-game tests of `core/menu.lua`.

#### Scenario: A missing asset
- **WHEN** the widget class cannot be loaded
- **THEN** a log line names the missing asset, the defaults apply and the game runs
- Checked by `harness/tests/test_fakegame_scenario_settings.py`.

### Requirement: Other game settings lock nothing
The mod SHALL NOT lock a menu row or refuse a command because of a game setting. This includes AI opponents 0 and an absent off-map adversary: the Yearly player raid, Great raid and Vassal raids levels stay free, and no warning shows.

#### Scenario: AI opponents 0 locks nothing and shows no warning
- **WHEN** the game was started with AI opponents 0 and the menu opens
- **THEN** no row is locked and no warning shows
- **AND** a command that sets all three raid levels to 3 is accepted
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`NoVassalsGuardTests`) and picture evidence.

#### Scenario: Off-map adversary absent locks nothing
- **WHEN** the game was started without the off-map adversary and the menu opens
- **THEN** no row is locked and no warning shows
- **AND** a command that sets Yearly player raid above 0 is accepted
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`NoVassalsGuardTests`).

#### Scenario: Normal settings lock nothing
- **WHEN** the game was started with AI opponents on
- **THEN** no row is locked and no warning shows
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`NoVassalsGuardTests`).

## REMOVED Requirements

### Requirement: The vassals guard value is a mod setting saved in ModState
**Reason**: Vassals work with AI opponents 0 (spike `spike-vassals-without-ai-opponents`, #543), so no guard value is needed.
**Migration**: None. The mod no longer reads the game setup for it. An old save may keep the unused key `vassals`.

### Requirement: An old save without the setting uses the live check
**Reason**: The guard value is removed, so there is nothing to check.
**Migration**: None.

### Requirement: AI opponents 0 warns that vassals are not enabled
**Reason**: Owner decision 2026-11-01: vassals work with AI opponents 0, so the warning is wrong and the box is removed.
**Migration**: None. The menu shows no warning.
