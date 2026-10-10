# Spec 03: Run launcher and run summary

Status: done for steps 1 to 6 (run folder, real phases, scenarios, screenshots, five runs, old scripts retired). Some open questions are not tested, see "Answers to the open questions".
Roadmap phase: 5 (outer harness).

## Goal
One command runs one complete test iteration of a mod, with no human input, and writes `runs/<id>/summary.json`.
The agent reads `summary.json` first. It opens screenshots and logs only if the summary says to.

The iteration: deploy the mod, start the game, load the test save, run a scenario, collect results, stop the game.

## Non-goals
- The content of scenarios and the telemetry sampling (planned spec 04). This spec only defines how a scenario is run and how its result is stored.
- MCP tools for the harness (planned spec 05).
- Making the simulation deterministic.

## Background (verified, see the other specs)
- Spec 01: the bridge gives live access to the game. Each run needs its own bridge folder.
- Spec 02: `HarnessBoot` loads the test save and reports `READY` with the game paused. 10 of 10 cold starts worked, 42 to 44 s each.
- The game does not close on a close request. The harness stops it with a kill.
- A direct launch of `ManorLords-Win64-Shipping.exe` passes environment variables to the mods (`implementation-notes/direct-launch-with-environment.md`).
  Each run can use its own folder with `HARNESS_RUN_DIR`.
