# Design: carry caps by raid type

## Context

Legacy source: `docs/mod/M03-raid_behavior/README.md`, open questions 1 and 4. The loot spikes are in `docs/harness/10-invasion-testability/implementation-notes/spike-S5.md` and `spike-S3.md`. The native loot per raider in the real runs is in `docs/mod/M03-raid_behavior/implementation-notes/iteration-01-native-plunder.md`.

## Open questions

1. Does the native AI stop looting at a written `ItemsLooted` cap? Answer: a spike in the real game (task 1.1). In the real runs of iteration 01 the native loot stayed below the cap of 10, so the cap never acted there.
2. What is the unit of `ItemsLooted` (items or silver) and does a cap by good (grain 10, iron 5) make sense? Answer: the same spike. If the value has no good, one cap by raid type is enough.
3. How does the tracker know the raid type? The tracker has the kinds plunder, subjugation and great. A bandit plunder raid has no kind today. Answer: task 1.2 decides where the type comes from.
4. Does the squad type (`spawnRaiders` against `spawnArmy`) change the loot? Answer: the same spike.
