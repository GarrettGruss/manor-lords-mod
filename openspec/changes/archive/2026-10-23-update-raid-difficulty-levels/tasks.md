## 1. Check
- [x] 1.1 Find where the code reads the global difficulty (squads, roles, waves, relief army). Notes in `notes/difficulty-call-sites.md`.

## 2. Code
- [x] 2.1 Keep three levels (`yearly`, `great`, `vassal`) in ModState, each 0 to 3, default 2. Remove the global difficulty and the Great raids On or Off setting.
- [x] 2.2 Make each raid type read its own level. Level 0 plans no raid, spawns none and shows no banner or menu entry.
- [x] 2.3 Change the start menu widget: three level settings plus the kept settings. Update `make_scenario_settings_widget.py` (done: five rows, four choices) and the pak (done: `raidmenu_P.pak` rebuilt with the UE editor, headless).
- [x] 2.4 Change the named commands: set one level, set all three (`invasion_set_difficulty`), skip the menu.

## 3. Tests
- [x] 3.1 Fake game tests: each level 0 to 3 per type, level 0 off, defaults, saved levels, an old save gets the defaults.
- [x] 3.2 Update the test scenarios of `scenario_settings/` and `invasion/` (`difficulty_pick.py`, `great_raids_off.py`).
- [x] 3.3 Picture evidence of the new menu (`ctx.screenshot`) in `evidence/`.
- [x] 3.4 Run the full test set and `openspec validate update-raid-difficulty-levels --strict`.
- [x] 3.5 Real game runs, see `notes/real-game-runs.md`: new_game_menu, difficulty_pick (levels 1, 2, 3), great_raids_off, subjugation_raid, raid_widget, great_raid_clock and great_raid_waves passed. invasion-first-raid has no passing run (crash, see notes). load_keeps_settings is not verified (needs the first real `save_game`).

## 4. Close
- [x] 4.1 Update the wiki, the affected skills and `CHANGELOG.md`.
- [ ] 4.2 Archive the change as the last commit.
