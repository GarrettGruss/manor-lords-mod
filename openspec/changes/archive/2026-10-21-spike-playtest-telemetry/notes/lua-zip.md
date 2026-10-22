# 1.4 Lua zip

## Question

How long does a pure Lua uncompressed ("stored") zip of a report with a save take, and can it run in steps without freezing the game?

## Method

`HarnessTelemetryProbe.zip_start` writes a stored zip (local headers, central directory, CRC32 in pure Lua). Entries: the fixture save (2632685 B), the session log (1884730 B) and `report.json`: 4.5 MB in total. It reads each file twice (once for the CRC, once to copy), in 64 KB chunks. Run ptt-files-2 (slot 2), test scenario `probe_playtest_files.py`.

Frame stall: a Python thread read the game clock through the bridge every 50 ms during each zip. A bridge call runs on the game thread, so its latency stands in for the frame time. Idle: mean 84 ms, max 109 ms (the polling itself is slow).

## Result

| Mode | Lua time | Longest step | Bridge read latency during the zip |
|---|---|---|---|
| one go | 195 ms | 195 ms (one call) | no read finished in the 0.31 s window: the game thread was blocked about 0.2 to 0.3 s |
| 64 KB every 20 ms | 3251 ms | 4 ms | mean 85, max 156 ms (idle level) |
| 256 KB every 20 ms | 965 ms | 12 ms | mean 72, max 110 ms |
| 1024 KB every 20 ms | 396 ms | 45 ms | mean 90, max 110 ms |

- All four zips pass `zipfile.ZipFile.testzip()`, and the save and the log inside are byte-identical to the originals. The format is standard (stored, no ZIP64, fine below 4 GB).
- A zip of a report with a save takes about 0.2 s in one go: a short hitch. Steps of 256 KB to 1 MB per 20 ms tick give no measurable stall and finish in 0.4 to 1 s.
- The step loop was a `LoopAsync`, so it may run off the game thread. A tick reads and writes only files, no UObject.

## Not verified

- A zip that opens in Windows Explorer or is accepted by an upload site (only Python was used as the reader).
- A save that is bigger (the fixture is 2.6 MB; a late game may give 10 MB).
- Compression. It is not needed: saves are already compressed, so the size is about the sum of the parts.

## Note on the folder name

The runs wrote to `Saved\InvasionMod`. Afterwards the probe folder was renamed `ProbeTelemetry` (test_boundary forbids the mod name in harness code). Run ptt-files-3 re-checked the renamed code (files and zip pass).
