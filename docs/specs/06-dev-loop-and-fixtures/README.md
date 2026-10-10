# Spec 06: Dev loop, mock kit and save fixtures

Status: done. Part A (hot reload), part B (mock kit) and part C (fixtures through a private LOCALAPPDATA) are built and tested in the real game. Roadmap phase: 8 (see `docs/specs/00-harness-overview/README.md`).

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
- Crash reports in the private folder (expected in `<run>\appdata\ManorLords\Saved\Crashes`; not tested, no crash was forced).
- Steam cloud or achievements with a redirected folder (not tested).

## Acceptance criteria
- [x] A Lua change reaches the running game in under 30 s, checked with a version line in `mod.log`, 3 times in a row. (2.3 s, 2.1 s, 2.1 s.)
- [x] A new mod can be tested with the mock kit in under 30 lines, shown by two tests.
- [x] The fixture `base` is installed, loaded by the launcher (`READY`, paused) and removed, and no user save file changed (SHA-256 before and after). 3 runs with `--fixture base` passed; 204 user files identical; the private folder was deleted each time.
