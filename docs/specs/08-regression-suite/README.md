# Spec 08: Regression suite and baselines

Status: done. Checked with the real game (see `implementation-notes/build-notes.md`, section Real runs). Roadmap phase: 10 (see `docs/specs/00-harness-overview/README.md`). Notes: `implementation-notes/build-notes.md`.

## Goal
Run many scenarios in one command, compare the results with baselines, and find flaky tests.
The agent runs the suite before a pull request and gets one report that says what changed.

## Non-goals
- Running on a schedule (needs an unlocked desktop session; see the open decisions in spec 00).
- Judging balance. The suite checks ranges that humans set.

## Background
- A run takes 1 to 3 minutes (spec 03). A suite of 10 scenarios takes 10 to 30 minutes.
- Scenarios return assertions (spec 04). Telemetry samples go to `telemetry.jsonl`.
- A single pass does not show that a test is stable. The 10-launch series showed that repeats find problems.
- The run lock allows one run at a time. The game is one process.

## Design

### Suite file
`harness/suites/<name>.json`:
```json
{ "name": "core", "scenarios": [ {"scenario": "smoke", "repeat": 1}, {"scenario": "time-advance", "repeat": 2, "fixture": "base"} ],
  "time_budget_s": 1800, "flake_retries": 1 }
```

### Variants (A/B, added for spec 10 U4)
An entry may have `variants` and an `expect` rule:
```json
{ "scenario": "smoke", "repeat": 5,
  "variants": [ {"name": "baseline"}, {"name": "with-pak", "paks": ["demo"], "env": {"X": "1"}} ],
  "expect": {"metric": "ticks", "direction": "lower", "min_rel_diff": 0.2} }
```
Without `variants` the entry has one implicit variant `default` (nothing changes). With variants, each repeat runs every variant in order (A, B, A, B), the launcher passes `--pak` and `--env` to `run.py`,
and `report.json` gets a `variants` list per scenario and an `ab` section (each later variant against the first, the 8 metrics with the largest effect size; the file stays under 8 KB).
The note `ab: different on N metrics` does not change pass or fail. A missed `expect` gives exit code 1. Rules and limits: `docs/specs/10-invasion-testability/implementation-notes/ab-statistics.md`.

### Runner
`python harness/suite.py --suite core [--max-minutes N]`:
- runs each entry in order through `run.py` (a subprocess per run, so a crash cannot stop the suite),
- stops early when the time budget or the iteration cap is reached, and says so in the report,
- retries a failed run up to `flake_retries` times and marks the scenario `flaky` when a retry passes,
- writes `runs/suite-<id>/report.json` (small) and `report.md` (human-readable table).

### Report
Per scenario: attempts, passes, verdicts, durations, failed assertions (names and values), flaky or stable, and the baseline comparison.
Top: totals, a verdict (`pass` if every scenario passed and none changed beyond its baseline), and what was skipped.

### Baselines
`harness/baselines/<scenario>.json` holds, for chosen metrics, a range `[lo, hi]` that a healthy run falls into (from telemetry or assertion values).
- `python harness/suite.py --update-baseline <scenario>` proposes ranges from the last N passing runs: min and max, widened by a margin. It writes a file that a human reviews.
  The tool never updates a baseline silently in a normal run.
- A run outside the range is a `drift` finding in the report. Drift does not fail the suite by itself unless the scenario marks the metric `strict`.
- Duration baselines catch a feature that makes the game much slower.

### Flake handling
- A scenario that passes and fails on the same code is flaky. The report lists the failing assertion and the run folders.
- The suite keeps a history file `runs/suite-history.jsonl` (verdict per scenario per run) so flake rates can be computed over time.

## Plan
1. [x] Write the suite runner and the report with unit tests (fake runs through a stub for `run.py`).
2. [x] Write 3 suites: `smoke` (1 scenario), `core` (the scenarios that exist), `soak` (one long scenario repeated).
3. [x] Run `core` twice in the real game. Record the report and the timings.
4. [x] Write the baseline tool. Make baselines for the scenarios that exist. Run again and check for drift.
5. [x] Test: a deliberate regression is caught by the suite. Done with an impossible baseline range (drift, strict drift) and the `selftest` scenarios (fail, timeout). No mod change was made to break a metric.
6. [x] (the roadmap in spec 00 is not changed here) Update the spec, the README and the roadmap.

## Open questions
- What margin for baselines? Start with 20% of the observed spread, plus a floor.
- How to compare telemetry curves (not only end values)? Start with end values and extremes.

## Acceptance criteria
- [x] `suite.py` runs a suite of at least 3 scenarios and writes `report.json` and `report.md`. (`core`: 3 scenarios, 5 runs, twice.)
- [x] A crash in one run does not stop the suite, and the report shows it. (A real fail and a real timeout did not stop `selftest`. A real game crash was not tested.)
- [x] A deliberate regression is reported as `fail` or `drift`.
- [x] The report for a passing suite is under 4 KB in `report.json`. (869 bytes for `core`.)
- [x] Baselines are written only on explicit request.
