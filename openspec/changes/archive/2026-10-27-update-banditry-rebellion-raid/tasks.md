## 1. Code
- [x] 1.1 `config.lua` (`bandits`): `timer_days` 60, `leavers` becomes `rebellion_families` 6, add `rebellion_squads` 1, `rebellion_weapon_ids` (default: all 13 ids in `design.md`), `loot_override_slots` 200. Keep `threshold`, `order_gain`, `tick_days`.
- [x] 1.2 New module `features/bandits/outlaws.lua` with idempotent `ensure_outlaw_pawn()`: `spawnBanditCamp()`, `addPawnRelations`, `just_die` and hide the 18 Brigands, `demolish(true)` on the bType 100 camp. Call it at game start, after each load and before each rebellion.
- [x] 1.3 `world.leave`: `ensure_outlaw_pawn()`, find valid families, pick `rebellion_families` at random, take all weapon and armor goods of their homes, kill the families and hide the bodies, `homeless_rebel` mode `home` at the first removed home. On a failed spawn, return the goods and log.
- [x] 1.4 Blocked case: fewer valid families than `rebellion_families`: no rebellion, timer stays expired, retry next tick, telemetry `rebellion_blocked`. Nothing is removed.
- [x] 1.5 Loot override module in `features/raid_behavior` (`set`, `get`, `take`, `clear_all`, `relink`), session key `GetAddress`. The bandits feature spreads the taken goods over the spawned units.
- [x] 1.6 Save the override map with ModState: `loot_slot_1..N` string keys, `loot_override_slots` config, slot write on `set`, `take` and drop, error when full. Stable unit key by the result of task 2.8.
- [x] 1.7 Re-link after a load (`relink`): link entries to units and bodies, drop and log the lost ones. Keep the entry on the body until pay-out or body expiry. Drop it when the unit leaves the map.
- [x] 1.8 Corpse pit pay-out reads the override first and clears it; fallback to the existing rules. Clear entries of vanished units.
- [x] 1.9 Update `bandits_state`, telemetry and log fields (valid families found, goods taken, goods returned, blocked).

## 2. Tests and spikes
- [x] 2.1 Spike: read the inventory of homes in real fixtures and check `rebellion_weapon_ids`. Write `notes/`.
- [x] 2.2 Fake-game tests in `harness/tests/test_fakegame_bandits.py`, `test_bandits_rules.py`, `test_fakegame_outlaws.py` (new) and `test_fakegame_raid_behavior.py`: config values; `ensure_outlaw_pawn` (pawn exists: no calls; pawn missing: camp, relations, kill, hide, demolish; second call does nothing); random selection of valid families; blocked case (fewer than 6 valid families, nothing removed, event logged, retry); goods taken from the chosen homes only; goods spread over 18 units; goods returned after a failed spawn; override at the pit; fallback without override; cleanup; native plunder untouched; squad at the first home.
- [x] 2.3 New test scenario `mod/InvasionMod/scenarios/bandits/rebellion_raid.py`, based on `harness/scenarios/probe_rebel_noai.py` (worktree `.claude/worktrees/rebel-noai`, do not edit it). It stocks weapons in homes, checks selection, goods removal, the spawn at the home, a burn and the "enough looted" log. Also the blocked case with fewer than 6 valid families.
- [x] 2.4 Real test for `ensure_outlaw_pawn()`: pawn missing, call, check that the pawn exists, the camp and its brigands are gone, and a second call does nothing.
- [x] 2.5 Real test for the loot override: kill a rebel brigand, deliver the body to the pit (fixture `base-corpse-pit`), check that the pit gets the override item.
- [x] 2.6 Real runs on `playtest-noai` (and `base`): repeat rebellion, plunder for Outlaws squads, removal at the map edge. Write `notes/`.
- [x] 2.7 Update `banditry_timer.py` for 60 days, the squad and the stocked homes.
- [x] 2.8 Spike: find a stable unit key across a save and a load (squad id and unit index, unit name or id, re-match by squad). Check that a body keeps it. Use the guarded `save_game` action only. Write `notes/`.
- [x] 2.9 New real test scenario `mod/InvasionMod/scenarios/bandits/rebellion_loot_roundtrip.py` (write run and read run, `--save`, `--env MODSTATE_PHASE=read`): start a rebellion, save with `save_game`, load, check that the slots are linked to the brigands, kill one and check the pit pay-out. Never a raw save call.
- [x] 2.10 Real test: Outlaws pawn survival over save and load. After the camp removal, save with `save_game`, load, and check that the pawn exists (or that `ensure_outlaw_pawn()` repairs it). Write `notes/`.
- [ ] 2.11 Manual: owner playtest of the militia exploit case (rally, then wait for the rebellion). The owner reports the result.

## 3. Close
- [x] 3.1 Update the Checked by lines, the wiki (bandits, raid_behavior, militia and camp removal facts) and the affected skills.
- [x] 3.2 `CHANGELOG.md` and `mod/InvasionMod/CHANGELOG.md` under Unreleased.
- [x] 3.3 Pictures of the raid in `evidence/`.
- [x] 3.4 Archive: `openspec archive update-banditry-rebellion-raid --yes`.
