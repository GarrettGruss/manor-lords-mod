# Step 4: parallel suite runner and EXCLUSIVE scenarios

Date: 2026-10-17.

## What it does
- `suite.py --slots N|all` runs a suite on several game slots at once. `--slots 1` (the default) keeps the old sequential runner (`suitelib/runner.py`) unchanged.
- `suitelib/pool.py` (`run_suite_parallel`) cuts the suite into jobs. A job is one repeat of one entry and one variant, with its retries. Jobs start in the order of the sequential runner (entries in order, variants interleaved: A, B, A, B), so the A and B runs of an A/B entry spread over all slots alike.
- One `SubprocessLauncher` per slot adds `--slot <n>` to `run.py`. The pool keeps a list of free slots and starts a job when a slot is free. The main thread waits for the first job to end (`concurrent.futures.wait`), then starts the next.
- Run ids stay unique: the run counter of `_SuiteRun` has a lock. Each run has its own run folder as before.
- `--slots all` takes the installed slots (`gameslots.installed_slots`). A number above the installed count is an error that names `install.ps1 -Slots`.

## EXCLUSIVE scenarios
- A scenario module can set `EXCLUSIVE = True`. `runlib.scenario.is_exclusive(name)` reads it.
- The pool starts an exclusive job only when no other job runs, and starts no job while an exclusive job runs. The jobs behind it wait, so the order stays the same.
- Set on the scenarios that use the real mouse: `place-building`, `policy-menu`, `probe-bailey`, `probe-manor-flow`, `probe-manor-module`, `probe-policy-followups`, `probe-steer`. Single mouse actions are already protected by `runs/.input.lock` (step 3). `EXCLUSIVE` is for scenarios that need the screen or the mouse for a long time, so another game window does not take the focus between clicks.
- A new scenario with real mouse or keyboard input must set it too. No test enforces this yet.

## A slot that fails to start
- `RunResult.start_failed` is true when `run.py` ends without `summary.json`, and the reason is not the iteration cap, an unknown scenario or a timeout. Then `run.py` refused before the run folder existed (slot not installed, slot lock held by a run outside the suite, a broken slot state file).
- The pool marks that slot bad and does not use it again. The job goes back to the front of the queue for another slot. The report lists `bad_slots` (JSON and markdown). A bad slot alone does not change the exit code.
- If no slot works, the suite stops with `no_slots` (exit code 3) and lists the entries that did not run.
- A run timeout stops only the game of that slot (`close_slot_game`, process search by exe path). The sequential runner still uses `game-close.ps1`.

## Tests
- `harness/tests/test_suitelib_pool.py` (12 tests): job order, 3 runs at the same time with the same verdicts as the sequential runner, variant order in the report, retries, an exclusive scenario never overlaps another run, a broken slot, no working slot, an unknown optional scenario, the iteration cap, separate run folders, the scenario flags.
- `harness/tests/test_suitelib_cli.py`: `--slots 2` passes `--slot` to each run, a broken slot (stub `HARNESS_STUB_BAD_SLOT`) is reported while the other slot finishes the suite, bad `--slots` values are refused. The stub launcher now locks its state file, because parallel stubs start at the same time.

## Not verified yet
- Step 5: a real A/B suite on 3 slots against the same suite on 1 slot (wall time and result ranges).
- An exclusive scenario in a real parallel suite.
