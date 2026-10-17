# Harness

## Run a test (run.py)

`harness/run.py` is the normal way to test a mod. One command runs one complete iteration with the real game
and writes `runs/<id>/summary.json` (spec 03). Read `summary.json` first. Open screenshots and logs only if it says to.
Steam does not have to be running (tested 2026-10-10). If it is not, the run carries a note. The game must not be started by hand.

```powershell
uv run python harness\run.py --list-scenarios
uv run python harness\run.py --scenario smoke [--keep-open] [--run-id ID] [--max-runs N]
uv run python harness\run_series.py --scenario smoke --runs 5
```

Exit code: 0 pass, 1 fail, 2 crash, 3 timeout, 4 harness error.
Run cap: `runs/.iterations` counts the runs. The default cap is 400. Change it with `--max-runs N` or the environment variable `HARNESS_MAX_RUNS`
(the option wins). At the cap, `run.py` stops with `Iteration limit reached` and says how to raise it. Do not delete `runs/.iterations`; raise the cap instead.
`run_series.py` runs the launcher N times, prints a table and writes `runs\series-<time>.json`. It exits 0 only if all runs pass.

Setup (once). From the repo root, make the venv from the lock file (`pyproject.toml`, `uv.lock`):

```powershell
uv sync
```

`uv run python ...` also syncs the venv before it runs. To add a package: `uv add <name>` (test-only: `uv add --dev <name>`).

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
Limits: the default is 90 s. A limit up to 300 s needs nothing more. A limit above 300 s (a soak) needs a text `LONG_REASON` in the module that says why. The most is 4200 s.
The suite runner and `run_series.py` give each run `LIMIT_S` plus 600 s (at least 900 s and 600 s), so their kill timer never ends a long scenario early (`suite.py --run-timeout-s` sets one fixed value).
While a long run is active, `wait_for_run` answers `running` with `scenario_limit_s`: call it again until the summary appears.
`ctx.run_until(predicate, timeout_s, what=, clock="wall"|"game", poll_s=, stall_s=, on_stall=, on_poll=)` waits for a condition (`runlib/waiting.py`).
`timeout_s` counts wall seconds or game seconds. The stall detector watches the game clock: after `stall_s` wall seconds with no progress it calls `on_stall`, and if the clock still stands still after another `stall_s` it raises `GameStalled`.
`WaitTimeout`, `GameStalled` and `TimeControlError` end the scenario with the verdict `fail` and a clear message (not a harness error).
Scenarios: `noop`, `smoke`. Test scenarios (`selftest-fail`, `selftest-timeout`) show with `--list-scenarios --include-test-scenarios`.

### Time control (`ctx.time`)
`set_speed(n)`, `run_game_seconds(n, speed)`, `run_game_days(n, speed)` and `pause()`. Speed 1, 2, 3 give clock rates 1, 4 and 8. One game day is 40 game seconds.
Each run function unpauses, sets the speed, waits, pauses, and checks that the clock stands still for 3 s. It returns
`{clock_start, clock_end, wall_s, paused_at_end, speed}` (days also have `days_start`, `days_end`, `day_start`, `day_end`).
It raises `TimeControlError` on a timeout, with a pause first. Days are counted with `daysTotal`, which does not wrap at the year end (365 days).
`absolute_day(date)` gives a day number for date asserts. A game pop-up (for example "Hunger!") pauses the game and gives a `TimeControlError`. `ctx.time.run_game_seconds` and `run_game_days` close pop-ups on their own every 2 s. Use `ctx.popups()` in your own wait loops (see below).
`set_speed` takes about 3 s, because it waits to see that the speed holds. Numbers: spec 04 `implementation-notes/time-measurements.md`.

### Telemetry
The mod `HarnessTelemetry` writes one JSON line every N wall seconds to `<run>/telemetry.jsonl` (clock, date, player, 7 regions, `errors`).
N is `--telemetry-interval` of `run.py` (default 5, 0 = off, saved in `config.json`). In a scenario: `ctx.telemetry.read()` and
`ctx.telemetry.window(start_clock, end_clock)`. `ctx.snapshot()` reads the same fields now through the bridge (a failed field is null and listed in `errors`).
Samples use wall time, so a short run at speed 3 has few samples. A metric of a mod that the scenario reads belongs in `HarnessCommands.metric` (see Mod state below): `HarnessTelemetry.register` only works for code in the state of the telemetry mod.

