## 1. Prepare

- [ ] 1.1 Confirm that `update-tech-tree-yearly-picks` (#499) is merged or rebase on it. Read its tree state: picks earned and free, common techs, common laws.
- [ ] 1.2 Copy `mockups/tech-tree-layout.html` of this change to `openspec/specs/mod/tech_tree_widget/mockups/tech-tree-layout.html` (the archive does not copy extra files). Commit it before the archive.

## 2. Pure code and tests

- [ ] 2.1 `lines.lua`: picks counter text, row and column of a node, status text, footer message, laws strip places. Tests in `harness/tests/test_fakegame_tech_tree.py` and `test_fakegame_laws.py` (counter, common tech without a path, no free pick, third law refused).
- [ ] 2.2 Config `tech_tree_widget`: card size, row label positions, strip position. Remove the three header lines.

## 3. Pak and widget

- [ ] 3.1 `mod/InvasionMod/ue/make_tech_widget.py`: new pools (11 node cards, 8 links, 9 card law buttons, 2 strip places, header, column heads, row labels, footer). Rebuild the pak. Grep the diff for the AES key before the commit.
- [ ] 3.2 `init.lua`: place and fill all controls. Use `IsValid` on each child from `GetChildAt`. Add no run-time Button hook (#308).
- [ ] 3.3 Update `tech_tree_widget_state` and `tech_tree_widget_press` for the strip repeal and the common techs.

## 4. Test scenarios and evidence

- [ ] 4.1 Update `mod/InvasionMod/scenarios/tech_tree/widget.py` (11 buttons) and `widget_laws.py` (strip, common laws).
- [ ] 4.2 Add `widget_picks.py` (common tech with no path, no free pick, footer message) and `widget_layout.py` (screenshots: no path; path with two techs; two laws in force).
- [ ] 4.3 Run the test scenarios in the real game. Take screenshots with `ctx.screenshot`, at most 1280x720, about 1 MB in total. Put them in `evidence/` with `evidence/README.md` (scenario and run id for each). The owner compares them with the mockup.

## 5. Close

- [ ] 5.1 Update the wiki page and the skills for the tech tree widget. CHANGELOG under Unreleased. Run the full test set and `openspec validate update-tech-tree-widget-layout --strict`.
- [ ] 5.2 Archive as the last commit: `openspec archive update-tech-tree-widget-layout --yes`.
