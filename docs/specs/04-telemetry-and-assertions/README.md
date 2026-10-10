# Spec 04: Telemetry, assertions and scenario control

Status: draft. Roadmap phase: 6 (see `docs/specs/00-harness-overview/README.md`).

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
  Details: `docs/specs/02-save-autoload/implementation-notes/in-game-messages-and-hud.md` and `jmap-findings.md`.
- The game starts at 1x after a load, and restarts its clock once after our first pause. `bIsPlayerPaused` is not reliable. Use the clock to decide if the game is paused.
- `pauseGame()` stops the clock. `setGameSpeed(0)` does not.
- The game speed settings are pause, 1x, 2x and 3x. The functions are `changeGameSpeed(newSpeedIndex, playSfx)`, `increaseGameSpeed`, `decreaseGameSpeed` and `unPauseGame`.

## Design

### Part A: time control (Python, `harness/scenarios/lib/timectl.py`)
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
- A mod can add its own metrics: `HarnessTelemetry.register(name, fn)` adds a field to every sample. `fn` runs on the game thread.

### Part C: snapshots and assertions (Python, `harness/scenarios/lib/`)
- `snapshot(ctx)`: read the same fields now through the bridge. Returns a dict with the same shape as one telemetry sample.
- `ctx.expect` records assertions. Each one has `name`, `ok`, `value`, and the rule:
  - `in_range(name, value, lo, hi)`
  - `at_least(name, value, lo)`, `at_most(name, value, hi)`
  - `changed(name, before, after, min_delta=None, max_delta=None)`
  - `equals(name, value, expected)` (for flags and names, not for simulation numbers)
  - `eventually(name, fn, timeout_s)`: poll `fn` until it returns true.
- `scenario_result(ctx)` returns `{"passed": all ok, "asserts": [...]}` and writes `scenario.json`.
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
1. Write `timectl` and test it against the real game with the bridge. Record real timings (at 1x, 2x and 3x) in `implementation-notes/`.
2. Write `HarnessTelemetry` with a mock test (the fake game API from `harness/tests/boot_state_machine.py`), then test in the real game.
3. Write the `ctx.expect` assertions and the unit tests (no game).
4. Write the scenarios `time-advance` and `telemetry-sanity`. Run each 3 times. Record the results.
5. Update the spec and the harness README.

## Open questions
- How fast does the game clock run at 2x and 3x, and does `changeGameSpeed` take an index or a value?
- Does the day counter ever skip or repeat? Is `TemporalComponent.day` the day of the year or of the month?
- Is a wall-time sample of 5 s enough to see changes? Does reading all regions each time slow the game?
- Does `daysTotal` ever become non-zero? (It read 0 with `day` = 61.)

## Acceptance criteria
- `run_game_days(2, 3)` ends with the game paused (clock stopped) and the date moved by 2 days, in 3 runs out of 3.
- `telemetry.jsonl` has samples in a run, with all fields present, and a sample every 5 s plus or minus 2 s.
- Every assertion type has a unit test for pass and fail. A run with a failing assertion gives the verdict `fail` and the failed assertion is in `summary.json`.
- The scenarios `time-advance` and `telemetry-sanity` pass 3 times in a row with the run launcher.
