# Proposal: remove the standalone test mods

Issue: #261. Branch: `feat/remove-standalone-test-mods`.

## Why

`mod/RefugeeWaves` (legacy spec 15) and `mod/PolicyMenu` (legacy spec 16) were standalone tests of ideas. The Invasion Mod absorbed both: refugee waves are the feature `refugees`, and policies are the laws of `tech_tree`, the laws list of `tech_tree_widget` and the vassal policies of `vassals`. The user decided on 2026-10-18 that the two mods go. Keeping them costs test time and confuses agents about which code is the real mod. The change `backfill-living-specs` (#253, design D8) already gives them no living spec.

## What Changes

- **BREAKING (players):** remove `mod/RefugeeWaves` and `mod/PolicyMenu` (scripts, manifests, changelogs, the PolicyMenu pak, art and UE sources).
- Remove their test scenarios `harness/scenarios/refugee_wave.py`, `policy_menu.py` and `policy_menu_clicks.py`, the fake-game test `harness/tests/test_fakegame_refugeewaves.py` and the art tool `harness/tools/make_policy_art.py`.
- Fix the tests that used the two mods as examples (`test_release_manifest.py`, `test_suitelib_pool.py`, `test_boundary.py`, `test_runlib_scenario.py`).
- Fix comments and docstrings that point to the removed files.
- Update the skills, the wiki, `design/mod/README.md` and `CHANGELOG.md`.

## Non-goals

- No change to the shared modules (`ManorCore`, `HarnessPolicies`, `HarnessHousing`, ...). The Invasion Mod and the harness still use them.
- No change to legacy specs 15 and 16. They stay as history.
- No change to the GitHub pre-release `refugeewaves-v0.1.0`, and no change in the game folder. The user decides about both.
- No fix of the temp folders that tests leave behind (#260).

## Legacy folders

`openspec/changes/archive/2026-10-15-legacy-15-bandit-settlement/` and `openspec/changes/archive/2026-10-15-legacy-16-policy-edicts/` (read-only, not changed).

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- None. No living spec covers the two mods (`skip_specs: true`).

## Impact

- Removed: `mod/RefugeeWaves/`, `mod/PolicyMenu/`, two test scenarios, one fake-game test, one tool.
- Changed: four Python tests, `harness/release.py` and `harness/tools/genimage.py` docstrings, comments in two Invasion Mod widgets and its UE workspace, five skills, six wiki pages, `design/mod/README.md`, `CHANGELOG.md`.
- The release tool keeps working: the Invasion Mod is the only releasable mod left.
