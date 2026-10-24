## 1. Spike
- [x] 1.1 Fake-game kit: add `spawnBanditCamp` and `addPawnRelations` to the fake engine if missing.
- [x] 1.2 Real game: record where the camp appears and its distance from the village on `base` and `playtest-noai`. Write `notes/camp-place.md`.

## 2. Code
- [x] 2.1 `world.leave`: remove families, then one camp; create the pawn when missing; `addPawnRelations` after a new pawn.
- [x] 2.2 Remove `families_per_squad` from `bandits` in `config.lua` and from the leave path. Keep it for refugees.
- [x] 2.3 Update `bandits_state`/telemetry fields (squads becomes camps).

## 3. Tests
- [x] 3.1 Fake-game tests in `harness/tests/test_fakegame_bandits.py`.
- [x] 3.2 Test scenario `mod/InvasionMod/scenarios/bandits/banditry_timer.py` checks camp, pawn and families.
- [x] 3.3 Real runs on fixtures `base` and `playtest-noai`; a picture of the new camp in `evidence/`.

## 4. Close
- [x] 4.1 Update the Checked by lines, the wiki and skills.
- [x] 4.2 `CHANGELOG.md` and `mod/InvasionMod/CHANGELOG.md` under Unreleased.
- [ ] 4.3 Archive: `openspec archive update-banditry-bandit-camp --yes`.
