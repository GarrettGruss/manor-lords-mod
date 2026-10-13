---
name: harness-game-spike
description: Safely experiment with the running game to find out what Lua can read or do (a spike). Use when a feature depends on an engine fact that is not known yet, such as a function, a property, a data table, or what a call changes.
---

# Run a spike in the real game

A spike answers one question about the engine with evidence. Write the question first (the spec's spike list, for example S4 or S6), then keep the work small.

## Setup
1. Read the existing notes in `docs/specs/*/implementation-notes/` for the same area (spike-S*.md, `actions-catalog.md`). Do not repeat a finished spike.
2. Start a game that stays open: `.venv\Scripts\python.exe harness\run.py --scenario noop --keep-open --run-id <id>` (or a hidden `probe-*` scenario, see `harness/scenarios/probe_raids.py`).
3. Talk to the game through the bridge (`ue4ss-bridge` MCP tools, or the bridge client from Python with the run's bridge folder; see `harness/README.md`). The MCP bridge tools may point to a different folder than a `--keep-open` run. Use the run's folder if they cannot reach it.
4. Raw Lua eval (`eval_lua`) is approved by the user (2026-10-10) for single-player experiments only. Mods and scenarios must not depend on it.

## Hard rules (CLAUDE.md Safety)
- Never call a function that saves: `PawnCPP:requestSaveFile`, `SaveToDiskWithThumbnail`, `IoHandler:SaveGameToSlot`, `RequestMenuSave`, `Request Autosave`. They write into the user's real save folder. The launcher only reports a change after it happened.
- Do not read struct values with soft object fields (`getItem`, `RowStruct`) through the bridge: it crashes the game.
- Touch UObjects only on the game thread. The bridge does this for you.
- One agent uses the game at a time. End every game process you start. Check `tasklist`.
- Read elements of a property array directly. Never call `:get()` on a struct element of a property array, and do not read a struct that a function returns by value (`getSquadByID`): both crashed the game inside UE4SS, and a pcall cannot catch it. Call `:get()` only on function return values (spike S11).
- Never write to the user's saves. A run installs its fixture as a new slot and removes it again (spec 06, part D); do not touch other slots.
- A game started without HarnessBoot (for example a new game from the main menu) keeps the game's autosave timer (about 10 min). It wrote
  `autosave.sav` into the REAL save folder during a spec 14 spike. Send `disable_autosave` (HarnessActions) right after the game starts and
  check `autosave_status` (remaining time about one year).
- Do not destroy actors that the game made for its own systems (for example the planner's `GhostStaticMeshActor` wall pieces). The game keeps
  pointers to them: after `K2_DestroyActor` on the 92 pieces of a wall, opening the manor planner crashed the game (null read, spec 14).
  Destroy only actors that the mod spawned itself.
- Do not scan all components (`FindAllOf` over mesh components) right after the game destroys actors (a demolish): a scan then crashed inside
  UE4SS (read 0x10). Let the game run a few seconds first, or read counts only.

## Method
- Change one thing, read before and after, write both numbers down. Count things (units, buildings, stock) instead of trusting a return value.
- Repeat a surprising result. A first-run effect can be a timing effect (the intro cinematic ends about 13 s after load and resets the speed).
- A game day is 40 game seconds. `getGameTimeAdjusted` is the reliable clock, not `bIsPlayerPaused`.
- A `--keep-open` run leaves the game paused. Unpause with `unPauseGame`, then `changeGameSpeed(3, false)` on the player pawn.
- The game drops to 1x when an army is spotted (often, when armies march through forest). Set the speed again every second during a spike; `ctx.time.run_game_*` does it for scenarios.
- Unit positions: read `SMUnit.realPos`. The actor location of a unit does not move.
- The bridge `call` passes only JSON values. A call that needs an object (a pawn, a region) needs a named mod command.
- The AI lords write their decisions to `RTSMultiEngineCPP.debugLog_AI_general`, `_tactics` and `_construction` (command `lords_state`).
- Time-box each primitive. If it does not work after a reasonable try, record what was tried. "Not possible from Lua, because ..." is a valid result.

## Turn it into a test
When a primitive works: add a data-only action (HarnessActions, validated inputs, no eval) or a mod command, a read command that counts the effect, a scenario with `COVERS`, and fake-game tests. Run the scenario 3 of 3. Only then mark the criterion (skill `harness-coverage`).

## Write it down
One note per spike in the spec's `implementation-notes/` folder: question, method, numbers, verdict, what is not verified. Update the spec README in the same commit.
