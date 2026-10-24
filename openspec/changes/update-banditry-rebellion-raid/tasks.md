## 1. Code
- [ ] 1.1 `config.lua` (`bandits`): `timer_days` 60, `leavers` becomes `rebellion_families` 5, add `rebellion_squads` 1. Keep `threshold`, `order_gain`, `tick_days`.
- [ ] 1.2 `world.leave`: remove families, create the Outlaws pawn only if missing (`spawnBanditCamp` and `addPawnRelations`), then `homeless_rebel` mode `home` at the first removed home.
- [ ] 1.3 Update `bandits_state`, telemetry and log fields (camps only when the pawn was created).

## 2. Tests
- [ ] 2.1 Fake-game tests in `harness/tests/test_fakegame_bandits.py` and `test_bandits_rules.py`: config values, squads at home, no camp when the pawn exists, pawn creation.
- [ ] 2.2 New test scenario `mod/InvasionMod/scenarios/bandits/rebellion_raid.py`, based on `harness/scenarios/probe_rebel_noai.py` (worktree `.claude/worktrees/rebel-noai`, do not edit it). It checks the spawn at the homes, a burn and the "enough looted" log.
- [ ] 2.3 Real runs on `playtest-noai` (and `base`): repeat rebellion, plunder for Outlaws squads, removal at the map edge. Write `notes/`.
- [ ] 2.4 Update `banditry_timer.py` for 60 days and the squad.

## 3. Close
- [ ] 3.1 Update the Checked by lines, the wiki and the affected skills.
- [ ] 3.2 `CHANGELOG.md` and `mod/InvasionMod/CHANGELOG.md` under Unreleased.
- [ ] 3.3 Pictures of the raid in `evidence/`.
- [ ] 3.4 Archive: `openspec archive update-banditry-rebellion-raid --yes`.
