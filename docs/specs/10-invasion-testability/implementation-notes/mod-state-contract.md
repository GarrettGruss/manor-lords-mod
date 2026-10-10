# Mod-state contract and the stand-in mod (spec 10, U10)

Status: built and tested with the fake game kit and fake bridges (2026-10-10). NOT verified in the real game: the real-game run of the three stand-in scenarios is pending.

## Why
The Invasion Mode mod adds systems that the base game does not have: outposts (O1 to O4, S4), captives (R5) and tribute (S5).
The harness must observe and drive that state the same way for every mod. This note defines one contract for it.
The stand-in mod `InvasionStandIn` is a toy that proves the contract. The real mod replaces it, and the scenarios run again against the real mod.

## The contract in one page
A mod exposes two things.

1. **Commands** (actions on mod state): `HarnessCommands.register(name, handler, schema)`.
2. **Metrics** (values over time): `HarnessTelemetry.register(name, fn)`.

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
- **Introspection.** `HarnessCommands.list()` gives `{name, args}` sorted by name. The built-in command `harness.list_commands` returns it, so the harness can see what a game has.

### Metrics
`HarnessTelemetry.register("MyMod.gold", function() return gold end)`. The function runs on the game thread at each telemetry sample.
Each sample in `telemetry.jsonl` holds the values under `custom`:
```json
{"n": 12, "clock": 1008, "date": {...}, "custom": {"MyMod.gold": 40, "InvasionStandIn.outposts_alive": 2}, "errors": []}
```
A metric function that raises an error is left out of the sample and `custom.<name>` appears in `errors`. Telemetry samples every 5 s of wall time by default (`HARNESS_TELEMETRY_INTERVAL_S`), also while the game is paused.
So a metric can be up to one interval old. After a command, wait for the metric (`ctx.mod.wait_metric`). The answer of a command is always current.

### How a request reaches a handler
```
scenario  ctx.mod.command("MyMod.add_gold", amount=5)
  -> <run>/commands/0007.json   {"id":"0007","command":"MyMod.add_gold","args":{"amount":5}}
  -> HarnessActions (game thread): a command name with a dot that is not built in goes to HarnessCommands.handleRequest
  -> HarnessJson.decode(request) -> validate args -> pcall(handler, args)
  <- <run>/commands/0007.result.json   {"id":"0007","command":"MyMod.add_gold","ok":true,"result":{"gold":40}}
```
The change in `mod/HarnessActions/Scripts/main.lua` is small on purpose (another worktree edits that file): one `require`, the command-name pattern now allows a dot, and one `elseif` branch in `runCommand`. `VERSION` was not changed.

### The Python side
`ctx.mod` is a `runlib.modstate.ModState`:

| Call | Meaning |
|---|---|
| `command(name, **args)` | Run a command, return its `result`. A refusal raises `ModCommandError` (`.command`, `.reason` with the message of the mod). No answer raises `CommandError` (the mod is not loaded, or the game stalls). |
| `refusal(name, **args)` | Run a command that must be refused. Returns the message, or `None` when the mod accepted it. |
| `commands()` | The registered commands with schemas. |
| `metric(name, default=...)` | The latest value of a metric in `telemetry.jsonl`. A missing metric raises `ModMetricError`, or gives `default`. |
| `wait_metric(name, predicate, timeout_s=15)` | Poll until `predicate(value)` is true. Returns the value. A timeout raises `ModMetricError` with the last value. |
| `metrics_window(names=None, start_clock=None, end_clock=None)` | One row `{clock, date, values}` per sample, for trends and rates. |

`CommandChannel` raises `CommandRefused` (a subclass of `CommandError`) when the mod answers `ok=false`. This is how `ModState` tells a refusal from a missing answer.
Use `ctx.expect.eventually(label, lambda: ctx.mod.metric(name, None) == 5, 20)` for an assertion on a metric. It records a pass or a fail and does not raise.

