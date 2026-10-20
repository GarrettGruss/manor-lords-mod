---
type: Concept
title: Safety rules
description: The rules that protect the user's real save folder and the game from harness code, with the guards that enforce them (guarded save_game, autosave push, save hash guard, slot ledger) and the crash-prone calls to avoid.
tags: [safety, saves, autosave, crash]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T15:30:28Z }
sources:
  - resource: repo://CLAUDE.md
  - resource: repo://mod/shared/HarnessSave/HarnessSave.lua
  - resource: repo://mod/shared/HarnessAutosave/HarnessAutosave.lua
  - resource: repo://mod/HarnessBoot/Scripts/main.lua
  - resource: repo://harness/runlib/harness_save.py
  - resource: repo://harness/runlib/saveslots.py
  - resource: repo://harness/runlib/fixtures.py
  - resource: repo://harness/runlib/phases.py
  - resource: repo://harness/tests/test_save_call_sites.py
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-24-mod-save-state/implementation-notes/save-hooks.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/implementation-notes/autosave.md
---

# Safety rules

The game writes saves into the user's REAL save folder (`%LOCALAPPDATA%\ManorLords\Saved\SaveGames`), also when a run has a private `LOCALAPPDATA`. A probe once overwrote the user's `saveGame_9` this way. The harness has layers of guards. The rules below are in CLAUDE.md (section Safety). If this page and CLAUDE.md differ, CLAUDE.md wins.

## Rules for the agent

- Never call a save function from a probe, a scenario or `eval_lua`. These are save functions: `PawnCPP:requestSaveFile`, `SaveToDiskWithThumbnail`, `IoHandler:SaveGameToSlot`, `RequestMenuSave`, `Request Autosave`. Never call `Request Autosave` or the native `SetAutosavePeriod`.
- The harness may save only through the action `save_game` (spec 24). `mod/shared/HarnessSave/HarnessSave.lua` is the only code that calls a save function.
- Player mods (the Invasion Mod) never call a save function. They react to the player's saves through hooks.
- Back up saves before tests. Never write to the original test save.
- Raw Lua eval is allowed only for single-player experiments and spikes. Mods and scenarios use named commands. See [mod commands and state](mod-commands-and-state.md).
- Do not edit `UE4SS-settings.ini` or other game files unless the task needs it. Say what you changed.
- Ask the user before you change files outside the repo, except the deploy folder.
- Compiled paks (`*_P.pak`) may be committed. The AES key must never be committed or written in the repo. Grep the diff for it before a pak commit. Do not commit original game paks.
- Treat a game crash as a result with logs, not as a harness failure.

## Guard 1: the guarded save_game

`Actions.save_game(label, keep=False)` (`harness/runlib/actions.py`) calls `ScenarioContext._guarded_save`, which takes `saveslots.saves_lock()` and calls `harness_save.save_game`. Order of steps:

1. `check_label`: letters, digits, space, `-`, `_`, up to 40 characters.
2. `choose_slot`: the next free slot `saveGame_<max+1>` (`saveslots.next_free_slot`). Refuse if any file of it exists.
3. `backup_folder`: copy the whole save folder to `BACKUP_ROOT` (`SHARED_RUNS/save-backups`, outside the game folder). Check the copy by hash. Keep the 5 newest backups.
4. Snapshot the folder (`fixtures.snapshot_user_files`: SHA-256 for each file).
5. Send the named command `save_game` (`save_slot`, `save_name` = `harness <label>`) to HarnessActions. The Lua side (`HarnessSave.check_request`) accepts only a slot that matches `^saveGame_%d+$` and a safe name. It refuses a slot that exists, and refuses when the existence check cannot run (fail closed). Then it calls `requestSaveFile` on the player pawn.
6. `wait_for_slot`: wait up to 30 s until `<slot>.sav` exists and the folder is unchanged for 2 polls.
7. `check_and_restore` with `judge`: only files of the new slot may be new. Any changed or removed existing file, or any unexpected new file, is a failure. Changed or removed files are restored from the backup, then `SaveGuardError` is raised.
8. Unless `keep`, `saveslots.record_saved` puts the new files in the slot ledger. The run end deletes them.

If the command or the wait fails, `_check_after_failure` still restores damage and registers stray slot files.

Status per CLAUDE.md: `save_game` has fake tests, but it has not run in the real game yet. The first real call needs a fresh backup and the user informed. Tests: `test_runlib_harness_save.py`, `test_fakegame_harnesssave.py`.

