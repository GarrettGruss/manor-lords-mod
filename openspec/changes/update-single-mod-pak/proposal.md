## Why

Issue: #471. The Invasion Mod has three paks in `mod/InvasionMod/paks/`: `raidmenu_P.pak` (menu widgets), `techmenu_P.pak` (tech tree widget) and `InvasionMod_P.pak` (data table rows, built by `pakmod.py buildmod InvasionMod`, with the 6th scenario template). `mod.json` names only `raidmenu`, so a player release lacks the template and the tech menu. The owner chose one pak (option B, 2026-10-24).

## What Changes

- One pak, `InvasionMod_P.pak`, holds all cooked widgets and all data rows. The widget assets move into the feature folders `mod/InvasionMod/data/<feature>/assets/` (the build already copies them into the pak).
- `mod.json` names `{"name": "InvasionMod", "source": "file"}`. The release zip holds only `InvasionMod_P.pak` under `~mods`.
- Harness runs load it with `--pak InvasionMod`. The test scenarios that named `raidmenu` or `techmenu` use it.
- `raidmenu_P.pak` and `techmenu_P.pak` are removed from the repo. The shared widget `WBP_ClickButton` is one asset in the pak (both old paks held the same file).
- Skills, wiki, scripts and comments that name the old paks are updated.

## Impact

- Specs: `harness/mod-releases` (ADDED), `harness/pak-mods` (ADDED), `mod/raid_widget` and `mod/tech_tree_widget` (MODIFIED: the pak name).
- Code: `mod/InvasionMod/mod.json`, feature assets, scenarios, Lua messages and comments, skills and wiki.
- The widget assets are binary files in `data/`. They are not shipped as files: only the pak is.
