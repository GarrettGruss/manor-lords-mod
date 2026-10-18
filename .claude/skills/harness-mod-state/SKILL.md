---
name: harness-mod-state
description: Let a Lua mod expose its own state, commands and metrics to the harness, and build or change a stand-in mod. Use when testing logic that a mod defines (raids, outposts, captives, tribute) or when adding a command to a mod.
---

# Mod state contract

Spec 10 (upgrade U10) and `docs/harness/10-invasion-testability/implementation-notes/mod-state-contract.md`.

## The fact that shapes the design
UE4SS gives every Lua mod its own Lua state. A shared module (`mod/shared/<Name>/<Name>.lua`) is loaded again in each mod. Tables and functions do not cross between mods. Files and game objects do. Real-game proof: run `20261010-172028-008b` failed when the registry was shared.

## Player-safe mods
A mod that players install (RefugeeWaves) must not need harness-only modules. It requires `ManorCore` (`mod/shared/ManorCore/ManorCore.lua`: region, settle region, spot finders, rebel raid, banner, and a logger with a `print` fallback). The Harness modules (HarnessLords, HarnessHousing, HarnessSack, HarnessBandits) call ManorCore, so the code exists once. `HarnessCommands` is optional there: `pcall(require, "HarnessCommands")`, and the test commands exist only when it is present. Rules: skill `harness-release`.

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

## Commands of HarnessActions (base game)
HarnessActions is version 53 on branch 28 (52 on branch 25 and 24; older branches use 49 to 51). Newer commands: `unit_stats`, `set_unit_stat`, `combat_hook` (module HarnessBattle, spec 25); `battlefield_anchor`, `battlefield_state` (module HarnessBattlefield: move all `battlefield_BP_C` to the manor while `lord_challenge` runs, restore after `delay_ms`); `steer_state`, `steer_select`, `steer_cursor`, `steer_mouse3d`, `steer_move`, `steer_rmb`, `steer_hook`, `steer_hook_log` (module HarnessSteer); `master_parts` (read only), `master_part_add`, `master_part_remove` (module HarnessParts, unsafe: need `HARNESS_ALLOW_UNSAFE=1`); `family_census`, `member_fields`, `family_add` option `adult`; `policy_enact_sweep` (unsafe spike command); `manor_blueprint_add` option `mesh` (asset path). Catalog: `docs/harness/07-feature-test-kit/implementation-notes/actions-catalog.md`.

## Keep mod values in the save (ModState)
Shared module `ModState` (mod M01). A feature of `InvasionMod` calls `ModState.open("invasion", "pawn", version)`, then `state:register(key, default, kind)`, `state:get`, `state:set` (flushes at once). Values are Tags `invasion:<key>=<value>` on the player pawn. They survive a save and a load. Never write Tags through the bridge (crash) and never remove a Tag: ModState overwrites in place. An unregistered key fails loudly. Test commands: `InvasionMod.mod_state_dump`, `mod_state_set`. Feature `invasion` (M02) adds `InvasionMod.invasion_state`, `invasion_force_next`, `invasion_set_difficulty`, `invasion_set_size`. Feature `raid_behavior` (M03) adds `InvasionMod.raid_behavior_state` (raids, living raiders, loot, burned, leaving). Feature `bandits` (M04) adds `InvasionMod.bandits_state`, `bandits_set_approval` and `bandits_tick_now` (optional forced `roll`). Feature `unit_balance` (M05) adds `InvasionMod.unit_balance_state`, `unit_balance_set`, `unit_balance_apply`. Scenarios that save use a write run and a read run (`--save`, `--env MODSTATE_PHASE=read`). Notes: `docs/mod/M01-mod_state/implementation-notes/tags-module.md`.

## Stand-in mods
`mod/InvasionStandIn` (outposts, captives, tribute) and `mod/RaidStandIn` (raid timeline, seasons, behavior, tiers, sack, politics) are toy models. They prove the test method for rules the base game does not have. RefugeeWaves (spec 15) is a real mod, not a stand-in. Its scenario is `refugee-wave`.
When the real mod exists, the same scenarios run against it (change the prefix). A criterion is "method verified" on the stand-in and "passing" only on the real mod. Say "a toy model" in every scenario description.

## Tests
`FakeGame(separate_states=True)` gives each mod its own Lua state, like the real game. Always use it for cross-mod tests. A test that passes only in one shared state proves nothing.

## Deploy
`harness\deploy.ps1` enables every folder in `mod/`. Never copy mod files by hand.

## Live unit tuning (spec 28)
Commands of HarnessActions (module HarnessTune): `tune_state` (per side `player`, `bandit`, `ai_lord`, `other` and per squad: living units, mean att, def, block, armorPierce, morale, baseDefence, baseBlock, charge, active overrides), `tune_set` (`side` or `squad`, `field`, `value`: writes ALL living units of the scope, keeps an override, re-applies every 2 s), `tune_reset` (optional `side`/`squad`, `field`: removes overrides and restores the value from before the first write), `tune_apply` (one re-apply pass). The side comes from the squad owner pawn, so it works for levies, bandits and AI lords without a registry. Overrides are lost on a restart.
UI: start a game with `uv run python harness/run.py --scenario noop --keep-open`, then `uv run streamlit run harness/tools/tune_ui.py -- --run <id>` (no `--run`: the newest run). The page has number inputs per side and stat, apply, reset, refresh, spawn test fight, and export to `docs/harness/28-unit-tuning/presets/`. Client code: `harness/runlib/tune.py`.

Spec 31 commands (HarnessParts and HarnessHousing): `master_artisan` (artisan job, workers, inventory, extension types of a plot; read only), `master_artisan_set` (UNSAFE: `job`, `lv`, `enable_recipe`, `extension_type`), `plot_upgrade` with `"artisan":true`, `master_parts` with `ext_limit`. Notes: `docs/harness/31-burgage-extension/implementation-notes/`.
