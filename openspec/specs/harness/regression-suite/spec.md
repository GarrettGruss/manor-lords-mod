# harness/regression-suite Specification

## Purpose
The regression suite runs many test scenarios, repeats and variants in one command, compares the results with baselines and with each other, and writes a short report. One run proves little, because the simulation is not deterministic.

## Requirements

### Requirement: A suite file defines the runs
`suite.py --suite <name>` SHALL read `harness/suites/<name>.json`. The file name SHALL equal `name`. The harness SHALL refuse unknown keys, a bad variant name, a repeat below 1, and an `expect` with fewer than two variants, with a clear message.

#### Scenario: A bad suite file
- **WHEN** a suite file has an unknown key or a name that differs from the file name
- **THEN** the suite is refused with a clear error
- Checked by `harness/tests/test_suitelib_suitefile.py`.

#### Scenario: The shipped suites
- **WHEN** the suites in `harness/suites/` are loaded
- **THEN** every one is valid
- Checked by `harness/tests/test_suitelib_suitefile.py`.

#### Scenario: An unknown suite name
- **WHEN** `--suite` names a missing file
- **THEN** the error lists the known suites
- Checked by `harness/tests/test_suitelib_suitefile.py`.

### Requirement: Each run is one launcher process
The suite SHALL start `run.py` once for each repeat and variant, with a run id `<suite_id>-<count>-<scenario>[-<variant>][-r<retry>]`. A variant SHALL become `--pak` and `--env` options. The suite SHALL read `summary.json` and `metrics.json` of the run. It SHALL kill a run that exceeds its timeout and close the game.

#### Scenario: Variant options
- **WHEN** a variant has paks and env values
- **THEN** the launcher gets one `--pak` and one `--env KEY=VALUE` for each
- Checked by `harness/tests/test_suitelib_ab.py`.

#### Scenario: A run hangs
- **WHEN** a run exceeds its timeout
- **THEN** the suite kills the process tree, closes the game once, counts a timeout and goes on
- Checked by `harness/tests/test_suitelib_launcher.py`.

### Requirement: Variants alternate and failures retry
Inside one entry the suite SHALL alternate the variants for each repeat (A, B, A, B). It SHALL retry a repeat that ended in `fail`, `crash` or `timeout` up to `flake_retries` times, and SHALL NOT retry a `harness_error`. An entry with passes and failures SHALL be `flaky`.

#### Scenario: A flaky pass
- **WHEN** a repeat fails and its retry passes
- **THEN** the entry is `flaky`, the suite exit code is 0, and the report lists it
- Checked by `harness/tests/test_suitelib_cli.py`.

#### Scenario: A harness error
- **WHEN** a run ends in `harness_error`
- **THEN** it is not retried
- Checked by `harness/tests/test_suitelib_runner.py`.

### Requirement: The suite stops at a budget
The suite SHALL stop early at the lower of `time_budget_s` and `--max-minutes`, or when `run.py` refuses a run because of the run cap. The report SHALL list what was not run. A scenario that is `optional` and unknown SHALL be skipped, not failed.

#### Scenario: The time budget ends
- **WHEN** the budget is used up
- **THEN** the exit code is 3 and the report names the entries not run
- Checked by `harness/tests/test_suitelib_runner.py`.

#### Scenario: The run cap
- **WHEN** a run is refused with an iteration limit
- **THEN** the suite stops, exits with code 3, and counts no result for that run
- Checked by `harness/tests/test_suitelib_cli.py`.

### Requirement: Baselines catch drift
The suite SHALL compare the metrics of passing runs with `harness/baselines/<scenario>.json`. A value outside its range, or missing, SHALL be a drift finding and a warning. A drift on a `strict` metric SHALL make the exit code 1. Failed runs SHALL not be compared.

#### Scenario: A deliberate regression
- **WHEN** a metric is outside its baseline range
- **THEN** the suite reports drift, exits with 0 unless the metric is strict, and leaves the baseline file unchanged
- Checked by `harness/tests/test_suitelib_cli.py`.

#### Scenario: A strict metric
- **WHEN** a strict metric is outside its range
- **THEN** the exit code is 1
- Checked by `harness/tests/test_suitelib_cli.py`.

### Requirement: A baseline is only proposed
`suite.py --update-baseline <scenario>` SHALL write a proposed baseline from the last N passing runs (default 5): the minimum and maximum, widened by 20 percent of the spread with a floor. It SHALL keep old `strict` flags. It SHALL fail when there are no runs. No other code SHALL write a baseline.

