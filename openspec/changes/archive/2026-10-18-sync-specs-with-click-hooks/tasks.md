# Tasks

## 1. Specs

- [x] 1.1 Write MODIFIED deltas for `mod/core`, `mod/tech_tree_widget` and `mod/raid_widget` from the code on `main` (`scheduler.lua` TICK_MS 100, `HarnessClickHooks.drain` in both widgets, no cooldown); verify with `openspec validate sync-specs-with-click-hooks --strict`
- [x] 1.2 Check that every "Checked by" path exists; verify with `git ls-files`

## 2. Docs

- [x] 2.1 Add the change to `CHANGELOG.md`; verify by review

## 3. Archive

- [x] 3.1 Nothing to build: archive in the single pull request before review; verify with `openspec list` and `openspec validate --all --strict`
