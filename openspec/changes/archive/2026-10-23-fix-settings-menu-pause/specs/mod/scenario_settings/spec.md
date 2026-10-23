## MODIFIED Requirements
<!-- Issue: #418 -->

### Requirement: The settings menu opens when a new game starts
When a new game starts, the mod SHALL open the scenario settings menu and SHALL keep the game paused for the whole time the menu is open, until the player clicks "Begin the game". This SHALL hold during and after the intro cinematic, and also when the harness (HarnessBoot) is absent, as in a normal player launch. If the game clock moves while the menu is open, the mod SHALL pause the game again. The mod SHALL NOT use, change or read the game's own new game menus or its Raider Frequency. The menu SHALL NOT open for a game loaded from a save.

#### Scenario: A new game opens the menu
- **WHEN** a new game has started and the intro is done
- **THEN** the menu is on screen and the game is paused
- **AND** after "Begin the game" the menu is closed and the game runs
- Checked by `mod/InvasionMod/scenarios/scenario_settings/new_game_menu.py` (run 20261022-045227-57f0; pictures: task 4.3 not done yet) and `harness/tests/test_fakegame_scenario_settings.py`.

#### Scenario: A player launch without the harness
- **WHEN** a new game starts from a normal launch with the menu open, and the intro cinematic ends
- **THEN** the game clock does not move until the player clicks "Begin the game"
- **AND** if the clock moves, the mod pauses the game again
- Checked by the new test scenario `mod/InvasionMod/scenarios/scenario_settings/player_launch_pause.py` (it disables the HarnessBoot pause) and the new fake-game test in `harness/tests/test_fakegame_scenario_settings.py`. Run 20261023-232209-eb8a (before the fix: 20261023-224512-647a). The test scenario also presses Space and 2 while the menu is open. Pictures: `evidence/`.

#### Scenario: A loaded game does not open the menu
- **WHEN** a save loads that holds the settings
- **THEN** the menu does not open and the mod does not pause the game
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (a loaded save does not open the menu or pause) and by the fixture runs of `scenario_settings/first_raid_delay.py` and `great_raids_off.py` (`savefileToLoad` is the slot name, the menu stays closed). The real load of a save with settings is `load_keeps_settings.py` (task 4.2, not run yet).
