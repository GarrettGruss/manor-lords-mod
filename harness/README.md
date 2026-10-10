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

Suites are files `harness\suites\<name>.json`: `smoke` (1 run), `core` (smoke x2, time-advance x2, telemetry-sanity x1; about 4.7 minutes), `soak` (smoke x10) and `selftest` (a failing, a timing-out and a passing scenario; it checks the suite itself and exits 2 on purpose).
Each entry has `scenario`, `repeat`, and optional `fixture` and `optional`. An `optional` entry is skipped, with a note, when its scenario does not exist yet.
The suite file has `time_budget_s` and `flake_retries`. A failed run is retried up to `flake_retries` times. A scenario that fails and then passes is marked `flaky`.

Output: `runs\suite-<id>\report.json` (under 4 KB for a passing suite) and `report.md`. History: `runs\suite-history.jsonl`.
Exit code: 0 pass (non-strict drift is allowed), 1 fail or strict drift, 2 crash or timeout left after retries, 3 time budget or iteration cap ended the suite early, 4 harness error.
If several apply, the order is 4, 3, 2, 1.

Baselines are in `harness\baselines\<scenario>.json`: `{"metrics": {"duration_s": [lo, hi]}, "strict": [...]}`.
A metric outside its range is `drift`. Drift fails the suite only for metrics listed in `strict` (add them by hand).
Only `--update-baseline` writes a baseline file. It uses the last N passing runs and widens min and max by 20% of the spread (at least 10% of the largest value). Review the file before you commit it.

Real baselines are in the repository. With only 2 to 4 runs, `--update-baseline` gives ranges that are too tight for timing metrics. Widen `duration_s`, `wall seconds` and sample counts by hand after you read the proposal.
On a run timeout the suite kills the `run.py` process tree and then runs `game-close.ps1`, so no game stays open. This cleanup is off when a custom launcher is used.

Test the suite without the game: `HARNESS_SUITE_LAUNCHER` (or `--launcher-command`) replaces `run.py`.

```powershell
.venv\Scripts\python.exe -m unittest discover -s harness/tests -p "test_suitelib*.py" -v
```

## Mock kit (no game needed)

`harness/tests/fakegame/` is a fake UE4SS API on `lupa`. A mod test needs fewer than 30 lines (spec 06, part B).
Read `harness/tests/fakegame/README.md` for how to write one, and for what the fake does not cover.