## Guard 2: only one file may name a save function

`harness/tests/test_save_call_sites.py` scans every code file (`.lua .py .ps1 .json .ini .cfg .toml .js`). It fails if a save function is called outside the allow-list (`HarnessSave.lua` and the test itself). Some files may name a function in a comment only. Docs (`.md`) may name them. Run it after you touch any save-related code.

## Guard 3: the autosave timer

The autosave timer of the game runs in real time, also while the game is paused (about 10 min after a load). `HarnessBoot` calls `HarnessAutosave.disable()` before READY. It uses `MLGameInstance:SetAutosavePeriodOnPawn` to restart the pawn timer with a period of one year (`DISABLED_PERIOD_S = 31536000`). It fails the boot if the timer is not pushed away. The module never calls a save function and never calls `SetAutosavePeriod` (it may write the settings file). A load restarts the game's 10 minute timer, so after READY `HarnessAutosave.guard_loads` hooks `MyPawnCPP_BP3_C:ReceiveBeginPlay` (one pre callback: a Blueprint script hook runs only its first callback). On each new player pawn it waits 2 s, pushes the timer away again with up to 5 tries, and logs the push or an error (change `fix-autosave-after-load`, #315). Commands: `autosave_status` (read only), `disable_autosave`. Test scenario: `autosave-after-load`. Notes: `openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/implementation-notes/autosave.md`. Test: `test_fakegame_harnessautosave.py`.

## Guard 4: hash of the user's save folder

- `fixtures.guarded(save_dir)` hashes all files before and after a block and raises `SaveFolderChanged` on any difference. `prepare_appdata` uses it, so a fixture preparation only reads the user's folder. The private appdata folder must not be inside the user's folder.
- The launcher takes a snapshot in preflight (`phases.user_files`, `ctx.state["user_saves_snapshot"]`). At run end, `_finish_appdata` removes the installed slot and the ledger saves, then compares the folder with the snapshot (plus files of kept saves). A difference fails the phase.
- The guard reports a change only after it happened. It does not prevent one.
- With `--keep-open`, the end comparison is skipped. The notes say how to clean up.

## Guard 5: the slot ledger

`harness/runlib/saveslots.py` installs a fixture save into the real folder under a free slot (see [dev loop and fixtures](../workflows/dev-loop-and-fixtures.md)). An install writes only new files (`open(..., "xb")`) and refuses when a target exists. Every file is written to a ledger (`SHARED_RUNS/.installed-slots.json`) with its SHA-256. An uninstall deletes only ledger files whose hash still matches. A changed or missing file is reported, never deleted. A lock (`saves_lock`) serializes all changes to the save folder and the ledger, because parallel runs share both. Entries of a run that is still alive are not removed by another run.

## Crash-prone calls

- A game crash writes its UE crash report into the REAL `%LOCALAPPDATA%\ManorLords\Saved\Crashes`, not the private one. The launcher copies it. See [debugging runs](../operations/debugging-runs.md).
- Do not read struct values with soft object fields (`getItem`, `RowStruct`) through the bridge. The game crashes.
- Never write a `Tags` array (names) through the bridge `set`. It crashes the game. Append in Lua: `object.Tags[#object.Tags + 1] = FName("x")`. `ModState` does this.
- Never write `region.regionName` with a made-up name and save: the load of that save crashes.
- Do not pass a Lua string to a UFunction with an `FName` argument on a component or mesh that may lack it. UE4SS crashes in `push_nameproperty` (access violation at `0x70`). Known cases: `pivot_attach`, and `GetSocketLocation` or `DoesSocketExist` on the ox shed meshes (spec 18 `hitch-socket-world-positions.md`). Read the socket list first (`GetAllSocketNames`), or skip the call.
- Unsafe spike commands need `HARNESS_ALLOW_UNSAFE=1`. Use them only in test games.

## Other design rules that protect the run

- Touch UObjects only on the game thread (`ExecuteInGameThread`).
- Write files atomically: `.tmp`, then rename.
- Use unique request ids and timeouts. Wipe bridge folders at launch.
- Use localhost only, single-player only. Cap the number of iterations.
- The simulation is not deterministic. Assert ranges, not exact values.
- Review any downloaded code before you install or run it.

See also [scenario run](../workflows/scenario-run.md).