## Security rules
- **No eval.** The request is decoded by `HarnessJson.decode`, a strict data parser (depth limit 6, size limit 16 KB, duplicate keys refused). No `load`, `loadstring`, `dofile`, `loadfile`, `os.execute` or `io.popen` in the new Lua files; a test scans the sources.
- **Only registered names run.** A name must match the pattern and be in the registry. A name with other characters is not matched at all (the command pattern in HarnessActions only reads `[%w_%.]`).
- **Arguments are data.** A string argument that holds Lua code is just a string (a test shows that it is never run).
- **Handlers are trusted code** of a mod that the developer deployed. The registry limits what the harness can send. It does not sandbox the handler.
- **Local only.** The channel is a file folder of the run. Single-player only. The commands never save the game: a mod must not register a command that calls a save function (see `CLAUDE.md`).
- The stand-in only changes its own Lua tables. It adds no hook and no loop. It reads `TemporalComponent.daysTotal` (read only) to move its toy rules by game days.

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
- Game days: the mod does not run a loop. Each command and each metric read first applies the days that passed since the last call (read from `daysTotal`, at most 4000 days at once).
- Commands: `found_outpost lose_outpost upgrade_outpost outpost reveal raid_target region_stock evacuate capture free_captives captives offer_tribute accept_tribute reject_tribute tribute set_year_days reset`.
- Metrics: `InvasionStandIn.outposts_alive`, `.trade_value`, `.captives`, `.tribute_paid`, `.leaked`.

## Scenarios (run in the real game later by the caller; each name says it is a toy)
| Scenario | Covers | What it does |
|---|---|---|
| `standin-outposts` | O1 O2 O3 O4 S4 | Lists the commands; founds two outposts; reveal inside and outside the border; first raid target; loses an outpost (trade drops, scouting blind); leaves one unprotected for 4 game days at speed 3 (tribute and leak flags, metric `leaked`); evacuates and reads both places. |
| `standin-captives` | R5 | Captures 5, frees 2, refuses a too large free, frees the rest; counts, freed total, ransom value, metric `captives`. |
| `standin-tribute` | S5 | Offers and accepts a payment, a refused unaffordable payment, hostages, vassalage; 5 game days at speed 3 with a 2-day toy year; treasury and yearly payments; metric `tribute_paid`. |

## What was tested (fake game kit, no game)
- `test_fakegame_harnesscommands.py`: registration (valid, invalid names, reserved prefix, duplicates, bad schemas), validation (unknown, missing, wrong type, limits, `oneOf`), handler errors, refusals, non-JSON results, slow handler warning, strings are not run, source scan for eval, `list`, `handleRequest`, the JSON decoder, and the dispatch through the real HarnessActions mod file in the kit (request file in, result file out).
- `test_fakegame_invasionstandin.py`: registration of commands and metrics, metrics in the telemetry file, every toy rule, reload, no engine.
- `test_runlib_modstate.py`: `ModState` with a fake mod behind the channel and fake telemetry files, and `ctx.mod` in the scenario context.
- `test_fakegame_standin_scenarios.py`: the three scenarios run against the real Lua files (the chain scenario, ModState, request files, HarnessActions, HarnessCommands, InvasionStandIn, HarnessTelemetry), a clock that overshoots, repeated runs, and broken rules that must fail the scenarios.

## NOT verified (needs the real game)
1. **One registry across mods.** The fake kit loads all mods in one Lua state, so `require("HarnessCommands")` and `require("HarnessTelemetry")` give the same table to every mod. UE4SS may give each mod its own Lua state. Then the registry that `HarnessActions` sees would not hold the stand-in commands. The first assertion of `standin-outposts` (`stand-in commands are registered`) shows this at once. The same question applies to `HarnessTelemetry.register` from another mod (spec 04 tested it only in the kit).
   If states are separate, the fix is to let `HarnessActions` load the registrations, for example a mod calls `ModRef:SetSharedVariable` with a request, or the stand-in module is loaded by `HarnessActions` with `dofile`. Decide after the real run.
2. That the new command pattern, `HarnessJson.decode` and the dot dispatch behave in the real Lua 5.4 of UE4SS (the kit embeds Lua 5.5).
3. `TemporalComponent.daysTotal` read from Lua (the Python side reads it through the bridge; the Lua read is new).
4. That a game day at speed 3 takes about 5 wall seconds with the stand-in loaded, and that the three scenarios fit their limits (120 s, 60 s, 120 s).
5. A real hot reload of the stand-in (the kit only runs the file twice).

`method_verified` stays false in `criteria.json` for O1 to O4, R5, S4 and S5. The scenarios are listed in `verified_by` as planned.
