# Mod-state contract and the stand-in mod (spec 10, U10)

Status: redesigned on 2026-10-10 after the first real-game run. The new design is built and tested with the fake game kit (now with one Lua state for each mod) and fake bridges. NOT verified in the real game: the run of the three stand-in scenarios with the new design is pending.

## Finding of 2026-10-10 (real game, run `20261010-172028-008b`)
UE4SS gives every Lua mod its OWN Lua state. A shared module such as `HarnessCommands` is loaded once for each mod, so each mod has its own, separate registry.
`InvasionStandIn.reset` was registered in the state of the stand-in, but `HarnessActions` (another state) answered `unknown command`. The same holds for `HarnessTelemetry.register` called from another mod.
Lua tables and functions cannot cross states. Files and UObjects can. `ModRef:SetSharedVariable` carries only primitives.
The first design (one registry, commands relayed by `HarnessActions`) therefore cannot work. The fake kit hid this because it ran all mods in one Lua state.

New design, with the fewest moving parts: **each mod serves its own commands and metrics, in its own state, through its own folder.**
- The first `HarnessCommands.register(...)` or `HarnessCommands.metric(...)` in a state starts a small poller (`LoopAsync`, 100 ms) in that state.
- The poller reads `<HARNESS_RUN_DIR>/modcmd/<ModName>/<number>.json` and writes `<number>.result.json` (same file rules as `HarnessActions`: `.tmp` then rename, numbers in order, an answered number is skipped after a restart).
- Without `HARNESS_RUN_DIR` no poller starts.
- `HarnessActions` no longer knows about mod commands (its dotted-command branch and its `require("HarnessCommands")` are removed; `VERSION` is "5").
- Metrics are served by the built-in command `harness.metrics` of each mod. They are no longer in `telemetry.jsonl`.
- The fake kit has the option `FakeGame(separate_states=True)`. Each `load_mod` then runs the mod in its own Lua state (own globals, own `require`, own loaded modules, same game API and objects). The mod tests use it, so a test fails when a design relies on a shared registry.

## Why
The Invasion Mode mod adds systems that the base game does not have: outposts (O1 to O4, S4), captives (R5) and tribute (S5).
The harness must observe and drive that state the same way for every mod. This note defines one contract for it.
The stand-in mod `InvasionStandIn` is a toy that proves the contract. The real mod replaces it, and the scenarios run again against the real mod.

## The contract in one page
A mod exposes two things. Both are served by the mod itself, in its own Lua state.

1. **Commands** (actions on mod state): `HarnessCommands.register(name, handler, schema)`.
2. **Metrics** (values that the harness reads): `HarnessCommands.metric(name, fn)`.

Both use the name rule `<ModName>.<name>`.

| Part | Rule |
|---|---|
| Command name | `^[A-Za-z][A-Za-z0-9_]*\.[A-Za-z][A-Za-z0-9_]*$`, for example `InvasionStandIn.found_outpost`. The prefix `harness.` is reserved. |
| Metric name | The same rule, for example `InvasionStandIn.outposts_alive`. The value is a number, a boolean or a string. |
| Module | `ModName` is the folder name of the mod. One name for one thing. |

