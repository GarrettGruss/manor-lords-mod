# 1.6 Volume

## Question

How much log does a soak make at a `decision` level, per game year and per feature?

## Method

Run ptt-soak-3 (slot 2): test scenario `soak-days`, `HARNESS_SOAK_WALL_S=1800`, `HARNESS_SOAK_KEEP_APPROVAL=1`, the fixture `base`. The probe mod was disabled for this run. The Invasion Mod features already log one `info` line per decision through `ManorCore.log`, so the volume is counted from `mod.log` after the READY line. Harness lines (`UEBridge`, `HarnessCommands`, `HarnessBoot`, `HarnessActions`, `HarnessTelemetry`) are left out, because a player has none of them.

Extrapolation: the run covered only 78 game days (the game ran at 1.73x of real time, not at the nominal 8x: 3139 game seconds in 1813 wall seconds). Per game year = value x 365 / 78 (x 4.68). A longer soak was not possible inside the 60 minute limit, and run ptt-soak-2 (first attempt, 3000 s) crashed in UE4SS after 65 s (see below). The scenario verdict is `fail` only because the days share rule (72 to 396 days) was missed by a slow game; the game did not crash.

## Result

After READY, 78 game days: 146 lines, 16247 bytes (111 bytes per line).

| Tag | Lines | Note |
|---|---|---|
| `bandits` (`game rewrote order`) | 55 | a repeating message, noise: a candidate for rate limiting |
| `raid_behavior` (`day`, `plunder`, start, end, role) | 50 | one raid in the window |
| `invasion` (`banner`, `difficulty`, `subjugation`) | 26 | banner and difficulty prompt lines repeat each day |
| `sack_and_terms`, `terms`, `tribute` | 6 | |

- Per game year: about 680 lines and about 76 KB. For 2 game years: about 150 KB. A raid-heavy year is higher (the 50 `raid_behavior` lines came from one raid), but even 10 times this is 1 MB per year.
- State samples: `HarnessTelemetry` samples are 1030 bytes each (7 regions). One sample per game day is 0.38 MB per game year; one per 5 game days is 0.08 MB.
- The 55 noise lines show the cost of an unleveled log: 38 percent of the lines are one repeating message.
- The file write cost is 10 us per flushed line (note `crash-safe-log.md`), so even 100 lines per game minute costs nothing.

## Run ptt-soak-2 (crash)

The first soak run crashed after 65 s with `EXCEPTION_ACCESS_VIOLATION` in `UE4SS!mainpositionTV() ... ltable.c:183` (a Lua table access in UE4SS), exit code 3. The probe mod was loaded but idle in that run. The cause is not known. It is a UE4SS Lua state crash, possibly a thread race between `LoopAsync` loops and the game thread; it may be an existing flake. Worth a look in the feature change: the new logger will add a `LoopAsync`, so run `soak-days` with the logger on before release. The crash report is in `runs/ptt-soak-2/crash/`.

## Not verified

- A full 2 game year soak (the unmanaged village is defeated in winter, and the run was slow).
- A raid-heavy or sack-heavy year: more lines of a different kind.
- Lines of the features that did not act in 78 days (tech tree, liege influence, refugees, manor stronghold).
