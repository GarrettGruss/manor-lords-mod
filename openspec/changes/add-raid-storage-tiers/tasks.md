# Tasks

## 1. Decisions and spikes

- [ ] 1.1 Run the spike on how to read the battle marker position and the unit distance, and on removing goods from a store without a crash; verify with a real game run, and write `notes/baron-steal-spike.md`
- [ ] 1.2 Run the spike on whether a game raid reaches the manor store; verify with a real game run, and write `notes/game-raid-manor-spike.md`
- [ ] 1.3 (Stretch) Find the third, common tech branch and the way to add the Manor tech; verify with a real game run, and write `notes/manor-tech-spike.md`
- [ ] 1.4 Get the owner's answers to the open questions in `design.md`; verify by review of `design.md`

## 2. Code

- [ ] 2.1 Add the tier list, the steal threshold, the steal rate and the steal goals to the feature config and `rules.lua`; verify with fake game tests in `harness/tests/test_fakegame_raid_behavior.py`
- [ ] 2.2 Add the baron AI raid stealing (distance check, tier 1 only, goal stop); verify with fake game tests
- [ ] 2.3 (Stretch) Add the Manor tech and the manor storage unlock; verify with a fake game test, and with a pak build test if a pak is used

## 3. Test scenarios and pictures

- [ ] 3.1 Add `storage_tiers.py` and `baron_steal.py` in `mod/InvasionMod/scenarios/raid_behavior/`; verify with a real game run of each
- [ ] 3.2 (Stretch) Add `manor_storage_tech.py` and capture picture evidence of the tech and the manor storage with `ctx.screenshot(name)` into `evidence/`; verify by review of the pictures
- [ ] 3.3 Run `native_plunder.py` and `loot_return.py` again; verify that they pass

## 4. Docs and results

- [ ] 4.1 Update the wiki page for raids and `CHANGELOG.md`; verify with `wiki.py check`
- [ ] 4.2 Fill the test results table of the implementation pull request; verify by review