### Raids and units (spec 10)
Actions (need the mod HarnessActions): `set_raid_timer(days_until, days_since=None)`, `spawn_raid(squads=1, elite=False)` (+18 units a squad, elite +54),
`spawn_bandit_camp()`, `kill_units(side, count, with_loot=False)`, `set_unit_loot(side, count, amount)`, `units_census(sample=0)` and `raid_state()`.
Sides: `player`, `ai`, `bandit` (raiders and bandits), `civil`. `harness/runlib/units.py` has helpers for the census (`side_count`, `loot_total`, ...).
Not possible: choose raid type or size, steer a squad, read unit type or health (`choose_raid_type`, `steer_squad` raise `ActionNotPossible`).
Telemetry: start the launcher with `HARNESS_TELEMETRY_UNITS=1` and every sample has `custom.units` (counts by side, loot totals).
Scenarios: `raid-timer`, `raid-spawn`, `raid-loot`, `raid-load`. The hidden `probe-raids` scenario (`HARNESS_PROBE=s1|s1b|s2|s5|s10`) is the research tool of the spikes.
The scenario limit cap is 300 s (it was 120 s). Notes: `docs/harness/10-invasion-testability/implementation-notes/`.

### Sack primitives and the loot stand-in (spec 10, spikes S6 and R3)
Actions (need `HarnessActions` version 8): `sack_census()` (read only: buildings by state, stock, stores, families, people of the player village),
`sack_buildings(percent= or count=, method="collapse"|"fire")`, `sack_goods(percent= or good=+amount=, store=)`, `sack_people(percent= or count=)`,
`sack_village(buildings_pct, stock_pct, people_pct, method)`. A percent of a count is rounded half up. Inputs are checked in Python (`SackError`) and again in Lua; there is no eval.
Fire burns for about 50 game seconds, then the building is rubble (type 75) and its goods are gone. A collapse is rubble at once and keeps the goods. Goods are removed one unit at a time (`consumeGoodNoCheck`), at most 5000 per call.
Loot: the base game has no loot on the ground, so `drop_loot(count, good)`, `loot_piles()` and `recover_loot(pile)` drive a stand-in ledger (module `HarnessLoot`): the piles are Lua tables, and a recovery adds the goods with `GiveItemByID`.
Scenarios: `sack-village` (S1), `sack-ruins` (the ruin state of R8; not tagged, because the rebuild cost is not verified), `sack-store-trip` (R7), `loot-drop-recovery` (R3). Helpers: `harness/runlib/sack.py`.
Tests: `test_runlib_sack.py`, `test_fakegame_harnesssack.py`, `test_fakegame_sack_scenarios.py`. Notes: `docs/harness/10-invasion-testability/implementation-notes/spike-S6.md` and `spike-R3.md`.

### Unit data, typed units, fights and mercenaries (spec 10, spikes S7, P5, C1 and C2)
Actions (need `HarnessActions` version 9): `datatable_info(table)`, `datatable_read(row, field, table)`, `datatable_rows(table="units")` and `datatable_write(row, field, value, table="units")`.
`table` is `"items"` (DT_Items, the default for old calls) or `"units"` (DT_UnitTemplates; the game has no `DT_units`). Unit fields: `cost`, `maxSize`, `minMeleeTraining`, `minArcheryTraining`, `minHouseLv`, `combatExperience`.
A write changes the table in memory only (no file) and lasts until the game ends: restore the value at the end of a scenario. Writing `maxSize` changes the size of the next squad of that template.
`spawn_units(side, template, count=1, dx=0, dy=0)` calls `spawnArmy` with a row of DT_UnitTemplates. `side` is `"player"` or `"bandit"` (the owner pawn gives the side); the place is the player pawn plus (dx, dy).
The module `HarnessBattle` keeps a registry of the squads it spawned or hired, so `battle_state(detail=False)` gives the start size, the living units and the experience per squad, per side and per template (`runlib/battle.py` has the helpers: `casualties`, `casualty_rate`, `mean_experience`, `unit_experience`).
`clear_battle(side=None)` kills the units of those squads. `set_squad_experience(squad, value)` writes `combatExperience`.
`mercenary_offers()` lists the companies that can be hired (name, cost, days until arrival, unit templates). `hire_mercenaries(company)` hires one: the silver cost is paid, the squads are there at once. The game itself does not check the cost, so the action refuses when the silver is below it.
`runlib/fights.py` `run_fight(ctx)` runs the game at speed 3 until one side is gone, nothing changes for 10 wall seconds, or 90 wall seconds pass, then pauses. `ctx.variant_option(name, default)` reads a `run.py --env` value in a scenario.
Scenarios: `unit-data` (C3), `mercenary-hire` (P5), `veterancy` (C2), `counters-ab` (C1). Suite `harness/suites/counters-ab.json` compares a spear squad and a heavy squad against the same bandit squad (`player_loss_rate`).
The base game has no horse unit in its templates, so C1 covers the templates that exist (spear, sword, polearm, bow, heavy retinue). Tests: `test_runlib_battle.py`, `test_fakegame_harnessbattle.py`, `test_fakegame_battle_scenarios.py`. Notes: `spike-S7.md`, `spike-P5.md`, `spike-C2.md`, `spike-C1.md`.

