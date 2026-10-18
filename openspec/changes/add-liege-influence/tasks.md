# Tasks

## 1. Decisions

- [ ] 1.1 Get the user's answers to the open questions in `design.md` (start of the backlog feature, what the player sends, cap, rate); verify by review of `design.md`

## 2. Code

- [ ] 2.1 Add the feature folder `liege_influence` (config, rules, commands `liege_state`, `liege_send_tribute`) that requires `mod_state` and `tribute`; verify with fake game tests in `harness/tests/test_fakegame_liege_influence.py`
- [ ] 2.2 Check that no code calls a save function; verify with `harness/tests/test_save_call_sites.py`

## 3. Test scenarios

- [ ] 3.1 Add `influence_roundtrip.py` and `send_tribute.py` in `mod/InvasionMod/scenarios/liege_influence/`; verify with a real game run of each
- [ ] 3.2 Run the `tribute` and `mod_state` test scenarios again; verify that they pass

## 4. Docs and results

- [ ] 4.1 Update the wiki, `CHANGELOG.md` and the living spec `mod/liege_influence`; verify with `wiki.py check` and `openspec validate --strict`
- [ ] 4.2 Fill the test results table of the implementation pull request; verify by review
