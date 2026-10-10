# Launch series: 10 cold starts

Date: 2026-10-09. Script: `harness/launch-series.ps1 -Runs 10`. Build: HarnessBoot with the 8 s pause hold (commit 2c021fb).
Raw data: `runs/launch-series-20261009-232136.json` (not in git).

Each run: close the game, start it through Steam, wait for HarnessBoot, wait 5 s, read the game clock twice over 6 s.

## Result: 10 of 10 runs READY and paused

| Run | State | Time to ready (s) | pauseGame calls | Clock change in 6 s |
|---|---|---|---|---|
| 1 | READY | 42 | 2 | 0.0 |
| 2 | READY | 44 | 2 | 0.0 |
| 3 | READY | 43 | 2 | 0.0 |
| 4 | READY | 43 | 2 | 0.0 |
| 5 | READY | 42 | 2 | 0.0 |
| 6 | READY | 43 | 2 | 0.0 |
| 7 | READY | 43 | 2 | 0.0 |
| 8 | READY | 42 | 2 | 0.0 |
| 9 | READY | 43 | 2 | 0.0 |
| 10 | READY | 43 | 2 | 0.0 |

"Time to ready" includes closing the old game (8 s wait, then a kill) and the Steam start. The `READY` wait inside `game-launch.ps1` was about 31 s.

## Findings
- The runs are very consistent: 42 to 44 s each, with no `FAILED` and no timeout.
- **Every run made exactly 2 `pauseGame` calls.** The game restarts its clock once after our first pause, every time.
  So the late restart is not random. It is part of how the game loads. The 8 s hold in HarnessBoot is needed.
  The cause is still not known.
- **The game never closed on the close request.** All runs ended with `still running after 8 s; killing it`.
  The harness can rely on a kill. It cannot rely on a normal close.
- The earlier failures in `mod.log` (slot not in the list, menu widget not found in 120 s) did not appear in these 10 runs.
  Those failures happened while the user was starting and stopping the game by hand, or before the fixes. They were not reproduced.
- The test save was `saveGame_0` (the user's own save, never written to). The launches only read it.

## What this means for the spec
- Acceptance criterion "10 of 10 launches reach READY": met for this setup.
- Not yet done: use of a copy of the save under its own slot name, and the case where the "still in development" dialog is open.
