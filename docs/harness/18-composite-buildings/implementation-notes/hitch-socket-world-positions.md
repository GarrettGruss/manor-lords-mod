# Hitch socket world positions (issue #104, runs s116-hs and s116-hs2, 2026-10-15)

No save function was called. The AES key came only from the environment. The game is closed and `~mods` is removed (by `pakmod.py remove --all`, because `--keep-open` blocks removal).

## Setup
- Pak `stable4b`, `run.py --scenario noop --keep-open`. Real click at (0.35, 0.3) placed row 125. Built after 14 game days at speed 3. Four `spawnAnimal(12)`. `stableCurrent` 4, `stableMax` 4.
- Master `SMBuildingMaster_2147457289` at (-31965.2, -54612.2), yaw 0. It has 2 `SMBuilding` actors (the parts), each with one `StaticMeshComponent0`.

## Part components
| part | actor location | offset from master | mesh |
|---|---|---|---|
| shed A (`SMBuilding_2147457281`) | (-31970.2, -54596.9, 3257.1) | (-5, +15) | `SM_MERGED_C_SG_OxShed_UBeam` |
| shed B (`SMBuilding_2147457280`) | (-31970.2, -53946.9, 3222.0) | (-5, +665) | same mesh |

## Sockets at run time
- On both parts, `StaticMesh.Sockets` is empty and `StaticMeshComponent:GetAllSocketNames` returns `[]`.
- So the merged ox shed mesh has NO `hitch0` / `hitch1` at run time, on shed A or on shed B. This matches the static finding that merged meshes have no sockets (`SMD_OxShed` is a build-time helper).
- `GetSocketLocation("hitch0")` and `DoesSocketExist("hitch0")` crashed the game (access violation, address 0x70) in 2 runs. Do not call them through the bridge. The crash reports are in the real `%LOCALAPPDATA%\ManorLords\Saved\Crashes`. No socket world position can be read.
- Reference positions below are computed, not read: master-relative (75, 208) and (75, -143) for shed A (from the `SMD_OxShed` offsets), and (75, 858) and (75, 507) for shed B (+650 in Y).

## Ox positions (run s116-hs2, `realPos` minus master, 13 samples every 20 s, unpaused)
- `K2_GetActorLocation` of an ox is useless (it stays at (305, 340), the `gathering` point). Use `realPos`.
- The oxen moved all the time. Ranges: x -256 to 245, y -286 to 287. Means: ox 0 (-95, 27), ox 1 (62, -23), ox 2 (-31, 84), ox 3 (7, 6).
- Nobody stood still at a spot. This differs from run s115-st4b (A and B steady about 270 s).

| reference point | nearest sample | samples within 100 units (of 52) |
|---|---|---|
| shed A hitch0 (75, 208) | 77 | 2 |
| shed A hitch1 (75, -143) | 58 | 8 |
| shed B hitch0 (75, 858) | 579 | 0 |
| shed B hitch1 (75, 507) | 238 | 0 |

## Meaning
- The oxen stay in y -290 to 290 around shed A (centre y +15). Shed B (y +665) is never used. The shed A reference points are only the nearest, not matched: no ox rested on one.
- No runtime socket exists, so the game cannot read hitch sockets from the mesh. The 2-spot pattern of s115-st4b is not explained by sockets. It is more likely derived from the master origin or `gathering`, or it was the work AI.
- The "130 units from hitch" match in s115-st4b was by offset only. It is not supported by this run.

## Next
- Hook the hitch/rest function on `VAMP_Ox_C` (`hook_function`) to find which position the game uses.
- Run unpaused at night, long, to see rest spots. Test a single long mesh or `Scene_*` probes as the spot.
