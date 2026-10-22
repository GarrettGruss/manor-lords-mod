## 1. Tracker

- [ ] 1.1 Count a raider as living only while the game census counts it (`world.lua`, `rules.lua`).
- [ ] 1.2 Fake game test for a raider that left the census (`test_fakegame_raid_behavior.py`).

## 2. Removed requirements

- [ ] 2.1 Remove the bandit squad leave code (peace, quiet spot removal, war restore) and its config and fake game tests.
- [ ] 2.2 Remove the loot return code (`return_loot`, `fallback_good`, store search) and its config, fake game tests and the test scenario `loot_return.py`. Keep the departure count at `exit_y`.
- [ ] 2.3 Update the coverage data and the wiki pages that name the removed parts.

## 3. Test scenario

- [ ] 3.1 `native_plunder.py`: accept `left` or `destroyed`; require the leave line only for `left`; drop the loot, burn and population checks; keep a safety cap on game days so the run ends.
- [ ] 3.2 Real game runs: 3 runs of `raid-behavior-native-plunder` pass.

## 4. Close

- [ ] 4.1 Write the new Purpose (proposal) into `openspec/specs/mod/raid_behavior/spec.md`.
- [ ] 4.2 Full test set, `CHANGELOG.md` (Removed group), archive.
