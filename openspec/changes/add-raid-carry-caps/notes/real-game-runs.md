# Real game runs (tasks 3.1 and 3.2)

Fixture `base`, difficulty 1, single player, no save call. Saves backed up before the first run. The fixture files were copied into the worktree (gitignored).

| Run id | Test scenario | Verdict | Key numbers |
|---|---|---|---|
| 20261021-030631-7493 | raid-behavior-carry-caps | harness_error | preflight: fixture files missing in the worktree (fixed by copying) |
| 20261021-030639-c378 | raid-behavior-carry-caps | pass | Hussite lord raid, 32 raiders at start, left after 15 days, reason `loot`, plundered 320 (limit 10 x 32 = 320), `carry_cap` 10 in state |
| 20261021-031021-395d | raid-behavior-native-plunder | fail | A1 native leave line missing; A5 tracker living 4 vs census 0 (days 8 to 13) |
| 20261021-031352-eb7c | raid-behavior-loot-return | pass | - |
| 20261021-031455-c1ae | raid-behavior-native-plunder | crash | game process ended during boot (not analysed) |
| 20261021-031527-374c | raid-behavior-native-plunder | fail | same two failures: leave line missing; tracker living 3 vs census 0 (days 8 to 12) |

## Analysis of the native-plunder failure

- The raid is native (`roles = false`, not a lord raid). In both runs the raiders died or left (deaths 14 to 18 of 18, `capped` 0, `looted_total` 17 to 18), the tracker kept 3 or 4 raiders as living while the census showed 0, and the raid ended as `destroyed` with no native leave line.
- `git diff main` shows this change touches only `rules.plunder_amount`, `rules.leave_reason` and `loot_goal`, which act on lord and role raids. The native tracking path (`world.lua`, tracker living count) is unchanged. So the failure is probably not caused by this change, but it was not compared with a run on `main`.
- Task 3.2 stays open until a run of `native_plunder` on `main` shows whether it failed before.
