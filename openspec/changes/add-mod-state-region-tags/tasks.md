# Tasks

## 1. Spikes

- [ ] 1.1 Take the limit numbers (entry count, entry length, save and load time) from the change `spike-mod-state-limits`, which runs that test; verify that its `notes/` hold the numbers before 2.1 starts
- [ ] 1.2 Run the region spike (region Tags after a settle and a loss of the region); verify with a real game run, and write `notes/region-tags.md`
- [ ] 1.3 Fill the open questions of `design.md` from the notes and set the time budget; verify by review

## 2. Code

- [ ] 2.1 Add the region owner to `ModState.open` and the limit check; verify with fake game tests in `harness/tests/test_fakegame_mod_state_region.py`
- [ ] 2.2 Keep the rule that no code calls a save function; verify with `harness/tests/test_save_call_sites.py`

## 3. Test scenarios

- [ ] 3.1 Add `mod/InvasionMod/scenarios/mod_state/region_roundtrip.py` and `tags_limit.py`; verify with a real game run of each (harness save and load only through `save_game`)
- [ ] 3.2 Run `mod_state/roundtrip.py`, `two_saves.py` and `default_load.py` again; verify that they pass

## 4. Docs and results

- [ ] 4.1 Update the wiki page for mod state and `CHANGELOG.md`; verify with `wiki.py check`
- [ ] 4.2 Fill the test results table of the implementation pull request; verify by review