```powershell
uv run --no-project --python 3.12 --with lupa python -m unittest discover -s harness/tests -p "test_fakegame*.py" -v
uv run --no-project --python 3.12 --with lupa python harness/tests/boot_state_machine.py [mode ...]

## Hot reload (no game restart)

`python harness\tools\reload_mods.py [--mod Name ...] [--run-dir DIR] [--no-deploy]` (spec 06, part A). The game must run with a run folder
(started by `run.py --keep-open`, or by a script that sets `HARNESS_RUN_DIR`). The tool deploys, restarts the mods that deploy changed
(or the ones named with `--mod`), and waits until each mod logs `loaded version <v>` with the `VERSION` of the file in `mod/`.
It prints one JSON line. Exit code: 0 all reloaded, 1 a reload failed (wrong version, timeout, error), 2 harness error.
The loop takes about 2 s. `HarnessBoot` and `HarnessReload` are not restarted by default. A shared module change restarts the mods that `require` it.

The mod `HarnessReload` does the work: it reads `<run>/reload.json` (`{"mod", "id"}`), calls `RestartMod`, and writes `reload.result.json`.
A reloadable mod needs `local VERSION = "..."` and a log line `loaded version <VERSION>` with its folder name as tag.
A syntax error is not in `mod.log`; look at `ue4ss\UE4SS.log` (`Error loading script`). Details: `docs/specs/06-dev-loop-and-fixtures/implementation-notes/hot-reload.md`.
UE4SS auto reload is also on in this install, but it reloads only one mod when two change together, so the tool does not rely on it.

```powershell
.venv\Scripts\python.exe harness\run.py --scenario noop --keep-open     # leaves the game running
.venv\Scripts\python.exe harness\tools\reload_mods.py                   # after you edit a mod
.venv\Scripts\python.exe -m unittest discover -s harness/tests -p "test_reload_mods.py" -v
```

## Save fixtures

Every run gives the game its own `LOCALAPPDATA` (`<run folder>\appdata`). The fixture (default `base`, a copy of the user's `saveGame_0`) is its `saveGame_0`.
The user's save folder is never used by the game in a run. It is hashed before and after, and a change fails the run. The private folder is deleted in teardown.
`--keep-open` leaves it in place and does not compare the user's save files. Stop the game with `harness\game-close.ps1`, then run
`.venv\Scripts\python.exe harness	oolsixtures.py remove --appdata runs\<id>ppdata` (about 4 MB per run).
A game crash writes its UE crash report into the user's REAL `Crashes` folder (not the private one). `collect` copies the reports of this game (matched by process id) into `crash/`,
and `teardown` stops the `CrashReportClient.exe` that the crash leaves open. Test it with `python harness/run.py --scenario selftest-crash` (verdict `crash`, exit 2).

`python harness\tools\fixtures.py list | record <name> --source-slot <slot> | install <name> --appdata DIR | remove --appdata DIR` (spec 06, part C).
`harness\fixtures\fixtures.json` lists fixtures: name, source slot, SHA-256 of each source file, description, tags. It holds no save data.
`run.py --fixture <name>` picks a fixture. A source that no longer matches its SHA-256 fails the preflight (run `record` to accept the new files).
The game lists only `autosave` and `saveGame_0` to `saveGame_27`, which is why a fixture is always installed as `saveGame_0` in the private folder.
Details and measurements: `docs/specs/06-dev-loop-and-fixtures/implementation-notes/fixtures.md`.

```powershell
.venv\Scripts\python.exe harness\run.py --scenario smoke --fixture base
.venv\Scripts\python.exe -m unittest discover -s harness/tests -p "test_runlib_fixtures.py" -v
```

## Actions (`ctx.actions`)

Spec 07. An action creates a game situation and checks that it happened. It checks that the world is loaded, reads the value, makes the change, reads again,
and returns `{"action", "ok", "args", "before", "after"}` (and `note` for a caveat). It adds one line to `notes` in the scenario result.
A failed read-back also adds a failed assertion, so the verdict is `fail`. Call actions while the game is paused: a running game changes silver and stock by itself.

| Action | Effect |
|---|---|
| `add_silver(n)`, `set_silver(n)` | player silver |
| `add_influence(n)`, `set_influence(n)`, `add_kings_favour(n)` | influence, king's favour |
| `set_day(n)`, `set_season("winter"/"spring"/"summer"/"autumn")` | calendar. `daysTotal` grows by 1 for each call |
| `set_region_value(name, value, region=None)` | `Approval`, `publicOrder`, `regionalWealth`, `supplies_food`. `region` is `None` (player region) or a `regionName`. The game recalculates Approval and supplies_food within days |
| `add_regional_wealth(n, region=None)`, `set_settlement_level(n, region=None)` | region |
| `give_item(id or "Timber"/"Planks"/"Fish", n)` | goods in the stock of the player region |
| `set_weather(name, value)` | `raining`, `snowing`, `fogLevel`, `droughtLevel`, `wind`. The game moves them back within seconds |
| `spawn_bandit_squad()` | +18 units |
| `place_building(type_id, fx=0.65, fy=0.65)` | One more building of that type in the player region. **Uses the OS mouse and keyboard focus: do not use it while a person works on this computer.** The window comes to the front, the real cursor clicks the ground at that fraction of the window, and the cursor goes back. Aborts with an error if the game is not the foreground window or no ground is under the cursor. The player needs the goods of the building (HitchingPost 30 is free); a spot that overlaps another building places nothing. Scenario `place-building`. Code: `harness/runlib/osinput.py` |
| `send_letter(["welcome_from_hildebolt"], sender=1)` | an AI lord sends a letter. Needs the mod `HarnessActions` |

`save_state`, `show_message`, `get_item_info`, `remove_all_families` and `spawn_raiders` raise `ActionNotPossible` with the reason. An unknown name does too.
The runner turns it into a failed scenario (assertion `action is possible`), not a crash. `ctx.actions.available()` lists the names.
Status, numbers and caveats of every action: `docs/specs/07-feature-test-kit/implementation-notes/actions-catalog.md`.

The cheat manager actions (`give_item`, `set_settlement_level`, `spawn_bandit_squad`) need the stock UE4SS mod `CheatManagerEnablerMod` to be on in `ue4ss\Mods\mods.txt`.
**Never call `PawnCPP:requestSaveFile`.** It writes into the user's real save folder, not into the private one (see the catalog).

Helpers in the bridge client: `write_property`, `count_objects`, `region_paths`, `player_region_path`, `hud_treasury_text` (the silver number of the HUD; it updates only while the game runs, and writes 1000 and more as `1.2k`).

### Autosave protection
The game's autosave timer runs in real time, also while the game is paused, and an autosave writes into the user's REAL save folder.
`HarnessBoot` has a step `DISABLING_AUTOSAVE` before `PAUSING`: it restarts the timer with a one year period (`MLGameInstance:SetAutosavePeriodOnPawn`) and fails the boot if the timer is not far away.
`PAUSING` does not call `pauseGame` while the intro cinematic plays (`PawnCPP.currentUIMode ~= 0`): its end restores 1x and would undo the pause (spec 02, `clock-restart-cause.md`). The 8 s hold stays as a safety net.
`ctx.actions.autosave_status()` reads the timer. Scenario `autosave-protection` checks it over 60 game seconds. Notes: `docs/specs/06-dev-loop-and-fixtures/implementation-notes/autosave.md`.

### DataTable commands (spec 09 first check)
`HarnessActions` also has `datatable_info`, `datatable_read` and `datatable_write` for number fields (`Weight`, `Value`, `spoilageRate`) of `RTSMultiEngineCPP.itemStats` rows.
Do not read `RowStruct` or whole `Item` structs through the bridge: it crashes the game. Notes: `docs/specs/09-asset-mods/implementation-notes/datatable-check.md`.

### Helper mod HarnessActions
For game functions that need object parameters. The client `runlib/commands.py` (`CommandChannel`) writes `<run>/commands/0001.json`, `0002.json`, ... in order. The mod runs the command on the game thread
and writes `<number>.result.json`. Both sides write `.tmp` first and then rename. Commands: `ping` and `send_letter` (`sender`, `paragraphs`). The mod never runs text as code; it checks every input.
A game crash while a letter is sent (plain strings instead of `FName` values) is recorded in the catalog.

### Scenarios of spec 07
`silver-change` (set, add and take silver; checks the player value, the telemetry and the HUD, about 50 s), `winter-region` (winter, forced Approval and wealth, 3 game days, about 65 s),
`letter-delivery` (a letter into the InBox, about 40 s), `place-building` (hidden, so the MCP tools and suites never start it: a real OS mouse click; do not run it while a person works on the computer). Hidden: `selftest-action` (an impossible action, must fail with a clear message) and `probe-actions`, `probe-building` (HARNESS_PROBE_B: read, mode, click, scan)
(the probe; choose a group with `HARNESS_PROBE`: money, time, region, cheat, cheat2, cheat3, weather, hud, mail, helper; the groups `message`, `items` and `names` end the game on purpose).
Tests: `.venv\Scripts\python.exe -m unittest discover -s harness/tests -p "test_runlib_actions.py" -v` and, with lupa, `test_fakegame_harnessactions.py`.

## Asset mods (spec 09)
`harness/tools/pakmod.py` builds, installs and removes `.pak` files. **Status: tested with a fake packer only. A real pak build is not verified.**
Use Lua first. Build a pak only when the data cannot be changed at runtime (`docs/specs/09-asset-mods/README.md`).

Setup (only you can do this; the repo has no pak tools and no AES key):
1. Get a pak tool, for example UnrealPak (from an Unreal Engine install) or `retoc`. Put it anywhere outside the repo.
2. Make a work folder outside the repo, for example `C:\modwork`. Put the edited asset files in `C:\modwork\<name>\`, with the in-game folder layout,
   for example `C:\modwork\myedit\ManorLords\Content\NotStronghold\Data\DT_Items.uasset`. The tool writes the mount path `../../../ManorLords/Content/...` for each file.
   Exports from FModel, `.usmap` files and AES keys stay outside the repo. Never commit them.
3. Write `harness\pakmod.local.json` (it is in `.gitignore`):
   ```json
   {"packer": "C:/tools/UnrealPak/UnrealPak.exe", "packer_args": ["-Create={response}", "{output}"], "work_dir": "C:/modwork"}
   ```
   `{response}` is replaced with the response file path, `{output}` with `<work_dir>\out\<name>_P.pak`. Change `packer_args` to what your tool needs. Give the AES key as an argument there only if the tool needs it, and keep the file out of git.
4. Run `.venv\Scripts\python.exe harness\tools\pakmod.py check`. It lists what is missing.

Commands (all accept `--dry-run` and `--game-dir`; the name matches `^[A-Za-z0-9_-]{1,40}$`):
```
pakmod.py check
pakmod.py build <name>       # writes <work_dir>\out\<name>_P.pak
pakmod.py install <name>     # copies it to ManorLords\Content\Paks\~mods\ and records its SHA-256 in ~mods\.harness-paks.json
pakmod.py list
pakmod.py remove <name>      # or: remove --all. Deletes only manifest files whose hash still matches
```
`uninstall.ps1 -Remove` also removes the manifest paks. Restart the game after install or remove (the launcher starts a new game for each run anyway).
To check the effect: `run.py --scenario datatable-vanilla` with `HARNESS_EXPECT_ITEM_ROWS='{"17": {"Value": 0.75}}'` (new values) after a pak that changes them.
Without a pak the scenario compares 24 `itemStats` rows with `harness/vanilla/itemStats.json` (about 50 s per run). Details: `docs/specs/09-asset-mods/implementation-notes/tooling.md`.
Tests: `.venv\Scripts\python.exe -m unittest discover -s harness/tests -p "test_pakmod.py" -v` and `test_runlib_itemtable.py`.
