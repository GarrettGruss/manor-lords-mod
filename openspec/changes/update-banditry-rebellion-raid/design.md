## Flow

1. The banditry timer expires (`timer_days` after the order fell below `threshold`).
2. `rebellion_families` families leave (`core.remove_families`). The village keeps `min_families_left`.
3. If no Outlaws pawn exists, `spawnBanditCamp()` makes it (one camp of 18 Brigands as a side effect), then `addPawnRelations(pawn)`.
4. `homeless_rebel` mode `home` spawns `rebellion_squads` Brigands squads (`spawnArmy`, owner = Outlaws) at the first removed home.
5. The native AI raids, logs "enough looted. Leaving map." and walks to the map edge.
6. The mod raises the order by `order_gain` and restarts the timer if the order is still below `threshold`.

## Known facts (`notes/rebel-noai-findings.md`)

- Fixture `playtest-noai` (no AI opponents): the squads raid at once. The first building burns after 37 to 108 game s, "enough looted" shows after 108 to 202 s, the squads reach the map edge after 268 to 312 s. 3 to 5 buildings burn.
- Fixture `base`: the squads waited about 500 s at an AI waypoint near (-31000,-22500). The likely cause is a neighbour AI lord army. Not proven.
- After the first sack, later squads may say "enough looted" at once (legacy note `homeless-rebellion.md`).
- Loot of goods comes only from `raid_behavior` plunder. Not verified for Outlaws squads.
- Squad removal at the map edge is not verified. The units may stay on the map and count as bandit units for the buy-back.
- The camp from `spawnBanditCamp` never joined the squads and stayed at its place.
- A save can have no player soldiers. The rebellion does not depend on them.

## Decisions

- Reuse `homeless_rebel` (proven). No new engine call.
- Keep `spawnBanditCamp` only to create the pawn. Accepted side effect: one camp of 18 Brigands, once.
- Config keys stay in the `bandits` table of `Scripts/config.lua`.
