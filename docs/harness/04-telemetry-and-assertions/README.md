# Spec 04: Telemetry, assertions and scenario control

Status: done. Real results are in `implementation-notes/` (`time-measurements.md`, `telemetry-real-game.md`). Roadmap phase: 6 (see `docs/harness/00-harness-overview/README.md`).

## Goal
A scenario can control game time, sample game state, and assert ranges. The result goes into `scenario.json` and `summary.json`,
so a run can say pass or fail for a mod feature.

## Non-goals
- Actions that create situations (give resources, place buildings, raids). That is spec 07.
- MCP tools (spec 05).
- Baselines and regression comparison (spec 08).

## Background (verified)
- Spec 03 runs a scenario function `run(ctx)` after the game is `READY` and paused. The result is `{"passed": bool, "asserts": [...]}`.
- The bridge reads and writes game state (spec 01). Readable state: `RTSMultiEngineCPP.TemporalComponent` (`day`, `month`, `Year`, `Season`),
  `RTSMultiEngineCPP:getGameTimeAdjusted()` (the game clock), `PawnCPP` (`silver`, `influence`, `kingsFavour`, `InBox`),
  `Region` (`Approval`, `publicOrder`, `regionalWealth`, `supplies_food`, `isSettled`, `getNumTotalPopulation()`, `getNumHomelessFamilies()`).
  Details: `docs/harness/02-save-autoload/implementation-notes/in-game-messages-and-hud.md` and `jmap-findings.md`.
- The game starts at 1x after a load, and restarts its clock once after our first pause. `bIsPlayerPaused` is not reliable. Use the clock to decide if the game is paused.
- Measured (see `implementation-notes/time-measurements.md`): speed index 1, 2, 3 give clock rates of 1, 4 and 8. One game day is 40 game seconds.
  `day` is the day of the year (1 to 365, wraps with `Year`). `daysTotal` counts days without a wrap. A game pop-up pauses the game.
- `pauseGame()` stops the clock. `setGameSpeed(0)` does not.
- The game speed settings are pause, 1x, 2x and 3x. The functions are `changeGameSpeed(newSpeedIndex, playSfx)`, `increaseGameSpeed`, `decreaseGameSpeed` and `unPauseGame`.

## Design

### Part A: time control (Python, `harness/runlib/timectl.py`, as `ctx.time`)
- `unpause(speed=1)`: unpause and set the speed. Verify that the clock moves.
- `pause()`: call `pauseGame`. Verify that the clock stands still for 3 s (the same rule as HarnessBoot).
- `run_game_seconds(n, speed)`: unpause, wait until the game clock has advanced by `n`, then pause. Limit: wall time `n / speed * 3` plus 10 s.
- `run_game_days(n, speed)`: the same, but count `TemporalComponent.day` changes. Handle the day counter wrap at month end by also reading `month` and `Year`.
- Every function returns a record `{"clock_start", "clock_end", "wall_s", "paused_at_end"}` and raises `TimeControlError` with a clear reason on a timeout.

### Part B: telemetry (Lua mod `mod/HarnessTelemetry/`)
A mod that samples game state on the game thread and appends one JSON line per sample to `<run>/telemetry.jsonl`.
- Settings from environment variables: `HARNESS_RUN_DIR` (folder), `HARNESS_TELEMETRY_INTERVAL_S` (default 5 wall seconds; 0 turns it off).
- One line per sample: `{"t": <unix>, "clock": <game clock>, "date": {"day","month","year","season"}, "player": {"silver","influence","kingsFavour"},
  "regions": [{"name","settled","approval","publicOrder","wealth","food","population","homeless"}], "paused": <clock stopped since last sample>}`.
- Each field is read with a guard. A field that cannot be read is `null`, and the error is counted in `errors`. A bad field never stops sampling.
- The mod works while the game is paused (it samples wall-time, not game-time).
- Lines are flushed one by one, like HarnessLog.
- A mod can add its own metrics: `HarnessTelemetry.register(name, fn)` adds a field to every sample. `fn` runs on the game thread. It only works for code in the Lua state of the telemetry mod: UE4SS gives every mod its own Lua state (found 2026-10-10). A metric that a scenario reads belongs in `HarnessCommands.metric` (spec 10, U10).

