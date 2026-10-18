## 1. Decisions

- [ ] 1.1 The owner answers question 1 and question 2 of design.md on the issue. Verified by review of the issue comment.
- [ ] 1.2 Record the decision in `proposal.md` and `design.md`. Verified by review.

## 2. Spikes (fixture `wall-u`, one launch at a time)

- [ ] 2.1 Try the planner functions with a manor selected. Write `notes/planner-wall-functions.md` with the calls, the values and the run id. Verified by a real game run.
- [ ] 2.2 Read the path grid properties before and after a planner wall is built. Verified by a real game run and a note.
- [ ] 2.3 Test a mod rule that slows or stops units at a wall line (poll `realPos`). Use an A/B test with at least 5 runs per side (skill `harness-ab-testing`). Verified by the suite result and a range check.
- [ ] 2.4 Look for any call that removes one wall piece. Verified by a real game run and a note.

## 3. Build the chosen route (only after task 1.2)

- [ ] 3.1 Add the named commands and Python wrappers. Verified by fake game tests in `harness/tests/`.
- [ ] 3.2 Add a test scenario: builders finish the wall and raiders are blocked. The THEN steps use ranges of crossings. Verified by 3 of 3 real runs.
- [ ] 3.3 Capture picture evidence of the wall and the blocked units with `ctx.screenshot(name)` into `evidence/`. Verified by `evidence/README.md`.
- [ ] 3.4 Write the delta spec for `harness/building-commands` with the issue comment. Verified by `openspec validate spike-blocking-wall-route --strict`.

## 4. Save and load

- [ ] 4.1 Test that the wall survives a save and a load, only through the guarded action `save_game`, after the owner approves and a fresh backup exists. Verified by a real game run and the launcher save guard.

## 5. Close

- [ ] 5.1 Move lasting engine facts from `notes/` into the wiki. Verified by `wiki.py check`.
- [ ] 5.2 Update `CHANGELOG.md` and the skill `harness-game-spike` if the method changed. Verified by review.
- [ ] 5.3 Fill the test results table of the implementation pull request. Verified by review.
