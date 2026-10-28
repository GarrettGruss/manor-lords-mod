## 1. Spikes (notes in `notes/`)

- [x] 1.1 Spike A: call `spawnArmy` with arrival days 1, 2 and 3. Record where and when the army appears, the return value, squad ids, and the war and challenge setup. Verified by a real game run and `notes/arrival-days.md`.
- [x] 1.2 Spike B: find the map bounds, the playable area, and a query that tells walkable land from water. Compute border points for the player region and a vassal region. Verified by a real game run and `notes/map-border.md`.
- [x] 1.3 Spike C (only if A fails): find the march order for a spawned army (lord army). Verified by a real game run and `notes/march-order.md`.
- [x] 1.4 Update `proposal.md`, `design.md` and the delta specs when a finding changes a decision. Verified by review and `openspec validate --strict`.

## 2. Code

- [x] 2.1 Add a border point module with pure logic (nearest valid side, far enough, away from the corners, direction words). Verified by `harness/tests/test_fakegame_border.py`.
- [x] 2.2 Use it in `lord_raid.lua`, the yearly and subjugation raids, the great raid waves and the final army (the raid stand-ins of HarnessBattle stay: test spawns only). Verified by fake game tests and real runs.
- [x] 2.3 Relief army: spike C found no safe way to bring it in (notes `march-order.md`). It stays at `relief_offset`. The owner decides. Verified by the notes.
- [x] 2.4 Count the raid start and the wave gap from arrival, and show the direction banner. Verified by `harness/tests/test_fakegame_raid_behavior.py` and `test_fakegame_border.py`.
- [x] 2.5 Add the config keys of `invasion.border`: `rule`, `margin`, `inset`, `min_spawn_distance`, `march_lead_days`, `arrival_radius`, `arrival_share`, `max_march_days`, `north_axis`. Verified by `harness/tests/test_fakegame_border.py`.

## 3. Tests and evidence

- [x] 3.1 Write the test scenario `mod/InvasionMod/scenarios/invasion/border_arrival.py` and update `great_raid_waves.py`. Verified by real game runs.
- [x] 3.2 Picture evidence: the direction banner, an army at the map edge, and the army walking in (`evidence/`, README). The relief army has no picture: it did not change. Verified by review.
- [x] 3.3 Run a great raid wave after the change and note any crash in UE4SS Lua. Verified by a real game run (side benefit only, not a pass condition).

## 4. Close

- [x] 4.1 Update `CHANGELOG.md` (Changed), the wiki (engine facts from the spikes) and the affected skills. Verified by `wiki.py check`.
- [x] 4.2 Run the full test set and `openspec validate update-spawn-from-map-border --strict`. Verified by the commands.
- [x] 4.3 Archive as the last commit. Verified by `openspec list`.
- [x] 4.4 Fill the test results table of the implementation pull request. Verified by review.
