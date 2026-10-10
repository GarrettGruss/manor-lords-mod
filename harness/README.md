# Harness

## deploy.ps1

Copies `mod/` into the UE4SS `Mods` folder (PowerShell 5.1):

- `mod/shared/*` is merged into `Mods\shared\`.
- Every other `mod/<name>/` is deployed to `Mods\<name>\` and set to `<name> : 1` in `mods.txt`
  (inserted above the `; Built-in keybinds` block; the first change backs up to `mods.txt.harness.bak`).
- Only changed files (SHA256) are copied; every deployed file is re-hashed afterwards and the script exits 1 on mismatch.
- `Mods\.harness-manifest.json` records what was deployed; `-Clean` only removes files listed there.

```powershell
powershell -ExecutionPolicy Bypass -File harness\deploy.ps1 -DryRun   # preview, changes nothing
powershell -ExecutionPolicy Bypass -File harness\deploy.ps1           # deploy
powershell -ExecutionPolicy Bypass -File harness\deploy.ps1 -Clean    # also remove manifest-listed files no longer in mod/
powershell -ExecutionPolicy Bypass -File harness\deploy.ps1 -GameDir 'D:\Games\Manor Lords'
```

If the game is running a warning is printed and the deploy continues (UE4SS hot reload).
`UE4SS-settings.ini` is never touched.

## Lua checks without the game

Run from the repo root. They need only `uv`.

- Syntax of all mods: `uv run --no-project --python 3.12 --with lupa python harness/tests/lua_syntax.py`
- HarnessBoot state machine against a fake game API:
  `uv run --no-project --python 3.12 --with lupa python harness/tests/boot_state_machine.py happy`
  Other modes: `noslot` (slot not in the list) and `missing` (save file missing).

These checks use Lua 5.4 from the `lupa` package. They find syntax errors and wrong variable names.
They cannot show that the real UE4SS API behaves like the fake one.

## Note: HarnessBoot auto-load switch

`HarnessBoot` loads the test save only when it is turned on.

- The file `ue4ss\harness\autoboot.enable` (in the game's `Win64` folder) turns it on. It was created for the first in-game test.
- While that file exists, every game launch that reaches the main menu loads `saveGame_0`.
- Delete the file to get normal play back. Ask Claude to delete it if you prefer.
- The run launcher (spec 03) will use the environment variable `HARNESS_AUTOBOOT=1` instead of this file.

## Disable or remove the harness

`uninstall.ps1` (PowerShell 5.1) has two modes. Both support `-DryRun` and `-GameDir`. Running twice is safe.

- Default (disable): deletes `ue4ss\harness\autoboot.enable` and sets every harness mod to `Name : 0` in `mods.txt`.
  All files stay. Run `deploy.ps1` to enable the harness again.
- `-Remove` (full uninstall): also deletes the files listed in the manifest, the harness lines in `mods.txt`,
  the manifest, and the folders `ue4ss\bridge` and `ue4ss\harness`.
  `mods.txt.harness.bak` is kept. The script prints its path, so you can restore it by hand.

```powershell
powershell -ExecutionPolicy Bypass -File harness\uninstall.ps1 -DryRun   # preview
powershell -ExecutionPolicy Bypass -File harness\uninstall.ps1           # disable
powershell -ExecutionPolicy Bypass -File harness\uninstall.ps1 -Remove   # full uninstall
```

The script never touches UE4SS, `dwmapi.dll`, stock mods, `UE4SS-settings.ini` or the game saves.
If the game is running, the script warns. Changes take effect at the next game start.
To turn UE4SS off for one launch, use the Steam launch option `--disable-ue4ss`.
To turn UE4SS off fully, rename `dwmapi.dll`. The script does neither.

## Start and stop the game

All scripts: `powershell -ExecutionPolicy Bypass -File harness\<script>.ps1`. They never touch save files.

| Script | What it does |
|---|---|
| `game-launch.ps1` | Starts the game through Steam (`steam://rungameid/1363080`). Deletes the old `boot.json` and `ready.marker` first. With `-WaitForBoot` it waits until HarnessBoot reports `READY` or `FAILED`. |
| `game-close.ps1` | Asks the game window to close, waits `-GraceSeconds` (default 20), then kills the game. `-NoForce` never kills. |
| `launch-series.ps1` | Closes and starts the game `-Runs` times (default 10). It records the HarnessBoot state, the time to ready, the number of `pauseGame` calls, and whether the game clock is stopped. Results go to `runs\launch-series-<time>.json`. |

Exit codes of `game-launch.ps1`: 0 started (and `READY` with `-WaitForBoot`), 1 already running or HarnessBoot is off,
2 the process did not start, 3 HarnessBoot `FAILED` or the game ended, 4 timeout, 5 other error.
Exit codes of `game-close.ps1`: 0 closed or not running, 1 killed or still running, 2 error.

Notes:
- Steam starts the game, so the scripts cannot pass environment variables to it. HarnessBoot is turned on with the switch file `ue4ss\harness\autoboot.enable`.
- `launch-series.ps1` needs the project venv (`.venv`, see `mcp\README.md`). It reads the clock through the bridge with `harness\tools\read_clock.py`.
- In the first test, the game did not close after the close request (20 s), so `game-close.ps1` killed it. A kill can lose the end of `UE4SS.log`.
  `mod.log` is flushed on each line and is not affected.
