## 1. Spike

- [x] 1.1 Find the hover route: read `ToolTipText` and `ToolTipWidget` on a live node `Border`, set a test text, and check if it shows on a real hover, also while paused (owner needed). Verified by `notes/hover-route.md` and a run id.
- [x] 1.2 Read the base capacity of a manor module to answer the storage percentage question. Verified by `notes/storage-percent.md`.
- [x] 1.3 Decide: Lua only, or a pak rebuild of `techmenu_P.pak` (`make_tech_widget.py`). Verified by review of `design.md` (update decision 5).

## 2. Text builder

- [x] 2.1 Add `KIND_TEXT` and `effect_lines` to `tech_tree_widget/lines.lua`: all 8 kinds, percent and flat, condition, policy line. Verified by `harness/tests/test_fakegame_tech_tooltip.py`.
- [x] 2.2 Test that the shipped tree makes the expected lines for every node and law. Verified by the same test.

## 3. Widget

- [x] 3.1 Set the tooltip of each shown node and law button on each menu refresh, and clear it on hidden buttons (Lua, or pak rebuild if task 1.3 says so). Verified by `mod/InvasionMod/scenarios/tech_tree/widget_tooltip.py`.
- [x] 3.2 Add the tooltip text of each button to `tech_tree_widget_state`. Verified by the same test scenario.

## 4. Evidence and docs

- [ ] 4.1 Capture picture evidence of a tooltip on a node and on a law with `ctx.screenshot(name)` into `evidence/` (owner mouse needed), listed in `evidence/README.md`. Verified by review.
- [x] 4.2 Update `CHANGELOG.md` (Unreleased, Added), the wiki page of the tech tree menu, and the affected skill if any. Verified by `wiki.py check`.
- [ ] 4.3 Run `openspec validate add-tech-tooltip --strict` and the full test set of CONTRIBUTING.md. Verified by command.
- [ ] 4.4 Archive as the last commit: `openspec archive add-tech-tooltip --yes`. Verified by `openspec list`.
- [ ] 4.5 Fill the test results table of the implementation pull request. Verified by review.
