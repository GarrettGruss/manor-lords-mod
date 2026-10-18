# M03 iteration 02 follow-up: untested paths (issue #172)

All runs in the real game, fixture `base`, no saves.

## Region give-back guard
- Test command `raid_behavior_test_take_region` writes the raid lord as owner of the home region (what a won challenge does).
- The guard (`check_region`) gave the region back within one look (under 5 s). The scenario cannot see the lord as owner by a read, so it checks the log line `region <name> was taken by the lord, given back=true`.
- Scenario `raid-behavior-region-guard`: runs `20261018-045632-3134`, `20261018-045812-6c93` pass. (First run `20261018-045437-c730` failed only because of the read race above.)
- Not done: a natural win by an unanswered challenge. With the anchored battlefield the challenge stayed open (M03.02 anchor spike), so the natural path was not reached. The forced win tests the same guard condition (owner is not the player).

## Leave reasons losses and time (lord raid)
- Test command `raid_behavior_test_set_leave` sets small values for the session (loot goal 1000 switches the loot rule off).
- `losses`: `raid_behavior_test_kill_raiders` kills 70 percent of the raiders. Run `20261018-052419-b005` pass (a first run `20261018-045940-972c` also passed).
- `time`: `max_days` 3. The rule fired on day 208 for a raid that started on day 205. Runs `20261018-052146-de38`, `20261018-050600-1510` pass.
- Walk-off after peace: 6 game days in run `20261018-050241-0196` (peace day 208, raid end day 214). The earlier loot run took 2 days. A4 says 1 to 3 days. The raid left the map each time, but the time varies. Open risk, no fix.

## Rerun invasion-no-double-raid (120 days) with lord raids on
- Run `20261018-050921-7007` pass (one raid spawn, planned raiders, base timer stayed high).

## Double raid edge case (fixed)
- Cause: `lord_raid.start` failed after some `spawnArmy` calls (or at the anchor or challenge step). `invasion` then spawned bandit squads on top.
- Fix: `lord_raid.start` returns a third value `true` when armies exist. It sends them away with peace. `invasion` does not spawn the fallback in that case. `raids_spawned` stays 0, so the next daily step tries again.
- Fake test: `test_a_lord_raid_that_fails_after_a_partial_spawn_adds_no_bandit_squads`.
