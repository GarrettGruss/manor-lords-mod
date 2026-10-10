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
