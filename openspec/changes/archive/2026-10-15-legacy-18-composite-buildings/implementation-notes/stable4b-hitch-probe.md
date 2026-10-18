# stable4b hitch probe (issue #104, run s115-st4b, 2026-10-15)

No save function was called. The AES key came only from the environment. The game was closed and `~mods` removed at the end.

## Setup
- Pak `stable4b`: same as `stable4` (row 125, class `BM_HarnessLargeStable`) plus probe Scene components `Scene_0..3`. Made with `BM_PROBES=1` in `mod/HarnessActions/ue/make_bm_stable.py`, then cook and `pakmod.py build stable4b`. Built file: `modtools/work/out/stable4b_P.pak` (git-ignored work folder).
- Run `s115-st4b`: `run.py --scenario noop --keep-open --pak stable4b`. Real click at (0.35, 0.3) placed row 125 (2 parts). Built after 14 game days at speed 3. `spawnAnimal(12)` four times. `stableCurrent` 4, `stableMax` 4.
- Master yaw is 0, so master-relative offsets equal the BM-local offsets.
- The run ended with a harness_error (paks-remove, file in use, because the game stays open). Known.

## Result
Unpaused, the oxen first went to work and then came back (about 60 s of real time). Positions relative to the master (x, y), stable over about 270 s:

| ox | position | near |
|---|---|---|
| A | about (-50, 255) | hitch socket 0 of shed A, (75, 208): about 130 away |
| B | about (45, -270) | hitch socket 1 of shed A, (75, -143): about 130 away |
| C | (-1, -18), fixed | master origin, centre of shed A |
| D | about (260, -140) | in front of shed A, close to `gathering` side |

- The oxen did NOT all stack at one point. They form 2 hitch positions (A, B) with 2 waiting oxen (C, D). This matches the user observation: the oxen use the 2 sockets of ONE shed.
- No ox went near `Scene_2` (74.7, 858.3) or `Scene_3` (75.1, 507.1), nor to shed B (`MainBld_901`, y about 665). No ox stood on `Scene_0`/`Scene_1` any closer than on the mesh sockets (the offsets of 130 are the same as a mesh socket offset; this probe did not read the sockets themselves).
- Screenshot `runs/s115-st4b/screenshots/near2.png` (git-ignored): oxen crowd at shed A, shed B is empty.

## Meaning
- Scene components `Scene_0..3` do not mark the hitch spots. The probe did not change the behaviour: oxen still use only the 2 hitch sockets of the first shed mesh.
- The hitch spots come from the sockets of the shed mesh (hitch0, hitch1 of `SM_MERGED_C_SG_OxShed_UBeam`) of the first part. The second shed adds capacity (`stableMax` 4) but its sockets are not used. So 4 oxen share 2 spots (2 and 2).
- Not tested: whether the game picks only the first `MainBld_*` part, or only the master transform. Not tested: socket world positions (read them from the mesh with the bridge).

## Next
- Read the socket names and world transforms of the part components (`GetSocketLocation`) and compare to A and B.
- Test: swap the order of the parts, or make one single long mesh with 4 sockets, or find which part the AI reads (a hook on the hitch function).
