## Context

Explore session with the owner on 2026-10-22 (see the proposal for the decisions). Existing parts:
- `HarnessLog` flushes each line, but it is harness-only. `HarnessTelemetry` samples state every 5 s into the run folder; harness-only too.
- `ManorCore.log` uses `HarnessLog` when present and `print()` otherwise.
- The release tool `harness/release.py` refuses a hard `require` of a harness-only module.
- ModState keys are saved with the game.
- The menu framework of #308 (`core/menu.lua`) and the raid menu of #340 show mod menus; a text box was never built.
- The test scenario `soak-days` (`spike-two-year-soak`) samples a long run.

Target shape of the later feature (to be confirmed by this spike):

```
  session N                          session N+1
  marker "running" + heartbeat       marker of N still there -> "closed unexpectedly"
  log lines, flushed each            -> offer: Create a bug report?
  crash -> marker stays              mod menu -> [Report a bug] -> same builder
  clean exit -> marker removed

  report builder -> Saved\InvasionMod\reports\report-<time>\ + report-<time>.zip
     logs (crashed session + current), state samples, report.json (versions, settings,
     features), tester text, newest UE crash folder, save copy if the box is ticked
```

## Decisions for the spike

- Probes live in a probe module (for example `mod/shared/HarnessTelemetryProbe/`) and hidden probe test scenarios. No feature code.
- Crash test: start a run with `--keep-open`, log a numbered line every game second, kill the game process from Python, then read the log file. Count lost lines.
- Quit hook: look for a reflected function that runs on quit (game instance shutdown, `ReceiveEndPlay` of the pawn or world) with a hook; fall back to a heartbeat time in the marker.
- File access: read `saveGame_<n>.sav` of the fixture copy in the run's private `LOCALAPPDATA`, never the user's folder. Read the newest folder under `Saved\Crashes` if one exists (the harness copies crash reports, so a test run can make one by the kill above).
- Zip: write a stored zip with a Lua CRC32; time it for the fixture save (about 2.6 MB) in one go and in steps of N KB per tick.
- Text box: try an `EditableTextBox` widget in a probe menu.
- Volume: run `soak-days` with probe decision lines from the main features at a `decision` level; report MB per game year and lines per feature.
- Bug replay: for #337, #357 and #325, list the events a bundle would need to show the cause.

## Risks

- A text box may need a pak widget; record the cost.
- UE4SS `io` may be sandboxed for some folders.
- A pure Lua zip may be slow; steps over frames are the fallback.
