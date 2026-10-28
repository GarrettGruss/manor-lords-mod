# Dangerous actions

This file lists the actions that write into the user's real saves, crash the game, or leak secrets. People and agents must read it before they touch saves, the game or the bridge. `CLAUDE.md` imports it.

When you find a new dangerous action, add it here in the same pull request as the finding.

## Saves

- Game save functions write into the user's REAL save folder, even when a run has a private `LOCALAPPDATA`: `PawnCPP:requestSaveFile`, `SaveToDiskWithThumbnail`, `IoHandler:SaveGameToSlot`, `RequestMenuSave`, `Request Autosave`. A probe overwrote the user's `saveGame_9` this way (restored from the user's backup).
  - The user approved that the harness makes saves (2026-10-15), but ONLY through the guarded harness action `save_game` (spec 24). It backs up the save folder, saves to the next free `saveGame_<N>` slot (above the highest one, as fixtures do), and fails and restores if any existing save file changes. `mod/shared/HarnessSave/HarnessSave.lua` is the only code that calls a save function. A test enforces it (`test_save_call_sites.py`).
  - `save_game` has run in real games (test scenarios `mod_state/roundtrip`, `two_saves`, `tags_limits`, `liege_influence/influence_roundtrip`). Back up the save folder before each test run that saves.
  - Never call a save function from a probe, a test scenario or `eval_lua`. Never call `Request Autosave`.
  - Player mods (the Invasion Mod) never call a save function. They react to the player's saves through hooks.
  - The launcher hashes the user's save folder before and after each run. That guard only reports a change after it happened.
- The game's autosave timer runs in real time, also while the game is paused (about 10 min after a load). `HarnessBoot` pushes it one year away before READY (`MLGameInstance:SetAutosavePeriodOnPawn`, checked 2026-10-10). Do not call `Request Autosave` or the native `SetAutosavePeriod`.
- Back up saves before tests: `%LOCALAPPDATA%\ManorLords\Saved\SaveGames`. Never write to the original test save.
- Never write `region.regionName` with a made-up name and save: the load of that save crashes.

## Calls that crash the game

- Do not read struct values with soft object fields (`getItem`, `RowStruct`, a whole `DT_UnitTemplates` row) through the bridge.
- Do not read Squad structs (`GetSquad`).
- Do not read the unit properties `currAnim`, `dropsTo` or `Speed`.
- Never write a `Tags` array (names) through the bridge `set`. Append in Lua instead: `object.Tags[#object.Tags + 1] = FName("x")` (spec 24).
- Do not pass a Lua string to a UFunction that takes an `FName` argument on a component or mesh that may lack it. UE4SS crashes in `push_nameproperty` (access violation at `0x70`). Known cases: `pivot_attach`, and `GetSocketLocation` or `DoesSocketExist` on the ox shed meshes (spec 18 `hitch-socket-world-positions.md`). Read the socket list first (`GetAllSocketNames`), or skip the call.
- Never call `Button.OnClicked:Add` on a Button made at run time (found in the menu framework, #308).
- Do not use `take_by_lord`.
- Never call `K2_DestroyActor` on an `SMUnit`, living or dead. It crashed the game in 4 of 4 tries (reading 0xe60 for bodies, 0x938 for living units; spike-rebel-without-corpses). Use `just_die`, and `SetActorHiddenInGame` if the body must not show.
- Do not run the harness actions `family_add` and then `building_assign_worker` in one test scenario. Together they crashed the game in 3 of 3 runs (`rb-loot-6` to `-8`, change `update-banditry-rebellion-raid`).
- Check a widget returned by `GetChildAt` (or any child lookup) with `IsValid` before you call a method on it. A `GetClass` call on an unchecked child crashed the game (change `fix-order-tooltip-arrows`, #462).
- A game crash writes its UE crash report into the REAL `%LOCALAPPDATA%\ManorLords\Saved\Crashes`, not the private one. The launcher copies it.

## Game files

- Do not edit `UE4SS-settings.ini` or other game files unless the task needs it. Say what you changed.
- Never run `harness\game-close.ps1` while other agents use game slots.

## Secrets

- The AES key must never be committed. It may exist only in the gitignored files `modtools/work/aes_key.txt` and `.env` (written by `harness/tools/aes_env.py`, owner decision 2026-10-19). Never print it or write it into any other file.
- Before every commit that adds a pak or a pak tool change, grep the diff for the key. Do not commit the original game paks from the game folder.
- `.env` also holds API tokens. Never print it, and never copy it into worktrees.
