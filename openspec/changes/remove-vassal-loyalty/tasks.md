## 1. Spike and decisions
- [ ] 1.1 Load an old fixture save with loyalty and a submitted vassal in the registry, with the loyalty fields ignored (design question 4). Verify with a real game run. Write `notes/old-save-registry.md`.
- [ ] 1.2 Ask the owner for the answers to design questions 1, 2 and 3. Verify by review.

## 2. Code
- [ ] 2.1 Remove loyalty, gift, submission and the raid protection change from `vassals` and `tribute`, and their config keys; add `tribute.share`; verify with `test_fakegame_vassals.py` and `test_fakegame_tribute.py`.
- [ ] 2.2 Remove the effect kind `vassal_loyalty` and `vassal_loyalty_bonus` from `tech_tree` and the effect from `tree.json`; verify with `test_fakegame_laws.py` and `test_fakegame_tech_tree.py`.
- [ ] 2.3 Remove the commands `vassals_set_loyalty`, `vassals_loyalty_tick_now`, `vassals_order_gift` and `vassals_submission_tick_now`; verify with `harness/tests/lua_syntax.py` and the fake game tests.

## 3. Test scenarios
- [ ] 3.1 Update or remove the test scenarios named in the proposal (row 13); verify with real game runs. Update the "Checked by" lines.

## 4. Close
- [ ] 4.1 Update the wiki page `docs/wiki/architecture/invasion-features.md`, the Purpose lines of `mod/vassals` and `mod/tribute`, the skills that name the removed commands, and the changelogs; verify with `wiki.py check`.
- [ ] 4.2 Run the full tests and write the test results table of the implementation pull request.
