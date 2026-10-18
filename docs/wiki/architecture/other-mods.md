---
type: Architecture
title: Harness and player mods
description: The Lua mods in mod/ besides the Invasion Mod - harness mods (HarnessBoot, HarnessTelemetry, HarnessReload, HarnessPlace, HarnessActions, UEBridge), player mods (PolicyMenu, RefugeeWaves), stand-in fixtures and probes.
tags: [lua, mods, harness, boot, stand-in]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T15:30:28Z }
sources:
  - resource: repo://mod/HarnessBoot/Scripts/main.lua
  - resource: repo://mod/HarnessTelemetry/Scripts/main.lua
  - resource: repo://mod/HarnessReload/Scripts/main.lua
  - resource: repo://mod/HarnessPlace/Scripts/main.lua
  - resource: repo://mod/HarnessActions/Scripts/main.lua
  - resource: repo://mod/UEBridge/scripts/main.lua
  - resource: repo://mod/PolicyMenu/Scripts/main.lua
  - resource: repo://mod/PolicyMenu/mod.json
  - resource: repo://mod/RefugeeWaves/Scripts/main.lua
  - resource: repo://mod/RefugeeWaves/mod.json
  - resource: repo://mod/InvasionStandIn/Scripts/main.lua
  - resource: repo://mod/RaidStandIn/Scripts/main.lua
  - resource: repo://mod/HarnessLoadProbe/Scripts/main.lua
  - resource: repo://mod/HarnessLogTest/Scripts/main.lua
  - resource: repo://harness/deploy.ps1
---
# Harness and player mods

