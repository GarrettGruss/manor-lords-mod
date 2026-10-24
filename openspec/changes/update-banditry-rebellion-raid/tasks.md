## 1. Code
- [ ] 1.1 `config.lua` (`bandits`): `timer_days` 60, `leavers` becomes `rebellion_families` 6, add `rebellion_squads` 1, `rebellion_weapons` 18, `rebellion_weapon_ids`. Keep `threshold`, `order_gain`, `tick_days`.
- [ ] 1.2 `world.leave`: weapon check first, then remove 18 weapons at random from homes, remove families, create the Outlaws pawn only if missing, then `homeless_rebel` mode `home` at the first removed home.
- [ ] 1.3 Weapon check and block: below 18 weapons, no rebellion, timer stays expired, retry next tick, telemetry `rebellion_blocked`.
- [ ] 1.4 Loot override module in `features/raid_behavior` (`set`, `get`, `take`, `clear_all`), key `GetAddress`. The bandits feature spreads the removed goods over the spawned units (one item per unit).
- [ ] 1.5 Corpse pit pay-out reads the override first and clears it; fallback to the existing rules. Clear entries of vanished units.
- [ ] 1.6 Use the result of the spike `spike-rebel-without-corpses` (bodies of killed families, removal without a body). Do not wait for it.
- [ ] 1.7 Militia case: count (and remove, if possible) weapons of rallied militia units of the rebelling region, by the result of task 2.2 and the fallback in `design.md`.
- [ ] 1.8 Update `bandits_state`, telemetry and log fields (camps only when the pawn was created; weapons found, removed, blocked).

## 2. Tests and spikes
- [ ] 2.1 Spike: read the inventory of homes in real fixtures and complete `rebellion_weapon_ids`. Write `notes/`.
- [ ] 2.2 Spike: can the mod read and remove equipped weapons of a rallied militia unit (`GetEquippedID` slots, unequip or consume calls)? Do weapons go back to homes on dismiss? Write `notes/`. Then mark the militia requirement as checked, or change the fallback.
- [ ] 2.3 Fake-game tests in `harness/tests/test_fakegame_bandits.py`, `test_bandits_rules.py` and `test_fakegame_raid_behavior.py`: config values, weapon check (enough, too few, nothing removed when blocked), random removal count, spread over units, override at the pit, fallback without override, cleanup, native plunder untouched, militia count, squads at home, no camp when the pawn exists, pawn creation.
- [ ] 2.4 New test scenario `mod/InvasionMod/scenarios/bandits/rebellion_raid.py`, based on `harness/scenarios/probe_rebel_noai.py` (worktree `.claude/worktrees/rebel-noai`, do not edit it). It stocks weapons, checks the removal, the spawn at the homes, a burn and the "enough looted" log.
- [ ] 2.5 Real test for the loot override: kill a rebel brigand, deliver the body to the pit (fixture `base-corpse-pit`), check that the pit gets the override item. Also a blocked rebellion with too few weapons, and a militia rally case.
- [ ] 2.6 Real runs on `playtest-noai` (and `base`): repeat rebellion, plunder for Outlaws squads, removal at the map edge. Write `notes/`.
- [ ] 2.7 Update `banditry_timer.py` for 60 days, the squad and the weapon stock.

## 3. Close
- [ ] 3.1 Update the Checked by lines, the wiki (bandits, raid_behavior, militia facts) and the affected skills.
- [ ] 3.2 `CHANGELOG.md` and `mod/InvasionMod/CHANGELOG.md` under Unreleased.
- [ ] 3.3 Pictures of the raid in `evidence/`.
- [ ] 3.4 Archive: `openspec archive update-banditry-rebellion-raid --yes`.
