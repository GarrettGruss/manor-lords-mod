## 1. Facts first

- [ ] 1.1 Start one real new game from the main menu. Record how the mod sees a new game (`savefileToLoad`, the pawn, the intro) and how to pause and un-pause. Note in `notes/new-game-detection.md`. Verified by one real game run on one slot.
- [ ] 1.2 Read the game year length in game days. Note in `notes/year-length.md`. Verified by a bridge read in a game run.

## 2. Settings and rules

- [ ] 2.1 Register the new mod state keys (`first_raid_years`, `size_class_fixed`, `great_raids`, `settings_applied`) and the defaults in `config.lua`. Verified by `harness/tests/test_fakegame_scenario_settings.py`.
- [ ] 2.2 First raid delay from years: change `plan_rules.first_raid`. Verified by a fake game test and `scenarios/scenario_settings/first_raid_delay.py`.
- [ ] 2.3 Fixed size class. Verified by a fake game test.
- [ ] 2.4 Great raids switch. Verified by a fake game test and `scenarios/scenario_settings/great_raids_off.py`.
- [ ] 2.5 `invasion_set_difficulty` marks the difficulty as chosen; no pick banner after the settings applied. Verified by a fake game test; `difficulty_pick.py` still passes.

## 3. Menu

- [ ] 3.1 Build the menu feature `scenario_settings` on the menu framework (#308), with PNG images in the pak, config text, four choice rows and two buttons. Verified by a fake game test and a real game run.
- [ ] 3.2 New game detection, pause until Begin, apply on Begin, no menu on load, defaults for an old save. Verified by a fake game test.
- [ ] 3.3 Missing asset: log, defaults, no pause. Verified by a fake game test.
- [ ] 3.4 Named commands `scenario_settings_skip`, `_set`, `_open`, `_state`. Verified by a fake game test.
- [ ] 3.5 Re-send `disable_autosave` after the intro and after Begin. Verified by a real game run (autosave period read back).
- [ ] 3.6 Remove the three difficulty buttons from the raid menu (F8) and their fake game tests and test scenarios. Verified by the fake game tests.

## 4. Real game runs (one save slot)

- [ ] 4.1 `new_game_menu.py`: new game, menu on screen, change the settings, Begin. Take pictures with `ctx.screenshot` (menu at the defaults, after changes, after Begin). Verified by the run summary.
- [ ] 4.2 `load_keeps_settings.py`: a guarded `save_game` after Begin with non-default values, then a load in a new run; the menu stays closed and the values are the same. Back up the save folder first and tell the user before the first real `save_game`.
- [ ] 4.3 Picture evidence: commit the pictures to `evidence/` (compressed, 1280x720 at most, about 1 MB in all) and list them in `evidence/README.md` with the test scenario and run id.

## 5. Close

- [ ] 5.1 Update the wiki (menu feature page), the skills that name test scenario setup (`harness-write-scenario`, `harness-mod-state`), and `CHANGELOG.md` under `Unreleased`. Verified by `wiki.py check`.
- [ ] 5.2 Run the full tests and `openspec validate add-scenario-settings-menu --strict`.
- [ ] 5.3 Archive as the last commit: `openspec archive add-scenario-settings-menu --yes`.
- [ ] 5.4 Fill the test results table in the implementation pull request (check, run id or test file, verdict, key number).
