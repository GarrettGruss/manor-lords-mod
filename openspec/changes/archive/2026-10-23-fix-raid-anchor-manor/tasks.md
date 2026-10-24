## 1. Code
- [x] 1.1 `HarnessBattlefield`: flag `home`, anchor = player manor, else average of the home-region buildings.
- [x] 1.2 `lord_raid.start_checked` passes `home = true`.

## 2. Tests
- [x] 2.1 Fake-game tests (manor, no manor, camera in another region).
- [x] 2.2 Real runs on fixtures `base` and `playtest-noai` (camera over another region).
- [x] 2.3 Picture of the army at the manor in `evidence/`.

## 3. Close
- [x] 3.1 Update the Checked by lines, the wiki and `CHANGELOG.md`.
- [x] 3.2 Archive: `openspec archive fix-raid-anchor-manor --yes`.
