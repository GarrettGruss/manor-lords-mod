---
type: Concept
title: Run folder and verdicts
description: What is in runs/<id>/ after a run, the fields of summary.json and config.json, the five verdicts with their exit codes and precedence, and the size limit of the summary.
tags: [harness, runs, summary, verdict]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T15:30:28Z }
sources:
  - resource: repo://harness/runlib/summary.py
  - resource: repo://harness/runlib/runfolder.py
  - resource: repo://harness/runlib/runner.py
  - resource: repo://harness/runlib/phases.py
  - resource: repo://harness/run.py
---

# Run folder and verdicts

Each run makes a folder `runs/<id>/`. The id is `YYYYMMDD-HHMMSS-<4 hex>` in UTC (`new_run_id`), or the value of `--run-id`. An id that already exists is refused (`FileExistsError`, `harness_error`). `runs/` is not in git. How a run is made: [Scenario run](../workflows/scenario-run.md).

## Files in the run folder

| Path | Written by | Content |
|---|---|---|
| `config.json` | `write_config` | The plan: scenario, fixture, slot, phase limits, paks, masked env, environment hashes. Written at the start, and again after preflight and deploy. Not size limited. |
| `summary.json` | `execute_run` | The result. Under 4 KB. |
| `scenario.json` | scenario phase | The full `scenario_result`: asserts, metrics. |
| `scenario.log` | `ScenarioLog` | Asserts, `ctx.log` lines, scenario tracebacks. |
| `boot.json` | HarnessBoot | State and history of the boot. |
| `mod.log` | `HarnessLog` | Live log of all mods. |
| `UE4SS.log` | collect, teardown | Copy of the buffered UE4SS log. |
| `hostmem.jsonl` | `runlib/hostmem.py` | PC free and total memory and game resident memory every 2 s during the scenario (spike #465). |
| `telemetry.jsonl` | HarnessTelemetry | Samples (clock, speed, silver). Absent if telemetry is off. |
| `mod_files.json` | deploy | SHA-256 of every mod file. |
| `game.json` | launch | Game pid, start time, appdata path. Used by `collect_crash.py`. |
| `screenshots/` | scenario, collect | `start.png`, `end.png`, others. |
| `crash/` | collect | Copies of UE crash folders and UE4SS `*.dmp`. |
| `bridge/`, `commands/`, `modcmd/<Mod>/` | bridge, commands | Request and result files. |
| `appdata/` | preflight | Private `LOCALAPPDATA`. Removed in teardown. |

Shared state is not in the run folder: `runs/.lock`, `.lock-<n>`, `.iterations`. They live in the main checkout, shared by git worktrees.

Files are written atomically: a `.tmp` file, then rename (`atomic_write_text`).

## summary.json

The data class is `Summary`. `compact` drops empty fields before the write. A phase with status `ok` keeps only `name` and `seconds`. A bad phase keeps status and detail.

| Field | Meaning |
|---|---|
| `run_id`, `scenario`, `started`, `duration_s` | Identity and time. `started` is UTC. A fake run has scenario `fake-<outcome>`. |
| `verdict`, `reason` | The result and why. |
| `phases` | List of `{name, status, seconds, detail}`. Status is one of `ok`, `failed`, `timeout`, `skipped`, `error`. |
| `boot` | `{state, seconds, pause_calls, reason}` of HarnessBoot. |
| `scenario_result` | The scenario output: `passed`, or a list `asserts` with `ok` per item. |
| `crash` | `{reason, exit_code}` if the game ended without a stop request. |
| `artifacts` | `logs`, `crash`, `screenshots`, `telemetry`. |
| `environment` | The short form: game build, test save, mods hash, fixture and user save hashes (12 chars), paks, env keys, git commit (`+dirty`). The full form is in `config.json`. |
| `notes` | Anything skipped, unknown or cut. Read it before you trust the verdict. |

If the JSON is over `MAX_SUMMARY_BYTES` (4096), `_fit_to_limit` adds a WARNING note and cuts long `detail` and `reason` strings in steps (300, 100, 30, 0 characters).

## Verdicts and exit codes

`EXIT_CODES`: `pass` 0, `fail` 1, `crash` 2, `timeout` 3, `harness_error` 4. `run.py` returns the code of the verdict.

`decide_verdict` takes the first match:

1. `crash`: `state["crash"]` is set. A crash explains the errors and timeouts after it.
2. `timeout`: a phase has status `timeout`.
3. `fail`: HarnessBoot ended in `FAILED`, or the scenario result says it failed (`passed` false, or any assert not ok). This is before `harness_error` because a failed scenario is a real result, and cleanup phases after it may also report problems.
4. `harness_error`: any phase with status `error`, `failed` or `skipped`.
5. `harness_error`: no phase ran, or the scenario result is missing or unclear (`scenario_passed` returns `None`).
6. `pass`.

`harness_error` also covers the failures before the run folder exists (bad options, busy lock, run cap). Those print to stderr and write no summary.

A `pass` needs all phases `ok`, including teardown with its save comparison. Step 4 turns every bad phase into `harness_error`, unless a higher rule matched first.

## Extending

Add a field: put the data in `ctx.state`, add it to `Summary` and `_build_summary`, and check the size. Add a verdict rule only with a new row in `EXIT_CODES` and a test in `test_runlib_summary.py`.

## Tests

`harness/tests/test_runlib_summary.py` (verdict rules, size limit), `test_runlib_runfolder.py` (ids, locks, counter), `test_runlib_runner.py` (phase order, skips, timeouts). Run with `uv run python -m unittest discover -s harness/tests -p "test_runlib_*.py"`.

Next step after a bad verdict: [Debugging runs](../operations/debugging-runs.md).
