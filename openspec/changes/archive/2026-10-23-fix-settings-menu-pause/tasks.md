## 1. Investigate

- [x] 1.1 Run the real game with the HarnessBoot pause disabled. Log the game clock and the pause state when the menu opens, when the cinematic ends and after. Write the cause to `notes/pause-cause.md`.

## 2. Fix

- [x] 2.1 While the menu is open, poll the game clock on the game thread. If it moves, call the pause again and log a warning.
- [x] 2.2 Stop the poll when "Begin the game" is clicked or the defaults apply.

## 3. Tests

- [x] 3.1 Add fake-game tests to `harness/tests/test_fakegame_scenario_settings.py`: the clock moves while the menu is open, and the mod pauses again.
- [x] 3.2 Add the test scenario `mod/InvasionMod/scenarios/scenario_settings/player_launch_pause.py`. It disables the HarnessBoot pause and checks that the clock does not move until Begin.
- [x] 3.3 Run the full test set from CONTRIBUTING.md and `openspec validate fix-settings-menu-pause --strict`.

## 4. Real run and evidence

- [x] 4.1 Run `player_launch_pause.py` in the real game. Record the run id.
- [x] 4.2 Take a picture of the menu over a paused game. Put it in `evidence/` with an `evidence/README.md`.

## 5. Close

- [x] 5.1 Update `CHANGELOG.md` under `Unreleased` (Fixed).
- [x] 5.2 Update the affected wiki page and skill. Run `wiki.py check`.
- [ ] 5.3 Archive as the last commit: `openspec archive fix-settings-menu-pause --yes`.