### Banner text, construction sites and ruins (spec 10, S9 and R8)
`ctx.actions.show_message(text, subtext)` shows a banner (`PawnCPP:playEventMessage` with an `FName` type) and reads the text back from the widget; `read_message()` and `list_messages()` only read. Text: letters, digits, space and `, . ! : -`, at most 60 characters.
Scenario `ui-countdown` (COVERS T4): "Raid in N days" for N = 4, 3, 2, widget text read back, screenshot for each N. Notes: `docs/harness/10-invasion-testability/implementation-notes/spike-S9.md`.
`building_sites(type)` lists the goods that a construction site needs; `ruin_building(type, method)` burns or collapses a built building; `demolish_ruins()`; `set_site_cost(type, good, amount)` lowers the cost of a site.
AI lords (spec 10, spike S11, `docs/harness/10-invasion-testability/implementation-notes/baron-model.md`): `lords_state(log=12)` (lords, squads, challenges, the AI decision logs), `lord_declare_war(lord, target=0)`, `lord_declare_peace(lord, target=0)`, `lord_set_influence(lord, value)`, `lord_challenge(lord, target=0)`, `lord_claim(lord, target=0)`, `lord_spawn_army(lord, template, count, dx, dy)`, `spawn_ai_lord(name, can_build=False)`, `lord_start_ai(lord, speed=1, can_build=False)`, `regions_state()`, `lord_relations(lord)`, `lord_take_region(lord, region)` (spike S13, `dynamic-lords.md`; `settleRegion` crashes the game and is not offered). A lord is a number from 1 (lord 1 was the baron); target 0 is the player. The game's AI moves the armies; these calls steer its inputs. While armies are seen the game drops to 1x; `ctx.time.run_game_*` sets the speed again about once a second (`speed_resets` in the record).

Manor (spec 12): `manor_state()`, `finish_manor_site(type)` (harness shortcut: the test village cannot finish a Keep), `manor_put(good, amount)`, `manor_take(good, amount)`, `manor_stock(good)`. Scenario `manor-storage` (COVERS M1, hidden: real mouse, run it alone with a visible game window, about 70 s). Worker slots: `manor_worker_slot(job=45, slots=3)` (the Keep gets the slots and role of a Storehouse; job 44 is a Granary), `manor_assign_worker(family=None)`, `manor_unassign_workers()`, `manor_worker_state()`. Scenario `manor-storage-workers` (COVERS M1, hidden: real mouse, run it alone, about 90 s): no goods arrive without a worker, a worker carries goods into the Keep after the assignment.
Scenario `rebuild-cost` (COVERS R8, hidden: it uses the real OS mouse through `place_building`, run it alone with `run.py --scenario rebuild-cost` and a visible game window, about 85 s). Notes: `spike-R8.md`.

### Pop-ups and soak runs (spec 10, S8 and Q1)
An open pop-up ("Hunger!") pauses the game until Accept is pressed. `ctx.actions.close_popups()` (command `close_popups` of `HarnessActions`) presses Accept on every open pop-up, and the game goes on at the old speed.
`ctx.popups()` does the same without checks and remembers the types (`ctx.popups.closed`). Use it as `on_poll` of `ctx.run_until`. `ctx.actions.popup_state()` only reads. Notes: `docs/harness/10-invasion-testability/implementation-notes/spike-S8.md`.
Scenario `soak-days` (COVERS Q1): 8x speed for 600 wall seconds (about 120 game days), pop-ups closed, 100 Fish every 10 game days (the start village is defeated at day 137 without food), `GameOver` on a defeat, then asserts on the game process, the days run, the clock rate while running and the process memory. `HARNESS_SOAK_WALL_S` (60 to 3900) sets the wall time and the scenario limit follows. A 2-year soak (3650 s) cannot finish on the start village: it is defeated in its first winter at about day 350 (`implementation-notes/soak-results.md`).

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
uv run python -m unittest discover -s harness/tests -p "test_runlib*.py" -v
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

- Syntax of all mods: `uv run python harness/tests/lua_syntax.py`
- HarnessBoot state machine against a fake game API:
  `uv run python harness/tests/boot_state_machine.py happy`
  Other modes: `noslot` (slot not in the list) and `missing` (save file missing).

These checks use Lua 5.4 from the `lupa` package. They find syntax errors and wrong variable names.
They cannot show that the real UE4SS API behaves like the fake one.

## Note: HarnessBoot auto-load switch

`HarnessBoot` loads the test save only when it is turned on.

