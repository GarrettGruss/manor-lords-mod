---
type: Runbook
title: Install and environment
description: How to set up the PC for the harness - uv and the venv, install.ps1 and uninstall.ps1 (settings backup, game slots), deploy.ps1, Windows paths and the key environment variables.
tags: [install, slots, uv, environment, windows]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T16:04:01Z }
sources:
  - resource: repo://harness/install.ps1
  - resource: repo://harness/uninstall.ps1
  - resource: repo://harness/installstate.ps1
  - resource: repo://harness/deploy.ps1
  - resource: repo://harness/runlib/gameslots.py
  - resource: repo://harness/runlib/shared.py
  - resource: repo://harness/runlib/game.py
  - resource: repo://harness/runlib/runfolder.py
  - resource: repo://harness/runlib/environment.py
  - resource: repo://pyproject.toml
  - resource: repo://mcp/README.md
  - resource: repo://harness/tests/test_install_scripts.py
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-11-parallel-game-slots/README.md
---

# Install and environment

## Platform

- Windows. Shell: PowerShell or Git Bash. Game root: `C:\Program Files (x86)\Steam\steamapps\common\Manor Lords`. Executable folder: `ManorLords\Binaries\Win64\`.
- UE4SS is an experimental build in the new layout: `dwmapi.dll` and `ue4ss\` in `Win64\`. Lua mods go to `ue4ss\Mods\`, shared modules to `ue4ss\Mods\shared\<Name>\<Name>.lua`. Engine: UE 5.5.4.
- `UE4SS.log` is buffered. Use `HarnessLog` (`ue4ss/harness/mod.log`) for live output.
- Git Bash rewrites `/Game/...` paths. Set `MSYS_NO_PATHCONV=1` when you pass them to scripts.

## Python with uv

The project is a uv project: `pyproject.toml`, `uv.lock`, Python 3.12 or newer, venv `.venv`.
- Runtime dependencies: `mcp==1.30.0`, `mss`, `psutil`, `streamlit`. Dev group: `lupa` (fake game kit), `pillow`, `pyyaml` (the `repo-wiki` skill script).
- Make the venv: `uv sync`.
- Start every Python command with uv: `uv run python harness\run.py --scenario smoke`. Tests: `uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"`.
- Never call `python`, `python3` or `py` directly. On this PC they are the Windows Store stub, which waits forever. Do not pipe code into Python on stdin.
- Add a package: `uv add <name>` (test only: `uv add --dev <name>`). Commit `pyproject.toml` and `uv.lock`.
- The MCP servers in `.mcp.json` start `.venv\Scripts\python.exe` directly. That is fine: Claude Code starts them. See [UE4SS bridge](../integrations/ue4ss-bridge.md) and [Harness MCP tools](../integrations/harness-mcp-tools.md).

## deploy.ps1

