# Changelog

All notable changes to this project are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Action `place_building(type_id, fx, fy)` (spec 07): places a building with a real OS mouse click on the game window (`harness/runlib/osinput.py`, tests `test_runlib_osinput.py`, scenario `place-building`). It uses the OS mouse and keyboard focus: do not use it while a person works on this computer. Verified in the real game with the HitchingPost; the earlier notes on why a faked mouse failed are in `building-placement.md`.
- Clock restart cause (spec 02): found with a temporary hook probe (source kept in `docs/specs/02-save-autoload/implementation-notes/`). Note `clock-restart-cause.md`. Hidden scenario `probe-building` and the note `building-placement.md` (spec 07): no verified way to place a building. Second attempt (fake mouse hooks, raw spawn call) also failed; probe source kept in the notes, not deployed.
- Fake game: `FakeGameClock(cinematic=(start, end))` models the intro cinematic. New boot test modes `cinematic`, `nocinematic`, `silentrestart`, `cinematicstuck`, and a check of the number of `pauseGame` calls.
- Asset mod tooling (spec 09): `harness/tools/pakmod.py` (`check`, `build`, `install`, `remove`, `list`, all with `--dry-run` and `--game-dir`), configured by the local file `harness/pakmod.local.json` (not committed). `uninstall.ps1 -Remove` also removes harness paks (only files in `~mods\.harness-paks.json` whose hash matches). Tested with a fake packer; a real pak build is not verified (needs UnrealPak or `retoc` from the user).
- Scenario `datatable-vanilla` and the file `harness/vanilla/itemStats.json` (24 vanilla `itemStats` rows, row count 213): the scenario compares the rows read in the game with the vanilla values. `HARNESS_EXPECT_ITEM_ROWS` states new values for a data pak. Hidden scenario `datatable-record` writes the vanilla file. Actions `ctx.actions.datatable_info()` and `ctx.actions.datatable_read(row, field)`.
- Autosave protection (spec 06): `HarnessBoot` state `DISABLING_AUTOSAVE` restarts the pawn autosave timer with a one year period before READY (shared module `HarnessAutosave`, `MLGameInstance:SetAutosavePeriodOnPawn`). The timer ran in real time, also in a paused game. `HarnessActions` commands `autosave_status` and `disable_autosave`, action `ctx.actions.autosave_status()`, scenario `autosave-protection`, and fake game support for the timer (`boot_state_machine.py` mode `autosavefails`).
- `HarnessActions` commands `datatable_info`, `datatable_read` and `datatable_write` with the shared module `HarnessDataTable` (spec 09 first check: number fields of `itemStats` rows can be read and written at runtime).
- Hidden scenario `selftest-crash`: makes the real game crash through the bridge (`getItem` or `playEventMessage`) to test the crash verdict and the crash report copy.
- Feature test kit (spec 07): `ctx.actions` (`harness/runlib/actions.py`) with 14 actions that were checked in the real game (silver, influence, king's favour, day and season, region values, wealth, goods, settlement level, weather, bandit squad, letters). Each action reads the value before and after and returns `{action, ok, args, before, after}`. Actions that are not possible (`save_state`, `show_message`, ...) and unknown names raise `ActionNotPossible`, which fails the scenario with the reason. Catalog with numbers: `docs/specs/07-feature-test-kit/implementation-notes/actions-catalog.md`.
- Mod `HarnessActions` and `harness/runlib/commands.py`: a command channel (`<run>/commands/0001.json`, ...) for game functions that need object parameters. First use: `send_letter`. Mock tests in `harness/tests/test_fakegame_harnessactions.py`.
- Scenarios `silver-change`, `winter-region` and `letter-delivery`, the hidden `selftest-action`, and the hidden probe `probe-actions`. New bridge helpers: `write_property`, `count_objects`, `region_paths`, `player_region_path`, `hud_treasury_text`. `ctx.fail(name, reason)` and `notes` in the scenario result.
- Hot reload without a game restart (spec 06): `python harness/tools/reload_mods.py [--mod Name] [--run-dir DIR]` deploys and restarts the changed Lua mods in the running game in about 2 s. The new mod `HarnessReload` calls `RestartMod` on a request file (`reload.json`) and writes `reload.result.json` with the version line. `HarnessLogTest`, `HarnessTelemetry` and `HarnessLoadProbe` now log `loaded version <v>`.
- Save fixtures (spec 06): every run gives the game its own `LOCALAPPDATA` (`<run>/appdata`) with the fixture `base` (a copy of the user's `saveGame_0`, listed in `harness/fixtures/fixtures.json`, no save data in git). The user's save folder is hashed before and after the run and is never used by the game. `run.py --fixture <name>`, `harness/tools/fixtures.py` (`list`, `record`, `install`, `remove`). Crash reports are collected from the private folder. The game lists only `saveGame_0` to `saveGame_27` and `autosave`, so a custom slot name does not work (`implementation-notes/fixtures.md`).
- `HarnessBoot` logs the slots of the load screen when the wanted slot is missing.
- `manor-harness` MCP server (`mcp/harness_tools/`) with start-and-poll tools to run scenarios and read results (spec 05).
- Mock kit `harness/tests/fakegame/`: a fake UE4SS API on lupa (objects, TArray, loops, key binds, hooks, fake time, fake game clock, a Manor Lords menu and game state). `boot_state_machine.py` now uses it. See `harness/tests/fakegame/README.md`.
- `HarnessLog` shared Lua module. It writes a log file that flushes on each line.
- `HarnessLogTest` mod to check that the log works.
- `harness/deploy.ps1` to copy mods into the UE4SS `Mods` folder and enable them.
- Spec `docs/specs/01-ue4ss-bridge/` with a review checklist.
- Spec `docs/specs/02-save-autoload/` for the save auto-load and ready signal.
- Spec `docs/specs/03-run-launcher/` for the run launcher and `summary.json`.
- Spec `docs/specs/09-asset-mods/`: when and how to change game data with pak files. Deferred, because no planned feature needs it yet.
- Spec `docs/specs/07-feature-test-kit/`: actions for scenarios (give resources, change time or state, read letters) with checked effects.
- `harness/run.py` and `harness/runlib/`: the run launcher core (run folder, lock, iteration cap, phase runner, `summary.json`) with fake phases for tests. Real game phases are not built yet.
- Real run phases (`preflight`, `deploy`, `launch`, `boot`, `scenario`, `collect`, `teardown`) and `harness/run.py --scenario noop`: one complete iteration with the real game, crash detection, and a scenario registry (`harness/runlib/scenario.py`).
- `harness/requirements.in` and a hash-locked `harness/requirements.txt` (psutil).
- Spec `docs/specs/00-harness-overview/`: the roadmap for the harness, the test layers, and what "90% of testing" means.
- Jmap findings for the game reflection data, in `docs/specs/02-save-autoload/implementation-notes/`.
- `CLAUDE.md` with project rules, including one feature branch for each spec and Sonnet for subagents.
- Security review of ue4ss-bridge, with required patches P1 to P7.
- Vendored `ue4ss-bridge` 1.2.1 (upstream a5eae1c): the `UEBridge` Lua mod in `mod/UEBridge/` and the MCP server in `mcp/ue4ss_bridge/`. See `vendor/ue4ss-bridge/PATCHES.md`.
- Project MCP config `.mcp.json` (stdio) and `.claude/settings.json`. Eval is denied. Risky bridge tools ask first.
- `HarnessLoadProbe` mod: press F8 in the main menu to load a save slot (default `saveGame_0`). It is a probe for spec 02.
- `HarnessBoot` mod: loads the test save from the main menu, pauses the game and holds the pause for 8 s of a stopped game clock, and writes `boot.json` and `ready.marker`. It is off unless `HARNESS_AUTOBOOT=1` or `ue4ss/harness/autoboot.enable` exists.
- `harness/tests/` with a Lua syntax check and a state machine test that need no game.
- `harness/uninstall.ps1`: disables the harness (mods set to 0, autoboot switch removed) or removes everything `deploy.ps1` installed with `-Remove`.
- `harness/game-launch.ps1` and `harness/game-close.ps1` to start and stop the game by hand.
- Scenario runner (`harness/scenarios/`, `ScenarioContext`, bridge helpers), scenario `smoke`, hidden test scenarios `selftest-fail` and `selftest-timeout`, and `run.py --list-scenarios`.
- Screenshots of the game window (`mss`), copy of UE4SS crash dumps, and `harness/run_series.py` to run the launcher N times.
- Time control for scenarios (`ctx.time`: `set_speed`, `run_game_seconds`, `run_game_days`, `pause`), typed assertions (`ctx.expect`), `ctx.snapshot()` and a telemetry reader (`ctx.telemetry`).
- `HarnessTelemetry` mod is deployed and used in runs. The launcher passes `HARNESS_TELEMETRY_INTERVAL_S` (`run.py --telemetry-interval`, default 5, 0 = off) and lists `telemetry.jsonl` in the summary.
- Scenarios `time-advance` and `telemetry-sanity`.
- Spec 04 notes with real speed, calendar and telemetry measurements.
- `harness/suite.py` and `harness/suitelib/`: the regression suite. It runs a suite through `run.py`, retries failures to find flaky scenarios, writes `report.json` and `report.md`, compares metrics with baselines, and writes baselines only on request. Suites are in `harness/suites/` (`smoke`, `core`, `soak`, `selftest`). Real baselines for `smoke`, `time-advance` and `telemetry-sanity` are in `harness/baselines/`. After a run timeout the suite kills `run.py` and closes the game (found in a real run: the game stayed open).

### Changed
- The preflight no longer fails when Steam is not running. The direct launch works without Steam (tested), so it only adds a note to the summary. `.claude/settings.json`: `run_scenario` is allowed without asking, by the user's decision.
- `HarnessBoot` waits for the end of the intro cinematic (`PawnCPP.currentUIMode ~= 0`) before it calls `pauseGame`, so the game does not undo the pause. One `pauseGame` call in each boot (5 of 5 smoke runs, before: two); the 8 s hold stays as a safety net.
- Fake clock: `late_revert_after` is off by default (the intro cinematic is the default restart).
- `summary.json` is smaller: it drops empty fields, keeps only the seconds of good phases, and has a short environment (the full mod hashes are in `config.json`). Assertion records use `rule` instead of `range`.
- Vendored bridge: raw Lua eval is off by default, and it is gated in the Python server too.
- Vendored bridge: the bridge folder follows `HARNESS_RUN_DIR`.
- MCP dependencies are locked with hashes (`mcp/requirements.in` and `mcp/requirements.txt`) and installed with uv.

### Fixed
- The command channel retries when the mod still holds a result file open (Windows `PermissionError`) or has written only part of it. A run of 120 reads failed with `PermissionError` before.
- Crash reports were never copied: the UE crash handler writes into the user's real `Crashes` folder, not the private `LOCALAPPDATA`. `collect` now searches both folders and matches the process id. `teardown` stops the `CrashReportClient.exe` that a crash leaves open.
- `--keep-open` now prints how to stop the game and delete the private appdata, and says that the user's save files were not compared.
- Vendored bridge: the poller no longer stays busy forever after a failed reply. Large responses and limits are capped. `dump` needs `allow_writes`.
- Vendored bridge: a nil property or function name no longer crashes the game. It returns an error.
