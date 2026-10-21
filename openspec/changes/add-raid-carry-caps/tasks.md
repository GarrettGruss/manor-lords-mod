# Tasks

## 1. Spikes

- [x] 1.1 Write a value above the cap into `ItemsLooted` in a real raid and watch whether the raider keeps looting; verify with a real game run, and write `notes/loot-cap-spike.md`
- [x] 1.2 Decide where the raid type comes from for the tracker; verify by review of `design.md`

## 2. Code

- [x] 2.1 Add the caps by raid type to the feature config, `rules.lua` and `init.lua`; verify with fake game tests in `harness/tests/test_fakegame_raid_behavior.py` (replaced by 2.3 after the owner decision of 2026-10-20)
- [x] 2.2 Show the cap of each raid in `raid_behavior_state`; verify with a fake game test
- [ ] 2.3 Apply `carry_cap` to the plundered goods of Hussite raids only, stop writing `ItemsLooted` of native raids, and remove the bandit cap, and use `carry_cap` as the loot goal of a Hussite raid in the leave rule and the plunder tick; verify with fake game tests in `harness/tests/test_fakegame_raid_behavior.py`

## 3. Test scenarios

- [ ] 3.1 Add `mod/InvasionMod/scenarios/raid_behavior/carry_caps.py`; verify with a real game run
- [ ] 3.2 Run `native_plunder.py` and `loot_return.py` again; verify that they pass

## 4. Docs and results

- [x] 4.1 Update the wiki page for raids and `CHANGELOG.md`; verify with `wiki.py check`
- [ ] 4.2 Fill the test results table of the implementation pull request; verify by review
