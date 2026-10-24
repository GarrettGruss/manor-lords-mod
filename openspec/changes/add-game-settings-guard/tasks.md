## 1. Spike
- [ ] 1.1 Confirm that `numGenericAILords` is in `currentGameSetup` and that `HarnessGameSetup` reads it. Use the results of spikes #430 and #416. Write findings to `notes/`.

## 2. Code
- [ ] 2.1 Guard module: read once at new game start, save `vassals` in ModState, live check for old saves (stores the result).
- [ ] 2.2 Menu: show the warning "vassals are not enabled" when `vassals` is false. No lock.

## 3. Tests
- [ ] 3.1 Fake-game tests `harness/tests/test_fakegame_game_settings_guard.py`.
- [ ] 3.2 Real runs on fixture `base` and fixture `playtest-noai`.
- [ ] 3.3 Picture of the warning in `evidence/`.

## 4. Close
- [ ] 4.1 Update the Checked by lines, the wiki and skills.
- [ ] 4.2 `CHANGELOG.md` under Unreleased.
- [ ] 4.3 Archive: `openspec archive add-game-settings-guard --yes`.