#### Scenario: Update from the last runs
- **WHEN** the command runs with `--from-last 3`
- **THEN** the proposal uses the last 3 passing runs
- Checked by `harness/tests/test_suitelib_cli.py`.

#### Scenario: No runs
- **WHEN** no passing run exists for the scenario
- **THEN** the command fails with a clear error
- Checked by `harness/tests/test_suitelib_cli.py`.

### Requirement: Variants are compared with small-sample statistics
For a suite with variants, the suite SHALL compare each later variant with the first, metric by metric, using only passing final attempts. The verdict per metric SHALL be `inconclusive` for fewer than 3 runs on a side, `different` for p <= 0.1 and |d| >= 0.5, `same` for p > 0.1 and |d| < 0.5, and `inconclusive` otherwise. The permutation test SHALL give the same p-value for the same data.

#### Scenario: Equal distributions
- **WHEN** both variants have the same distribution
- **THEN** the verdict is `same`
- Checked by `harness/tests/test_suitelib_ab.py`.

#### Scenario: Shifted distributions
- **WHEN** one variant is clearly shifted
- **THEN** the verdict is `different`
- Checked by `harness/tests/test_suitelib_ab.py`.

#### Scenario: Two runs per side
- **WHEN** a side has only two runs
- **THEN** the verdict is `inconclusive`
- Checked by `harness/tests/test_suitelib_ab.py`.

### Requirement: An expectation turns a result into pass or fail
An `expect` with `metric`, `direction` and `min_rel_diff` SHALL be met only when the verdict is `different`, the median moved in the wanted direction, and the relative difference is at least `min_rel_diff`. A missing metric SHALL not be met. A missed expectation SHALL make the exit code 1.

#### Scenario: A met expectation
- **WHEN** the verdict is `different` and the median moved the wanted way by enough
- **THEN** the expectation is met and the suite passes
- Checked by `harness/tests/test_suitelib_ab.py`.

#### Scenario: The wrong direction
- **WHEN** the median moved against the wanted direction
- **THEN** the suite exits with code 1
- Checked by `harness/tests/test_suitelib_ab.py`.

### Requirement: Reports are short
The suite SHALL write `report.json` and `report.md` in `runs/suite-<id>/`. `report.json` SHALL be at most 4096 bytes, or 8192 bytes with an A/B section of at most 8 metrics for each compared variant. The suite SHALL append one line for each run to `runs/suite-history.jsonl` and compute the flake rate over the last 20 runs of a scenario.

#### Scenario: A large suite
- **WHEN** a suite has 10 scenarios or many durations
- **THEN** `report.json` stays under its size limit
- Checked by `harness/tests/test_suitelib_report.py`.

#### Scenario: Exit codes
- **WHEN** a suite ends
- **THEN** the exit code is 0 for pass, 1 for fail or strict drift or a missed expectation, 2 for an unresolved crash or timeout, 3 for a budget or cap stop, and 4 for a harness error
- Checked by `harness/tests/test_suitelib_report.py`.

### Requirement: A suite can use several game slots
`suite.py --slots N|all` SHALL run jobs on free installed game slots at once, keep the sequential job order, and hand each run its slot. A scenario marked `EXCLUSIVE` SHALL run when no other game runs. A slot that fails to start SHALL be dropped, and the suite SHALL stop with `no_slots` when none work.

#### Scenario: Three slots
- **WHEN** a suite runs on three slots
- **THEN** the verdicts equal those of a sequential run and no two runs share a folder
- Checked by `harness/tests/test_suitelib_pool.py`.

#### Scenario: An exclusive scenario
- **WHEN** a scenario is exclusive
- **THEN** it never runs together with another game
- Checked by `harness/tests/test_suitelib_pool.py`.

#### Scenario: A broken slot
- **WHEN** one slot fails to start its run
- **THEN** the other slots finish the suite
- Checked by `harness/tests/test_suitelib_cli.py`.

### Requirement: A series repeats one scenario
`run_series.py --scenario X --runs N` SHALL run `run.py` N times in a row (1 to 20), print a table with the verdict and boot seconds of each run, write `runs/series-<time>.json`, and exit 0 only if every run passed. A launcher that prints no result line SHALL give a `harness_error` row.

#### Scenario: No result line
- **WHEN** the launcher prints no result line
- **THEN** the row is a `harness_error`
- Checked by `harness/tests/test_runlib_series.py`.

#### Scenario: The table and tally
- **WHEN** a series ends
- **THEN** the table lists each run and a tally of verdicts
- Checked by `harness/tests/test_runlib_series.py`.
