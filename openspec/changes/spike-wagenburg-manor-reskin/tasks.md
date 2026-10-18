## 1. Decisions

- [ ] 1.1 The owner answers questions 1, 2 and 7 of design.md on the issue. Verified by review of the issue comment.
- [ ] 1.2 If the owner says stop, record that in the issue and close it. Verified by review.

## 2. Open checks

- [ ] 2.1 Study an AI lord with a manor and a wall. Verified by a real game run and `notes/ai-manor.md`.
- [ ] 2.2 Check the per-manor reskin after a manor rebuild. Verified by a real game run (`probe-manor-wagenburg`) and a note.
- [ ] 2.3 Check save and load with the pak installed and removed, only through the guarded action `save_game`, after the owner approves and a fresh backup exists. Verified by a real game run and the launcher save guard.
- [ ] 2.4 Test a closed gate, defenders on the wall, wall damage and fire, and several rings. Verified by real game runs with ranges for crossings (bandits entering through the gate, 0 wall crossings).
- [ ] 2.5 Capture picture evidence of the wagon wall and the tent keep with `ctx.screenshot(name)` into `evidence/`. Verified by `evidence/README.md`.

## 3. Ship (only after task 1.1 says yes)

- [ ] 3.1 Make the models the owner asked for (gate, tower, taller wagon). Verified by picture evidence.
- [ ] 3.2 Add a mod feature that applies the reskin by named commands. No raw eval. Verified by fake game tests and a test scenario.
- [ ] 3.3 Write the delta spec with the issue comment. Verified by `openspec validate spike-wagenburg-manor-reskin --strict`.
- [ ] 3.4 Run the AES key grep on the diff before the commit that adds a pak. Verified by the grep result in the pull request.

## 4. Close

- [ ] 4.1 Move lasting engine facts into the wiki; update `CHANGELOG.md`. Verified by `wiki.py check` and review.
- [ ] 4.2 Fill the test results table of the implementation pull request. Verified by review.