`harness/deploy.ps1 [-GameDir] [-DryRun] [-Clean]` copies `mod/` into `ue4ss\Mods\`, verifies SHA-256 of the copies, enables the mods in `mods.txt` (a backup `mods.txt.harness.bak` is kept) and writes `Mods\.harness-manifest.json`. Do not copy files by hand. The run launcher calls it before each run, for the slot's game folder. See [Scenario run](../workflows/scenario-run.md).

## install.ps1 and uninstall.ps1

Why: the game reads and writes its settings in the REAL user folder `%LOCALAPPDATA%\ManorLords\Saved`, not in the private folder of a run (spec 11, spike 2). So a run cannot have private settings. The harness is installed into a state and uninstalled back.

`harness\install.ps1 [-GameDir] [-UserDir] [-SlotsDir] [-Slots 2] [-SettingsOnly] [-SkipDeploy]`:
1. `Assert-GameNotRunning`. The game writes its settings when it exits, so the script refuses while a game runs.
2. `Backup-UserFiles` copies `Config\Windows\GameUserSettings.ini`, `Config\Windows\UserSettings.ini` and `SaveGames\rtsSettings.sav` to `slots\.install\backup\` with SHA-256. It does this once. A second install keeps the first backup. The state file `slots\.install\settings.json` is written before the first change.
3. `Set-HarnessUserSettings` writes the harness values: lowest scalability groups, resolution quality 50, windowed 1280x720, 30 fps, no VSync. Other keys (key bindings) stay.
4. Unless `-SettingsOnly`: `New-Slot` builds `slots\<n>\Manor Lords\` for each new slot, appends it to `slots\.install\slots.json` after each slot, and runs `deploy.ps1 -GameDir <slot root>`.

A slot folder:
- `Win64` is a full copy (robocopy): exe, UE4SS, mods.
- `Content\Paks` is a real folder. The game paks are hard links, so slots must be on the same drive as the game. `~mods` is per slot and starts empty, so pak A/B tests do not mix.
- `Engine`, `ManorLords\Plugins`, `Content\Movies` and `Content\Slate` are junctions to the game folder (`$script:SlotJunctions`).
- About 0.6 GB per slot. Slot 0 is the normal game folder. Maximum slot number is 3 (`MAX_SLOT`).
- `slots/` is git-ignored. The main checkout owns it: `Get-MainCheckout` and `shared.py` make all git worktrees use the same slots, locks, run counter and fixture ledger. `HARNESS_SHARED_ROOT` overrides this (tests).

`harness\uninstall.ps1 [-GameDir] [-DryRun] [-Remove] [-SlotsDir]`:
- Both modes first restore the user files and check their hashes (`Restore-UserFiles`). A backup that changed since install is not restored and is an error. A file that did not exist before the install is removed. Only a full verified restore deletes the backup.
- Default mode (disable): delete the switch file `ue4ss\harness\autoboot.enable`, set every harness mod to `Name : 0` in `mods.txt`. Files stay. `deploy.ps1` enables them again.
- `-Remove`: also delete the files listed in the manifest, the pak files from `~mods` (only if the SHA-256 still matches), the folders `ue4ss\bridge` and `ue4ss\harness`, and the slot folders. Junctions are removed first, as links, so a delete never reaches the game folder.
- UE4SS itself, `dwmapi.dll`, `UE4SS-settings.ini` and saves are never touched. The script refuses a path outside `-GameDir`.

While installed, the user's own play also uses the harness settings. Run `uninstall.ps1` before you play.

Python reads the result in `harness/runlib/gameslots.py`: `installed_slots()` returns slot 0 plus each slot in `slots.json` whose exe exists. `settings_installed()` is true when `settings.json` exists. The user-save guard of a run always leaves out `rtsSettings.sav` (`GAME_REWRITTEN_SAVE_FILES`), because the game rewrites it at any time. Each slot has a screen tile (`TILES`) for its 1280x720 window.

## Key environment variables

| Variable | Set by | Meaning |
|---|---|---|
| `HARNESS_RUN_DIR` | launcher, per run | Run folder. The bridge folder and logs derive from it. |
| `HARNESS_AUTOBOOT`, `HARNESS_TEST_SAVE`, `HARNESS_TELEMETRY_INTERVAL_S` | launcher (`build_game_environment`) | Boot mode, save to load, telemetry period (0 is off). `HARNESS_NEW_GAME` and `HARNESS_NEW_GAME_MAP` start a new game on a map. `HARNESS_BOOT_NO_PAUSE=1` (set with `run.py --env`) makes HarnessBoot skip its pause step, to test a player launch. |
| `LOCALAPPDATA` | launcher, per run | Private folder for the run's saves and crash data. It does not hold the game settings (see above). |
| `HARNESS_MAX_RUNS` | user | Cap on runs in the runs folder. Default 400. `--max-runs` wins. Reset: delete `runs/.iterations`. |
| `HARNESS_GAME_ARGS` | user | Extra game command line arguments, space separated. |
| `HARNESS_SHARED_ROOT` | tests | Replaces the main checkout as the shared root. |
| `HARNESS_RUNS_ROOT` | tests | Runs folder for the MCP tools. |
| `UE4SS_BRIDGE_*` | launcher, `.mcp.json` | See [UE4SS bridge](../integrations/ue4ss-bridge.md). |

`run.py --env KEY=VALUE` adds a variable to the game process. Names starting with `HARNESS_RUN_DIR`, `LOCALAPPDATA`, `PATH` or `UE4SS_BRIDGE` are refused (`runlib/extra_env.py`). The pak AES key is a local setting and is never written to the repo: see [Pak mods](../workflows/pak-mods.md).

Every run records its setup in `summary.environment` (`runlib/environment.py`): game build id, exe size and date, test save and its SHA-256, Python version, run dir, git commit and dirty flag, and hashes of the deployed mods. See [Run folder and verdicts](../concepts/run-folder-and-verdicts.md).

## Safety

- Back up `%LOCALAPPDATA%\ManorLords\Saved\SaveGames` before tests. Never write to the original test save.
- Do not edit `UE4SS-settings.ini` or other game files unless the task needs it. Say what you changed.
- Ask before you change files outside this repo, except the planned deploy folder.
- Install and uninstall change the real settings files. Run them with the game closed.

## Tests

`harness/tests/test_install_scripts.py` runs both scripts with temp folders and real PowerShell (skipped without it). It checks a bit-for-bit restore of the user files, that a second install keeps the first backup, and that `-Remove` never deletes a file in the game folder. Slot logic: `harness/tests/test_parallel_slots.py`.
