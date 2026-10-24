# Findings

- Both old widget paks held the same `WBP_ClickButton` (equal SHA-256). It is one asset now, owned by feature `invasion`.
- The release tool could not build the Invasion Mod zip. Three fixes were needed (found by the dry run):
  1. `releaselib/files.py`: a `require` of a Lua file of the mod itself (`config`, `scheduler`, `feature_list`, `feature_loader`) counted as an undeclared shared module. Local files are now excluded.
  2. `mod/shared/HarnessRaids`: a trace helper did a hard `require("HarnessLog")`. It is `pcall(require, ...)` now.
  3. `mod.json` listed `HarnessAutosave`, which is harness-only. It is removed from `shared`. The harness still deploys all of `mod/shared`.
- Owner question: without `HarnessAutosave` a player release does not push the autosave timer away while the new game menu is open (`scenario_settings` uses `pcall(require, "HarnessAutosave")` and logs a warning). Default chosen: ship without it. A player-safe autosave helper would be a new change.
- `mod/InvasionMod/CHANGELOG.md` has no `0.1.0` section yet, so the dry run needs one. The dry run used a temporary heading and the file was restored. A real release needs the version section.
- Run 20261024-035307-31aa of `tech-tree-widget` failed once on `set_settlement_level read-back 2 -> 2` (not about the pak); a rerun passed (20261024-040849-6a65).
