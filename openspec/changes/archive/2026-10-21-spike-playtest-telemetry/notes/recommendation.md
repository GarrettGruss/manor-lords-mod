# 1.8 Recommendation for `add-playtest-telemetry`

## Design

- Logger: a player-safe module (not `HarnessLog`) that opens `Saved\ProbeTelemetry`-style folder `Saved\InvasionMod\logs\session-<time>.log`, flushes every line, builds paths with forward slashes, keeps the last N sessions. It must not use `HarnessLog` or `HarnessTelemetry` (refused in a release). `ManorCore.log` uses it when `HarnessLog` is absent. Cost is 10 us per line, so no batching is needed.
- Levels: `error`, `warn`, `decision` (default), `trace` (off). A `decision` line holds the inputs and the result of one decision. Write an intent line (flushed) before a call that can kill the game, and a result line at +N game seconds after a timed effect (note `bug-replay.md`). Rate-limit repeated messages (38 percent of the soak lines were one repeating line).
- Budget: about 76 KB per game year at `decision` level (about 680 lines); cap each session log at 5 MB and keep 5 sessions. State sample once per game day (1 KB, 0.38 MB per year) with a `custom` object that holds tracker values next to game values (raids, vassals); cap 2 MB.
- Crash detection: marker `session.marker` with a heartbeat every 3 s, plus the rule "marker says `running` AND a folder in `Saved\Crashes` is newer than the session start". There is no quit hook (note `crash-detection.md`), so the marker alone gives false alarms.
- Report: `Saved\InvasionMod\reports\report-<time>\` with logs (crashed session and current), samples, `report.json` (versions, settings, features), the tester text, the newest crash folder, the save if the box is ticked. Zip it stored: 4.5 MB takes 0.2 s in one go; build it in 256 KB to 1 MB steps per tick if the game must not hitch. Find the newest save and crash folder with `io.popen('dir /b /o-d')`.
- Menu: a runtime-built widget with `MultiLineEditableTextBox`, `CheckBox` (ticked by default) and `Button` works without a pak (note `menu-text-box.md`). Typing works after `SetKeyboardFocus`.

## Open points for the owner

1. Is "closed unexpectedly" offered only after a UE crash (a crash folder is there), not after a kill or a hang? The menu button stays for those.
2. Hotkeys while the text box has focus: needs a spike with a real keyboard (and `SetInputMode_UIOnly`).
3. Where is the button: the menu framework of #308 is not on `main`; the feature depends on it.
4. Is a console flash from `os.execute` and `io.popen` (`mkdir`, `dir`) acceptable on a tester's PC?
5. UE4SS crash in `ltable.c` in run ptt-soak-2 (one of 3 soak runs): should it get its own bug issue before more `LoopAsync` loops are added?
6. A clean picture of the menu needs slot 0.
