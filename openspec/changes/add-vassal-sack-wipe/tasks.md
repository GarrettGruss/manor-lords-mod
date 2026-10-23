## 1. Spike
- [x] 1.1 Delete all villagers of a vassal region in the real game. Record what the AI does and how the mod can sack houses there (design questions 1 and 6). Verify with a real game run. Write `notes/empty-ai-village.md`.
- [x] 1.2 Raise the villager count of an emptied region to 5. Record whether the AI rebuilds and how long it takes (design question 2). Verify with a real game run. Write `notes/restore-to-five.md`.
- [x] 1.3 Ask the owner for the gold cost and the answers to design questions 3, 4 and 5. Verify by review. Done: Q3 flat 100 silver, Q7 goods for the rebuild, Q8 fixed by #357 (owner, 2026-10-21). Q4 and Q5 use the design defaults; listed for the owner in the pull request. See `notes/owner-questions.md`.

## 2. Code
- [x] 2.1 Remove the fallback capital move, its commands and its test scenario; verify with the fake game tests and `harness/tests/lua_syntax.py`.
- [x] 2.2 Remove `take_by_lord` and `vassals_set_loss_region`; verify with `test_fakegame_vassals.py`.
- [x] 2.3 Add the sack of vassal houses and the 80 percent ruin check; verify with fake game tests.
- [x] 2.4 Add the wipe (delete villagers, free the slot, record the wiped region); verify with fake game tests.
- [x] 2.5 Set the refugee wave to 50 percent of the population; verify with `test_fakegame_refugees.py`.
- [x] 2.6 Add the restore command with the gold cost and the tribute restart; verify with fake game tests.
- [x] 2.7 Close open terms offers after a sack of the player region; verify with `test_fakegame_sack_and_terms.py`.

## 3. Test scenarios
- [x] 3.1 Add or update the test scenarios (`loss_and_submission.py`, `refugee_wave.py`, `vassal_targets.py`, a new `vassal_wipe.py`); verify with real game runs. Update the "Checked by" lines.
- [x] 3.2 Capture picture evidence of the village of rubble and of the rebuild into `evidence/` with `ctx.screenshot(name)`; list it in `evidence/README.md`.

## 4. Close
- [x] 4.1 Update the wiki pages, the skills that name the removed commands, the Purpose lines of the changed living specs, and `CHANGELOG.md`; verify with `wiki.py check`.
## 5. Rebuild order (owner decisions, 2026-10-22)
- [x] 5.1 Add `world.rebuild_ruins`, the wood removal at sack start, the give and rebuild at sack end, the handover and rebuild in the restore, the command `vassals_rebuild_ruins` and `vassals_end_sack`; verify with `test_fakegame_vassals.py`.
- [ ] 5.2 Update `vassal_wipe.py` and add a test scenario for a sack that ends without a wipe; verify with real game runs.
- [ ] 5.3 Move the engine facts (typeBeforeChange, SetupBuilding, convertBlueprintsToBuildings, AI rebuild) into the wiki; verify with `wiki.py check`.

- [x] 5.4 End a sack without a wipe when its raid ends (`raid_behavior.watch_end`); verify with `test_fakegame_vassals.py`.
- [ ] 5.5 Wipe in three polls (crash fix); verify with `test_fakegame_vassals.py` and four real runs of `vassals-wipe`, notes in `notes/wipe-crash.md`.

## 6. Final
- [ ] 6.1 Run the full tests and write the test results table of the implementation pull request.
