# Spec 06: Dev loop, mock kit and save fixtures

Status: in progress: part B (mock kit) done; hot reload (part A) and fixtures (part C) pending. Roadmap phase: 8 (see `docs/specs/00-harness-overview/README.md`).

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
- A fixtures folder `harness/fixtures/` holds a manifest `fixtures.json` only: name, source slot, SHA-256, description, tags (the save files stay out of git).
- `python harness/tools/fixtures.py install <name>` copies the files of a slot to a NEW slot name `harness_<name>` in the save folder (additive; it never overwrites a file that is not a harness slot).
  It also writes `<slot>_descr.sav` and the image files the menu needs. `remove <name>` and `remove --all` delete only `harness_*` slots.
- The run launcher gets `--fixture <name>`: it installs the fixture and sets `HARNESS_TEST_SAVE=harness_<name>`.
- `harness/uninstall.ps1 -Remove` removes the `harness_*` slots too.
- First fixture: `base` (a copy of the user's `saveGame_0`). More fixtures are made by the agent through scenarios that save a game state (`PawnCPP:requestSaveFile`), spec 07.

## Plan
1. Test the hot reload options in the real game. Record the results (what works, how long, side effects like double hooks).
2. Build `reload_mods.py` for the working option, with tests. Measure the loop time.
3. [x] Build the mock kit and move the HarnessBoot test onto it. Write a second mod test as a proof. (Done: part B, see `implementation-notes/mock-kit.md`.)
4. Test in the real game whether the load screen lists `harness_base`. Then build `fixtures.py` and `--fixture`.
5. Run the launcher with `--fixture base` 3 times.
6. Update the spec, the README and the uninstall script.

## Open questions
- Which hot reload option is safe for mods that use `RegisterHook`?
- Do custom slot names work? What does the menu need (descriptor, thumbnail)?
- The `_descr.sav` holds `saveSlot`. Is it a plain copy problem, or must the descriptor be edited for the new slot name?

## Acceptance criteria
- A Lua change reaches the running game in under 30 s, checked with a version line in `mod.log`, 3 times in a row.
- A new mod can be tested with the mock kit in under 30 lines, shown by two tests.
- `harness_base` is installed, loaded by the launcher (`READY`, paused), and removed, and no non-harness save file changes (checked with hashes before and after).
