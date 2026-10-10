# Build notes: suite runner, report, baselines (spec 08, steps 1, 2 and 4 in code)

Everything here was built and tested with fake runs and a stub launcher. No game was started.

## Code
- `harness/suite.py`: the CLI. `harness/suitelib/`: `suitefile`, `runner`, `report`, `baselines`, `history`, `launcher`, `runresult`.
- `run_one(scenario, run_id, fixture) -> RunResult` is injected into `run_suite`. The default (`launcher.SubprocessLauncher`) starts `run.py` with `--scenario`, `--run-id` and `--runs-root`, with a time limit (default 900 s) per run.
- `--launcher-command` or the env variable `HARNESS_SUITE_LAUNCHER` replaces `run.py`. The tests use `harness/tests/stub_launcher.py`.

## Decisions
- Retry rule: only `fail`, `crash` and `timeout` are retried. A `harness_error` is not, because the same setup fails the same way.
- Flaky means: the same scenario both passed and failed in one suite run. A flaky scenario that ends in a pass gives exit code 0 and is listed.
- Missing `summary.json` is a `harness_error` with the stderr tail. A run that hits the time limit without a summary is a `timeout`. If a summary exists, it wins.
- Iteration cap: detected from the text "Iteration limit" in stderr of `run.py`. The refused run is not counted as a scenario result. The suite stops, lists what was not run, and exits 3.
- Optional entries: detected from "Unknown scenario" in stderr. The entry is skipped with a note. A required entry that is unknown is a `harness_error`.
- Time budget: checked before every attempt. A run in progress is not cut by the suite budget, only by the per-run limit. `--max-minutes` can only lower the budget.
- Exit code priority when several apply: 4, 3, 2, 1, 0. A timeout counts as 2 together with a crash.
- Suite verdict: `pass`, `drift` (non-strict drift, exit 0), `incomplete` (exit 3), `fail`.
- Baseline metrics: `duration_s` and every numeric `value` of `scenario_result.asserts`, by assertion name. Only passing runs are compared.
- Baseline proposal: min and max, widened by `max(20% of spread, 10% of the largest absolute value, 0.001)`. The floor keeps a constant metric from getting a zero-width range.
- `strict` is a list of metric names in the baseline file. `--update-baseline` keeps the old strict list but never makes a metric strict.
- History: one line per attempt. Flake rate is the share of non-pass runs among the last 20 runs of a scenario (`harness_error` ignored). A rate of 0 means stable, 1 means broken, between means flaky.
- Report size: lists are capped (5 failed assertions, 5 run folders, 3 drift findings, 12 durations), and text is cut to 60 or 120 characters.

## Not verified
- No real run. The timings, the 900 s run limit, and the 4 KB size with real summaries are untested.
- `run.py` has no `--fixture` option yet. A suite entry with `fixture` makes `run.py` fail with an argument error (harness_error) until spec 03 adds it.
- The scenarios `smoke`, `time-advance` and `telemetry-sanity` do not exist yet. The `smoke` entry fails as harness_error until it is added to `runlib/scenario.py`.
- On a run timeout the suite kills only `run.py` (via `subprocess.run`). Child processes such as the game may stay alive. `run.py` stops stale games in its preflight, but this was not tested.
- Real baselines do not exist. `harness/baselines/` is empty.
- Plan steps 3 (two real runs of `core`), 4 (real baselines and drift check) and 5 (a real regression) need the game.
- One existing test, `test_runlib_phases.StalePreflightTest.test_missing_save_fails`, fails in this worktree before and after my change. It is not part of this work.

## Real runs (real game, 2026-10-10)
The "Not verified" list above is the state before these runs. The items below replace it.

### Core suite, twice (plan step 3)
`core` = smoke x2, time-advance x2, telemetry-sanity x1 (the `optional` marks were removed; the optional feature still works and is unit tested).
- Run 1: pass, exit 0, 5 runs, 278.7 s. Run 2: pass, exit 0, 5 runs, 283.1 s.
- `report.json` is 869 bytes (limit 4 KB). Nothing was flaky. Pass rate 10 of 10.
- Durations (s): smoke 41.5 to 42.7, time-advance 52.8 to 55.8, telemetry-sanity 83.6 to 88.4.

Report (run 1):

| Scenario | Verdict | Passes | Stability | Durations (s) | Baseline |
|---|---|---|---|---|---|
| smoke | pass | 2/2 | stable | 42.7, 41.7 | none |
| time-advance | pass | 2/2 | stable | 54.1, 55.7 | none |
| telemetry-sanity | pass | 1/1 | stable | 83.6 | none |

