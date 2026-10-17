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

## Real runs (2026-10-17)
The `core` suite (smoke x2, time-advance x2, telemetry-sanity x1) with `--slots all` (slots 0, 1, 2). Four suites, one after the other, with fixes in between:

| Suite | Result | Wall time | What happened |
|---|---|---|---|
| `20261017-201437-9e1d` | 5 of 5 pass | 312.8 s | slot 2 marked bad: `run.py` crashed before its run folder (see "Lock file race"). The other 2 slots finished the suite. |
| `20261017-202947-630e` | 5 of 6 pass, smoke flaky | 268.4 s | one teardown hit its 30 s limit while it waited for `runs/.saves.lock` |
| `20261017-203613-7410` | 4 of 5 pass, exit 4 | 243.9 s | a bridge call got no response in 15 s, and the bridge then called the live game "gone" |
| `20261017-204212-3120` | 5 of 5 pass, exit 0 | 247.5 s | no problem |

The same suite on 1 slot took 289 to 298 s (4 suites on 2026-10-10). So `core` gains only about 15%. Its scenarios are short (10 to 57 s), and the boot takes most of each run. In parallel, a boot takes 35 to 90 s, against about 25 to 30 s alone: three games load maps at the same time, and the save list lock (below) lets only one game at a time through the main menu. Suites with long scenarios (A/B raids, soaks) should gain much more. Step 5 measures that.

## Problems found and fixed
- **Save list read at the same time.** Three `run.py` started at the same moment: two games showed only `autosave` in their save list and failed with "slot did not appear in the save list in 30 s". The third game started 50 s later and saw all 47 saves. Fix: the launch phase takes `runs/.saves.lock` before it starts the game, and the boot releases it when the boot state leaves `WAITING_FOR_MENU` (or after 90 s, or at READY or FAILED). So a game reads the list while no other game reads it and no run changes the folder. After the fix, 3 runs started at the same moment all passed (twice).
- **Lock file race on Windows.** `os.open(O_EXCL)` raises `PermissionError`, not `FileExistsError`, while another process deletes the file. A delete also fails (WinError 32) while a waiting process reads the file. Both crashed `run.py` (`bump_iterations`). Fix: `PidLock` treats `PermissionError` as "taken" and retries a blocked delete for up to 2 s. Test: 6 processes count 90 times through `bump_iterations` with no crash and no lost count.
- **Phase limits did not count the lock wait.** Preflight, launch and teardown wait for `runs/.saves.lock` (up to 180 s). Their limits are now 60, 60 and 30 s plus 180 s. `RUN_OVERHEAD_S` (the kill timer of the suite and `run_series.py`) is now 1200 s.
- **False "game is gone".** After a bridge timeout, the bridge client checks the game with `tasklist` by image name (10 s timeout). Under the load of 3 games a failed `tasklist` reported a live game as gone (`popen.poll()` was still `None`). Fix: the launcher sets `UE4SS_BRIDGE_GAME_PID`, and the bridge then checks that one process with psutil.

## Open
- With 3 games, a bridge call can wait more than 15 s (`DEFAULT_TIMEOUT`) for the game thread. It happened once in 26 parallel runs. The run then ends with `harness_error`, which the suite does not retry. Not fixed: a longer timeout or a retry of such runs is a separate decision.
- Step 5: a real A/B suite on 3 slots against the same suite on 1 slot (wall time and result ranges).
- An exclusive scenario in a real parallel suite.

## Worktrees share the state (2026-10-17)
- Problem: every checkout built its paths from its own folder. A session in a git worktree saw only slot 0 (no `slots` folder) and none of the locks, the run counter or the fixture ledger of other sessions. Two sessions could start a game in the same slot, and a run's save check saw another session's fixture as a change to the user's saves.
- Fix: `harness/runlib/shared.py` finds the main checkout from the worktree's `.git` file. The slots, run locks, start claims, `.iterations`, the fixture ledger and `.saves.lock`, `.input.lock` and the save backups use the main checkout. A run folder stays in its own checkout. A non-default `--runs-root` keeps its own locks (tests). `install.ps1` and `uninstall.ps1` use the same rule.
- Real check: a temp worktree of the fix branch listed slots 0, 1 and 2. Three `run.py --slot auto` smoke runs, two from the main checkout and one from the worktree, started 1 s apart: all passed, in slots 0, 1 and 2, with fixture saves 51, 52 and 53, and the user's saves did not change.
