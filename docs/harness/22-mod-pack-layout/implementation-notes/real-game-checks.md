# Real-game checks (2026-10-16)

Both open checks passed. No code fix was needed.

## Check 1: require of the loader (plan step 3)
- Run `20261016-062223-2e6c` (scenario `noop`, verdict pass). InvasionMod was deployed with `deploy.ps1`.
- `mod.log` lines:
  - `[InvasionMod] InvasionMod example feature loaded`
  - `[InvasionMod] feature loaded: example`
  - `[InvasionMod] ready, features: example`
- So `require("feature_loader")`, `config`, `feature_list` and `features.example.init` all load from the Scripts folder.
- The second run (below) also logged `ready, features: example, second`.

## Check 2: buildmod and the pak in the game (A3, A4)
Test branch: `test/22-23-integration` (spec 22 merged with spec 23). A second feature `second` was added (ids `buildingStats` 1100 to 1199, `DT_Upgrades` 127 to 136). The `example` feature already patched row 1000 and upgrade 117.
- `pakmod.py buildmod InvasionMod` built one pak of 4 files (101910 bytes). The pak list matched the folder.
- Run `s22-check2` (throwaway scenario, `--pak InvasionMod`, verdict pass, no crash). Values read through `building_stat` and `upgrade_stat`:
  - building 1000: exists, `bVisibleInUi` true (set by the patch).
  - building 1100: exists, `bVisibleInUi` true.
  - upgrade 117: `upgradesInto` 1000. Upgrade 127: `upgradesInto` 1100.
  - The cloned rows keep the fields of their source (name `hitching_post`, from row 30).
- Planted conflict (both features set `bVisibleInUi` of `buildingStats/30`): exit 1, message `conflict: field bVisibleInUi of buildingStats/30 is set by data/example/patches/09-conflict.json and by data/second/patches/09-conflict.json`.
- Planted bad id (row 1200 in feature `second`): exit 1, message `data/second/patches/09-range.json: new row 1200 is outside the range [1100, 1199] of feature second for buildingStats`.
- Both failures happen before any tool starts. The planted files were removed.

## Lessons
- `buildmod` needs `MANORLORDS_AES_KEY` in the environment. Set it from `modtools/work/aes_key.txt` inside the command.
- `deploy.ps1` needs `powershell -ExecutionPolicy Bypass -File`.
- The `manor-harness` MCP tool deploys from the main checkout. To test branch code, run `run.py` from the worktree.
- `run.py` removes the installed pak at the end. InvasionMod stays in `mods.txt` until it is removed by hand.
