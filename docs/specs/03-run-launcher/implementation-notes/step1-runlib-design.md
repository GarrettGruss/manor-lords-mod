# Step 1: run folder, runner and summary (fake phases)

Date: 2026-10-09. Code: `harness/runlib/`, `harness/run.py`. Tests: `harness/tests/test_runlib_*.py` (48 tests, all pass).
Run the tests: `.venv\Scripts\python.exe -m unittest discover -s harness/tests -p "test_runlib*.py" -v`
Try the CLI: `.venv\Scripts\python.exe harness\run.py --fake pass --runs-root <temp folder>`

Written by a Sonnet agent. Reviewed by Claude: `summary.py`, `runner.py` and `run.py` were read in full and the tests were run.
Only fake phases exist. No game was started.

## What exists
| File | Job |
|---|---|
| `runlib/runfolder.py` | run ids (UTC), run folder, atomic config write, run lock with stale takeover, iteration counter |
| `runlib/summary.py` | `PhaseResult`, `Summary`, verdict rules, exit codes, size-limited atomic write |
| `runlib/runner.py` | phases with time limits, skip rules, `execute_run` (always writes the summary) |
| `runlib/fake_phases.py` | fake preflight, deploy, launch, boot, scenario, collect, teardown for the 5 outcomes |
| `run.py` | CLI: lock, iteration counter, folder, config, run, one-line result, exit code |

Exit codes: 0 pass, 1 fail, 2 crash, 3 timeout, 4 harness error.

## Decisions that the spec did not make
- **Verdict order, first match wins:** crash, timeout, fail, other failed or error or skipped phase (`harness_error`), missing scenario result (`harness_error`), pass.
  Crash is first because it explains the errors after it. `fail` is before `harness_error` because a failed scenario is a real result.
  Side effect: if the scenario fails and then `teardown` times out, the verdict is `timeout`. The `fail` is still visible in `scenario_result`. Check this when real phases exist.
- **Phase status:** each phase has `status` (ok, failed, timeout, skipped, error) and not the `ok: true` of the spec example.
- **Scenario passes** if its result has `passed: true`, or an `asserts` list where every item is `ok`. A result with neither is "unclear" and gives `harness_error`.
- **`PhaseFailed`:** raising this makes the phase `failed` (a real failure). Any other exception makes it `error` (a harness problem).
- **Timeouts:** each phase runs in a daemon thread that is joined with the limit. Python cannot kill a thread, so a timed-out thread keeps running.
  Real phases must stop their own work (for example, kill the game process) when they see a timeout.
- **Interrupt:** on `KeyboardInterrupt` the `collect` and `teardown` phases still run, then the interrupt is raised again. `summary.json` is written in a `finally` block.
- **Summary size:** over 4096 bytes, the `detail` and `reason` strings are cut step by step (300, 100, 30, 0 characters) and a WARNING goes into `notes`.
  `reason` is cut too, because it can copy a long `detail`.
- **Lock and counter:** both come before the run folder. A lock error or an iteration-limit error has no run folder, so there is no `summary.json`: the CLI prints to stderr and exits with 4.
  A duplicate run id also gives exit 4, but the iteration counter was already raised.
- **Stale lock:** a lock file whose process is dead is taken over, and the takeover is written into `notes`. A lock file with an unreadable PID is refused.
- **Defaults:** `--max-runs` is 20. The run id timestamp is UTC.

## Not verified
- A dead process whose PID was reused by another process can look like a live lock holder.
- The interrupt test uses `_thread.interrupt_main`. A real Ctrl+C was not tried.
- Line endings: the appended README section uses LF, and the rest of the file uses CRLF. Git normalizes this on commit.

## Next (step 2)
Real phases: `preflight`, `deploy`, `launch`, `boot`, `teardown`, with the real game. See the plan in the spec.
