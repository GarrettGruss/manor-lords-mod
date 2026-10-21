## 1. Spike
- [x] 1.1 Delete all villagers of a vassal region in the real game. Record what the AI does and how the mod can sack houses there (design questions 1 and 6). Verify with a real game run. Write `notes/empty-ai-village.md`.
- [x] 1.2 Raise the villager count of an emptied region to 5. Record whether the AI rebuilds and how long it takes (design question 2). Verify with a real game run. Write `notes/restore-to-five.md`.
- [ ] 1.3 Ask the owner for the gold cost and the answers to design questions 3, 4 and 5. Verify by review.

## 2. Code
- [ ] 2.1 Remove the fallback capital move, its commands and its test scenario; verify with the fake game tests and `harness/tests/lua_syntax.py`.
- [ ] 2.2 Remove `take_by_lord` and `vassals_set_loss_region`; verify with `test_fakegame_vassals.py`.
- [ ] 2.3 Add the sack of vassal houses and the 80 percent ruin check; verify with fake game tests.
- [ ] 2.4 Add the wipe (delete villagers, free the slot, record the wiped region); verify with fake game tests.
- [ ] 2.5 Set the refugee wave to 50 percent of the population; verify with `test_fakegame_refugees.py`.
- [ ] 2.6 Add the restore command with the gold cost and the tribute restart; verify with fake game tests.
- [ ] 2.7 Close open terms offers after a sack of the player region; verify with `test_fakegame_sack_and_terms.py`.

## 3. Test scenarios
- [ ] 3.1 Add or update the test scenarios (`loss_and_submission.py`, `refugee_wave.py`, `vassal_targets.py`, a new `vassal_wipe.py`); verify with real game runs. Update the "Checked by" lines.
- [ ] 3.2 Capture picture evidence of the village of rubble and of the rebuild into `evidence/` with `ctx.screenshot(name)`; list it in `evidence/README.md`.

## 4. Close
- [ ] 4.1 Update the wiki pages, the skills that name the removed commands, the Purpose lines of the changed living specs, and `CHANGELOG.md`; verify with `wiki.py check`.
- [ ] 4.2 Run the full tests and write the test results table of the implementation pull request.
