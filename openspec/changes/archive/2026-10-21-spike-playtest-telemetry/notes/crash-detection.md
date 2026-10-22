# 1.2 Clean exit vs crash

## Question

Can the mod tell a clean exit from a crash (a quit hook, or a heartbeat in a marker file), and detect the crash at the next start?

## Method

- Marker file `Saved\InvasionMod\session.marker`, written atomically (`.tmp`, `os.remove`, `os.rename`) at start and every 3 s: `{"state":"running","heartbeat":<unix time>,"log":"<session log path>"}`.
- Quit signals tried (runs ptt-quit-1 and ptt-quit-2, test scenario `probe_playtest_quit.py`):
  - `RegisterHook` on `GameInstance:ReceiveShutdown`, `KismetSystemLibrary:QuitGame`, `UserWidget:Destruct`, `Actor:ReceiveEndPlay`, `Actor:ReceiveDestroyed` and `PlayerController:ClientReturnToMainMenuWithTextReason`. Each hook logs to the flushed log.
  - A table with a `__gc` finalizer. Lua closes the mod state when UE4SS ends (the UE4SS log shows "Event loop end").
- The scenario closes the window of its own game with `WM_CLOSE` (a clean exit, no mouse). The game ended in 5 to 6 s.
- Next-start detection (run ptt-files-2): the marker and logs of the killed run ptt-crash-3 were copied into the private appdata, then `detect_previous` ran.

## Result

- Detection of a stale marker works: `crashed=true`, heartbeat age 218 s, path of the crashed log (ptt-files-2).
- No quit hook fires. After `WM_CLOSE` the log has 0 hook lines in both runs, although the hooks were registered (`GameMode:ReceiveEndPlay` and `PlayerController:ConsoleCommand` do not exist as UFunctions). The `__gc` finalizer did not run either: no `gc` line, and the marker was still there. The tick loop simply stops.
- So a clean quit by the window close and a crash look the same to the mod: a marker with `running`. A marker alone would show "closed unexpectedly" at every start. It is not usable alone.
- The exit through the in-game menu was not tried (it needs a mouse). `QuitGame` has a native hook, so that path would be seen if the menu calls the Blueprint node. Not verified.

## Options for the feature

1. Marker plus UE crash folder (recommended). Offer the report only if the marker says `running` AND a folder in `Saved\Crashes` is newer than the session start (the folder mtime, or `<TimeOfCrash>` in `CrashContext.runtime-xml`). A UE crash writes a folder (the real user folder has 120 of them). A kill by the Task Manager or a hang writes none and is not offered; the menu button covers it.
2. Find the exit function of the game's own menu and hook it (needs a spike with a real click).
3. A watcher process started with `os.execute` that waits for the game PID. Not recommended: it is a console process, antivirus may object, and it adds a second thing that can fail.

## Not verified

- A real UE crash with the marker. The crash folder is written by `CrashReportClient` after the process ended. Its mtime against the last heartbeat was not measured. The harness test `selftest-crash` makes a crash, but it uses a call that the Safety list forbids for probes, so it was not used.
- The exit through the in-game menu. Alt+F4 is the same as `WM_CLOSE`.

## Note on the folder name

The runs wrote to `Saved\InvasionMod`. Afterwards the probe folder was renamed `ProbeTelemetry` (test_boundary forbids the mod name in harness code). Run ptt-files-3 re-checked the renamed code (files and zip pass).