Every folder in `mod/` except `shared/` is one UE4SS mod. This page covers all of them except `InvasionMod/`. `harness/deploy.ps1` copies them all to `ue4ss\Mods\` and turns them on in `mods.txt`. They share code through [shared Lua modules](shared-lua-modules.md). The Invasion Mod is in [Invasion Mod structure](invasion-mod.md).

| Group | Mods |
|---|---|
| Harness mods (run control) | `HarnessBoot`, `HarnessTelemetry`, `HarnessReload`, `HarnessActions`, `HarnessPlace`, `UEBridge` |
| Player mods (released) | `PolicyMenu`, `RefugeeWaves` |
| Stand-in fixtures | `InvasionStandIn`, `RaidStandIn` |
| Probes and smoke mods | `HarnessLoadProbe`, `HarnessLogTest` |

## Harness mods

### HarnessBoot

Loads the test save from the main menu and says when the game is ready. It does nothing unless the harness turns it on: env `HARNESS_AUTOBOOT=1`, or the file `autoboot.enable` in the harness folder. Spec: `docs/harness/02-save-autoload/`.

- Env: `HARNESS_TEST_SAVE` (slot name, default `saveGame_0`), `HARNESS_NEW_GAME=1` with `HARNESS_NEW_GAME_MAP` (default `Jagged_Cliffs`) for a fresh start, `HARNESS_RUN_DIR`.
- State machine: `WAITING_FOR_MENU`, then `LOADING_SAVE` (or `STARTING_NEW_GAME` in new-game mode), `WAITING_FOR_READY`, `DISABLING_AUTOSAVE`, `PAUSING`, `READY`. Each wait has a timeout and can go to `FAILED`. `READY` means the game clock was measured as stopped.
- Output in the run folder: `boot.json` (state and history, always current) and `ready.marker` (written once at READY). Files are written atomically.
- `DISABLING_AUTOSAVE` uses `HarnessAutosave` to push the autosave timer one year away. This is a safety step (see [Safety rules](../concepts/safety-rules.md)).
- A poll runs every 500 ms and each step runs on the game thread.
- The Python side that reads these files and has a model of the state machine: `harness/tests/boot_state_machine.py`.

### HarnessTelemetry

Starts the shared `HarnessTelemetry` sampler (`telemetry.start()`). With `HARNESS_TELEMETRY_UNITS=1` it adds `custom.units` (unit counts by side and loot totals, about 10 ms a sample) through `HarnessUnits.register_telemetry`. Output: `telemetry.jsonl` in the run folder.

### HarnessReload

Restarts one Lua mod in the running game (spec 06, part A). See [Dev loop and fixtures](../workflows/dev-loop-and-fixtures.md).

1. An external tool writes `<run dir>/reload.json` with `{"mod": "Name", "id": "unique-id"}`.
2. The mod reads and deletes the file, checks that the mod folder exists (UE4SS `RestartMod` does not fail for an unknown name), and calls `RestartMod` on the game thread.
3. It waits up to 20 s for the line `[Name] loaded version <v>` in `mod.log`.
4. It writes `reload.result.json`: `id, mod, ok, version, line, error, seconds`.

A mod that wants to be reloaded must log `loaded version <v>` through `HarnessLog`, with its folder name as the tag. Each id is handled once. Tool side: `harness/tools/reload_mods.py`.

### HarnessActions

Runs a fixed list of named commands for the Python action kit (spec 07). Python writes `commands/<id>.json` in the run folder. The mod runs it on the game thread and writes `<id>.result.json`. The ids are 0001, 0002, ... in order. It needs object references that the bridge cannot pass (for example `send_letter`). It also holds the `paks/`, `ue/` helper sources for test pak assets. See [Mod commands and state](../concepts/mod-commands-and-state.md).

### HarnessPlace

Places a normal building at a world point without a mouse device (spec 18). It does nothing until `HarnessPlace.arm` runs. Then it hooks the pawn Blueprint tick and the cursor reads, writes the target point into the preview component `DummyBuilding` after each tick, and a short script presses and releases the left mouse button event.

- Commands (via `HarnessCommands`, prefix `HarnessPlace.`): `arm`, `disarm`, `state`, `bp`, `press`, `release`. `blueprint_route.lua` serves the `bp` command.
- Limits: building type 1..600, world coordinates within 200000.
- Notes: `docs/harness/18-composite-buildings/implementation-notes/mousefree-preview-hook.md`.

### UEBridge

The file-based request and response channel for live control: an external process writes `request.json` in `<ue4ss>\bridge\`, the mod runs the Lua on the game thread and writes `response.json`. Ops: `hello`, `ping`, `eval`, `batch`. Protocol 3. It is game-agnostic. The MCP server and the eval gate are in [UE4SS bridge](../integrations/ue4ss-bridge.md). The mod has `mod.toml`, `scripts/main.lua`, `scripts/json.lua` and `scripts/settings.lua`.

## Player mods

A player mod must run without the harness. It needs only `ManorCore`. `HarnessCommands` is optional: the mod loads it with `pcall(require, ...)`. Without it only the test commands are missing. Each mod has `mod.json` (name, version, `shared`, `pak`, `tested` versions, `gate_scenarios`) and a `CHANGELOG.md`. The release flow is in [Mod releases](../workflows/releases.md).

### PolicyMenu

A menu that lists the policies of the player region. A click signs or unsigns one (spec 16). F7 opens and closes it.

- The layout is a cooked Widget Blueprint in `policymenu_P.pak`, built by `mod/PolicyMenu/ue/make_widget.py`. Lua fills labels, colors and visibility at run time.
- The Blueprint has no graph. Lua polls `Button:IsPressed` every 40 ms. A press that ends with the mouse on the button is one click. It calls `Region:setPolicySigned` through `ManorCore`.
- Commands (prefix `PolicyMenu.`): `open`, `close`, `toggle`, `read`. Metrics: `clicks`, `entries`.
- Gate scenario: `policy-menu`.

### RefugeeWaves

A random event: homeless refugee families arrive (spec 15, issue #51).

- Each game month there is a chance (`chance_percent`, default 15) when the village has at least `min_families` families and no wave is active.
- A wave is 1 to 3 calls of `ManorCore.settle_region`, near the woods (`forest_spot`) or the village (`tent_find_spot`). A banner shows the event.
- The wave ends when the homeless count is back to the count before the wave. If refugees stay homeless too long, or approval falls under the floor, a share of the wave families leaves and returns as a bandit raid (`ManorCore.rebel_raid_rally`).
- The mod keeps no state that the game cannot rebuild. After a load, a new Lua state adopts the homeless families it finds as the active wave.
- It never calls `Region:AddNewFamily` (it crashes the game).
- Commands (prefix `RefugeeWaves.`): `configure`, `start_wave`, `check`, `status`, `forget_wave`.
- Gate scenario: `refugee-wave`. Test: `test_fakegame_refugeewaves.py`.

## Stand-in fixtures

`InvasionStandIn` and `RaidStandIn` are test fixtures. They are not real mods and not for normal play. Their header says: use on a developer machine only, do not ship. `harness/deploy.ps1` has no exception for them, so a deploy copies and enables them with the other mods. Only the stand-in scenarios use them.

- They model mod-defined state in plain Lua tables: outposts, captives and tribute (`InvasionStandIn`); the raid director, tiers, warlord, sack rule, laws, morale and seasons (`RaidStandIn`). Rules use fixed numbers, so a test can predict them. `RaidStandIn` uses a seeded random generator and a toy calendar (360 days a year).
- They change no game object. The only game read is the day counter (`TemporalComponent.daysTotal`).
- They register commands and metrics in `HarnessCommands` as `InvasionStandIn.<name>` and `RaidStandIn.<name>`.
- Purpose: prove that the harness can drive and observe mod-defined state before the real Invasion Mod exists (spec 10, U10). The real mod later passes the same scenarios.
- Scenarios: `harness/scenarios/standin_outposts.py`, `standin_tribute.py`, `raid_behavior.py`, `raid_seasons.py`, `raid_politics.py`. Tests: `test_fakegame_invasionstandin.py`, `test_fakegame_raidstandin.py`. Notes: `docs/harness/10-invasion-testability/implementation-notes/mod-state-contract.md` and `raid-standin.md`.

## Probes and smoke mods

- `HarnessLoadProbe`: manual probe for loading a save from the main menu. F8 opens the load screen and calls `mainMenu_widget_C:LoadGame`. The final logic lives in `HarnessBoot`.
- `HarnessLogTest`: logs a heartbeat every 5 s for about 30 s. It confirms that `HarnessLog` writes live, and it is the test mod for hot reload (change `VERSION`, reload, see the new number in `mod.log`).

## Extend

- New harness mod: add `mod/<Name>/Scripts/main.lua`. Log `loaded version <v>` with `HarnessLog` so hot reload works. Register commands with `HarnessCommands`. Do not use eval.
- New player mod: depend only on `ManorCore`, add `mod.json` and `CHANGELOG.md`, and make `HarnessCommands` optional.
- Load a mod in a fake-game test with `game.load_mod("<Name>")` (see [Fake game kit](../testing/fake-game-kit.md)).
