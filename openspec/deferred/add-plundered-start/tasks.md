# Tasks

## 1. Decisions and spikes

- [ ] 1.1 Run the share spike (several shares, check that the village stays playable for 10 game days); verify with a real game run, and write `notes/start-sack-shares.md`
- [ ] 1.2 Decide when the sack runs (first load or first game day) and how the flag stops a repeat; verify with a real game run, and write `notes/start-sack-timing.md`
- [ ] 1.3 Get the user's answer on the shares and on the start of this backlog feature; verify by review of `design.md`

## 2. Code

- [ ] 2.1 Add the feature folder `plundered_start` (config, rules, start-done flag) that requires `mod_state`; verify with fake game tests in `harness/tests/test_fakegame_plundered_start.py`
- [ ] 2.2 Check that no code calls a save function; verify with `harness/tests/test_save_call_sites.py`

## 3. Test scenarios and pictures

- [ ] 3.1 Add `start_sack.py` and `start_sack_once.py` in `mod/InvasionMod/scenarios/plundered_start/`; verify with a real game run of each
- [ ] 3.2 Capture picture evidence of the village before and after the sack (ruins, empty stores) with `ctx.screenshot(name)` into `evidence/`; verify by review of the pictures

## 4. Docs and results

- [ ] 4.1 Update the wiki, `CHANGELOG.md` and the living spec `mod/plundered_start`; verify with `wiki.py check` and `openspec validate --strict`
- [ ] 4.2 Fill the test results table of the implementation pull request; verify by review
