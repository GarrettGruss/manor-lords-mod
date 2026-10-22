## 1. Code
- [ ] 1.1 Add the year and season roll state to ModState and the yearly roll in `plan.lua`; remove the first-raid and subjugation wait ranges; verify with fake game tests in `harness/tests/test_fakegame_invasion.py`.
- [ ] 1.2 Add the setting `yearly.chance_by_season` to `config.lua`; verify with the fake game tests.

## 2. Tests
- [ ] 2.1 Update `first_raid.py`, `no_double_raid.py` and `subjugation_raid.py` to the new timing; verify with real game runs.
- [ ] 2.2 Add the test scenario `yearly_raid.py` (quiet first year, one raid in each later year); verify with a real game run. Update the "Checked by" lines in the spec.

## 3. Close
- [ ] 3.1 Update the wiki page of the invasion feature and `CHANGELOG.md`; verify with `wiki.py check`.
