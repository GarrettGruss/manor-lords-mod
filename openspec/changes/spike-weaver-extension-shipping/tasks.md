## 1. Decisions

- [ ] 1.1 The owner answers questions 1 and 2 of design.md on the issue. Verified by review of the issue comment.
- [ ] 1.2 If the owner says stop, record that in the issue and close it. Verified by review.

## 2. Open checks

- [ ] 2.1 Check the plot panel text and icon for the weaver. Capture picture evidence with `ctx.screenshot(name)` into `evidence/`. Verified by `evidence/README.md` and a real game run.
- [ ] 2.2 Build the weaver on several plots. Check stocks over game days: wool to yarn and flax to linen at about 1 to 1. Verified by a real game run and ranges on the stocks.
- [ ] 2.3 Save and load round trip, only through the guarded action `save_game`, after the owner approves and a fresh backup exists. Verified by a real game run and the launcher save guard.
- [ ] 2.4 Check the shed texture after the spec 33 re-cook. Capture picture evidence into `evidence/`. Verified by `evidence/README.md`.

## 3. Ship (only after task 1.1 says yes)

- [ ] 3.1 Add a mod feature with named commands that set the job and the recipe after each load. No raw eval. Verified by fake game tests and a test scenario.
- [ ] 3.2 Add the `DT_Upgrades` row edit and the pak to the mod pack. Run the AES key grep on the diff. Verified by a real game run and the grep result.
- [ ] 3.3 Write the delta spec for the new feature with the issue comment. Verified by `openspec validate spike-weaver-extension-shipping --strict`.

## 4. Close

- [ ] 4.1 Move lasting engine facts into the wiki; update `CHANGELOG.md`. Verified by `wiki.py check` and review.
- [ ] 4.2 Fill the test results table of the implementation pull request. Verified by review.
