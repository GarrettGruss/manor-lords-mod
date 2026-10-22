# 1.1 Crash-safe log

## Question

Can a player-safe Lua logger write each line to `%LOCALAPPDATA%\ManorLords\Saved\InvasionMod\logs\` and keep its lines when the game process is killed?

## Method

- Probe: `mod/shared/HarnessTelemetryProbe` (`log_start`, `burst`), loaded by the harness-only probe mod `mod/PlaytestProbe`. Test scenario: `harness/scenarios/probe_playtest_crash.py` (hidden).
- `io.open(path, "a")` with `file:flush()` after every line. A second control file gets the same lines and is never flushed (default C buffer).
- A `LoopAsync` writes a numbered tick line every second. The scenario writes a burst of 500 lines, then starts a burst of 100000 lines and kills only its own game process (psutil `kill()` of the PID of the run) 0.6 s later, in the middle of the burst.
- The files are read in Python after the kill.

## Result (run ptt-crash-3, slot 2)

| File | Lines | Bytes | Last line |
|---|---|---|---|
| flushed log | 63603 | 1884730 | complete (`burst 63095`) |
| control, no flush | 63517 | 1882140 | cut in the middle of a line (`bur`) |

- Flushed log: no gap in the sequence numbers and no broken line. A kill in the middle of a burst loses no line.
- Control log: 86 lines (2590 bytes, the C buffer) are lost, and the last line is cut.
- The marker file (see `crash-detection.md`) stayed with `"state":"running"` and a heartbeat 3 s before the kill.
- Cost: 10 us per flushed line (500-line burst). The 100000-line burst wrote about 63000 lines in 0.6 s (about 100000 lines per second). A `decision` log of a few lines per game minute is negligible.
- Ticks (async thread) and bursts (game thread) wrote to the same file without a damaged line.

## Other runs

ptt-crash-1 (a harness error: `ctx.run.id` does not exist) and ptt-crash-2 (the probe refused the path, because `LOCALAPPDATA` has backslashes) gave no result. They are probe bugs, not game facts. Lesson for the feature: build the base path with forward slashes.

## Not verified

- Power loss or a Windows crash: after `flush()` the data is in the OS cache, not on disk. A process kill (the case here, and a game crash) is covered.
- A path with non-ASCII characters in the user name.
- A disk that is full, or a folder that the user cannot write.
- A crash from inside UE. The harness kill is a `TerminateProcess`. Open file data is owned by the OS after `flush()`, so a UE crash should behave the same.

## Note on the folder name

The runs wrote to `Saved\InvasionMod`. Afterwards the probe folder was renamed `ProbeTelemetry` (test_boundary forbids the mod name in harness code). Run ptt-files-3 re-checked the renamed code (files and zip pass).
