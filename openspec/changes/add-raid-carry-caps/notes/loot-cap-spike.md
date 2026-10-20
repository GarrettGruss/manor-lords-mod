# Loot cap spike (task 1.1)

## Question

If `ItemsLooted` is written above the cap in a real raid, does the raider keep looting? What is the unit of `ItemsLooted`? Does the squad type change the loot? (design.md, open questions 1, 2 and 4)

## Method

Probe test scenario `mod/InvasionMod/scenarios/raid_behavior/probe_loot_cap.py` (options `LOOT_VALUE`, `ROLES`). Base fixture, difficulty 1, small raid, forced at once. It writes `ItemsLooted` on every bandit unit (`set_unit_loot`) and samples the tracker and the census every 2 game seconds.
For the spike the mod caps were set to 1000 (`config.lua`, reverted afterwards), so the tracker did not cut the loot itself (`capped` stayed 0 in all runs).

## Runs (4 of 6 used; all single-player, no save call; save folder file count 314 before and after)

| Run | Raid | Value written | Result |
|---|---|---|---|
| `s275-a-nocap2` | native (`spawnRaiders`, 18 raiders) | 50 | tracked loot 900 -> 100 within about one sample, then 18 (after 5 burned buildings), then returned to stores |
| `s275-b-fine` | native | 50 | same: 900 -> 100 -> 18 -> 1; looted_total never above 18 |
| `s275-c-v20` | native | 20 | tracked loot 360 -> 40 (2 samples of 2 game s) -> 17; later 20 total (natural looting goes on) |
| `s275-d-roles` | role raid (`spawnArmy`, 32 units) | 50 | tracked loot stayed 0; `looted_total` rose 0 -> 128 by `plundered` only |

(`s275-a-nocap` stopped in preflight before the game started: fixture files were missing in the worktree.)

## Findings

1. A native raid does NOT keep a value above its own level. The written 50 (or 20) per raider fell to about 5 (2 to 6 per raider) within a few game seconds, with no mod cap acting (cap 1000). The native AI (or the game) rewrites `ItemsLooted` on raiders that are on a raid job. So the native AI already limits the carried loot to about 5 per raider, and a mod cap of 5 or 10 never acts on a native raid.
2. The 18 idle bandit units that the tracker does not follow kept their 50 until the end (`loot_max` 50). The reset only touches raiders that run the raid.
3. `ItemsLooted` is a plain number of items. It has no good. The good is only known when the loot is returned to a store (`good=9` or `133` in the `loot returned` log lines). A cap by good (grain 10, iron 5) cannot be read from the unit; it would need a rule in the mod. Not built.
4. A role raid (`spawnArmy`, Hussite or bandit role) does not use `ItemsLooted` at all: tracked loot was 0 while `looted_total` grew by the `plundered` counter (30 per step, 128 total). So a carry cap by `ItemsLooted` has no effect on role raids either. The spec scenario for a Hussite cap of 10 grain cannot be shown with `ItemsLooted`.
5. Native looting continues after the reset (loot 17 -> 20 in run c): the reset is not a stop to looting.

## Not verified

- Whether the reset is a native cap value (about 5) or the AI "drops" the loot at a store. The sample step (2 game s) is too coarse to see one unit. A per-unit read would show it.
- Spike did not test a value between 6 and 10 (the proposed caps); a native raider seems to stay under it anyway.
- The run `s275-d-roles` wrote loot on the idle bandits, not on the raiders (raiders carry none), so it shows only that role raiders hold no `ItemsLooted`.

## Open question for the owner

The change adds caps of 10 (Hussite) and 5 (bandit) on `ItemsLooted`. The spike shows that native raiders never exceed about 5 and role raids carry no `ItemsLooted`. Both caps would never act, so the feature changes nothing in play. Options:

1. Keep the caps as a safety net only (no gameplay change) and drop the scenario that expects a cut.
2. Move the cap idea to the `plundered` counter of role raids (the real loot of Hussite raids), as a rule in the mod.
3. Drop the change (the design values are already the native behavior).
