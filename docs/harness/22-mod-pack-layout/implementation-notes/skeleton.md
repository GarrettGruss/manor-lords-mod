# Skeleton notes (plan steps 3, 4, 7, 6)

## Step 3: mod/InvasionMod
- Files: `mod.json`, `CHANGELOG.md`, `Scripts/main.lua`, `Scripts/config.lua`, `Scripts/feature_list.lua`, `Scripts/feature_loader.lua`, `Scripts/features/example/init.lua`.
- `feature_loader.lua` is pure Lua (no game API). `order` sorts the enabled features by `requires`. `load` requires each one.
- Fails loudly on: duplicate feature, config entry for an unknown feature, a requirement that is not in the list, a requirement that is disabled, a cycle (the message shows the path), a feature that errors on load.
- A feature without a config entry is disabled.
- `feature_list.lua` repeats the `features` of `mod.json` (name and requires), because Lua cannot read JSON in the game. A test compares the two lists.
- Path handling: `main.lua` requires `feature_loader`, `config` and `feature_list` from `Scripts/`. Features load as `features.<name>.init` (explicit `.init`, because UE4SS may not search `?/init.lua`).
- Not checked yet: in the real game, `require("features.example.init")` must resolve under `Scripts/`. Check this when the skeleton runs (acceptance A2). If it fails, move the loader to `dofile` with a path built from the mod folder.
- Tests: `harness/tests/test_fakegame_featureloader.py`.

## Step 4: scenario discovery
- `load_scenario_modules` also loads `mod/<Name>/scenarios/**/*.py`. A name that is already registered now fails loudly (before, a repeat was skipped).

## Step 7: boundary test
- `harness/tests/test_boundary.py` fails when a file under `harness/` names the mod (`InvasionMod`). Generic discovery by path and `mod.json` is allowed.

## Step 6: release
- Manifest: optional `display_name` (string) and `features` (list of `{name, requires, ids}`).
- The gate covers `gate_scenarios` (empty list is allowed when `features` is set).
- The zip leaves out `data/` and `scenarios/` of a mod.
