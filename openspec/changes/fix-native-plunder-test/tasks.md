## 1. Tracker

- [x] 1.1 Count a raider as living only while the game census counts it (`world.lua`, `rules.lua`).
- [x] 1.2 Fake game test for a raider that left the census (`test_fakegame_raid_behavior.py`).

## 2. Removed requirements

- [x] 2.1 Remove the bandit squad leave code (peace, quiet spot removal, war restore) and its config and fake game tests.
- [x] 2.2 Remove the loot return code (`return_loot`, `fallback_good`, store search) and its config, fake game tests and the test scenario `loot_return.py`. Keep the departure count at `exit_y`.
- [x] 2.3 Update the coverage data and the wiki pages that name the removed parts.

## 3. Test scenario

- [x] 3.1 `carry_caps.py`: assert at every sample that the tracker count of living raiders equals the census count, and that the raid ends `left` or `destroyed`. Remove the test scenario `native_plunder.py` and its coverage entries.
- [x] 3.2 Real game runs: 3 runs of the carry cap test scenario pass.

## 4. Close

- [x] 4.1 Write the new Purpose (proposal) into `openspec/specs/mod/raid_behavior/spec.md`.
- [ ] 4.2 Full test set, `CHANGELOG.md` (Removed group), archive.