### Commands
```lua
local commands = require("HarnessCommands")
commands.register("MyMod.add_gold", function(args)
    -- args holds only checked values
    if args.amount > stock() then return nil, "not enough gold" end  -- a refusal with a message
    return { gold = addGold(args.amount) }                           -- any value that HarnessJson can encode
end, {
    amount = { type = "integer", required = true, min = 1, max = 1000 },
    reason = { type = "string", maxLength = 20, oneOf = { "tax", "loot" } },
})
```
- **Schema.** A table of argument name to rule. A rule has `type` (`number`, `integer`, `string`, `boolean`) and may have `required`, `min`, `max` (number types), `maxLength` (strings, default 64) and `oneOf` (strings). An unknown rule key is an error at registration (it catches typos). The registry keeps a private copy.
- **Validation.** Before the handler runs, the registry refuses unknown arguments, missing required arguments, wrong types (`null` is a wrong type, an integer must have no fraction), values out of range, strings that are too long or not in `oneOf`. The error names the command and the argument. The handler never sees an unchecked value.
- **Handler.** It runs on the game thread inside `pcall`. An error becomes `{ok=false, error="MyMod.add_gold failed: ..."}` and the registry goes on. To refuse on purpose, return `nil, "message"`. Returning only `nil` is refused too.
- **Result.** The result must be encodable by `HarnessJson.encode` (tables, numbers, booleans, strings). A function or userdata in the result is refused with a clear error.
- **Time.** A handler must be quick: it blocks the game thread. A handler that takes more than 0.05 s (`os.clock`) is logged as a warning in `mod.log`. It is not stopped (Lua cannot stop it safely). Do slow work in steps, over several commands.
- **Duplicates.** `register` raises an error for a name that exists. A mod that can hot reload calls `HarnessCommands.unregister(name)` first (the stand-in does).
- **Introspection.** `HarnessCommands.list(modName)` gives `{name, args}` sorted by name, for the commands of that mod and the built-in ones. The built-in command `harness.list_commands` returns it, so the harness can see what a mod has.
- **Own mod only.** The poller of mod X runs only `X.*` commands and `harness.*` commands. A request for `Y.cmd` in the folder of X is refused.

### Metrics
`HarnessCommands.metric("MyMod.gold", function() return gold end)`. The function returns a number, a boolean or a string.
The harness reads all metrics of a mod with the built-in command `harness.metrics`. The answer is `{"metrics": {"MyMod.gold": 40}, "errors": {}}`.
A metric function that raises an error, or returns another type, is left out of `metrics` and named in `errors` with the reason.
A second call with the same name replaces the function (a reload runs the file again).
The function runs on the game thread when the harness asks, so a value is always current. There is no history: `ctx.mod.metrics_window()` returns the reads that the scenario made itself.
Metrics are no longer written to `telemetry.jsonl` (the telemetry mod and its own `HarnessTelemetry.register` are unchanged for metrics that belong to the telemetry sampler, for example `custom.units`).

### How a request reaches a handler
```
scenario  ctx.mod.command("MyMod.add_gold", amount=5)
  -> <run>/modcmd/MyMod/0007.json   {"command":"MyMod.add_gold","args":{"amount":5}}       (written as .tmp, then renamed)
  -> the poller of HarnessCommands in the Lua state of MyMod (game thread): HarnessJson.decode -> validate args -> pcall(handler, args)
  <- <run>/modcmd/MyMod/0007.result.json   {"ok":true,"result":{"gold":40},"command":"MyMod.add_gold","id":"0007"}
```
- The folder is the mod name: the text before the first dot of the command name. The harness never creates it. The mod creates it when it registers its first command or metric, so a missing folder means the mod is not loaded.
- Numbers: the client writes `0001`, `0002`, ... in order (UE4SS Lua cannot list a folder). A new client continues after the highest request already in the folder. After a restart the poller skips the numbers that have a result.
- `HarnessActions` is not involved.

### Hot reload
UE4SS gives a restarted mod a new Lua state and stops the loops of the old state (`06-dev-loop-and-fixtures/implementation-notes/hot-reload.md`, observed with `HarnessLogTest`).
We rely on that. As a second guard, each poller writes a random token to `modcmd/<ModName>/owner.txt` when it starts and stops itself when the file holds another token.
So two pollers never serve the same folder for longer than one poll tick (100 ms). A test starts a second state for the same mod and checks that the old poller stops. In the same state, a second call to `register` starts no second poller (a per-state table).
A reloaded mod has a fresh registry. The stand-in calls `unregister` before `register` only for the case that the file runs twice in one state.

### The Python side
`ctx.mod` is a `runlib.modstate.ModState`:

| Call | Meaning |
|---|---|
| `command(name, **args)` | Run a command, return its `result`. A refusal raises `ModCommandError` (`.command`, `.reason` with the message of the mod). No folder or no answer raises `ModDidNotAnswer` ("mod did not answer: <ModName>": the mod may not be loaded, or the game stalls). |
| `refusal(name, **args)` | Run a command that must be refused. Returns the message, or `None` when the mod accepted it. |
| `commands(mod)` | The commands that the mod registered, with schemas. |
| `metric(name, default=...)` | The current value of a metric (one `harness.metrics` command). A missing metric raises `ModMetricError`, or gives `default`. A mod that does not answer always raises. |
| `read_metrics(mod)` | All metrics of a mod now, as `{name: value}`. |
| `wait_metric(name, predicate, timeout_s=15)` | Poll (every 0.5 s) until `predicate(value)` is true. Returns the value. A timeout raises `ModMetricError` with the last value. |
| `metrics_window(names=None, start_s=None, end_s=None)` | `{t, values}` for each read that the scenario made (`t` is seconds since `ctx.mod` was made). The mod keeps no history. |

`ModCommandChannel` (in `runlib/commands.py`) is the client of the folders. It raises `ModDidNotAnswer` (a `CommandError`) and `CommandRefused` when the mod answers `ok=false`. This is how `ModState` tells a refusal from a missing answer.
Use `ctx.expect.eventually(label, lambda: ctx.mod.metric(name, None) == 5, 20)` for an assertion on a metric. It records a pass or a fail and does not raise (a mod that does not answer still raises).

## Security rules
- **No eval.** The request is decoded by `HarnessJson.decode`, a strict data parser (depth limit 6, size limit 16 KB, duplicate keys refused). No `load`, `loadstring`, `dofile`, `loadfile`, `os.execute` or `io.popen` in the new Lua files; a test scans the sources.
- **Only registered names run.** A name must match the pattern and be in the registry of the mod. A name with other characters is not in the registry. The mod name in the folder path is checked by the Python client and by `HarnessLog.make_dir` (the only `os.execute` is in `HarnessLog`, with a checked path).
- **Arguments are data.** A string argument that holds Lua code is just a string (a test shows that it is never run).
- **Handlers are trusted code** of a mod that the developer deployed. The registry limits what the harness can send. It does not sandbox the handler.
- **Local only.** The channel is a file folder of the run (`modcmd/`). Single-player only. The commands never save the game: a mod must not register a command that calls a save function (see `CLAUDE.md`).
- The stand-in only changes its own Lua tables. It adds no hook and no loop (the poller of HarnessCommands is the only loop). It reads `TemporalComponent.daysTotal` (read only) to move its toy rules by game days.

## The stand-in mod `InvasionStandIn`
A test fixture in `mod/InvasionStandIn/Scripts/main.lua`. `deploy.ps1` copies and enables every folder in `mod/`, so it is also loaded in other runs. It is inert there: it registers commands and metrics and does nothing else.
The rules are deterministic and simple (they only prove the method):
- Regions 1 to 8; region 1 is home. Each region starts with 20 families and 200 grain. The treasury starts at 1000.
- Outpost: level 1 to 3, `trade_value = 10 + 10 * level`, `scouting_range = 5 + 5 * level`. A lost outpost has both at 0.
- `reveal(region_id, distance)`: seen when the outpost is alive and `distance <= scouting_range`.
- `raid_target()`: the alive outpost with the lowest region number, else the town.
- An alive, unprotected outpost pays tribute to the invader and leaks intel after 3 game days.
- `evacuate`: moves families and grain from any region to a region with an alive outpost; refused when the stock is too small.
- Captives: `capture`, `free_captives`, `captives`; ransom is 15 per captive held.
- Tribute: `offer_tribute(kind, amount)` with kind `payment` (once from the treasury), `hostages` (a count) or `vassal` (a yearly payment, every `year_days` game days, default 365; `set_year_days` shortens the toy year for tests). `accept_tribute`, `reject_tribute`, `tribute`.
- Game days: the mod runs no loop of its own (only the command poller of HarnessCommands). Each command and each metric read first applies the days that passed since the last call (read from `daysTotal`, at most 4000 days at once).
- Commands: `found_outpost lose_outpost upgrade_outpost outpost reveal raid_target region_stock evacuate capture free_captives captives offer_tribute accept_tribute reject_tribute tribute set_year_days reset`.
- Metrics (`HarnessCommands.metric`, read with `harness.metrics`): `InvasionStandIn.outposts_alive`, `.trade_value`, `.captives`, `.tribute_paid`, `.leaked`.

