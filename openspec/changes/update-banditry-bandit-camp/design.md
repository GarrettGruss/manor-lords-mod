## Decisions

- `world.leave(region, count)` removes the families with `core.remove_families` (as now for the remaining families), then calls `world.spawn_camp()`. It no longer calls `homeless_rebel`. The refugees feature keeps `world.rebel` and its own `families_per_squad`.
- `world.spawn_camp()`: if no bandit pawn exists, call `spawnBanditCamp` once (it makes the pawn and a camp), then `addPawnRelations(pawn)`. If the pawn exists, call `spawnBanditCamp` once. Both cases make exactly one camp per leave event. Reuse the proven `HarnessRaids` call if it fits (`measuredSpawn`).
- "Create the pawn first" and "spawn the camp" are the same call, so the first leave with no pawn makes the pawn and the camp together. No second call.
- The guard (`add-game-settings-guard`) needs no banditry lock. The live check no longer reads the bandit pawn for `villager_banditry`.
- Camp place: no argument exists. Task 1.2 records the place and the distance from the village on `base` and `playtest-noai`.

## Risks

- Many camps in a short time (spike #430: one crash with 3 camps). Mitigation: one camp per leave event; the leave timer is 90 days.
- The camp squads walk on their own and may raid the village. This is the wanted bandit behavior.
