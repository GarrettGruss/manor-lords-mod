## 1. Spikes (notes in `notes/`)

- [ ] 1.1 Spike A: call `spawnArmy` with arrival days 1, 2 and 3. Record where and when the army appears, the return value, squad ids, and the war and challenge setup. Verified by a real game run and `notes/arrival-days.md`.
- [ ] 1.2 Spike B: find the map bounds, the playable area, and a query that tells walkable land from water. Compute border points for the player region and a vassal region. Verified by a real game run and `notes/map-border.md`.
- [ ] 1.3 Spike C (only if A fails): find the march order for a spawned army (lord army and bandit walk). Verified by a real game run and `notes/march-order.md`.
- [ ] 1.4 Update `proposal.md`, `design.md` and the delta specs when a finding changes a decision. Verified by review and `openspec validate --strict`.

## 2. Code

- [ ] 2.1 Add a border point module with pure logic (nearest valid point, next valid point along the border). Verified by a fake game test, `harness/tests/test_fakegame_invasion.py`.
- [ ] 2.2 Use it (or the game arrival time) in `lord_raid.lua`, the great raid waves, the final army and raid stand-ins. Verified by fake game tests.
- [ ] 2.3 Use it in `relief.lua` and remove the use of `relief_offset`. Verified by a fake game test.
- [ ] 2.4 Use it in the bandits feature and in `HarnessBandits` spawns. Verified by `harness/tests/test_fakegame_bandits.py`.
- [ ] 2.5 Count the raid start, the banner and the wave gap from arrival. Verified by `harness/tests/test_fakegame_raid_behavior.py`.
- [ ] 2.6 Add the config keys `border_rule`, `arrival_days`, `min_spawn_distance`. Verified by a fake game test.

## 3. Tests and evidence

- [ ] 3.1 Write the test scenario `mod/InvasionMod/scenarios/invasion/border_arrival.py` and update `great_raid_waves.py` and `convert_families.py`. Verified by real game runs.
- [ ] 3.2 Capture picture evidence with `ctx.screenshot(name)`: an army entering at the map edge for a raid, a wave, the relief army and a bandit band. Put it in `evidence/` with `evidence/README.md`. Verified by review.
- [ ] 3.3 Run a great raid wave after the change and note any crash in UE4SS Lua. Verified by a real game run (side benefit only, not a pass condition).

## 4. Close

- [ ] 4.1 Update `CHANGELOG.md` (Changed), the wiki (engine facts from the spikes) and the affected skills. Verified by `wiki.py check`.
- [ ] 4.2 Run the full test set and `openspec validate update-spawn-from-map-border --strict`. Verified by the commands.
- [ ] 4.3 Archive as the last commit. Verified by `openspec list`.
- [ ] 4.4 Fill the test results table of the implementation pull request. Verified by review.
