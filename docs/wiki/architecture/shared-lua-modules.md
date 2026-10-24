---
type: Architecture
title: Shared Lua modules
description: What the modules in mod/shared are, how mods load them, the rules they all follow, and which of them have fake-game tests.
tags: [lua, shared, modules, harness]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T15:30:28Z }
sources:
  - resource: repo://mod/shared/
  - resource: repo://mod/HarnessActions/Scripts/main.lua
  - resource: repo://harness/deploy.ps1
  - resource: repo://harness/tests/fakegame/README.md
---
# Shared Lua modules

`mod/shared/` holds 30 Lua modules. Each one is a folder `mod/shared/<Name>/<Name>.lua`. A mod loads one with `require("<Name>")`. No mod folder holds a copy.

## Loading and deploy

- `harness/deploy.ps1` copies every top-level folder of `mod/` into `ue4ss\Mods\`. It treats `shared` as a library: it adds no `mods.txt` line for it. Every other folder becomes a mod and is set to `: 1`. The `paks/`, `ue/` and `art/` folders of a mod are not copied.
- UE4SS resolves `shared\<Name>\<Name>.lua` for `require` (see `openspec/changes/archive/2026-10-15-legacy-01-ue4ss-bridge/README.md`).
- Each mod has its own Lua state. A module is loaded once for each state, so two mods never share a table. State that must cross mods goes through files (see [Harness and player mods](other-mods.md) and `HarnessCommands` below).
- A player mod that is released lists the modules it needs in `mod.json` (`"shared": ["ManorCore"]`). It must not need a `Harness*` module.

## Rules that every module follows

- Touch game objects only on the game thread.
- No save function. Only `HarnessSave` calls one (see [Safety rules](../concepts/safety-rules.md)). A test (`test_save_call_sites.py`) enforces it.
- No eval. Every input is checked (type, range, cap) before it is used.
- Read struct fields one by one. Do not read soft-object fields or use `:get()` on struct arrays: this can crash the game.
- Modules return a table `M`. A function takes a request table and returns a result table, or `{ ok = false, error = ... }`.
- Most modules say in their header which spec and which `implementation-notes` file hold the game facts.

## Modules by area

### Core and logging

| Module | Role |
|---|---|
| `HarnessLog` | Line-buffered, flush-on-write log. File: `$HARNESS_RUN_DIR/mod.log`, else `ue4ss/harness/mod.log`. Line: `<unix_time> <LEVEL> [<tag>] <message>`. `log.try` runs a function with a stack trace on error. |
| `HarnessJson` | JSON encoder and strict decoder. A table with keys `1..n` is an array. Other tables are objects with sorted keys. nil, NaN and infinity become null. The decoder only reads data. |
| `HarnessLoop` | `every(ms, fn)`: a repeating timer on the game thread (`LoopInGameThreadWithDelay`; `fn` returns true to stop). `HARNESS_LOOP_MODE=async` switches to `LoopAsync` for A/B tests. Falls back to `LoopAsync` when the UE4SS functions are missing. The fake game kit has `LoopInGameThreadWithDelay` and `CancelDelayedAction`, so tests run the game mode. Users: scheduler, HarnessCommands, HarnessActions, HarnessTelemetry, HarnessTune, mod_state, UEBridge, HarnessBoot, HarnessReload. |
| `HarnessCommands` | Command and metric registry (see below). |
| `HarnessTelemetry` | Sampler. It appends one JSON line per sample to `telemetry.jsonl`. `register(name, fn)` adds a metric. `start()` is safe to call twice. Env: `HARNESS_TELEMETRY_INTERVAL_S` (default 5, 0 turns it off). It uses wall time, so it works while the game is paused. |
| `ManorCore` | Game calls that a player mod needs, with no harness dependency: logger (uses `HarnessLog` if it exists), player region, `settle_region`, `forest_spot`, `tent_find_spot`, `rebel_raid_rally`, `show_banner`, policy list and `set_policy_signed`. The harness modules `HarnessLords`, `HarnessHousing`, `HarnessSack` and `HarnessBandits` call it, so there is one copy of the code. |

### Save, state and data

| Module | Role |
|---|---|
| `HarnessSave` | The only code that calls a game save function (`PawnCPP:requestSaveFile`). It accepts only a slot name that matches `^saveGame_%d+$` and refuses a slot that exists. The Python side (`harness/runlib/harness_save.py`) makes the backup and chooses the slot. |
| `HarnessAutosave` | Reads the autosave timer and pushes it one year away with `SetAutosavePeriodOnPawn`. It never calls `SetAutosavePeriod` or a save function. `HarnessBoot` uses it, before READY and (through `guard_loads`) after every later world load. |
| `ModState` | Keeps mod values in a save. Values are Names `<mod>:<key>=<value>` in the `Tags` array of the player pawn. It only touches entries with its own prefix and changes an entry in place. See [Mod commands and state](../concepts/mod-commands-and-state.md). |
| `HarnessDataTable` | Reads and writes single number fields of rows in `DT_Items` or `DT_UnitTemplates`. Only listed fields are read, because a whole-struct read crashes the game. A write changes memory only. |
| `HarnessGameSetup` | Reads and writes the game goal (`EGameGoals`: 0 Conquest, 1 Dominance, 2 Endless, 3 Growth). |

### Game actions and world

| Module | Role |
|---|---|
| `HarnessUnits` | Census of all units by side, role, squad type and state in one pass. Finds the side through the squad owner. Caps sample and squad rows. Can register itself as a telemetry source. |
| `HarnessRaids` | Raid and unit commands: raid state, spawn raiders, kill units, set loot. |
| `HarnessSteer` | Move orders for squads (`PawnCPP:formALineArmy`). |
| `HarnessLords` | Reads and steers the AI lords by number. |
| `HarnessBandits` | Letters to the bandit faction, settle raiders, and the reverse path (families turn to bandits). |
| `HarnessPolicies` | Reads and enacts the policies of the player region. |
| `HarnessHousing` | Housing, homeless tents and families. |

### Combat

| Module | Role |
|---|---|
| `HarnessBattle` | Spawns units of a template on a side (`spawnArmy`), hires mercenaries, counts casualties. It keeps a registry squad id to side, template and start count in the Lua state of the loading mod. A game restart empties it. |
| `HarnessBattlefield` | Moves the battle site of a challenge by placing every `battlefield_BP_C` actor at one anchor for a short time. |
| `HarnessTune` | Live unit stat overrides by side or squad. A timer applies them again to new units. It records the original value so `tune_reset` can restore it. |
| `HarnessLoot` | Stand-in for ground loot: piles as plain Lua tables. |

### Buildings and manor

| Module | Role |
|---|---|
| `HarnessSack` | Takes a share of a village away: burn or collapse buildings, remove goods, kill families. Every change is read back with a census before and after. |
| `HarnessBuild` | Reads site goods, ruins a building, clears ruins, lowers the cost of a site. A cost can only be lowered. |
| `HarnessManor` | Reads the manor (Keep, type 57, and its modules) and keeps goods in it. `finish_site` is a harness shortcut. |
| `HarnessWalls` | Builds walls outside the manor system (a `Road` actor with roadType 3 and a wallType). |
| `HarnessParts` | Reads, adds and removes the parts of a built composite building. Write commands are unsafe test commands and need `HARNESS_ALLOW_UNSAFE=1`. |
| `HarnessGarrison` | Opt-in bonus for the manor garrison limit by a post-hook. Env: `HARNESS_GARRISON_BONUS`, `HARNESS_GARRISON_MODULE_TYPE`. Not installed when the bonus is unset or 0. |
| `HarnessEncampment` | Finds camp sites and spawns a placed mesh actor. It destroys only actors it spawned. |
| `HarnessWagenburg` | Reskins the walls and keep of one manor with wagon and tent meshes (spec 32). |

### UI

| Module | Role |
|---|---|
| `HarnessUi` | Shows a text banner (`PawnCPP:playEventMessage`) and reads the text back from the widget. The message type must be an FName. Text is limited to a safe character set. |

## HarnessCommands in detail

`HarnessCommands` is the link between Python and any mod.

1. A mod calls `register("Mod.command", handler, schema)` or `metric("Mod.name", fn)`. Names match `<Mod>.<name>`. The prefix `harness.` is reserved.
2. The first call in a Lua state starts a poller in that state.
3. The client writes `$HARNESS_RUN_DIR/modcmd/<Mod>/<number>.json`. The poller runs the handler on the game thread inside pcall and writes `<number>.result.json` (`{"ok":true,"result":...}` or `{"ok":false,"error":...}`). Files are written as `.tmp` and renamed. Numbers go in order (0001, 0002, ...), because UE4SS Lua cannot list a folder.
4. The schema lists every allowed argument. Unknown, missing or wrongly typed arguments are refused before the handler runs.
5. Built-in commands: `harness.list_commands` and `harness.metrics`.
6. Hot reload: each poller writes a token to `<Mod>/owner.txt` and stops when the file holds another token.

Without `HARNESS_RUN_DIR` no poller starts.

## Who loads what

`HarnessActions` (`mod/HarnessActions/Scripts/main.lua`) requires most of the harness modules (Json, Autosave, DataTable, Raids, Sack, Loot, Battle, Ui, Build, Manor, Lords, Walls, Policies, Bandits, Housing, Parts, Steer, Battlefield, Tune, Garrison, GameSetup, Save, Encampment, Wagenburg) and serves them as fixed commands through `commands/<id>.json` files. See [Mod commands and state](../concepts/mod-commands-and-state.md). Other mods are listed in [Harness and player mods](other-mods.md).

## Extend

- Add a folder `mod/shared/<Name>/<Name>.lua`. Put the spec, the reason and the game facts in the header. Follow the rules above.
- If the harness must call it, add a command in `HarnessActions` or register one with `HarnessCommands`.
- Add a fake-game test. A new module that touches a save function fails `test_save_call_sites.py`.

## Tests

Fake-game tests run the Lua code without the game. See [Fake game kit](../testing/fake-game-kit.md).

```
uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"
```

Files named `test_fakegame_harness<name>.py` exist for Autosave, Bandits, Battle, Battlefield, Build, Commands, DataTable, Encampment, Housing, Log, Lords, Manor, Parts, Policies, Sack, Save, Tune, Units and Walls. `ModState` has `test_fakegame_modstate.py`. `HarnessTelemetry` is covered by `test_telemetry_mock.py`. `ManorCore` is covered through the mod tests (refugees, vassals). `HarnessGarrison` has no test that names it.