### Part C: snapshots and assertions (Python, `harness/runlib/snapshot.py` and `expectations.py`)
- `snapshot(ctx)`: read the same fields now through the bridge. Returns a dict with the same shape as one telemetry sample.
- `ctx.expect` records assertions. Each one has `name`, `ok`, `value`, and the rule:
  - `in_range(name, value, lo, hi)`
  - `at_least(name, value, lo)`, `at_most(name, value, hi)`
  - `changed(name, before, after, min_delta=None, max_delta=None)`
  - `equals(name, value, expected)` (for flags and names, not for simulation numbers)
  - `eventually(name, fn, timeout_s)`: poll `fn` until it returns true.
- `ctx.result()` (instead of `scenario_result(ctx)`) returns `{"passed": all ok, "asserts": [...]}` and writes `scenario.json`.
- Assertion records stay short (under 200 bytes each) so that `summary.json` stays under 4 KB. Long data goes to `telemetry.jsonl`.

### Part D: scenario format
A scenario is a Python module in `harness/scenarios/<name>.py` with:
```python
DESCRIPTION = "..."
LIMIT_S = 180            # hard cap for the whole scenario
def run(ctx): ...        # use ctx.time, ctx.bridge, ctx.expect, ctx.telemetry, ctx.log
```
`ctx.telemetry.read()` returns the samples so far. `ctx.telemetry.window(start_clock, end_clock)` returns a part.
Built-in scenarios: `smoke` (spec 03), `time-advance` (run 2 game days at 3x, check the date moves and the clock stops), `telemetry-sanity` (check that the samples have the expected fields and sane ranges).

## Plan
1. `timectl` and real timings. **Done.** (`time-measurements.md`)
2. `HarnessTelemetry` with a mock test, then the real game. **Done.** It worked unchanged. (`telemetry-real-game.md`)
3. `ctx.expect` assertions, `snapshot`, telemetry reader, compact `summary.json`, with unit tests. **Done.** 157 launcher tests, 19 telemetry mock tests.
4. Scenarios `time-advance` and `telemetry-sanity`, 3 runs each. **Done.** All pass.
5. Update the spec and the harness README. **Done.**

## Answers to the open questions
- `changeGameSpeed` takes an index: 1, 2, 3 give `gameSpeed` 1, 4, 8 (clock rate the same). Index 0 stops the clock.
- `day` is the day of the year, 1 to 365, and wraps to 1 with `Year` + 1. The counters were consistent. `daysTotal` never wraps.
- A 5 s wall sample is enough at 1x (a game day is 40 s). At 8x a game day is 5 wall s, so there is about one sample for each day. Reading 7 regions did not slow the game (clock rate 1.001 at 1x).
- `daysTotal` does change: it counts days from the load (0 at day 61).
- New finding: after the boot pause the game drops the speed back to 1x about 3 s after the first `changeGameSpeed`. `set_speed` retries. A pop-up (for example "Hunger!") pauses the game and the bridge cannot close it.

## Acceptance criteria
Results of 2026-10-10 (real game, launcher runs):
- `run_game_days(2, 3)`: done in 3 of 3 `time-advance` runs (pass, 54 s each in the launcher, scenario about 24 s). Date moved by 2, `daysTotal` by 2, clock stopped for 3 s, wall time 12 s.
- `telemetry.jsonl`: samples in every run, all fields present, no read errors, gap 5 s in every gap checked (3 of 3 `telemetry-sanity` runs, 10 samples in the 40 s window).
- Each assertion type has a unit test for pass and fail (`harness/tests/test_runlib_timectl.py`). A real run with a failing assertion (`selftest-fail`) gave verdict `fail`, exit 1, and the failed assertion is in `summary.json`.
- `time-advance` 3 of 3 pass and `telemetry-sanity` 3 of 3 pass (about 89 s each), `smoke` pass (43.8 s). Summaries are 1.9 KB, 3.4 KB and 2.0 KB. The first two `time-advance` runs failed before the speed fix (see `time-measurements.md`). The three counted runs used the final code.
