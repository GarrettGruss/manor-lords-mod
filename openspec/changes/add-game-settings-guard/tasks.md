## 1. Spike
- [ ] 1.1 Find the fields for AI opponents count and off-map adversary in `currentGameSetup`; add them to `HarnessGameSetup` if missing. Use the results of spikes #430 and #416.
- [ ] 1.3 Confirm in the real game that `hussites_enabled` maps to the off-map adversary field (for example `adversary_baron`): read its value with Off Map Adversary Present and Absent (use spike #430 and #416 data). Write findings to `notes/`.
- [ ] 1.2 Confirm in the playtest-noai world that Hussite raids do not work with the off-map AI off (spike #430 Q3). The lock rule is decided either way. Write findings to `notes/`.

## 2. Code
- [ ] 2.1 Guard module: read once at new game start, save `vassals` and `hussites_enabled` in ModState, live check for old saves (stores the result).
- [ ] 2.2 Menu: lock rows, show warnings; commands refuse locked values.

## 3. Tests
- [ ] 3.1 Fake-game tests `harness/tests/test_fakegame_game_settings_guard.py`.
- [ ] 3.2 Real runs on fixture `base` and fixture `playtest-noai`.
- [ ] 3.3 Pictures of the locked rows in `evidence/`.

## 4. Close
- [ ] 4.1 Update the Checked by lines, the wiki and skills.
- [ ] 4.2 `CHANGELOG.md` under Unreleased.
- [ ] 4.3 Archive: `openspec archive add-game-settings-guard --yes`.
