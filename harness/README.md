# Harness

## Run a test (run.py)

`harness/run.py` is the normal way to test a mod. One command runs one complete iteration with the real game
and writes `runs/<id>/summary.json` (spec 03). Read `summary.json` first. Open screenshots and logs only if it says to.
Steam must be running. The game must not be started by hand.

```powershell
.venv\Scripts\python.exe harness\run.py --list-scenarios
.venv\Scripts\python.exe harness\run.py --scenario smoke [--keep-open] [--run-id ID] [--max-runs N]
.venv\Scripts\python.exe harness\run_series.py --scenario smoke --runs 5
```

Exit code: 0 pass, 1 fail, 2 crash, 3 timeout, 4 harness error.
`run_series.py` runs the launcher N times, prints a table and writes `runs\series-<time>.json`. It exits 0 only if all runs pass.

Setup (once). Install the locked packages (`psutil`, `mss`) into the project venv:

```powershell
uv pip install --python .venv\Scripts\python.exe --require-hashes -r harness\requirements.txt
```

To lock again after a change of `harness\requirements.in`:
`uv pip compile harness\requirements.in --generate-hashes --python-version 3.12 -o harness\requirements.txt`

### Phases
`preflight`, `deploy`, `launch`, `boot`, `scenario`, `collect`, `teardown`. `collect` and `teardown` always run.
The launcher starts `ManorLords-Win64-Shipping.exe` directly with `HARNESS_RUN_DIR`, `HARNESS_AUTOBOOT` and `HARNESS_TEST_SAVE`.
Teardown ends the game with a terminate, because the game ignores a close request. `--keep-open` leaves the game running.
A stale game process is stopped in `preflight` and recorded in `notes`. A game that ends before teardown is a `crash`.
The test save `saveGame_0` is only read.

### Scenarios
A scenario is a module in `harness/scenarios/` with `LIMIT_S` (hard time limit, in seconds) and `run(ctx)`.
`ctx` gives `read_clock()`, `unpause()`, `pause()`, `read_calendar()`, `check(...)`, `check_range(...)`, `log.info(...)`, `run_dir` and `bridge`.
`run` returns `ctx.result()`: `{"passed": bool, "asserts": [...]}`. It is also saved as `scenario.json`. The log is `scenario.log`.
A scenario that is over its limit gives the verdict `timeout`.
Scenarios: `noop`, `smoke`. Test scenarios (`selftest-fail`, `selftest-timeout`) show with `--list-scenarios --include-test-scenarios`.

### Time control (`ctx.time`)
`set_speed(n)`, `run_game_seconds(n, speed)`, `run_game_days(n, speed)` and `pause()`. Speed 1, 2, 3 give clock rates 1, 4 and 8. One game day is 40 game seconds.
Each run function unpauses, sets the speed, waits, pauses, and checks that the clock stands still for 3 s. It returns
`{clock_start, clock_end, wall_s, paused_at_end, speed}` (days also have `days_start`, `days_end`, `day_start`, `day_end`).
It raises `TimeControlError` on a timeout, with a pause first. Days are counted with `daysTotal`, which does not wrap at the year end (365 days).
`absolute_day(date)` gives a day number for date asserts. A game pop-up (for example "Hunger!") pauses the game and gives a `TimeControlError`.
`set_speed` takes about 3 s, because it waits to see that the speed holds. Numbers: spec 04 `implementation-notes/time-measurements.md`.

### Telemetry
The mod `HarnessTelemetry` writes one JSON line every N wall seconds to `<run>/telemetry.jsonl` (clock, date, player, 7 regions, `errors`).
N is `--telemetry-interval` of `run.py` (default 5, 0 = off, saved in `config.json`). In a scenario: `ctx.telemetry.read()` and
`ctx.telemetry.window(start_clock, end_clock)`. `ctx.snapshot()` reads the same fields now through the bridge (a failed field is null and listed in `errors`).
Samples use wall time, so a short run at speed 3 has few samples. Other mods can add a metric with `HarnessTelemetry.register(name, fn)`.

### Assertions (`ctx.expect`)
`in_range`, `at_least`, `at_most`, `changed(name, before, after, min_delta, max_delta)`, `equals` and `eventually(name, fn, timeout_s)`.
Each adds `{name, ok, value, rule}`. Use ranges for simulation numbers. A failed assertion gives the verdict `fail`. `ctx.check` and `ctx.check_range` still work.

