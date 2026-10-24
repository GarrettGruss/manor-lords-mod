## 1. Spike
- [ ] 1.1 Find the fields for AI opponents count and off-map adversary in `currentGameSetup`; add them to `HarnessGameSetup` if missing. Use the results of spikes #430 and #416.
- [ ] 1.2 Confirm the dependency map: do Hussite raids spawn with no off-map adversary? Do vassals work with AI opponents 0? Write findings to `notes/`.

## 2. Code
- [ ] 2.1 Guard module: read at new game start, store in ModState, live check for old saves.
- [ ] 2.2 Menu: lock rows, show warnings; commands refuse locked values.
- [ ] 2.3 Start banner.

## 3. Tests
- [ ] 3.1 Fake-game tests `harness/tests/test_fakegame_game_settings_guard.py`.
- [ ] 3.2 Real runs on fixture `base` and fixture `playtest-noai`.
- [ ] 3.3 Pictures of the locked rows in `evidence/`.

## 4. Close
- [ ] 4.1 Update the Checked by lines, the wiki and skills.
- [ ] 4.2 `CHANGELOG.md` under Unreleased.
- [ ] 4.3 Archive: `openspec archive add-game-settings-guard --yes`.