- `harness/game-launch.ps1`, `game-close.ps1` and `launch-series.ps1` existed, but they use Steam and one shared folder. The run launcher replaces them for runs.
- Crash data: UE crash reports are in `%LOCALAPPDATA%\ManorLords\Saved\Crashes\`, and UE4SS keeps its own log and crash dumps in `ue4ss\`.

## Design

### Language and entry point
Python 3.12 in the project `.venv` (managed with uv). Reasons: the bridge client is Python, and screenshots (`mss`) and process control (`psutil`) are easy.
Entry point: `python harness/run.py --scenario <name> [--run-id <id>] [--keep-open]`.
No PowerShell wrapper is needed.
Exit code: 0 pass, 1 fail, 2 crash, 3 timeout, 4 harness error.

### Run folder
`runs/<id>/` with `<id>` = `YYYYMMDD-HHMMSS` plus a short suffix. It holds everything for the run:

| File | From |
|---|---|
| `summary.json` | the launcher (written last, always) |
| `config.json` | the launcher: scenario, test save, limits, environment, mod hashes |
| `boot.json`, `ready.marker`, `mod.log` | HarnessBoot and HarnessLog (through `HARNESS_RUN_DIR`) |
| `bridge/` | UEBridge request and response files |
| `scenario.json` | the scenario result (written by the scenario code) |
| `screenshots/` | the launcher |
| `UE4SS.log`, `crash/` | copied by the launcher at teardown |

### Phases
Each phase has a time limit. The launcher records the start, the end and the result of each phase in `summary.json`.

1. `preflight`: check that Steam is running, that no game process is running (kill a stale one and record it), and that the `.venv` and the test save exist.
   Take the run lock (`runs/.lock`) so two runs cannot overlap.
2. `deploy`: run `harness/deploy.ps1`. Verify the hashes. Record the mod hashes.
3. `launch`: start the game with Python `subprocess.Popen`. The working folder is the `Win64` folder. Set these variables:
   `HARNESS_RUN_DIR`, `HARNESS_AUTOBOOT=1`, `HARNESS_TEST_SAVE`. Do not use Steam URLs.
4. `boot`: wait for `boot.json` to say `READY` or `FAILED`. Check that the process is alive every second. Limit 300 s.
5. `scenario`: load `harness/scenarios/<name>.py` and call `run(context)`. The context gives the bridge client, the run folder, a logger, and helpers
   (read the clock, unpause for N game seconds, pause). The scenario returns a result and may raise. Its limit is set by the scenario, with a hard cap.
6. `collect`: take a screenshot of the game window (at the start and at the end of the scenario), copy `UE4SS.log`, and copy UE crash reports that are newer than the run start.
7. `teardown`: stop the game (close request, then kill). Wait until the process is gone. Release the lock.

A failure in a phase skips the later phases, except `collect` and `teardown`. These two always run.

### Verdict
| Verdict | Meaning |
|---|---|
| `pass` | all phases ok, and the scenario returned pass |
| `fail` | the scenario ran and failed its assertions, or HarnessBoot ended in `FAILED` |
| `crash` | the game process ended during `boot` or `scenario` without a teardown request, or a new crash report exists |
| `timeout` | a phase hit its time limit |
| `harness_error` | the launcher itself failed (preflight, deploy, an unexpected exception) |

A crash is a result with logs. It is not a harness error.

### summary.json (first version)
Keep it small (about 1 to 2 KB), so the agent can read it in one step.

```json
{
  "run_id": "20261009-233000-a1b2",
  "verdict": "pass",
  "reason": null,
  "scenario": "smoke",
  "started": "2026-10-09T23:30:00Z",
  "duration_s": 118,
  "phases": [{"name": "boot", "ok": true, "seconds": 43}],
  "boot": {"state": "READY", "pause_calls": 2},
  "scenario_result": {"asserts": [{"name": "clock moves", "ok": true, "value": 1, "range": [0, 5]}]},
  "crash": null,
  "artifacts": {"screenshots": ["screenshots/start.png"], "logs": ["mod.log", "UE4SS.log"]},
  "environment": {"game_build": "...", "ue4ss": "...", "mods": {"HarnessBoot": "<sha256>"}, "test_save": "saveGame_0"}
}
```

### Rules
- Never write to the user's saves. (First version: the test reads `saveGame_0`. A separate copy is planned, see the open questions.)
- Localhost only. Single-player only. Cap the iterations: a counter file `runs/.iterations` and a `--max-runs` limit for each session.
- Every wait has a time limit. Every external process call has a time limit.
- Write `summary.json` atomically, in a `finally` block, so that it exists even after an error.
- The summary says what is unknown. Never report `pass` for a phase that was skipped.
- Use per-run folders only. No state is shared between runs, except the run lock and the iteration counter.

## Plan
1. Write the run folder, config and `summary.json` code, with fake phases and unit tests (no game). **Done.** (`implementation-notes/step1-runlib-design.md`)
2. Add `preflight`, `deploy`, `launch`, `boot` and `teardown` with the real game. **Done.** (`implementation-notes/step2-real-phases.md`)
3. Add the scenario runner and a `smoke` scenario. **Done.** Scenarios are modules in `harness/scenarios/` with `LIMIT_S`. `smoke` takes about 9 s. (`implementation-notes/step3-6-scenarios-screenshots.md`)
4. Add `collect`: screenshots, `UE4SS.log`, crash reports and dumps. **Done.** Tested with a game killed in the middle of the scenario (verdict `crash`).
5. Run 5 runs in a row. **Done.** 5 of 5 `pass`, 42 to 45 s each. Self tests: `fail` (exit 1) and `timeout` (exit 3) work.
6. Retire `launch-series.ps1` and the Steam-based launch scripts. **Done.** `launch-series.ps1` is replaced by `harness/run_series.py`. `game-launch.ps1` and `game-close.ps1` stay for manual use. The harness README starts with `run.py`.

## Open questions
- Screenshots: does `mss` capture the game window when it is not in front, or on another monitor? Does the "A New Message" banner cover the screen?
- Where does the UE crash reporter write the crash folder, and how fast? (An earlier crash: `...\Saved\Crashes\UECC-Windows-<id>_0000`.)
- Steam closed: does a direct launch still work? If not, the launcher must start Steam, or fail with a clear error.
- Test save copy: does the load screen list a slot with a custom name? If it does, copy `saveGame_0` to a harness slot for each run.
- Can the scenario unpause the game reliably, given that the game restarts the clock by itself after a load?
- Is a game started with Python `Popen` killed when the launcher exits? Decide whether the game must outlive the launcher (`--keep-open`).

## Answers to the open questions
Details and numbers: `implementation-notes/step3-6-scenarios-screenshots.md`.
- Screenshots: `mss` captures screen pixels, so a window in front of the game is in the picture (the UE4SS GUI was seen). The picture shows the real game otherwise.
  Another monitor, a minimized window and the "A New Message" banner were not tested with the real game.
- UE crash folder: not answered. A terminate does not produce one. No real UE crash happened in these steps.
- Steam closed: TESTED 2026-10-10 (the user closed Steam). The direct launch works without Steam, see implementation-notes/direct-launch-with-environment.md. Old text: not tested (asking Steam to exit is not safe). `preflight` fails with a clear message if Steam is not running (unit test only).
- Test save copy: not tested. The runs only read `saveGame_0`, and its hash did not change.
- Unpause after a load: works in the runs made (7 of 7 smoke runs), because HarnessBoot holds the pause first.
- `Popen` and launcher exit: not tested. The launcher always stops the game in `teardown`. `--keep-open` leaves it on purpose, and was not tested with the real game.

## Acceptance criteria
- One command from the repo root runs a complete iteration and writes `summary.json` for these outcomes: `pass`, `fail` (a failing assertion), `crash` (game killed in the middle of the scenario), `timeout`, and `harness_error`.
- Five runs in a row all end with `pass`, each in its own run folder, and the game is not running afterwards.
- A stale game process from an earlier run does not break the next run, and the summary records it.
- `summary.json` is under 4 KB and is enough to decide what to do next without opening other files.
- No file outside `runs/` and the game's `ue4ss` folder is changed by a run, and no save file is changed.
