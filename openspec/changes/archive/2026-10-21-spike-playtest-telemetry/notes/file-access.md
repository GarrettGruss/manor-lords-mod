# 1.3 File access

## Question

Can UE4SS Lua `io` read a save file and the newest folder in `Saved\Crashes`, and write a report folder?

## Method

Test scenario `harness/scenarios/probe_playtest_files.py`, run ptt-files-2 (slot 2). The scenario copied a fixture save (`harness/fixtures/saves/base/slot.sav`, 2632685 bytes) and two real UE crash folders (read only from the user's `Crashes` folder) into the PRIVATE appdata of the run, under `ManorLords\Saved\InvasionMod\fixture\` and `ManorLords\Saved\Crashes\`.

The harness does not keep a save copy in the private appdata (the game loads saves only from the real folder), so the scenario made the copy. The probe refuses any path that contains `savegames`, so no real save was touched.

## Result

- Read a binary file: `io.open(path, "rb")`, `seek("end")` for the size, `read(65536)` chunks. Size 2632685 read, CRC32 (pure Lua) equal to Python `zlib.crc32` (2874399708). 113 ms with the CRC.
- Newest crash folder: `io.popen('dir /b /ad /o-d "<Crashes>"')` works in UE4SS and gives the newest folder first (it found the one with the newer mtime of two). `dir /b /a-d` lists its files: `CrashContext.runtime-xml` (48 KB), `CrashReportClient.ini` (160 B), `UEMinidump.dmp` (0.83 MB). `io.open` reads the xml.
- `popen` and `os.execute` start `cmd`. No flash was visible on the screenshots. A console flash on a player PC is not excluded.
- Write: `os.execute('mkdir ...')` (`HarnessLog` already uses it) and atomic write (`.tmp` plus `os.rename`) work. The report folder `reports\report-<time>\` got `report.json`, `session.log` (a copy of the log) and `tester-text.txt`.
- Lua cannot list a folder without `popen dir`. This is the only way found to get "the newest save" or "the newest crash".
- A raw byte of the save in a command answer broke the harness answer (ptt-files-1 failed on this, the answer was not valid UTF-8). It is a probe issue, not a game issue.

## Not verified

- A read of the real `SaveGames` folder in a player's game (refused on purpose here). It is the same `io.open` call. The open of a save that the game writes at that moment was not tried.
- Paths with non-ASCII characters or spaces in the user name (the probe path check refuses them, and `cmd` code pages may break `dir` output).
- Speed of `dir` with many folders (120 exist in the real `Crashes`; one call was fast, not timed).

## Note on the folder name

The runs wrote to `Saved\InvasionMod`. Afterwards the probe folder was renamed `ProbeTelemetry` (test_boundary forbids the mod name in harness code). Run ptt-files-3 re-checked the renamed code (files and zip pass).
