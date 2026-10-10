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
