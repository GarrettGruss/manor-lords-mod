## 1. Scenario

- [x] 1.1 Write the test scenario: open the tech tree menu, wait 300 s, read the state twice a second, assert state alive, then do 10 real single clicks and assert exactly 10 counted. Verified by 3 of 3 real runs.
- [ ] 1.2 Decide where the scenario runs (regular suite or a long suite). Verified by review.
- [x] 1.3 Change the "Not checked yet" line of the scenario "A menu stays open" in `mod/core` to name the new scenario (after #267 is merged). Verified by `openspec validate --all --strict`.

## 2. Clean source widget

- [ ] 2.1 Make a click button source without the leftover graph errors and rebuild the menu paks. Run the AES key grep on the diff. Verified by the existing scenarios `tech-tree-widget-clicks`, `tech-tree-widget` and `invasion-raid-widget` (10 of 10 clicks counted).
- [ ] 2.2 Capture picture evidence of both menus with `ctx.screenshot(name)` into `evidence/`. Verified by `evidence/README.md`.

## 3. Close

- [ ] 3.1 Update the wiki page for click hooks, `CHANGELOG.md` and the skill `harness-pak-mod` if the method changed. Verified by `wiki.py check` and review.
- [ ] 3.2 Fill the test results table of the implementation pull request. Verified by review.
