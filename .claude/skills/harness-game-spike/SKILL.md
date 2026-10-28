---
name: harness-game-spike
description: Safely experiment with the running game to find out what Lua can read or do (a spike). Use when a feature depends on an engine fact that is not known yet, such as a function, a property, a data table, or what a call changes.
---

# Run a spike in the real game

A spike answers one question about the engine with evidence. Write the question first (in the proposal or design of the OpenSpec change that needs it), then keep the work small.

## Setup
1. Read what is known for the same area: the wiki (`docs/wiki/`), notes of open and archived changes (`openspec/changes/**/notes/`), and the legacy notes in `openspec/changes/archive/*-legacy-*/implementation-notes/` (spike-S*.md, `actions-catalog.md`). Do not repeat a finished spike.
2. Start a game that stays open: `uv run python harness\run.py --scenario noop --keep-open --run-id <id>` (for a new game: `--new-game --scenario noop --keep-open`) (or a hidden `probe-*` scenario, see `harness/scenarios/probe_raids.py`).
3. Talk to the game through the bridge (`ue4ss-bridge` MCP tools, or the bridge client from Python with the run's bridge folder; see `harness/README.md`). The MCP bridge tools may point to a different folder than a `--keep-open` run, and they may not be connected. Then use the Python client: set `UE4SS_BRIDGE_DATA_DIR=<run>/bridge`, and call `ue4ss_bridge.server.one(op, ...)` or `server.batch([...])` (from `mcp/`, started with `uv run python <file>`). Ops: `hook`, `events`, `get`, `set`, `call`, `props`, `objects` (arg `class_name`), `funcs` (arg `ref`), `world`. `get` and `set` take `ref` and `name`. Prefer one `batch` call over many single calls: each process start is slow.
4. Raw Lua eval (`eval_lua`) is approved by the user (2026-10-10) for single-player experiments only. Mods and scenarios must not depend on it.

## Hard rules (CLAUDE.md Safety)
- Never call a function that saves: `PawnCPP:requestSaveFile`, `SaveToDiskWithThumbnail`, `IoHandler:SaveGameToSlot`, `RequestMenuSave`, `Request Autosave`. They write into the user's real save folder. The launcher only reports a change after it happened.
- Do not read struct values with soft object fields (`getItem`, `RowStruct`) through the bridge: it crashes the game.
- Touch UObjects only on the game thread. The bridge does this for you.
- Never change cvars through the console (bridge `console_command`, for example `r.*`, `sg.*`, `t.MaxFps`). The game saves them into the user's REAL settings (`UserSettings.ini`, `rtsSettings.sav`), also with a private `LOCALAPPDATA` (spec 11, spike 2). Game settings belong to `harness/install.ps1`.
- One agent uses the game at a time. End every game process you start. Check `tasklist`. `harness\game-close.ps1` may be refused by PowerShell policy. Then close the game window (`CloseMainWindow`).
- Background shells can be killed by Claude Code when memory is low. Do not restart them on your own. Report it.
- Read elements of a property array directly. Never call `:get()` on a struct element of a property array, and do not read a struct that a function returns by value (`getSquadByID`): both crashed the game inside UE4SS, and a pcall cannot catch it. Call `:get()` only on function return values (spike S11).
- Never write to the user's saves. A run installs its fixture as a new slot and removes it again (spec 06, part D); do not touch other slots.
- A game started without HarnessBoot (for example a new game from the main menu) keeps the game's autosave timer (about 10 min). It wrote
  `autosave.sav` into the REAL save folder during a spec 14 spike. Send `disable_autosave` (HarnessActions) right after the game starts and
  check `autosave_status` (remaining time about one year).
- Do not destroy actors that the game made for its own systems (for example the planner's `GhostStaticMeshActor` wall pieces). The game keeps
  pointers to them: after `K2_DestroyActor` on the 92 pieces of a wall, opening the manor planner crashed the game (null read, spec 14).
  Destroy only actors that the mod spawned itself.
- Real mouse clicks need a mouse device in Windows (#115). Without one, `GetSystemMetrics(SM_MOUSEPRESENT)` is 0, the game gives no mouse
  position, `getMouse3d` returns Z -100000 and no ghost follows the cursor. Hover tooltips still work, so it looks like a bad click spot.
  `osinput` now raises `InputError` ("no mouse device"). If you see it, stop: plug in a mouse or ask the user. Do not retry clicks and do not
  burn launches. Check first with `uv run python harness/tools/s115_input_env.py` (`SM_MOUSEPRESENT 1` is needed).
- Do not scan all components (`FindAllOf` over mesh components) right after the game destroys actors (a demolish): a scan then crashed inside
  UE4SS (read 0x10). Let the game run a few seconds first, or read counts only.

## Method
- Change one thing, read before and after, write both numbers down. Count things (units, buildings, stock) instead of trusting a return value.
- Repeat a surprising result. A first-run effect can be a timing effect (the intro cinematic ends about 13 s after load and resets the speed).
- A game day is 40 game seconds. `getGameTimeAdjusted` is the reliable clock, not `bIsPlayerPaused`.
- A `--keep-open` run leaves the game paused. Unpause with `unPauseGame`, then `changeGameSpeed(3, false)` on the player pawn.
- The game drops to 1x when an army is spotted (often, when armies march through forest). Set the speed again every second during a spike; `ctx.time.run_game_*` does it for scenarios.
- Unit positions: read `SMUnit.realPos`. The actor location of a unit does not move.
- Player silver and influence are the properties `silver` and `influence` on the player pawn (`MyPawnCPP_BP3_C`). Set them with the bridge `set`. The UI updates after the next action.
- Hooks see only ProcessEvent (Blueprint) calls. Native UI actions (build mode, placement clicks) fire no hook. To test them, use the real mouse (`steer_*`, `osinput`).
- Screenshot of the live game: `runlib.phases.capture_game_window(path, pids)`.
- Placing a building with the real mouse (`activateBuildingMode(type)` + `ctx.click_with_mouse`): a valid ghost is WHITE; a red ghost or an error text means invalid. Click on open grass next to a road, away from plots and buildings, or the game refuses it (for example "no road access" on a burgage plot). Check the ghost in a screenshot before the click.
- The bridge `call` passes only JSON values. A call that needs an object (a pawn, a region) needs a named mod command.
- The AI lords write their decisions to `RTSMultiEngineCPP.debugLog_AI_general`, `_tactics` and `_construction` (command `lords_state`).
- A new field of a HarnessActions command must also be added to the field parser in `mod/HarnessActions/Scripts/main.lua` (a list of `raw:match` patterns). A field that is missing there is dropped without an error: the spike for `days` of `spawnArmy` ran with 0 in its first run (change `update-spawn-from-map-border`). Check the answer echoes the value.
- `centre_camera_on` moves the player pawn, so `distance_to_player` in `lords_state` is then the distance to the camera.
- Time-box each primitive. If it does not work after a reasonable try, record what was tried. "Not possible from Lua, because ..." is a valid result.

## Turn it into a test
When a primitive works: add a data-only action (HarnessActions, validated inputs, no eval) or a mod command, a read command that counts the effect, a scenario with `COVERS`, and fake-game tests. Run the scenario 3 of 3. Only then mark the criterion (skill `harness-coverage`).

## Write it down
In a worktree, copy the fixture saves and `harness/pakmod.local.json` from the main checkout first (they are git-ignored).
One note per spike in the change's notes folder (`openspec/changes/<change-name>/notes/<topic>.md`): question, method, numbers, verdict, what is not verified. If the verdict changes a decision, update the proposal, design or delta spec of the change in the same commit. Before the change is archived, add the facts that stay true to the wiki.
