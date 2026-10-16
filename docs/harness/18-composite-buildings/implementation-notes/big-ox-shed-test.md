# Big ox shed test (issue #104, run s21b-1, 2026-10-15)

Pak `bigshed` (row 125, one Meshy shed `BM_BigOxShed`, `stableSpace` 4). Mesh note: `docs/specs/21-mesh-generation/implementation-notes/spike-b-big-ox-shed.md`. Branch `main`, nothing committed. No save function. The game is closed. `~mods` is removed (the `--keep-open` run could not remove it; `pakmod.py remove --all` did after I stopped the game).

## Steps and numbers
1. Real click at (0.35, 0.3) on a white ghost placed the master (1 part). Built after 14 game days at speed 3.
2. Oxen before: `stableCurrent` 0, `stableMax` 4, `animals` 0. I called `SMBuildingMaster:spawnAnimal(12)` four times (harness spawns, not purchases; the task asked for 3, I added a fourth to fill the 4 places). After: `stableCurrent` 4 (3 after the first three).
3. New named command `building_assign_worker` (`type`, optional `family`) in `HarnessHousing`, registered in HarnessActions version 50, with a fake-game test. Answer: family 7 assigned, job 51, `max_slots` 2, assigned 0 to 1. No eval used.
4. Unpaused (speed 1 and up) for about 15 min of real time. Positions are `realPos` minus the master origin. The shed footprint is x +-306, y +-252.

## Ox positions
First samples (first 40 s after the unpause, oxen at rest):
| ox | position | in footprint |
|---|---|---|
| 1 | (181, -153) | yes, d 237 |
| 2 | (-225, 108) | yes, d 250 |
| 3 | (-8, 13) | yes, d 15 (fixed) |
| 4 | (-63, 281) | no, 29 outside the edge, d 288 |

About 60 s later the family went to work. Two oxen (1 and 2) walked away. Later samples (classified, 10 samples, 40 s apart, 6 min):
- 2 oxen in the shed footprint: one fixed at the origin (d 18) and one that wanders along the shed edge (d 249 to 307, now and then just outside).
- 2 oxen outside: fixed at d 13137 and d 12350 (about 12 to 13 k units away). They did not move for the whole run. They did not come back.
- 0 oxen moved to a new "spot" inside the roof. The one at the origin is the same fixed spot as in earlier runs (the master origin).

## What this says
- The user is right: only 2 oxen really use the shed. The other 2 are elsewhere. The earlier "ring of about 300 units" is the wander of the second ox along the edge, not 3 separate spots.
- Real hitch spots: about 2 (the origin and one loiter point). The other oxen get no spot and stay where the work AI leaves them. A bigger mesh with the footprint 600 x 600 does not add spots, as the sockets are not in the mesh and the logic is native (see `ox-hitch-hook.md`).
- Why the 2 stay outside is not found. A guess: the 2 far oxen got a work task (the assigned family works the fields or hauls) and wait at a work site. Not proven. The oxen were 12 k units away at a fixed point, so they are not idling in the shed or at the village edge.
- Overlap check: no ox is stacked at one point (the two inside are 250 apart).

## Open
- Which ox sees which spot: read `getTargetPos` natively (no reflected function, see hook note).
- Test with 2 oxen and 2 sheds, or the worker removed, to see if the far oxen come back when idle.
- Run in summer for the texture.
