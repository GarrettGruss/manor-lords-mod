# Fire during a raid (task 1.1)

Date: 2026-10-20. Test scenario: `probe-sack-raid` (hidden, `harness/scenarios/probe_sack_raid.py`), slot 1. It saves nothing.

## Method
- Spawn raiders in the village with `spawn_units` (side `bandit`, template `Brigands`, 2 squads = 36 units, at the player pawn). Wait 5 game seconds.
- `sack_buildings` with `method fire`, count 2. The same 2 buildings burn each time (the first standing ones in game order: store ids ...468110 type 80 and ...468274 type 72).
- Read the census every 5 game seconds at speed 3 (rubble, burning, `bAnyBuildingOnFire`), and 12 villagers near the village (`Tasks[].Type`, position).
- Baseline: the same without raiders. Control: raiders 20000 units away (`HARNESS_RAIDER_DX=20000`).

## Runs
| Run id | Variant | Rubble 10 s after lighting | Rubble 30 s after lighting |
|---|---|---|---|
| `20261021-034539-1b8d` | raiders in the village | 2 of 2 | not read (ended at 10 s) |
| `20261021-035316-f1d4` | raiders in the village | 2 of 2 | 2 of 2 |
| `20261021-034745-78c1` | no raiders | 0 of 2 | 0 of 2 |
| `20261021-035711-e76b` | no raiders | 1 of 2 | 1 of 2 |
| `20261021-040038-56c9` | raiders 20000 units away | 0 of 2 | 0 of 2 |

Run `20261021-035001-6d97` and `20261021-035125-0db3` were property searches (no fire). Run `56c9` has verdict `harness_error`: the save guard saw a new `saveGame_57` in the real folder. It is the fixture slot of a parallel run in another slot (this run used `saveGame_56`); the probe never saves. Its data is valid.

## Answers
1. Villagers flee and leave the fires with raiders in the village: yes, as data.
   - With raiders in the village (`f1d4`): no villager has a task of type 49, 50 or 62 (the firefighting tasks seen in the other variants). Five villagers stand still with an empty task list at one point (about -43745, -62592) from t+5 to t+20 s, and resume work at t+25 s. Both fires ended, and both buildings stayed rubble (2 of 2 in two runs).
   - Without raiders (`78c1`, `e76b`) and with raiders far away (`56c9`): villagers take tasks 50, 62 or 49 and walk to the fire (positions near -35000, -49000). 0 of 2, 1 of 2 and 0 of 2 buildings stayed rubble. The `sack-ruins` run `20261020-112444-595a` fits this.
   - The task type numbers are not named in the game data we read. We call 49, 50 and 62 "firefighting" because they appear only near the fire, only in the runs where the fire is put out, and not with raiders near.
2. Burn time without firefighting: the fire flag ended between 5 and 10 game seconds after lighting in every run (the region flag `bAnyBuildingOnFire` was true at t+5 and false at t+10; resolution 5 s). The building was already rubble (census `rubble` 2) at the moment of lighting, so the "burn time to rubble" is zero in the census. The fire ends by itself in under 10 game seconds; firefighting seems to rebuild the building (rubble falls back to 0) rather than to stop a slow burn. A time limit of 30 game seconds is enough for the fire to end (data to 30 s).
3. Flee is tied to nearby soldiers, not to the alarm bell: with raiders 20000 units away the villagers fought the fire (`56c9`), with raiders at the village they did not (`f1d4`, `1b8d`). The alarm bell was not tested (no known property or action). Not verified for the bell, and the exact distance of the flee is not known (between 20000 units and the village).
4. Raiders still in the village when the sack runs: not measured in the game. From the code: the sack runs from `start_leave` in `raid_behavior/init.lua` when a role raid begins to leave. At that moment the raid still exists and the mod removes units only later, in a quiet spot far from the village (`leave.quiet_distance`). So the raiders are normally still near the village. Needs a real `raid_sack` run to confirm.

## Not verified
- The alarm bell as a trigger.
- Question 4 in the game.
- Names of the task types 49, 50, 62.
- The sample is 2 runs with raiders, 2 without, 1 far. The simulation is not deterministic.
