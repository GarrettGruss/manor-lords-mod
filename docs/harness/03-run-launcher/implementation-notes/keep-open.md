# `--keep-open` with the real game (spec 03 follow-up)

Date: 2026-10-10. Runs: `keepopen-1` and later ones (`keepopen-2` to `keepopen-4` were used for the probes of specs 06 and 09).

## Test

`python harness/run.py --scenario smoke --keep-open --run-id keepopen-1`

| Check | Result |
|---|---|
| Launcher exit | verdict `pass`, exit code 0, after the scenario (about 45 s) |
| Game after the launcher exit | still running (`ManorLords-Win64-Shipping`, PID 21832, 3.6 GB) |
| Game paused | yes: `read_clock.py` gave change 0.0 over 3 s, `gameSpeed` 0. The game answered bridge calls without the launcher |
| Private appdata | `runs/keepopen-1/appdata` still existed (3.8 MB, 201 files) |
| Run lock `runs/.lock` | gone: the launcher process ended and released it. Another run can start at once |
| Stop | `powershell -File harness\game-close.ps1` asked the window to close, the game did not close in 20 s, the script killed it ("the game was killed", exit 1). No game process left |
| After the stop | the appdata folder stays on disk until someone removes it |

## What `--keep-open` does and does not do

- No game process is stopped. The summary notes say so: "--keep-open: the game was left running" and the path of the appdata.
- **The user's save folder is not compared** in this mode (the compare is part of the appdata cleanup). The notes now say this.
- The private appdata is not deleted. It is a leak of about 4 MB per run when the user forgets it.
  The folder is inside `runs/<id>/` (not in git), and no lock or process is tied to it.
- A later normal run does not touch the old appdata. Its preflight stops a stale game process (the left-over game), and creates its own appdata.

## Cleanup (no new tool needed)

```powershell
powershell -File harness\game-close.ps1                        # stop the game (kills it if it ignores the close request)
.venv\Scripts\python.exe harness\tools\fixtures.py remove --appdata runs\<id>\appdata
```

`fixtures.py remove` refuses any folder that is not named `appdata` and has no `ManorLords/Saved` inside. It removed 201 to 205 files in 4 tests.
The teardown note for `--keep-open` now prints these two commands.

## Not verified

Direct launch with Steam closed, a minimized game window and another monitor (the other items of the spec 03 follow-up) were not tested.

## Late crashes (2026-10-15)

The collect phase copies crash reports once, at the end of the run. A kept-open game can crash later (run s104h-2 crashed 4 minutes after collect), and its report stayed only in the real `Crashes` folder.

- The launch phase now writes `runs/<id>/game.json`: the game pid, the run start time and the private appdata folder.
- `harness/tools/collect_crash.py runs/<id>` copies new crash folders of that pid and new UE4SS dumps into `runs/<id>/crash/`. It skips items already copied. It fails if `game.json` is missing (runs older than this change).