### Baselines (plan step 4)
`--update-baseline` with `--from-last 10` used 4 passing runs (smoke, time-advance) and 2 (telemetry-sanity).
Observed assertion values were constant (calendar day 61, region count 7, approval 50, publicOrder 100, days moved 2).
The first `core` run after writing the proposal reported drift: duration and timing metrics were outside the tight proposals:
- time-advance `wall seconds` 11.2 (range 11.21 to 14.19; seen 11.2 to 13.2).
- telemetry-sanity `a sample taken after the pause` 6.0 (range 0.8 to 5.7), `samples while running` 10 (range 7.1 to 9.9).
Lesson: with 2 to 4 runs, min and max plus 20% is too tight for timing metrics. I widened these by hand and widened every `duration_s` to about 0.6x to 1.6x of the observed value:
- smoke: `duration_s` [30, 70], `clock moves after unpause` [0.3, 1.0]; the other metrics are the proposal (calendar day [54.9, 67.1], month [2.7, 3.3], year [0.9, 1.1], clock stopped [-0.001, 0.001]).
- time-advance: `duration_s` [40, 90], `wall seconds` [9, 16], days moved [1.8, 2.2].
- telemetry-sanity: `duration_s` [65, 130], `a sample taken after the pause` [0, 10], `samples while running` [6, 12], `clock rate while sampling` [0.9, 1.1]; the others are the proposal (approval [45, 55], publicOrder [90, 110], gaps [4.5, 5.5], region count [6.3, 7.7]).
After this, `core` gave pass with every baseline `ok`, exit 0, 284.3 s. The files are in `harness/baselines/`.

### Deliberate regression (plan step 5)
- Copy of the baselines with smoke `duration_s` = [1, 2] (`--baselines-dir`): verdict `drift`, exit 0, line `drift duration_s = 41.5 is above [1.0, 2.0]`.
- The same with `"strict": ["duration_s"]`: verdict `fail`, exit 1, `baseline` column `strict-drift`, line ends with `(strict)`.
- The real baseline files were not changed for this test.
- `harness/suites/selftest.json` (kept): selftest-fail, selftest-timeout, smoke, 1 retry. Result: exit 2, 198.4 s, 5 runs, 1 passed, report.json 1465 bytes.
  - selftest-fail: `fail`, 0/2, stable, failed assertion `clock moves while the game is paused (must fail) = 0.0`, both run folders listed.
  - selftest-timeout: `timeout`, 0/2, stable, reason `phase scenario timeout: exceeded the time limit of 5 s`.
  - smoke after them: pass, baseline ok. The suite continued after the fail and the timeout.
  - Hidden scenarios need no flag in `run.py --scenario`. The flag only changes the listing.
- A flaky run (fail then pass) was NOT seen with the real game. It is only covered by unit tests.

### Timeout and the game (plan step 4 of the task)
Two kinds of timeout exist:
1. The scenario limit (selftest-timeout: 5 s). `run.py` itself ends the run with verdict `timeout` and its teardown closes the game. After the selftest suite no game process was left.
2. The suite limit (`--run-timeout-s`). I used 20 s so that the suite killed `run.py` while the game ran. Result: bug. `ManorLords-Win64-Shipping` stayed open (PID seen with `tasklist`) and `mod.log` stopped in the PAUSING phase. I closed it with `game-close.ps1`.
Fix: `SubprocessLauncher` now uses `Popen`, kills the process tree with `taskkill /T /F` on a timeout, and then calls `close_game()` (`game-close.ps1`, grace 10 s). `suite.py` sets the cleanup only for the real `run.py`, not for a custom launcher.
Real check after the fix: same 20 s test gave `timeout`, exit 2, no game process afterwards, and the next `smoke` suite passed (so no stale state blocked it).

### Other bug fixed
A run and its retry that failed the same way listed the same failed assertion twice in the report. The report now lists each (name, value) once. Test: `test_same_failed_assertion_in_a_retry_is_listed_once`.

### History and flake rate (plan step 5 of the task)
`runs/suite-history.jsonl` had one line per attempt (34 lines after all tests). `report.json` has `flake_rate` for each scenario: 0.0 for smoke, time-advance and telemetry-sanity; 1.0 for selftest-fail and selftest-timeout (always failing, so "broken", not "flaky"). All lines of one suite get the same time stamp, because history is written at the end of the suite.

### Tests
New: `test_suitelib_launcher.py` (timeout kills the run and calls the cleanup once; no hook is fine) and the dedupe test. Suite tests (60) pass. The whole harness test folder: 261 tests, 1 error: `test_telemetry_mock` needs the `lupa` package, which is not in the venv (not part of this work).

### Still not verified
- A real game crash during a suite run.
- A flaky run with the real game.
- `fixture` entries (`run.py` has no `--fixture` option yet).
- The iteration cap path (exit 3) with the real `run.py`; unit tests only.
- The 900 s default run limit; real runs take at most 90 s.
- Baselines come from 2 to 4 runs and were set by hand for timing metrics. Re-check them after more runs.
