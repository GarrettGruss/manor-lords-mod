## 1. Spike and decisions
- [x] 1.1 Old registry with loyalty and a submitted vassal is ignored (design question 4). Done in a fake-game test (`OldSaveTests` in `test_fakegame_vassals.py`) instead of a real game run, because ModState ignores unknown keys by design. See `notes/old-save-registry.md`.
- [x] 1.2 Owner answers (chat, 2026-10-21): 1 drop the gift order; 2 Trade Pacts keeps only `tribute_share` +0.25; 3 remove the loyalty text from `design/mod/invasion-mod.md` and `design/mod/decisions.md`.

## 2. Code
- [x] 2.1 Remove loyalty, gift, submission and the raid protection change from `vassals` and `tribute`, and their config keys; add `tribute.share`; verify with `test_fakegame_vassals.py` and `test_fakegame_tribute.py`.
- [x] 2.2 Remove the effect kind `vassal_loyalty` and `vassal_loyalty_bonus` from `tech_tree` and the effect from `tree.json`; verify with `test_fakegame_laws.py` and `test_fakegame_tech_tree.py`.
- [x] 2.3 Remove the commands `vassals_set_loyalty`, `vassals_loyalty_tick_now`, `vassals_order_gift` and `vassals_submission_tick_now`; verify with `harness/tests/lua_syntax.py` and the fake game tests.

## 3. Test scenarios
- [x] 3.1 Update or remove the test scenarios named in the proposal (row 13). Updated; `tribute-protection-and-loyalty` removed. Not run in the real game (no game run in this implementation pass). Update the "Checked by" lines.

## 4. Close
- [x] 4.1 Update the wiki page `docs/wiki/architecture/invasion-features.md`, the Purpose lines of `mod/vassals` and `mod/tribute` (done by the archive merge of the delta specs), the skills that name the removed commands (none do), the changelogs and the loyalty text in `design/mod/`; verify with `wiki.py check`.
- [ ] 4.2 Run the full tests and write the test results table of the implementation pull request.