### Scenarios for spec 04
`time-advance` (2 game days at speed 3, about 54 s a run) and `telemetry-sanity` (40 game seconds at speed 1, then checks on the samples and a snapshot, about 89 s).
Each module has `DESCRIPTION` and `LIMIT_S`.

### summary.json size
`summary.json` leaves out empty fields, lists good phases as name and seconds only, and has a short `environment` (game build, save, `mods_hash`, git commit).
The full data (all mod hashes, limits, telemetry interval) is in `config.json`.

### Run folder
`summary.json`, `config.json`, `boot.json`, `ready.marker`, `mod.log`, `scenario.json`, `scenario.log`, `UE4SS.log`,
`bridge/`, `screenshots/start.png` and `end.png`, and `crash/` (new UE crash reports and UE4SS dumps).
Screenshots show the screen area of the game window. Windows in front of the game are in the picture. A failed screenshot adds a note and does not fail the run.

### Unit tests (no game)
```powershell
.venv\Scripts\python.exe -m unittest discover -s harness/tests -p "test_runlib*.py" -v
```

## deploy.ps1

Copies `mod/` into the UE4SS `Mods` folder (PowerShell 5.1):

- `mod/shared/*` is merged into `Mods\shared\`.
- Every other `mod/<name>/` is deployed to `Mods\<name>\` and set to `<name> : 1` in `mods.txt`
  (inserted above the `; Built-in keybinds` block; the first change backs up to `mods.txt.harness.bak`).
- Only changed files (SHA256) are copied; every deployed file is re-hashed afterwards and the script exits 1 on mismatch.
- `Mods\.harness-manifest.json` records what was deployed; `-Clean` only removes files listed there.

```powershell
powershell -ExecutionPolicy Bypass -File harness\deploy.ps1 -DryRun   # preview, changes nothing
powershell -ExecutionPolicy Bypass -File harness\deploy.ps1           # deploy
powershell -ExecutionPolicy Bypass -File harness\deploy.ps1 -Clean    # also remove manifest-listed files no longer in mod/
powershell -ExecutionPolicy Bypass -File harness\deploy.ps1 -GameDir 'D:\Games\Manor Lords'
```

If the game is running a warning is printed and the deploy continues (UE4SS hot reload).
`UE4SS-settings.ini` is never touched.

## Lua checks without the game

Run from the repo root. They need only `uv`.

- Syntax of all mods: `uv run --no-project --python 3.12 --with lupa python harness/tests/lua_syntax.py`
- HarnessBoot state machine against a fake game API:
  `uv run --no-project --python 3.12 --with lupa python harness/tests/boot_state_machine.py happy`
  Other modes: `noslot` (slot not in the list) and `missing` (save file missing).

These checks use Lua 5.4 from the `lupa` package. They find syntax errors and wrong variable names.
They cannot show that the real UE4SS API behaves like the fake one.

## Note: HarnessBoot auto-load switch

`HarnessBoot` loads the test save only when it is turned on.

- The file `ue4ss\harness\autoboot.enable` (in the game's `Win64` folder) turns it on. It was created for the first in-game test.
- While that file exists, every game launch that reaches the main menu loads `saveGame_0`.
- Delete the file to get normal play back. Ask Claude to delete it if you prefer.
- The run launcher (spec 03) will use the environment variable `HARNESS_AUTOBOOT=1` instead of this file.

## Disable or remove the harness

`uninstall.ps1` (PowerShell 5.1) has two modes. Both support `-DryRun` and `-GameDir`. Running twice is safe.

- Default (disable): deletes `ue4ss\harness\autoboot.enable` and sets every harness mod to `Name : 0` in `mods.txt`.
  All files stay. Run `deploy.ps1` to enable the harness again.
- `-Remove` (full uninstall): also deletes the files listed in the manifest, the harness lines in `mods.txt`,
  the manifest, and the folders `ue4ss\bridge` and `ue4ss\harness`.
  `mods.txt.harness.bak` is kept. The script prints its path, so you can restore it by hand.

```powershell
powershell -ExecutionPolicy Bypass -File harness\uninstall.ps1 -DryRun   # preview
powershell -ExecutionPolicy Bypass -File harness\uninstall.ps1           # disable
powershell -ExecutionPolicy Bypass -File harness\uninstall.ps1 -Remove   # full uninstall
```

The script never touches UE4SS, `dwmapi.dll`, stock mods, `UE4SS-settings.ini` or the game saves.
If the game is running, the script warns. Changes take effect at the next game start.
To turn UE4SS off for one launch, use the Steam launch option `--disable-ue4ss`.
To turn UE4SS off fully, rename `dwmapi.dll`. The script does neither.

## Start and stop the game by hand

These scripts are for manual use. `run.py` does not use them. They start the game through Steam (`steam://rungameid/1363080`),
so they cannot pass per-run settings. HarnessBoot is turned on with the switch file `ue4ss\harness\autoboot.enable`.
They never touch save files. `powershell -ExecutionPolicy Bypass -File harness\<script>.ps1`.