- The file `ue4ss\harness\autoboot.enable` (in the game's `Win64` folder) turns it on. It was created for the first in-game test.
- While that file exists, every game launch that reaches the main menu loads `saveGame_0`.
- Delete the file to get normal play back. Ask Claude to delete it if you prefer.
- The run launcher (spec 03) will use the environment variable `HARNESS_AUTOBOOT=1` instead of this file.

## Install the harness state (spec 11)

The game reads and writes its settings in your REAL `%LOCALAPPDATA%\ManorLords\Saved`, so a run cannot have private settings.
`install.ps1` puts the PC into the harness state:

- It backs up `GameUserSettings.ini`, `UserSettings.ini` and `rtsSettings.sav` into `slots\.install\` with SHA-256, once. A second install keeps the first backup.
- It writes the harness values into the real files: low quality, windowed 1280x720, 30 fps. Other keys (key bindings) stay.
- It builds the slot folders `slots\<n>\Manor Lords\` (default 2; the game folder is slot 0) and runs `deploy.ps1` for each.

While installed, your own play also uses the harness settings. Run `uninstall.ps1` before you play.
Both scripts refuse to work while the game runs, because the game writes its settings when it exits.

```powershell
powershell -ExecutionPolicy Bypass -File harness\install.ps1                 # settings and 2 slots
powershell -ExecutionPolicy Bypass -File harness\install.ps1 -SettingsOnly   # settings only
```

### Parallel runs in slots

After `install.ps1`, up to 3 runs can run at the same time, one per game slot (spec 11, step 3):

```powershell
uv run python harness\run.py --scenario smoke --slot auto   # the first free slot
uv run python harness\run.py --scenario smoke --slot 2      # slot 2 only; it fails if slot 2 is busy
```

- Slot 0 is the game folder (`runs\.lock`). Slot n uses `runs\.lock-<n>`. The default is `--slot 0`, as before.
- Each run deploys to its own slot, and stops only the game of its own slot.
- Changes to the real save folder (fixture install, save check, `save_game`) wait for `runs\.saves.lock`. OS mouse and key actions wait for `runs\.input.lock`.
- After READY the window moves to the slot's screen tile.
- MCP: `run_scenario(name, slot="auto")` is the default. `game_status` lists the slots and `free_slots`.

## Disable or remove the harness

`uninstall.ps1` (PowerShell 5.1) has two modes. Both support `-DryRun` and `-GameDir`. Running twice is safe.
Both modes first restore the settings files that `install.ps1` backed up, and check each hash.

- Default (disable): deletes `ue4ss\harness\autoboot.enable` and sets every harness mod to `Name : 0` in `mods.txt`.
  All files stay. Run `deploy.ps1` to enable the harness again.
- `-Remove` (full uninstall): also deletes the files listed in the manifest, the harness lines in `mods.txt`,
  the manifest, and the folders `ue4ss\bridge` and `ue4ss\harness`. It deletes the slot folders that `install.ps1` built;
  their junctions are removed as links first, so no game file is deleted.
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
It is registered in `.mcp.json`. To start it by hand: `$env:PYTHONPATH = "mcp;harness"; uv run python -m harness_tools`.

A run takes 1 to 3 minutes, so the tools start and poll:
1. `run_scenario(name)` starts `harness/run.py` in the background and returns `{"status": "started", "run_id": ...}`.
2. `wait_for_run(run_id)` waits up to 45 s (cap 50 s). It returns the summary, or `{"status": "running", ...}`. Call it again.
3. `read_summary`, `read_log`, `read_telemetry` and `list_screenshots` read the result.

Other tools: `list_scenarios`, `list_runs`, `game_status`, `stop_game` (refuses while a run holds the lock).
The read-only tools are allowed in `.claude/settings.json`. `run_scenario` and `stop_game` ask first.
`HARNESS_RUNS_ROOT` moves the runs folder. It is for tests only.
Tests: `uv run python -m unittest discover -s harness/tests -p "test_harness_tools*.py"`.

## Regression suite

`harness/suite.py` runs many scenarios in one command and writes one report (spec 08).
Each run is a separate `run.py` process, so a crash in one run does not stop the suite.

```powershell
uv run python harness\suite.py --suite core [--slots N|all] [--max-minutes N] [--runs-root DIR]
uv run python harness\suite.py --list
uv run python harness\suite.py --update-baseline <scenario> [--from-last N]
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

Parallel suites (spec 11): `--slots all` (or a number) runs up to one run per installed game slot at the same time (`harness/install.ps1`). A job is one repeat of one entry and variant, with its retries. Jobs start in the order of the sequential runner, so A and B runs stay interleaved across slots. A scenario with `EXCLUSIVE = True` (real mouse or keyboard) waits until no other game runs, and no other run starts while it runs. A slot whose run does not start (no `summary.json`, for example a slot that is not installed) is not used again; its job runs on another slot, and the report lists it under `bad_slots`. If no slot works, the suite stops (`no_slots`, exit code 3). A run timeout stops only the game of that slot.

Test the suite without the game: `HARNESS_SUITE_LAUNCHER` (or `--launcher-command`) replaces `run.py`.

```powershell
uv run python -m unittest discover -s harness/tests -p "test_suitelib*.py" -v
```

## Mock kit (no game needed)

`harness/tests/fakegame/` is a fake UE4SS API on `lupa`. A mod test needs fewer than 30 lines (spec 06, part B).
Read `harness/tests/fakegame/README.md` for how to write one, and for what the fake does not cover.

```powershell
uv run python -m unittest discover -s harness/tests -p "test_fakegame*.py" -v
uv run python harness/tests/boot_state_machine.py [mode ...]

## Hot reload (no game restart)

`python harness\tools\reload_mods.py [--mod Name ...] [--run-dir DIR] [--no-deploy]` (spec 06, part A). The game must run with a run folder
(started by `run.py --keep-open`, or by a script that sets `HARNESS_RUN_DIR`). The tool deploys, restarts the mods that deploy changed
(or the ones named with `--mod`), and waits until each mod logs `loaded version <v>` with the `VERSION` of the file in `mod/`.
It prints one JSON line. Exit code: 0 all reloaded, 1 a reload failed (wrong version, timeout, error), 2 harness error.
The loop takes about 2 s. `HarnessBoot` and `HarnessReload` are not restarted by default. A shared module change restarts the mods that `require` it.

The mod `HarnessReload` does the work: it reads `<run>/reload.json` (`{"mod", "id"}`), calls `RestartMod`, and writes `reload.result.json`.
A reloadable mod needs `local VERSION = "..."` and a log line `loaded version <VERSION>` with its folder name as tag.
A syntax error is not in `mod.log`; look at `ue4ss\UE4SS.log` (`Error loading script`). Details: `docs/harness/06-dev-loop-and-fixtures/implementation-notes/hot-reload.md`.
UE4SS auto reload is also on in this install, but it reloads only one mod when two change together, so the tool does not rely on it.

```powershell
uv run python harness\run.py --scenario noop --keep-open     # leaves the game running
uv run python harness\tools\reload_mods.py                   # after you edit a mod
uv run python -m unittest discover -s harness/tests -p "test_reload_mods.py" -v
```

## Save fixtures

Spec 06, part D (2026-10-11). The game lists and loads saves only from the user's REAL save folder, and before this date every run
started a NEW game instead of the fixture (`docs/harness/06-dev-loop-and-fixtures/implementation-notes/fixture-load-bug.md`).
- A fixture's files are kept in `harness\fixtures\saves\<name>\` (`slot.sav`, `slot_descr.sav`, images). Git ignores that folder.
  `harness\fixtures\fixtures.json` keeps the hashes, the description and the tags.
- A run copies the fixture into the user's save folder under the next free name (`saveGame_<max+1>`), rewrites `saveSlot` in the copied
  descriptor, and loads it. `HarnessBoot` sets `MLGameInstance.savefileToLoad` and fails the boot if the game did not load that slot.
- Teardown deletes the installed files (only those whose hash matches the ledger `runs\.installed-slots.json`), then compares the user's
  save folder with the preflight snapshot. A change fails the run. `--keep-open` leaves the slot; the next run removes it.
- The run still gives the game its own `LOCALAPPDATA` (`<run folder>\appdata`) for config, logs and crash reports. Remove it after
  `--keep-open` with `harness\tools\fixtures.py remove --appdata runs\<id>\appdata`.
A game crash writes its UE crash report into the user's REAL `Crashes` folder (not the private one). `collect` copies the reports of this game (matched by process id) into `crash/`,
and `teardown` stops the `CrashReportClient.exe` that the crash leaves open. Test it with `python harness/run.py --scenario selftest-crash` (verdict `crash`, exit 2).

Commands:
- `harness\tools\load_save.py <fixture | path\to\saveGame_N.sav>`: start the game with that save and leave it open (paused).
- `run.py --fixture <name>` or `run.py --save <path to .sav>`: any scenario on that save.
- `load_save.py --new-game [--map Jagged_Cliffs]` and `run.py --scenario <name> --new-game [--map NAME]`: a fresh new game, no save is loaded
  (spec 06, part E). HarnessBoot (`HARNESS_NEW_GAME=1`) opens the map with `open /Game/NotStronghold/Maps/NewMapSets/<map>`, pushes the autosave
  timer away, pauses, and writes READY. No slot is installed. The village is a random start region with 5 homeless families (day 61).
  Not with `--save` or `--fixture`.
- `harness\tools\fixtures.py import <name> --source-slot saveGame_28` (or `--from <path to .sav>`) `--description ... --tags a,b`.
- `harness\tools\fixtures.py list | uninstall | remove --appdata DIR | record` (`record`: the old kind, an entry that points to a user slot).
- Fixtures now: `base` (the user's `saveGame_0`: day 266, 24 buildings, 10 families) and `manor-bailey` (`saveGame_28`: day 106, manor with gate and bailey).

```powershell
uv run python harness\tools\load_save.py manor-bailey
uv run python harness\run.py --scenario smoke --fixture base
uv run python -m unittest discover -s harness/tests -p "test_runlib_*slot*.py" -v
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

`get_item_info`, `remove_all_families` and `spawn_raiders` raise `ActionNotPossible` with the reason. An unknown name does too.
`save_game(label, keep=False)` (spec 24) is the guarded save into a new `saveGame_<N>` slot: backup of the save folder first, files deleted at the run end unless `keep=True`, restore and raise if an existing file changes. Not run in the real game yet.
The runner turns it into a failed scenario (assertion `action is possible`), not a crash. `ctx.actions.available()` lists the names.
Status, numbers and caveats of every action: `docs/harness/07-feature-test-kit/implementation-notes/actions-catalog.md`.

The cheat manager actions (`give_item`, `set_settlement_level`, `spawn_bandit_squad`) need the stock UE4SS mod `CheatManagerEnablerMod` to be on in `ue4ss\Mods\mods.txt`.
**Never call `PawnCPP:requestSaveFile`.** It writes into the user's real save folder, not into the private one (see the catalog).

Helpers in the bridge client: `write_property`, `count_objects`, `region_paths`, `player_region_path`, `hud_treasury_text` (the silver number of the HUD; it updates only while the game runs, and writes 1000 and more as `1.2k`).

### Autosave protection
The game's autosave timer runs in real time, also while the game is paused, and an autosave writes into the user's REAL save folder.
`HarnessBoot` has a step `DISABLING_AUTOSAVE` before `PAUSING`: it restarts the timer with a one year period (`MLGameInstance:SetAutosavePeriodOnPawn`) and fails the boot if the timer is not far away.
`PAUSING` does not call `pauseGame` while the intro cinematic plays (`PawnCPP.currentUIMode ~= 0`): its end restores 1x and would undo the pause (spec 02, `clock-restart-cause.md`). The 8 s hold stays as a safety net.
`ctx.actions.autosave_status()` reads the timer. Scenario `autosave-protection` checks it over 60 game seconds. Notes: `docs/harness/06-dev-loop-and-fixtures/implementation-notes/autosave.md`.

### DataTable commands (spec 09 first check)
`HarnessActions` also has `datatable_info`, `datatable_read` and `datatable_write` for number fields (`Weight`, `Value`, `spoilageRate`) of `RTSMultiEngineCPP.itemStats` rows.
Do not read `RowStruct` or whole `Item` structs through the bridge: it crashes the game. Notes: `docs/harness/09-asset-mods/implementation-notes/datatable-check.md`.

### Helper mod HarnessActions
For game functions that need object parameters. The client `runlib/commands.py` (`CommandChannel`) writes `<run>/commands/0001.json`, `0002.json`, ... in order. The mod runs the command on the game thread
and writes `<number>.result.json`. Both sides write `.tmp` first and then rename. Commands: `ping` and `send_letter` (`sender`, `paragraphs`). The mod never runs text as code; it checks every input.
A game crash while a letter is sent (plain strings instead of `FName` values) is recorded in the catalog.

### Scenarios of spec 07
`silver-change` (set, add and take silver; checks the player value, the telemetry and the HUD, about 50 s), `winter-region` (winter, forced Approval and wealth, 3 game days, about 65 s),
`letter-delivery` (a letter into the InBox, about 40 s), `place-building` (hidden, so the MCP tools and suites never start it: a real OS mouse click; do not run it while a person works on the computer). Hidden: `selftest-action` (an impossible action, must fail with a clear message) and `probe-actions`, `probe-building` (HARNESS_PROBE_B: read, mode, click, scan)
(the probe; choose a group with `HARNESS_PROBE`: money, time, region, cheat, cheat2, cheat3, weather, hud, mail, helper; the groups `message`, `items` and `names` end the game on purpose).
Tests: `uv run python -m unittest discover -s harness/tests -p "test_runlib_actions.py" -v` and, with lupa, `test_fakegame_harnessactions.py`.

## Asset mods (spec 09)
`harness/tools/pakmod.py` finds and extracts assets from the game paks, converts them to JSON and back, builds a patch pak, and installs and removes it.
Tools: repak (paks) and the UAssetGUI command line (one asset). **Status: verified with the real tools and the real game (spike 2026-10-10, `docs/harness/09-asset-mods/implementation-notes/pak-spike-findings.md`).**
Use Lua first. Build a pak only when the data cannot be changed at runtime (`docs/harness/09-asset-mods/README.md`).

Setup (only you can do this; the repo has no tools and no AES key):
1. Get `repak.exe` (github.com/trumank/repak releases) and `UAssetGUI.exe` (v1.1.0 is verified) (github.com/atenfyr/UAssetGUI releases). Review them. Put them outside the repo, for example `C:\modtools\`.
2. Make the `.usmap`: start the game with UE4SS, then call the bridge tool `dump` with `kind: "usmap"` (UE4SS dumper). The file lands in the `ue4ss` folder. Copy it to the work folder. It must match the game build.
   The bridge MCP server reaches only a game that uses its own bridge folder. For a game that `run.py --keep-open` started, call `ue4ss_bridge.server.one('dump', timeout=600, kind='usmap')` from Python with `UE4SS_BRIDGE_GAME_DIR` (the `Win64` folder) and `UE4SS_BRIDGE_DATA_DIR` (the `bridge` folder of that run) set.
   UAssetGUI 1.1.0 reads a mapping by NAME from `%LOCALAPPDATA%\UAssetGUI\Mappings\<name>.usmap`. Copy the file there as well, and set `usmap_name` in the config. `check` compares both files.
   Use `engine_version` `VER_UE5_5` (the text `5.5` does not work in 1.1.0). The game paks are encrypted: set `aes_key_env` and fill that variable from your key file in the shell.
3. Make a work folder outside the repo, for example `C:\modwork`. Exports, `.usmap` files and AES keys stay outside the repo. Never commit them.
4. Copy `harness\pakmod.local.example.json` to `harness\pakmod.local.json` (it is in `.gitignore`) and set the paths, `usmap`, `engine_version` (`5.5`) and `work_dir`.
   Leave `sha256` empty. If the game paks are encrypted, set the environment variable named in `aes_key_env` (the key itself never goes into a file).
5. Run `uv run python harness\tools\pakmod.py check --pin`. It writes the SHA-256 of both tools into the config and prints them. This is a reviewed action: only pin files you trust.
   Later `check` runs refuse (exit code 3) when a tool file changed.

Commands (all accept `--dry-run` and `--game-dir`; a mod name matches `^[A-Za-z0-9_-]{1,40}$`):
```
pakmod.py check [--pin]       # config, tool hashes, tool versions, usmap, work folder, game Paks folder
pakmod.py find <text>         # case-insensitive search in the index of every game pak (max 50, index cached in <work_dir>\.index-cache)
pakmod.py extract <asset>     # ManorLords/Content/.../Name -> <work_dir>\extracted\...\Name.uasset/.uexp (+ .ubulk/.uptnl if present)
pakmod.py tojson <asset>      # UAssetGUI -> <work_dir>\json\...\Name.json
pakmod.py fromjson <json> [--to <name>]   # JSON -> asset in <work_dir>\fromjson\ or in the build folder <work_dir>\<name>\
pakmod.py roundtrip <asset>   # extract, tojson, fromjson, then compare bytes with the original (a difference is reported, not an error)
pakmod.py build <name>        # repak pack <work_dir>\<name>\ -> <work_dir>\out\<name>_P.pak, then checks the pak list against the folder
pakmod.py install <name>      # copies it to ManorLords\Content\Paks\~mods\ and records its SHA-256 in ~mods\.harness-paks.json
pakmod.py list
pakmod.py remove <name>       # or: remove --all. Deletes only manifest files whose hash still matches
```
Exit codes: 0 ok, 1 error, 3 a tool does not match its pinned hash, 4 the built pak lists other files than the folder.
The build folder `<work_dir>\<name>\` holds the edited files in the game layout, for example `ManorLords\Content\NotStronghold\Data\DT_Items.uasset`.
The config can override the argument templates (key `templates`), because the real tools may differ by version. Command facts: `docs/harness/09-asset-mods/implementation-notes/cli-reference.md`.

`uninstall.ps1 -Remove` also removes the manifest paks. Restart the game after install or remove (the launcher starts a new game for each run anyway).
To check the effect: set `HARNESS_EXPECT_ITEM_ROWS='{"17": {"Value": 0.75}}'` in the shell, then run `run.py --scenario datatable-vanilla --pak <name>`. It passes with the pak and fails without it (verified). `fromjson` needs an absolute path for the JSON file.
Without a pak the scenario compares 24 `itemStats` rows with `harness/vanilla/itemStats.json` (about 50 s per run). Details: `docs/harness/09-asset-mods/implementation-notes/tooling.md`.
Tests: `uv run python -m unittest discover -s harness/tests -p "test_pakmod.py" -v` and `test_runlib_itemtable.py`.

## Coverage of a feature (criteria and COVERS)
The tool `harness/tools/coverage.py` measures how many criteria of spec 10 (Invasion Mode) have a verified test method. Data: `docs/harness/10-invasion-testability/criteria.json`.
- Tag a scenario: add a module constant `COVERS = ["T1", "T2"]` (criterion ids). The tool reads it with `ast`. It never runs the scenario file. An unknown id is an error.
- Mark a criterion verified: a scenario that covers it and has a passing run (newest `runs/*/summary.json` of that scenario with verdict `pass`) counts. A spike result counts too: set `method_verified` to true in `criteria.json` and list the evidence (note path or scenario name) in `verified_by`.
- Run: `uv run python harness\tools\coverage.py` (options: `--json`, `--min-verified 0.9`, `--runs-root`, `--criteria`, `--check-spec`). Exit code 0 is ok, 1 is a failed check, 2 is bad input.
- Numbers: automatable share is (A + P) / all criteria. Verified share is the A and P criteria with a verified method / all A and P criteria. The target is 90%. Blocked criteria (missing game systems) stay in the count, so they lower the share. The gap list names A and P criteria with no scenario and no verification.
- Tests: `uv run python -m unittest harness/tests/test_coverage.py`.

## A/B variants and statistics
Combat is not deterministic, so a feature is judged over N runs per variant (spec 10, U4). Rules and limits: `docs/harness/10-invasion-testability/implementation-notes/ab-statistics.md`.
- `run.py --pak <name>` (repeatable) installs the built pak `<work_dir>\out\<name>_P.pak` before the game starts and always removes it at the end (also after a crash). The work folder comes from `harness\pakmod.local.json` (`--pak-config`).
- `run.py --env KEY=VALUE` (repeatable) sets a variable for the game process. Name `^[A-Z][A-Z0-9_]{0,63}$`, not starting with `HARNESS_RUN_DIR`, `LOCALAPPDATA`, `PATH` or `UE4SS_BRIDGE`. Value printable, no newline, at most 256 characters. A value is hidden in `config.json` if the name contains KEY, TOKEN, SECRET or PASSWORD. `summary.environment` lists env keys only.
- Suite entry with variants (the first variant is the reference; no `variants` means one variant `default`):
```json
{ "scenario": "smoke", "repeat": 5,
  "variants": [ {"name": "baseline"}, {"name": "with-pak", "paks": ["demo"], "env": {"X": "1"}} ],
  "expect": {"metric": "ticks", "direction": "lower", "min_rel_diff": 0.2} }
```
  Runs alternate A, B, A, B. `expect` is optional: it needs a `different` verdict, the median moving in `direction`, and a relative difference of at least `min_rel_diff`. If not met, the suite exits with 1. Example suite: `harness\suitesb-example.json`.
- Metrics per run: `duration_s`, the numeric values of the scenario asserts, and `metrics.json` in the run folder: a flat `{"name": number}` file. A scenario writes it with `ctx.metric("ticks", 120)` (name `A-Z a-z 0-9 _ . -`, finite number; the same name replaces the value; it wins over an assert of the same name).
- Report: `report.json` has `variants` per scenario and an `ab` section (each later variant against the first, per metric: verdict `different`, `same` or `inconclusive`, Cohen's d, relative difference of the medians, p-value, range overlap; the 8 strongest metrics per variant). It stays under 8 KB (a suite without variants: 4 KB). `report.md` has the tables. Fewer than 3 runs per variant is always `inconclusive`.
- Tests: `test_suitelib_stats.py`, `test_suitelib_ab.py`, `test_runlib_variant.py`.

## Mod state: commands and metrics of a mod
A mod can expose its own state to the harness (spec 10, U10). Full rules, an example and the security rules: `docs/harness/10-invasion-testability/implementation-notes/mod-state-contract.md`.
- In the mod: `require("HarnessCommands").register("MyMod.command", handler, schema)` for actions, and `require("HarnessCommands").metric("MyMod.metric", fn)` for values. Names follow `<ModName>.<name>`. UE4SS gives every mod its own Lua state, so each mod serves its own commands: the first call starts a poller for `<run>/modcmd/MyMod/` in the state of the mod. The schema lists each argument with `type` (`number`, `integer`, `string`, `boolean`) and optional `required`, `min`, `max`, `maxLength`, `oneOf`. Bad arguments are refused before the handler runs.
- In a scenario: `ctx.mod.command("MyMod.command", amount=5)` (returns the result, raises `ModCommandError` with the message of the mod), `ctx.mod.refusal(...)`, `ctx.mod.commands("MyMod")`, `ctx.mod.metric("MyMod.metric", None)`, `ctx.mod.wait_metric(name, predicate, timeout_s)`, `ctx.mod.metrics_window()`. A metric is read from the mod when you ask (the command `harness.metrics`), so it is current. A mod that is not loaded raises `ModDidNotAnswer` ("mod did not answer: MyMod"). The fake game kit has `FakeGame(separate_states=True)` to run each mod in its own Lua state, like UE4SS.
- Stand-in scenarios `standin-outposts`, `standin-captives` and `standin-tribute` use the test mod `InvasionStandIn` (a toy model, not the real mod). They are tested with the fake game kit only; the real-game run is pending.
- Raid stand-in scenarios (the test mod `RaidStandIn`, a toy model of the raid director, tiers, warlord, sack rule and pressure systems; notes: `docs/harness/10-invasion-testability/implementation-notes/raid-standin.md`):
  `raid-timeline` (T1, T3; waits real game days), `raid-seasons` (T5, P6), `raid-behavior` (R1, R4, R6), `raid-tiers` (D1, D2, D3; reports `tierN_mean_size` and `tierN_mean_raids` with `ctx.metric`),
  `raid-sack` (S2, S3), `raid-politics` (P1, P2, P4). The commands `set_day` and `advance_days` move the toy clock, `configure seed=N` makes a run repeatable. The helper package `harness/raidstandin/` is not a scenario package.
  The suite `raid-size-ab` runs `raid-tiers` with `RAID_STANDIN_SIZE_PERCENT` 100 and 150 as a real A/B example for the mod. Tested with the fake game kit only (`test_fakegame_raidstandin.py`, `test_fakegame_raid_scenarios.py`); the real-game run is pending.
- Tests: `uv run python -m unittest discover -s harness/tests -p "test_fakegame*.py"` and `uv run python -m unittest discover -s harness/tests -p "test_runlib_modstate.py"`.
