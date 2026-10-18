# Report of agent group H2 (harness tooling)

## Numbers
Columns: requirements, scenarios with a real check, scenarios "Not checked yet".

| Capability | Req | Checked | Not checked |
|---|---|---|---|
| harness/game-actions | 10 | 23 | 1 |
| harness/mod-commands | 8 | 17 | 0 |
| harness/coverage | 5 | 13 | 0 |
| harness/stand-in-mods | 9 | 25 | 0 |
| harness/pak-mods | 11 | 29 | 0 |
| harness/mod-releases | 8 | 21 | 2 |
| harness/mesh-pipeline | 6 | 6 | 5 |
| harness/unit-tuning | 7 | 13 | 1 |

All eight files pass `openspec validate backfill-living-specs --strict` with no error or warning in these files.

## Dropped capability
- `harness/trailer-pipeline`: nothing is built. No `trailer/` folder, no `build.py`, no `review.py`. Only the plan in `docs/harness/27-trailer-animatic/README.md` exists. Dropped.

## Legacy claims dropped
- Spec 07: the catalog says 14 usable and 5 not possible actions. The code now has about 150 actions (spec 10 and later). The spec groups them by kind. The old counts are not stated.
- Spec 07: `save_state` as an action. Replaced by the guarded `save_game` (owned by `harness/save-game`, H1). Not written here.
- Spec 07: "set_season shows snow and trees". Not verified, not written.
- Spec 07: the fixed note "CheatManagerEnablerMod is needed". Engine/mod fact, not written.
- Spec 09: A/B pak numbers, spike findings and datatable proof (engine facts). Not written.
- Spec 22: the Lua skeleton and loader parts belong to `mod/core` (group MA).
- Spec 23: the proposed id blocks (100 ids per feature, 1000 to 9999). The code only enforces the `ids` range in `mod.json`, so only that rule is written. The proposal is a design choice, not code.
- Spec 10: spike results S1 to S13 (owned by H3) and the 90 percent result numbers (36 of 39). The numbers change with data, so no number is stated.
- Spec 19: the idea of a full release flow in CI. Only what `release.py` does is written.
- Spec 28: "export of presets to `docs/harness/28-unit-tuning/presets/`". The code writes there, but the folder is a legacy path. Only the client behavior is written.
- Spec 21 and 33: costs of about 30 credits are in the code (cap), but the real model quality, grey material cause and sizes are engine facts. The cause is only kept as one sentence in a requirement.

## Doubts
- Python tests use `uv run python` rules. I used `python3` once in a shell to edit spec text (no repo code was run).
- `harness/mesh-pipeline`: only `genmesh.py` has a test. `genimage.py`, the UE scripts, `meshy_material.py` and `recook_meshy_pak.py` have no test, so most scenarios say "Not checked yet".
- `HarnessPlace` (mouse-free placement) has no test and is a spike tool (version 11). Its requirement is thin on purpose. Check whether it should be in the spec at all.
- `place_building` (real mouse) is checked by a hidden scenario and `test_runlib_osinput.py`. The hidden scenario needs the real game.
- `game-actions` lists the unsafe-command rule with a check in `test_fakegame_harnessparts.py`. The same rule exists in `HarnessHousing`, `HarnessWalls` and `HarnessPolicies`; those belong to H3 specs.
- `mod-releases`: the publish step (clean tree, HEAD in `origin/main`, `gh release create --prerelease`) has no test.
- `coverage`: the default criteria path is in a legacy folder (`docs/harness/10-invasion-testability/`). If that folder moves, the requirement text must change.
- `stand-in-mods`: the stand-in scenarios `standin-outposts`, `standin-captives`, `standin-tribute`, and the `raid-*` scenarios are checked against the fake game only. Real-game verification is in legacy notes, not tested by a repo file.
- `game-actions` and `mod-commands` overlap on the command channel. The `HarnessActions` channel is in game-actions, the `modcmd` channel in mod-commands.
