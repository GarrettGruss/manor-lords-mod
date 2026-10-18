# Pathing test: units against the wagon wall (2026-10-18)

Spec 32, issue #233. Fixture `manor-closed`, scenario `probe-manor-wagenburg`, speed 1, `--slot auto`. No mouse, no eval, no save call.

## Method
1. Read the 56 built wall pieces (`mesh_actors`, owner `SMBuilding`) and the gatehouse. The ring is a square with its centre at (10829, -51754), radius 23.3 m, gate at (11013, -49697) (north-east side).
2. Bait: 32 player spear militia at the ring centre (`spawn_units`). Bandits: 18 Brigands at 58 m from the centre on the side opposite the gate (start (10309, -57564)). They attack on sight.
3. Track the bandit squad with `squad_positions` every 0.5 s for 70 game seconds (141 samples). The rows are `track.jsonl`.
4. Metrics: the first sample with a bandit inside the ring and how far that bandit is from the gate; the maximum inside; wall crossings (`harness/tools/s32_track_report.py`: each unit is matched to the nearest unit of the previous sample, a step that cuts a wall edge, not counting the gate edge, is a crossing).
5. Control (no pak) against the pak `s32wall` (wagons). Same fixture, same spawn points. The simulation is not deterministic, so only ranges are compared.

## Results
| Run | Pak | First sample inside | Distance of that unit to the gate | Max inside | Wall crossings | Obstacles |
|---|---|---|---|---|---|---|
| `s32-2` | none | 27 | 165 cm | not stored | not stored | 337 |
| `s32-8` | none | 25 | | 18 | 0 | 337 |
| `s32-10` | none | 28 | | 18 | 0 | 337 |
| `s32-3` | `s32wall` | 28 | 189 cm | not stored | not stored | 337 |
| `s32-9` | `s32wall` | 28 | 182 cm | 18 | 0 | 337 |
| `s32-11` | `s32wall` | 24 | | 18 | 0 | 337 |
(`s32-2` and `s32-3` ran before the ring file was stored; the report tool needs `ring.json`.)

- Control and wagons give the same behaviour. The bandits start south of the ring, walk round the wall (the shortest line to the bait crosses the south wall), and the first one is inside after about 25 to 28 samples, 1.7 to 1.9 m from the gate. All 18 are inside later. There is no wall crossing in 4 runs with the tool.
- The wagon mesh did not change the obstacle count (337) or the path. This matches the cause found in spec 14: the block is the obstacle list, not the mesh.
- The gate works the same with wagons: it is the only opening.

## Limits
- The tool matches units by the nearest position. A crossing at the gap between two pieces near a corner could be missed in rare cases. A positive control (a ring without obstacles, where bandits walk through) was not run here; spec 14 showed it for a demolished wall (8 of 8 crossings) and for a free wall (through).
- A closed gate and the defenders were not tested. The bait stood still at the centre and did not hold the wall.
- Only bandit attackers were tracked. Player units were not tracked.
- Clock problem: after the keep build the clock did not restart (`s32-5`, `s32-6`). The path test and the keep build ran in separate runs.
