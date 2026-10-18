# Tasks

## 1. Remove

- [x] 1.1 Remove `mod/RefugeeWaves/`, `mod/PolicyMenu/`, `harness/scenarios/refugee_wave.py`, `harness/scenarios/policy_menu.py`, `harness/scenarios/policy_menu_clicks.py`, `harness/tests/test_fakegame_refugeewaves.py` and `harness/tools/make_policy_art.py`; verify with `git grep` that no code imports or loads them

## 2. Fix tests and code

- [x] 2.1 Fix `test_release_manifest.py` (a fixture mod instead of RefugeeWaves), `test_suitelib_pool.py` (another exclusive scenario), `test_boundary.py` (another sample name) and the scenario list in `test_runlib_scenario.py`; verify the four test files pass
- [x] 2.2 Fix the docstrings of `harness/release.py` and `harness/tools/genimage.py`, the comments in the `raid_widget` and `tech_tree_widget` features, `mod/InvasionMod/ue/make_raid_widget.py` and the UE project description; verify `lua_syntax.py` and the boundary test pass

## 3. Docs

- [x] 3.1 Update the skills `harness-overview`, `harness-mod-state`, `harness-pak-mod`, `harness-release` and `harness-write-scenario`; verify with `git grep` that no skill names the removed mods as current
- [x] 3.2 Update the wiki pages that name the mods and `design/mod/README.md`; verify with `wiki.py check`
- [x] 3.3 Add the removal to `CHANGELOG.md` under Removed; verify by review

## 4. Checks

- [x] 4.1 Run the full Python tests and compare with `main`: the only differences are the removed tests; verify by the counts (WSL, 2026-10-18: `main` 1874 tests and 160 failing; branch 1853 tests and 139 failing; the 21 fewer are the removed `test_fakegame_refugeewaves.py`, and no test fails only on the branch)

## Workflow follow-up

- Push, open the pull request that closes #261, and wait for the user's review.
- After the review, run `openspec archive remove-standalone-test-mods --yes` as the last commit, then merge.
