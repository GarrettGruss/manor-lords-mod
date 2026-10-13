# Spec 06: Dev loop, mock kit and save fixtures

Status: done (2026-10-12). Part D merged (PR 46). Part A (hot reload) and part B (mock kit) are done. **Part C was wrong:** no run ever loaded the fixture; every run started a new game (`implementation-notes/fixture-load-bug.md`). Part D replaces it. Roadmap phase: 8 (see `docs/specs/00-harness-overview/README.md`).

## Goal
Make iteration fast and the test situations repeatable:
1. Change a Lua mod and see it in the running game in under 30 s, with no game restart.
2. Test mod logic without the game, with a reusable fake game API.
3. Start runs from different test saves, without ever writing to the user's own saves.

## Non-goals
- Actions that create game situations (spec 07).
- Regression comparison (spec 08).

## Background
- Today a mod change needs a full run (about 1 to 2 min) or a game restart. `UEBridge` can reload only itself (`reload`). Other mods need a restart.
- `EnableHotReloadSystem` and `EnableAutoReloadingLuaMods` are 0 in `UE4SS-settings.ini`. The settings file is stock UE4SS config; changing it is a decision for this spec.
- The fake game API in `harness/tests/boot_state_machine.py` works but is private to that test.
- Save slots are files in `%LOCALAPPDATA%\ManorLords\Saved\SaveGames`: `<slot>.sav`, `<slot>_descr.sav`, and images. The menu lists slots by `saveSlot` name. It is not known if a custom slot name is listed.
- A mod that registers hooks twice after a reload may run twice. Reload must be safe for hooks (check `RegisterHook` behaviour on reload).

## Design

