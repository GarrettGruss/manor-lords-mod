## 1. Decisions

- [ ] 1.1 The owner answers questions 1 and 2 of design.md on the issue. Verified by review of the issue comment.
- [ ] 1.2 If the owner says no, record that in the issue and close it. Verified by review.

## 2. Open checks

- [ ] 2.1 Place a new-row camp (host b) with the real mouse. Verified by a real game run (`place-building` method) and `notes/host-b-placement.md`.
- [ ] 2.2 Spawn bandit units at the camp centre and check they leave the ring. Verified by a real game run and `realPos` samples in a note.
- [ ] 2.3 Test a mix of tent camps and Wagenburg camps. Verified by a real game run and a note.
- [ ] 2.4 Check the camp texture after the spec 33 re-cook. Capture picture evidence with `ctx.screenshot(name)` into `evidence/`. Verified by `evidence/README.md`.

## 3. Ship (only after task 1.1 says yes)

- [ ] 3.1 Add the row 100 patch and the pak to the Invasion Mod pack. Verified by a real game run: bandit camp count in a range, bandit unit count equal to the control within a range.
- [ ] 3.2 Add a mod spawn command, a saved place list in ModState and a respawn on load for host c. Verified by fake game tests and a test scenario.
- [ ] 3.3 Write the delta spec for the owning feature with the issue comment. Verified by `openspec validate spike-wagenburg-bandit-camp --strict`.
- [ ] 3.4 Run the AES key grep on the diff before the commit that adds a pak. Verified by the grep result in the pull request.

## 4. Close

- [ ] 4.1 Move lasting engine facts into the wiki; update `CHANGELOG.md` and the mod changelog. Verified by `wiki.py check` and review.
- [ ] 4.2 Fill the test results table of the implementation pull request. Verified by review.
