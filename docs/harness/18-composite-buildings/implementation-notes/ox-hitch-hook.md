# Ox rest and hitch: hook spike (issue #104, run s117-hook, 2026-10-15)

No save function was called. The AES key came only from the environment. The game is closed. `~mods` is removed with `pakmod.py remove --all` (the `--keep-open` run could not remove it itself, as before).

## Setup
- `run.py --scenario noop --keep-open --pak stable4 --run-id s117-hook`. Real click at (0.35, 0.3) placed row 125. Built after 14 game days at speed 3. Four `spawnAnimal(12)` on the new master. `stableCurrent` 4, `stableMax` 4.
- The MCP bridge tools pointed to another folder ("bridge down"). The Python bridge client with the run folder worked.
- Unpaused at speed 3 for about 6 minutes of real time.

## Hooks tried (34, all registered, all 0 events)
- `SMUnit`: setTask, getTargetPos, getWorkplace, getHome, GetAction, getTaskLabel, getJobType, getStatus, step, GetInterpolatedLocation, capSpeedToPersonInFront, animationLoopEnded.
- `SMBuildingMaster`: setSleep, getSleep, canSleep, getAnimals, getAnimalsCurrentlyOnPasture, RecomodateAnimalsOfType, getBuildingArea, getOccupants, getLivestockWorkerRole, getMaxOxen.
- `PawnCPP:getPlayersOxen`, `AffectAnimalLairs`. `RTSMultiEngineCPP`: SpawnLivestock, breedAnimal, findUnitByPos, getNearestBuildingTo, pickNearestPos, getAnimalRoleFromGoodType.
- Controls: `Actor:ReceiveTick`, `K2_SetActorLocation`, `K2_AddActorWorldOffset`, `K2_SetActorTransform`. Also 0 events, while the game clock ran and the oxen moved. Only my own `getAnimals` call was seen (1 event).
- `VAMP_Ox_C` has no own function. It has only `SMUnit` and `Actor` functions. There is no reflected class for stable, hitch, pasture or animal AI (`list_types`: only `AnimalSpace`, `LivestockSettings`).

## Result
- No hook fires. The ox rest and hitch logic is native code. It does not call any reflected function, so a Lua hook cannot see the function or its target position. This matches the AI build result in `mousefree-ai-route.md`.
- Not possible from Lua: reading the function. Not tried: a native code patch, a hook by address.

## Ox positions (4 oxen of the new stable, relative to the master origin, 28 samples, 69 s apart, unpaused)
After a short walk (about 2 game hours), the oxen settle at 3 places for the rest of the run:

| ox | position | note |
|---|---|---|
| 1 | about (-20, -3), fixed (never moved) | the master origin (shed A centre is (-5, +15)) |
| 2 | (-100..-190, -210..-265) | jitter of about 50 |
| 3 | (30..190, -230..-270) | jitter of about 50 |
| 4 | (-215..-280, 50..175) | jitter of about 50 |

- Oxen 2, 3 and 4 stand on a ring of radius about 250 around the master origin (angles about 240, 285 and 165 degrees). Ox 1 stands on the origin.
- Nobody goes near shed B (y +665) or the old Scene points (they are not in this pak).
- So the spots are NOT 2 sockets. This run shows 1 origin spot and 3 ring spots with a loose wander (an idle loiter around the master). Earlier runs (s115, s116) saw other mixes, so the pattern is not fixed.

## Meaning
- Position source: most likely the master origin (ox 1 is exactly on it) plus a native loiter point around it. Not the mesh sockets (none exist), not shed B.
- Could a pak give 4 distinct spots? Not proven. The ring spots depend on the master origin and the nearby space, not on parts we add. A pak can only add components (Scene, `workpos`-like) or a longer mesh. The game may read `workpos` or `gathering` natively, but the hooks cannot show it. The ring radius (about 250) is not tied to the shed offsets (-5,+15) and (-5,+665).
- Next test: add `workpos`-named and `gathering`-named components at known offsets (for example 4 `workpos_N` at 400 units away from the origin) in a new pak, and compare oxen positions. A change of the positions shows the source. Also test moving the master origin to the middle of both sheds (the master origin is the root of the BM blueprint).
