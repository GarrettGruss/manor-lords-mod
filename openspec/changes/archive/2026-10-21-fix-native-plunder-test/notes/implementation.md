# Implementation notes: fix-native-plunder-test

## Tracker (task 1.1)

- The game census (`HarnessUnits.census`) counts a unit by its squad: the side comes from `unit.assignedSquadID.Value` found in `HarnessUnits.squadMap()`. A unit whose squad is not in the map is "civil" and is not counted as a raider.
- `world.read_units(tracked, ...)` now reads `squadMap()` once per look and marks a tracked unit as dead when its squad id is not in the map. `rules.update` already treats a dead unit as gone, so no rule change was needed.
- Why this way: it is one extra read of the squad map per look (the census does the same) and one read of `assignedSquadID` per living tracked unit. It does not read Squad structs.
- The filter is off at the spawn look (`tracked == nil`), so the raiders of a fresh spawn are never dropped before the game gives them a squad. It is also off when `HarnessUnits` is not available.
- Not proven in the real game before the runs of task 3.2: whether the dead raiders that the old tracker kept were really missing from the squad map. The carry cap test scenario checks the equality at every sample.

## Removed code (tasks 2.1, 2.2)

- Bandit squad leave: `world.make_peace`, `world.restore_war`, `world.home`, `rules.exit_quiet`, `leave.quiet_distance`, the war restore in `step_raid`.
- A raid without a lord never gets a leave reason now: `check_leave` and `force_leave` act on lord raids only. `rules.leave_reason` is unchanged.
- Loot return: `return_loot`, `fallback_good`, `rules.nearest_store`, `rules.pick_good`, `rules.record_return`, `rules.record_loss`, `world.deposit`. The departure count at `exit_y` stays. The Hussite carry cap stays.
- Kept on purpose: the summary fields `returned` and `lost` and the ModState keys `raid_returned` and `raid_lost` (always 0 now). The living spec requirement "The raid state is kept and shown by command" names them and this change does not modify it. Open question for the lead: remove them in a follow-up change.
- Test scenarios removed: `native_plunder.py`, `loot_return.py`. The suite `raid-behavior-ab` now runs `raid-behavior-carry-caps` (its `INVASION_SIZE` variants have no effect there). The scenario list in `test_runlib_scenario.py` lost the two names.
- Coverage data (`criteria.json`, `criteria.md`) named neither scenario, so nothing changed there. `coverage.py --check-spec` passes. The wiki page `invasion-features.md` was updated.

## Test scenario (task 3.1)

`carry_caps.py` takes the census squads that the spawn made (squad ids new after `invasion_force_next`, sides `bandit` or `ai`), compares the sum of their sizes with the tracker `living` at every day sample (one retry after 2 s), and accepts `left` or `destroyed`. Counting a whole census side was wrong: it also counts other AI units.

## Deviation: leave marking of a bandit squad raid stays

The sack and terms features (`sack_and_terms`) hear of a leaving role raid through `watch_leave` and `force_leave("terms")`, also for a bandit squad raid. To keep them working, `start_leave` still sets the leave reason and calls the watchers for a raid without a lord. It makes no peace, restores no war and removes no unit for such a raid (`world.make_peace`, `restore_war`, `exit_quiet` are gone).

## Real game runs (slot 1, branch deployed with deploy.ps1)

| run id | verdict | note |
|---|---|---|
| 20261022-013721-d240 | harness_error | fixture `base` missing in the worktree; copied from the main checkout (gitignored) |
| 20261022-013745-23c1 | fail | the scenario compared the tracker with the census side `ai`, which also counts other AI units; changed to count the squads that the spawn made |
| 20261022-014209-ff72 | pass | |
| 20261022-014538-68e7 | crash | game process ended during boot (before the scenario) |
| 20261022-014610-043a | pass | |
| 20261022-015022-77b8 | pass | |