| Script | What it does |
|---|---|
| `game-launch.ps1` | Starts the game through Steam. Deletes the old `boot.json` and `ready.marker` first. With `-WaitForBoot` it waits for `READY` or `FAILED`. |
| `game-close.ps1` | Asks the game window to close, waits `-GraceSeconds` (default 20), then kills the game. `-NoForce` never kills. |

Exit codes of `game-launch.ps1`: 0 started (and `READY` with `-WaitForBoot`), 1 already running or HarnessBoot is off,
2 the process did not start, 3 HarnessBoot `FAILED` or the game ended, 4 timeout, 5 other error.
Exit codes of `game-close.ps1`: 0 closed or not running, 1 killed or still running, 2 error.
The old `launch-series.ps1` was removed. Use `run_series.py`.

## Agent tools

`mcp/harness_tools/` is an MCP server (`manor-harness`, spec 05). An agent uses it instead of shell commands.
It is registered in `.mcp.json`. To start it by hand: `$env:PYTHONPATH = "mcp;harness"; .venv\Scripts\python.exe -m harness_tools`.

A run takes 1 to 3 minutes, so the tools start and poll:
1. `run_scenario(name)` starts `harness/run.py` in the background and returns `{"status": "started", "run_id": ...}`.
2. `wait_for_run(run_id)` waits up to 45 s (cap 50 s). It returns the summary, or `{"status": "running", ...}`. Call it again.
3. `read_summary`, `read_log`, `read_telemetry` and `list_screenshots` read the result.

Other tools: `list_scenarios`, `list_runs`, `game_status`, `stop_game` (refuses while a run holds the lock).
The read-only tools are allowed in `.claude/settings.json`. `run_scenario` and `stop_game` ask first.
`HARNESS_RUNS_ROOT` moves the runs folder. It is for tests only.
Tests: `.venv\Scripts\python.exe -m unittest discover -s harness/tests -p "test_harness_tools*.py"`.

## Regression suite

`harness/suite.py` runs many scenarios in one command and writes one report (spec 08).
Each run is a separate `run.py` process, so a crash in one run does not stop the suite.

```powershell
.venv\Scripts\python.exe harness\suite.py --suite core [--max-minutes N] [--runs-root DIR]
.venv\Scripts\python.exe harness\suite.py --list
.venv\Scripts\python.exe harness\suite.py --update-baseline <scenario> [--from-last N]
```

Suites are files `harness\suites\<name>.json`: `smoke` (1 run), `core` and `soak` (smoke x10).
Each entry has `scenario`, `repeat`, and optional `fixture` and `optional`. An `optional` entry is skipped, with a note, when its scenario does not exist yet.
The suite file has `time_budget_s` and `flake_retries`. A failed run is retried up to `flake_retries` times. A scenario that fails and then passes is marked `flaky`.

Output: `runs\suite-<id>\report.json` (under 4 KB for a passing suite) and `report.md`. History: `runs\suite-history.jsonl`.
Exit code: 0 pass (non-strict drift is allowed), 1 fail or strict drift, 2 crash or timeout left after retries, 3 time budget or iteration cap ended the suite early, 4 harness error.
If several apply, the order is 4, 3, 2, 1.

Baselines are in `harness\baselines\<scenario>.json`: `{"metrics": {"duration_s": [lo, hi]}, "strict": [...]}`.
A metric outside its range is `drift`. Drift fails the suite only for metrics listed in `strict` (add them by hand).
Only `--update-baseline` writes a baseline file. It uses the last N passing runs and widens min and max by 20% of the spread (at least 10% of the largest value). Review the file before you commit it.

Test the suite without the game: `HARNESS_SUITE_LAUNCHER` (or `--launcher-command`) replaces `run.py`.

```powershell
.venv\Scripts\python.exe -m unittest discover -s harness/tests -p "test_suitelib*.py" -v
```
