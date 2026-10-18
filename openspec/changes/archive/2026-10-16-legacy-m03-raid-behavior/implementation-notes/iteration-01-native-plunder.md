# Iteration 01: native-plunder (notes)

## Design
- Feature `mod/InvasionMod/Scripts/features/raid_behavior/` (`init.lua`, pure rules in `rules.lua`, game reads in `world.lua`). It needs `invasion`.
- The invasion feature gets `watch_spawn(before, after)`. The tracker takes the list of all `SMUnit` before and after `spawnRaiders`. The new units are the raiders. (The census cannot tell raiders from camp bandits: the squad type is not readable.)
- A check runs every 1000 ms real time while a raid is active. It reads each unit with as few reads as possible: `dead`, then `ItemsLooted`, and `realPos` only for a unit that carries loot.
- A unit that is dead, or no longer listed, is gone. If it was last seen with loot at `y <= exit_y` (-85000, the map edge of the test map) it walked off the map and keeps its loot. Any other gone unit died.
- Death: the last seen loot goes to the nearest standing building that holds goods (distance from the last seen place). The good is the one the store holds most of. `addToInventory({Type, amt})` puts it in, and the code reads the building inventory back. If no store exists or the deposit fails, the loot is counted as lost and logged.
- Carry cap: loot above `carry_cap` (10) is cut back by writing `ItemsLooted`. The native AI reached 4 to 7 per unit, so the cap did not act in the real runs. The fake game test covers it.
- Raid end: the native AI writes `Outlaws (n) Army - enough looted. Leaving map.` to `RTSMultiEngineCPP.debugLog_AI_general`. The tracker counts matching lines among the newest 60 lines and compares with the count at the spawn. A higher count marks the raid as `left` (log line `RAID_BEHAVIOR native leave line seen`). All raiders dead gives `destroyed`.
- ModState keys (mod "invasion"): `raid_count`, `raid_start_day`, `raid_state` (0 none, 1 active, 2 left, 3 destroyed), `raid_returned`, `raid_lost`, `raid_burned`. They are written only when the value changes.
- Command `InvasionMod.raid_behavior_state`: day, `raids` (id, start_day, end_day, squads, state, initial, living, deaths, departures, loot, looted_total, carried_out, peak_loot, returned, lost, capped, burned, leaving), `active`, `population`, `carry_cap`.
- Log lines `RAID_BEHAVIOR start|day|loot returned|native leave line seen|end`.

## Findings
- The raiders loot, burn 5 to 10 buildings and leave under the native AI. 1 squad: leave line 14 game days after the spawn in all runs. 2 squads: 12 to 19 days. A raid of 2 squads sometimes reached the village late (first burn on day 16 in one run), so the scenario allows 30 days. A1 holds at 20 days for 1 squad.
- After the leave line the raiders stay near the map edge for many days. They do not leave the unit list. So "left" means "the native leave line was seen", not "units gone".
- The raiders spawn at the map edge (y about -89000). A dead unit read there must not count as left: a unit that is dead in view always counts as dead.
- Natural deaths happen (0 to 6 per raid). Their loot went back to a store (`returned` 1 to 7 in the runs).
- Loot per raider stays small: 70 to 87 total for 18 raiders (1 squad), 134 to 179 for 36 raiders (2 squads), 173 to 180 for medium at difficulty 1 (2 squads).
- Per-raider carried loot can be read (`ItemsLooted`). The unit of the number (items or silver) is still unknown. The mod treats one unit as one item.
- The loot good is unknown. Design choice: the good that the nearest store holds most of.

## Deviations
- A1: "left" is the native leave line, not "gone from the unit list" (units wait at the edge). The day limit is 30 for 2 squads or more.
- Per-unit loot is tracked by polling once a second. A raider that dies loses at most one second of loot change. No unit-death hook was found or needed.

## Crash finding (important)
- The first version read `realPos`, `ItemsLooted`, `dead` and `assignedSquadID` of every unit every second and wrote ModState each second. Raids of 2 squads crashed the game (access violation, `0xffffffffffffffff`) in about 2 of 3 runs. Raids of 1 squad did not crash.
- Bisect with 2 squads (env switch, removed afterwards): tracker off 4 of 4 without crash; village read only 2 of 2; AI log read only 2 of 2; unit read only 1 crash in 2.
- Fix: read `dead` first, `ItemsLooted` next and `realPos` only for a loot carrier, drop the squad read, write ModState only on change. Result: 1 crash in 9 suite runs plus 4 of 4 pass in a short series. A rare crash remains in 2-squad raids. A later iteration should use fewer or no polling reads, or a hook.

## Runs
- Loot return (`raid-behavior-loot-return`): `m03-loot-return-d` pass. Earlier runs a, b, c failed on scenario issues (loot written on non-raiders, a dead raider read at the spawn edge counted as left, an action self-check).
- A1 to A5, 1 squad: `m03-plunder-2` pass; suite `20261017-060551-d673` runs 001, 004, 007 pass.
- A6 suite `raid-behavior-ab` (`runs/suite-20261017-060551-d673`): looted_total per run
  - small, difficulty 1 (1 squad): 70, 74, 87 (mean 77)
  - small, difficulty 2 (2 squads): 134, 175, crash (run 008); extra run `m03-a6-small-d2-extra`: 179 (mean 163 over 3 valid runs)
  - medium, difficulty 1 (2 squads): 176, 173, 180 (mean 176)
  - Both 2-squad variants loot more than the 1-squad raid on average (about 2.1 and 2.3 times). The A/B tool says `different` for medium against small; small d2 is `inconclusive` only because of the crashed run.
- Earlier suites with the first version (crashes): `suite-20261017-013322-d421`, `suite-20261017-014336-0886`, `suite-20261017-023205-8036`, `suite-20261017-042002-f474`.
