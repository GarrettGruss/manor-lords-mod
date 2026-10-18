# Tasks

## 1. Decisions and spikes

- [ ] 1.1 Run the spike on a loss share per trip without a crash; verify with a real game run, and write `notes/store-loss-spike.md`
- [ ] 1.2 Get the user's list of guarded and open building types, the shares and the discount; verify by review of `design.md`
- [ ] 1.3 Run the spike on how to set the rebuild discount (Lua or pak row); verify with a real game run, and write `notes/ruin-rebuild-spike.md`

## 2. Code

- [ ] 2.1 Add the tier list and the loss share to the feature config and `rules.lua`; verify with fake game tests in `harness/tests/test_fakegame_raid_behavior.py`
- [ ] 2.2 Add the ruin rebuild discount; verify with a fake game test, and with a pak build test if a pak is used

## 3. Test scenarios and pictures

- [ ] 3.1 Add `storage_tiers.py` and `ruin_rebuild.py` in `mod/InvasionMod/scenarios/raid_behavior/`; verify with a real game run of each
- [ ] 3.2 Capture picture evidence of a burned building, the ruin and the rebuilt building with `ctx.screenshot(name)` into `evidence/`; verify by review of the pictures
- [ ] 3.3 Run `native_plunder.py` and `loot_return.py` again; verify that they pass

## 4. Docs and results

- [ ] 4.1 Update the wiki page for raids and `CHANGELOG.md`; verify with `wiki.py check`
- [ ] 4.2 Fill the test results table of the implementation pull request; verify by review
