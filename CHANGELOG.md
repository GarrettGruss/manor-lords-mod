# Changelog

All notable changes to this project are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `manor-harness` MCP server (`mcp/harness_tools/`) with start-and-poll tools to run scenarios and read results (spec 05).
- `HarnessLog` shared Lua module. It writes a log file that flushes on each line.
- `HarnessLogTest` mod to check that the log works.
- `harness/deploy.ps1` to copy mods into the UE4SS `Mods` folder and enable them.
- Spec `docs/specs/01-ue4ss-bridge/` with a review checklist.
- Spec `docs/specs/02-save-autoload/` for the save auto-load and ready signal.
- Spec `docs/specs/03-run-launcher/` for the run launcher and `summary.json`.
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
- `summary.json` is smaller: it drops empty fields, keeps only the seconds of good phases, and has a short environment (the full mod hashes are in `config.json`). Assertion records use `rule` instead of `range`.
- Vendored bridge: raw Lua eval is off by default, and it is gated in the Python server too.
- Vendored bridge: the bridge folder follows `HARNESS_RUN_DIR`.
- MCP dependencies are locked with hashes (`mcp/requirements.in` and `mcp/requirements.txt`) and installed with uv.

### Fixed
- Vendored bridge: the poller no longer stays busy forever after a failed reply. Large responses and limits are capped. `dump` needs `allow_writes`.
- Vendored bridge: a nil property or function name no longer crashes the game. It returns an error.
