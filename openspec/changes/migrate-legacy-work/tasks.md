# Tasks

## 1. Inventory and conversion

- [x] 1.1 Convert the open mod work (group LM) and write `notes/inventory-mod.md`; verify each change with `openspec validate --strict`
- [x] 1.2 Convert the open harness work, specs 00 to 13, 19, 21 to 24, 27, 33 (group LH1), and write `notes/inventory-harness-1.md`; verify with `openspec validate --strict`
- [x] 1.3 Convert the open harness work, specs 14 to 18, 25, 26, 28 to 32, 34 and #104 (group LH2), and write `notes/inventory-harness-2.md`; verify with `openspec validate --strict`
- [x] 1.4 Resolve overlaps (`add-mod-state-region-tags` takes its limit numbers from `spike-mod-state-limits`) and give the loose mod items a change (`decide-open-mod-rules`); verify by review

## 2. Issues

- [x] 2.1 Retitle the ten open legacy issues to `Change: <name>` with a comment, make 17 new issues, close the done issues #203, #237, #126; verify with `gh issue list`
- [x] 2.2 Write each issue number into its change (`x-issue`, proposal, delta spec comments); verify that no `TBD` is left and `openspec validate --all --strict` passes

## 3. Rules and docs

- [x] 3.1 Write the MODIFIED delta of `process/spec-workflow`; update CONTRIBUTING.md, the git workflow skill, the legacy banners and the wiki; verify with `wiki.py check`
- [x] 3.2 Add the change to `CHANGELOG.md`; verify by review

## 4. Archive

- [x] 4.1 Archive only this change (the 27 converted changes stay open); verify with `openspec list`