## Scenarios (run in the real game later by the caller; each name says it is a toy)
| Scenario | Covers | What it does |
|---|---|---|
| `standin-outposts` | O1 O2 O3 O4 S4 | Lists the commands; founds two outposts; reveal inside and outside the border; first raid target; loses an outpost (trade drops, scouting blind); leaves one unprotected for 4 game days at speed 3 (tribute and leak flags, metric `leaked`); evacuates and reads both places. |
| `standin-captives` | R5 | Captures 5, frees 2, refuses a too large free, frees the rest; counts, freed total, ransom value, metric `captives`. |
| `standin-tribute` | S5 | Offers and accepts a payment, a refused unaffordable payment, hostages, vassalage; 5 game days at speed 3 with a 2-day toy year; treasury and yearly payments; metric `tribute_paid`. |

## What was tested (fake game kit with one Lua state for each mod, no game)
- `test_fakegame_harnesscommands.py`: registration, validation, handler errors, refusals, non-JSON results, slow handler warning, strings are not run, source scan for eval, `list`, `serve`, metrics, the JSON decoder, and the poller (request file in, result file out, order and gaps, own mod only, no poller without a run folder, reload skips answered numbers, a stale poller stops, two mods with separate registries).
- `test_fakegame_invasionstandin.py`: the stand-in runs in its own state next to `HarnessActions` and `HarnessTelemetry`. The registry of another state does not hold the stand-in commands (this test fails with the old shared-registry design). Every toy rule, reload, no engine.
- `test_fakegame_kit.py`: the `separate_states` option (own globals, own loaded modules, shared game API).
- `test_runlib_modstate.py`: `ModCommandChannel` and `ModState` with a fake mod behind the request files, "mod did not answer" for a missing folder, and `ctx.mod` in the scenario context.
- `test_fakegame_standin_scenarios.py`: the three scenarios run against the real Lua files through the request files, a clock that overshoots, repeated runs, a mod that is missing, and broken rules that must fail the scenarios.

## NOT verified (needs the real game)
1. The whole new design in UE4SS: the poller starts in the stand-in state, creates `modcmd/InvasionStandIn/`, reads and answers the files. The first assertion of `standin-outposts` shows it at once.
2. That `LoopAsync` and `ExecuteInGameThread` work from a shared module that a mod `require`s (the module code runs in the state of the mod, but this is not checked in the real game).
3. That the old poller of a hot-reloaded mod stops (the loop stops with the old state, as seen for `HarnessLogTest`; the token file is a second guard that the real game has not exercised).
4. That the new command pattern, `HarnessJson.decode` and `os.execute("mkdir ...")` from `HarnessLog.make_dir` behave in the real Lua 5.4 of UE4SS (the kit embeds Lua 5.5).
5. `TemporalComponent.daysTotal` read from Lua (the Python side reads it through the bridge; the Lua read is new).
6. That a game day at speed 3 takes about 5 wall seconds with the stand-in loaded, and that the three scenarios fit their limits (120 s, 60 s, 120 s). A metric read now costs one command round trip (about 0.1 s) instead of a wait for the next telemetry sample.

`method_verified` stays false in `criteria.json` for O1 to O4, R5, S4 and S5. The scenarios are listed in `verified_by` as planned.
