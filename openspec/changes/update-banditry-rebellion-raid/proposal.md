## Why

Issue: #480. Owner decisions 2026-10-24. The camp outcome of `update-banditry-bandit-camp` (18 families leave, one camp of 18 Brigands far away) does not hurt the village. The spike `rebel-noai` (`notes/rebel-noai-findings.md`) showed that squads of the bandit pawn "Outlaws", spawned at the homes of removed families, raid the village at once in fixture `playtest-noai`, burn buildings, log "enough looted" and leave the map. That is the rebellion the owner wants.

## What Changes

- The banditry outcome becomes a rebellion. `rebellion_families` (default 5) families leave, and `rebellion_squads` (default 1) Brigands squad of the pawn "Outlaws" spawns at the home of the first removed family (`HarnessBandits.homeless_rebel`, mode `home`, `spawnArmy`). The native Outlaws AI raids the village, logs "enough looted" and leaves the map.
- The mod no longer calls `spawnBanditCamp` for each leave event. It calls it only when the Outlaws pawn is missing, to create the pawn, and then calls `addPawnRelations`. Side effect, accepted: that call also makes one camp of 18 Brigands (the owner accepted random camps earlier).
- Config values in the `bandits` table of `mod/InvasionMod/Scripts/config.lua` (the config of the feature): `threshold` 25 (unchanged), `timer_days` 60 (was 90), `order_gain` 25 (unchanged), `tick_days` 30 (unchanged), `leavers` renamed `rebellion_families` with default 5 (was 18), new `rebellion_squads` with default 1.
- The other order rules stay: manor term +10 plus tech bonus, homeless term -5 per homeless family.

## Open questions (with defaults)

1. Families removed per rebellion. Default 5. Proposed default, owner to confirm.
2. Soldiers per rebellion. Default one Brigands squad (18 units) at the first removed home. Proposed default, owner to confirm.
3. The camp side effect when the pawn is missing. Default: accepted. One camp of 18 Brigands appears once, far from the village (45000 to 115000 units in the spike).

## Impact

- Specs: `mod/bandits` (RENAMED and MODIFIED: the conversion requirement; MODIFIED: the banditry timer requirement).
- Code (gate 2): `mod/InvasionMod/Scripts/features/bandits/world.lua` (`M.leave`), `init.lua`, `rules.lua`, `mod/InvasionMod/Scripts/config.lua`, tests, one test scenario.
- Risk: the raid may be slow when a neighbour AI army exists. Loot and squad removal at the map edge are unverified (see `design.md`).
- Overlap: the change `update-spawn-from-map-border` touches the same conversion requirement. Check it on rebase.
