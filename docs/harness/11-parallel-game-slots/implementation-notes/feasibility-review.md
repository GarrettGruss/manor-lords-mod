# Feasibility review (2026-10-17)

Code review only. No game was started. The spikes in the README plan (steps 1 and 2) are still needed.

## Verdict
Concurrent sessions look possible, but the README design has gaps. The shared real save folder is the largest one.
The design must change in three places before step 3.

## Shared state found in the code

| Shared thing | Where | Already isolated? | What slots need |
|---|---|---|---|
| Win64 folder (exe, UE4SS, Lua mods) | `runlib/game.py` `GameInstall.win64` | No | Per-slot copy (README design 1) |
| `HarnessLog` output | `mod/shared/HarnessLog/HarnessLog.lua` | Yes, `HARNESS_RUN_DIR` per run | Nothing |
| Bridge folder | `runlib/scenario.py` (`UE4SS_BRIDGE_DATA_DIR`) | Yes, per run | Nothing |
| Config, logs | private `LOCALAPPDATA` | Yes | Nothing |
| **Saves** | `runlib/saveslots.py` | **No.** The game loads saves only from the REAL folder (`06-.../fixture-load-bug.md`) | See gap 1 |
| **Pak mods** | `runlib/paks.py`: `Content/Paks/~mods` | No | See gap 2 |
| Crash reports | real `%LOCALAPPDATA%\...\Crashes` | No | Match by pid and time (README design 6) |
| Process search | `game.py` `find_game_processes`, `game-close.ps1`, `game-launch.ps1`, `deploy.ps1` | No, by name | By exe path (README design 5) |
| Run lock, iteration counter | `runlib/runfolder.py` | No | Per-slot lock (README design 3) |
| OS mouse, focus, screen capture | `runlib/osinput.py`, `windows.py`, `screenshot.py` | No | `EXCLUSIVE` scenarios (README design 9) |

## Gap 1: the real save folder is shared
- Each run installs its fixture into the real save folder under `saveGame_<max+1>` and removes it in teardown.
- Two runs that install at the same time can pick the same number. `install` refuses existing files, so one run fails, or the race is lost between the check and the write.
- The ledger `runs/.installed-slots.json` is one file. Two writers can lose an entry.
- The save hash guard hashes the whole real folder before and after a run. Another slot's install or removal changes that hash. Every parallel run would report a false change, or the guard would have to be weakened.
- Fix: a short global lock around "choose slot + install + ledger write" and around removal. Change the guard to ignore files listed in the ledger, and to check only the user's own files. Each run keeps its own fixture slot number.
- Open: does the game's load list cope with saves added by another process while it is in the menu? `HarnessBoot` finds the slot by index from `SlotNameFromIndex`. Check in the spike.

## Gap 2: a content junction shares `~mods`
- The README plans a junction to `ManorLords\Content`. Paks live in `Content\Paks\~mods`, so all slots would share the same pak mods. An A/B test with `--pak` would break.
- Fix: per slot, make a real `Content\Paks\` folder with hard links (or symlinks) to the 20 original pak files, and a real per-slot `~mods`. Junction the rest of `Content`. Hard links need the slot on the same drive as the game.
- Check in the spike that the game accepts linked pak files.

## Gap 3: crash reporter and stop
- `find_crash_reporters` finds `CrashReportClient.exe` by name. A teardown could close the reporter of another slot. Match by parent pid or command line.

## Lower risks
- RAM: 16 GB, about 1.3 GB per game. Three slots fit (README budget). VRAM 8 GB is likely the real cap with three rendering windows.
- CPU: game clock rate may drop at 8x. Time-limited waits (`timectl.py`) use game clock with a wall cap, so slower clocks lead to timeouts, not wrong results. Measure in spike 2.
- A single-instance mutex is not known. The spike answers this in minutes.

## Expected gain
- Most runs take 40 to 70 s, and about 30 s of it is boot. With 3 slots a 15 min suite drops to about 5 to 7 min.
- Scenarios that use the OS mouse (`place_building`, `policy_menu`, `manor_storage*`, `rebuild_cost`, probes) do not gain. They run alone.

## Recommended next step
Spike 1 and 2 from the README, with these added checks: a second game with an `~mods` folder that differs, two fixture installs in the real save folder at once, and the load list in the menu when a save appears late.