### Part A: hot reload
Options to test, in this order:
1. UE4SS hot reload: enable `EnableHotReloadSystem`, and trigger it with the Ctrl+R key (`PostMessage` or `SendInput` to the game window), or find a Lua or console call that does the same.
2. A `HarnessReload` mod: the bridge asks it to restart a named mod (`RestartMod` if the UE4SS Lua API has it, or `dofile` of the mod's main script with a guard against double hooks).
3. If neither is safe: a fast "restart and reload save" path (about 40 s) as the fallback.
Deliverable: `python harness/tools/reload_mods.py [--mod Name]` that deploys, reloads, and checks that the new code is active (the mod writes a version line to `mod.log`; the tool waits for it).

### Part B: mock kit (`harness/tests/fakegame/`)
- A Python package on top of `lupa`: fake UObjects (properties, methods, `IsValid`), TArray with `GetArrayNum` and 1-based index, structs, `FindFirstOf`, `StaticFindObject`, `ExecuteInGameThread`, `LoopAsync`, `RegisterHook`, `RegisterKeyBind`, `NotifyOnNewObject`, fake time, and a fake game clock with pause and speed.
- A `FakeGame` builder that creates a game state for tests (menu, regions, player, letters).
- Refactor `boot_state_machine.py` to use it. Add `docs` on how to write a mod test. A new mod needs a test in under 30 lines.

### Part C: save fixtures
Changed after a real-game test: the load screen lists only `autosave` and `saveGame_0` to `saveGame_27`, so a slot named `harness_<name>` is never listed (`implementation-notes/fixtures.md`).
New design: the launcher sets `LOCALAPPDATA=<run folder>\appdata` for the game process only. The game then reads and writes its saves in `<run>\appdata\ManorLords\Saved\SaveGames`.
- `harness/fixtures/fixtures.json` holds the manifest only: name, source slot, SHA-256 of each source file, description, tags (no save data in git).
- A run copies the fixture into the private folder as `saveGame_0` (and a read-only copy of the user's `Saved\Config`). The user's save folder is never opened by the game.
- `run.py --fixture <name>` (default `base`, a copy of the user's `saveGame_0`). The redirect is used by all runs.
- Hash guard: all user save files are hashed in preflight and in teardown. A difference fails the run. The private folder is deleted in teardown.
- `python harness/tools/fixtures.py list|record|install <name> --appdata DIR|remove --appdata DIR`.
- More fixtures are made by the agent through scenarios that save a game state (`PawnCPP:requestSaveFile`), spec 07.

**Correction (2026-10-11):** part C never worked. The game lists and loads saves only from the user's REAL save folder, so the copy in the private folder was never read. Worse, `HarnessBoot` passed the list entry through `:get()`, the menu's `LoadGame` then got no usable slot, and the game started a NEW game on the slot's map. The boot still reached READY, so the runs looked fine. Evidence and the fix: `implementation-notes/fixture-load-bug.md`.

### Part D: local fixture files and a slot install (user request, 2026-10-11)
Goal: keep save fixtures as files in the repo folder and load any of them with one command.
- Store: `harness/fixtures/saves/<name>/` holds the slot files under the stem `slot` (`slot.sav`, `slot_descr.sav`, `slot.png`, `slot_coat_<n>.png`). The folder is in `.gitignore` (save files are user data and a few MB). The manifest `fixtures.json` keeps the SHA-256 of each stored file, the description and the tags.
- `fixtures.py import <name> --source-slot <slot>` copies a slot of the user's save folder into the store. `--from <path to a .sav>` copies a slot from any folder.
- Install (`runlib/saveslots.py`): a run copies the stored files into the user's save folder under the next free name `saveGame_<max+1>` (the load screen lists only `saveGame_<n>` with numbers up to the highest one). It rewrites `saveSlot` in the copy of `_descr.sav` to the new name, because the game takes the slot name from that file, not from the file name. `saveName` (the name in the load list) becomes `harness <name>`. It never overwrites a file. A ledger `runs/.installed-slots.json` lists each copy with its hashes.
- Load: `HarnessBoot` loads that slot. It writes `MLGameInstance.savefileToLoad` before `LoadGame`, and it fails the boot when the field does not hold the wanted slot after the load (the bug above).
- Remove: teardown deletes exactly the installed files whose hashes still match the ledger, before it compares the user's save folder with the preflight snapshot. A file that changed is kept and reported. Preflight removes copies that an earlier run left (for example after `--keep-open`); `fixtures.py uninstall` does it by hand.
- Command: `python harness/tools/load_save.py <fixture name | path to a .sav>` starts the game with that save and leaves it open (a `noop` run with `--keep-open`). `run.py --save <path>` does the same for any scenario.
- A fixture with no stored files (`source_slot` only, the old kind) is loaded from its source slot by name, read only.
- Safety: this writes into the user's save folder, which the user asked for. Only new files with a free name are written, and only files that the ledger lists are deleted.

### Part E: fresh start, no save (user request, 2026-10-12)
Goal: start the game in a NEW game with one command, so agents can test the first minutes of a village without a click on "New Game".
Non-goals: choosing the start region, the family name or the difficulty. Loading a save (part D does that).
- Launcher: `load_save.py --new-game [--map NAME]` and `run.py --scenario <name> --new-game [--map NAME]`. The default map is `Jagged_Cliffs`.
  No fixture is installed and no slot is written. The run still uses the private `LOCALAPPDATA` and the save folder guard.
- Boot mode: the launcher sets `HARNESS_NEW_GAME=1` and `HARNESS_NEW_GAME_MAP=<name>`. HarnessBoot then skips the load screen.
  In the main menu it makes sure `MLGameInstance.savefileToLoad` is empty and opens the map `/Game/NotStronghold/Maps/NewMapSets/<map>`
  with the console command `open`. This is the same effect as the load bug of part C (a map that opens with no slot starts a new game).
- Then the normal steps run: wait for the map, push the autosave timer away, pause, write `ready.marker`. The autosave step is not optional:
  a new game keeps the 10 minute autosave timer, which writes into the user's REAL save folder.
- Check: after the map is ready, `savefileToLoad` must still be empty. A slot name there means a save was loaded: FAILED.
- Map names: only letters, digits and `_` are allowed (checked in Python and in Lua).

Plan for part E:
1. [x] Write this part.
2. [x] HarnessBoot mode `HARNESS_NEW_GAME`, with fake game tests (READY on a new game, FAILED on a timeout and on a loaded slot).
3. [x] Launcher options `--new-game` and `--map`, with unit tests.
4. [x] Real game check (2 launches): READY after 28 s, autosave pushed away, user saves unchanged. `PlayerController:ConsoleCommand` is not callable
   from Lua (`attempt to call a TrivialObject`, run `fresh-start-1`); `KismetSystemLibrary:ExecuteConsoleCommand` works (run `fresh-start-2`).
5. [x] Update `harness/README.md`, the skill `harness-run-scenario`, and `CHANGELOG.md`.

Acceptance for part E:
- [x] `load_save.py --new-game` reaches READY (paused) in the real game with no save loaded (run `fresh-start-2`, `savefileToLoad` empty).
- [x] The village is a fresh start: day 61, March, year 1, region Hochweg with 5 homeless families and 10 people (telemetry). The autosave timer went
  from 600 s to 31535400 s (boot log). `autosave_status` was not read: HarnessActions had no scenario in this run.
- [x] The user's save folder is identical before and after the run (240 files, fingerprint `4d4304b366f5`, checked by hand because `--keep-open` skips the compare).
- [x] Mock kit: a new game that starts gives READY. A map that never opens gives FAILED. A load of a slot gives FAILED.

## Plan
1. [x] Test the hot reload options in the real game. Record the results (what works, how long, side effects like double hooks). (Done: `implementation-notes/hot-reload.md`.)
2. [x] Build `reload_mods.py` for the working option, with tests. Measure the loop time. (Done: 2.1 to 2.3 s.)
3. [x] Build the mock kit and move the HarnessBoot test onto it. Write a second mod test as a proof. (Done: part B, see `implementation-notes/mock-kit.md`.)
4. [x] Test in the real game whether the load screen lists `harness_base`. **It does not.** Switched to a private `LOCALAPPDATA` per run (`implementation-notes/fixtures.md`). Built `fixtures.py` and `--fixture`.
5. [x] Run the launcher with `--fixture base` 3 times. All 3 runs passed (boot 31.0, 30.0, 31.0 s). The user's 204 save files were identical after the runs.
6. [x] Update the spec and the README. `uninstall.ps1` needs no change (no slot files are written to the user's folder).

## Answers to the open questions
- Which hot reload option is safe for mods that use `RegisterHook`? `RestartMod`: it gives the mod a new Lua state and UE4SS unregisters the old hooks. Auto reload is not safe for a change of two mods at once (only one is reloaded). See `hot-reload.md`.
- Do custom slot names work? **No.** The load screen asks `SlotNameFromIndex` for 30 fixed numbers and never reads another name.
- How is a fixture loaded then? The game gets a private `LOCALAPPDATA`, and the fixture is its `saveGame_0`. This works: boot reaches READY in about 31 s, the same as before.

## Open questions
- Does the load list keep working when the installed number is far above the user's slots? Only `max+1` is used, so this is not needed.
- Crash reports in the private folder (expected in `<run>\appdata\ManorLords\Saved\Crashes`; not tested, no crash was forced).
- Steam cloud or achievements with a redirected folder (not tested).

## Acceptance criteria
Part D:
- [x] `load_save.py manor-bailey` starts the game on day 106 with the manor (`manor_state`: region manor set), from files in `harness/fixtures/saves/manor-bailey/` (run `load-save-2`).
- [x] A run with `--fixture manor-bailey` passes 3 times; after each, the user's save folder equals the preflight snapshot (the installed copy is gone). Runs `manor-load-1` to `-3`.
- [x] A boot that starts a new game instead of the wanted slot ends in FAILED (mock kit mode `newgame`).
- [x] The `base` fixture is imported from `saveGame_0` and its runs load it (boot log `loaded slot confirmed`; run `base-load-1`: day 266, 24 buildings, 10 families).

Part A to C:
- [x] A Lua change reaches the running game in under 30 s, checked with a version line in `mod.log`, 3 times in a row. (2.3 s, 2.1 s, 2.1 s.)
- [x] A new mod can be tested with the mock kit in under 30 lines, shown by two tests.
- [x] The fixture `base` is installed, loaded by the launcher (`READY`, paused) and removed, and no user save file changed (SHA-256 before and after). 3 runs with `--fixture base` passed; 204 user files identical; the private folder was deleted each time.
