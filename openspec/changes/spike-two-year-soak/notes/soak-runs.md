# Soak runs (tasks 1.2, 1.3, 2.3)

Scenario `soak-days` with `HARNESS_SOAK_WALL_S=12000` and `HARNESS_SOAK_KEEP_APPROVAL=1`. The scenario now logs units, buildings, days and memory every 120 wall s (`soak extra` lines in `scenario.log`). The fixture starts at day 205. Saves backup: `SaveGames-backup-286-0211`. The user's saves did not change.

| Run | Verdict | Wall s | Days run | Rate (game s per wall s) | Memory MB start / end | Pop-ups |
|---|---|---|---|---|---|---|
| s286-soak-1 | crash | 1399 | about 67 (day 205 to 272) | about 8 early | 4709 / 4458 | 0 |
| s286-soak-2 | fail (rate assert 1.11 < 1.5, by design) | 12054 | 333 (day 205 to 537) | 1.11 | 4194 / 1932 | 0 |

## Run 1: crash at day 272
- Exit code 3, `EXCEPTION_ACCESS_VIOLATION reading 0xffffffffffffffff`. Crash folder in `runs/s286-soak-1/crash/`.
- Call stack: a Lua error inside a UScriptStruct metamethod, then `luaL_traceback` -> `findfield` -> `lua_next` (UE4SS Lua table walk). It happened right after the log line `SACK step people` (InvasionMod `sack_and_terms`) at the end of the first Invasion Mod raid (day 265, 68 raiders).
- So a Lua error was raised while the mod read or wrote a struct in the sack "people" step, and UE4SS crashed while it built the traceback. The cause is not in the soak scenario.
- Not reproduced in run 2: the same step ran at day 254 (`SACK ... families 14->11`) and the run went on. Treat it as a rare mod or UE4SS crash. Needs its own change if the owner wants a fix (open question).

## Run 2: 333 days, no crash
- Wall 12014.7 s, 13337 game s, rate 1.11 for the whole run (overall = running). No stalled poll, no pop-up. 33 feedings.
- Memory: 4194 MB at start, falls to about 1.5 to 1.6 GB by day 311, then 1.8 to 1.94 GB. Growth after the drop is about +90 MB per 1000 wall s at first, then flat (1932 MB at the end).
- Approval write: the game overwrites it between polls (as before), the village still lived through winter. No defeat to day 537.
- Raids ran by themselves (Invasion Mod raid 2 at day 323, 104 raiders). No periodic raid was added (owner decision).

## Why the clock rate falls (task 1.2)
Units and buildings grow while days pass:

| Wall s | Day | Units | Buildings | Wall s per game day |
|---|---|---|---|---|
| 9 | 206 | 348 | 146 | about 17 (first 1000 s: 56 days) |
| 1958 | 287 | 491 | 161 | about 40 |
| 5862 | 384 | 598 | 192 | about 40 |
| 11706 | 530 | 725 | 228 | about 40 |

Nominal at 8x is 5 wall s per day. The rate was already near 1.0 from about day 290, when units were 490 and buildings 160, and then stayed near 1.0 while the village doubled. So the fall is a step in the first about 1000 s, not a steady slope with village size. A growing village alone does not explain it. Cause not found. Suspects: the 8x speed is capped by tick cost once the village passes a size, or the Invasion Mod or the harness polls (Approval write every 3 s, popup guard) cost time. A short run with another start fixture or without the Approval write would tell. This is an open question for the owner.

## Verdict on the owner decision
333 days is enough (owner, 2026-10-19). Run 2 gives 333 days with no crash and flat memory after the early drop. Run 1 shows one rare crash in the mod sack step.
