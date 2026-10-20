# Suite speedup: --slots 1 vs --slots 3

Date 2026-10-20. Branch `feat/11-parallel-game-slots` (95ea3b6). Suite `core` (5 runs: smoke x2, time-advance x2, telemetry-sanity x1). Save backup made before the runs.

| Suite id | Slots | Wall time (s) | Verdict | Runs passed |
|---|---|---|---|---|
| suite-20261020-064557-dd4d | 1 | 296.7 | drift | 5/5 |
| suite-20261020-065742-66da | 1 | 296.8 | drift | 5/5 |
| suite-20261020-065120-d970 | 3 (0,1,2) | 187.3 | drift | 5/5 |
| suite-20261020-065435-e514 | 3 (0,1,2) | 186.2 | drift | 5/5 |

- Speedup: 296.7 / 186.8 = 1.59x (not 3x).
- Reason: a run under 3 games takes longer. smoke 46 s with 1 slot, 55 to 105 s with 3. telemetry-sanity 91 s with 1 slot, 104 to 115 s with 3. The longest run (about 105 to 115 s, plus boot) sets the floor for 5 runs on 3 slots (two rounds).
- Results: all 5 runs passed in all 4 suites. The drift lines (calendar day 266, influence 660, silver 83) are identical with 1 and 3 slots. They come from the base fixture and are not caused by slots. The baseline ranges are old.
- No `harness_error` and no bridge timeout in the 2 parallel suites (task 3.1 count: 0 of 10 runs).

## Setup notes
- The first attempt failed in preflight: the gitignored fixtures `harness/fixtures/saves` were missing in the worktree. They were copied from the main checkout (ignored by git).
- `--slots 3` first failed with "only 1 game slot installed": `gameslots.SLOTS_DIR` is `REPO_ROOT/slots`, and a worktree has no `slots` folder. The slots are in the main checkout. A junction `slots` in the worktree to the main `slots` fixed it. Finding: slot lookup does not work from a worktree without this. Owner question: make `SLOTS_DIR` use the main checkout (as `install.ps1` does)?
- No game file was changed. `install.ps1` was not run.
