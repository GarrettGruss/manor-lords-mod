---
name: harness-mod-state
description: Let a Lua mod expose its own state, commands and metrics to the harness, and build or change a stand-in mod. Use when testing logic that a mod defines (raids, outposts, captives, tribute) or when adding a command to a mod.
---

# Mod state contract

Spec 10 (upgrade U10) and `docs/specs/10-invasion-testability/implementation-notes/mod-state-contract.md`.

## The fact that shapes the design
UE4SS gives every Lua mod its own Lua state. A shared module (`mod/shared/<Name>/<Name>.lua`) is loaded again in each mod. Tables and functions do not cross between mods. Files and game objects do. Real-game proof: run `20261010-172028-008b` failed when the registry was shared.

## How a mod exposes commands
```lua
local commands = (require("HarnessCommands"))   -- parentheses: require returns two values
commands.register("MyMod.reset", function(args) ... return {ok = true} end,
                  { count = { type = "number", required = true, min = 1, max = 100 } })
commands.metric("MyMod.captives", function() return state.captives end)
```
- Names are `Mod.command`. `harness.*` is reserved. Duplicates are refused.
- The first `register` or `metric` starts a poller (100 ms) in the mod's own state. It serves `<run>/modcmd/<Mod>/<n>.json` and answers `<n>.result.json` (atomic write). Built-in commands: `harness.list_commands`, `harness.metrics`.
- Arguments are checked against the schema before the handler runs. The handler runs in `pcall`, returns a JSON-encodable value, or `nil, "message"` to refuse. No eval. Requests go through the data-only `HarnessJson.decode`.
- Do not advance rules with a loop. The stand-ins read `TemporalComponent.daysTotal` lazily on each command or metric read.

## From a scenario
```python
ctx.mod.command("MyMod.capture", count=5)            # returns the result, raises ModCommandError / ModDidNotAnswer
ctx.mod.refusal("MyMod.free_captives", count=10)     # returns the refusal text, or None if it was accepted
ctx.mod.metric("MyMod.captives", None)               # current value
ctx.mod.wait_metric("MyMod.captives", lambda v: v == 0, timeout_s=20)
ctx.mod.commands("MyMod")                            # the commands of one mod
```
"mod did not answer: X" means the mod is not loaded or has no poller. Check `mod.log` for its `loaded version` line.

## Stand-in mods
`mod/InvasionStandIn` (outposts, captives, tribute) and `mod/RaidStandIn` (raid timeline, seasons, behavior, tiers, sack, politics) are toy models. They prove the test method for rules the base game does not have. When the real mod exists, the same scenarios run against it (change the prefix). A criterion is "method verified" on the stand-in and "passing" only on the real mod. Say "a toy model" in every scenario description.

## Tests
`FakeGame(separate_states=True)` gives each mod its own Lua state, like the real game. Always use it for cross-mod tests. A test that passes only in one shared state proves nothing.

## Deploy
`harness\deploy.ps1` enables every folder in `mod/`. Never copy mod files by hand.
