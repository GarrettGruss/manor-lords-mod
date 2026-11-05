## 1. Rules and state

- [x] 1.1 Add `law_extra_slots`, `laws_unlocked`, `laws_sources` to mod state. Slots = min(5, `max_active_laws` (1) + extra). Verified by `harness/tests/test_fakegame_laws_menu.py`.
- [x] 1.2 Add `laws_unlock(id, source)`, `laws_add_slot()` (cap 5) and the commands `InvasionMod.laws_unlock`, `laws_add_slot`. Verified by the same test.
- [x] 1.3 Let the tech tree enact rule accept a contract-unlocked law (no node, no path) and the extra slots. Verified by `harness/tests/test_fakegame_laws.py` (updated) and the new test.
- [x] 1.4 Yearly actions: 1 enact and 1 revoke, refreshed in spring, saved in mod state. Verified by `harness/tests/test_fakegame_laws_menu.py`.

## 2. Feature `laws_menu`

- [x] 2.1 Write `view.build` (header, nine cards, filter, tones, hints, dialog). Verified by a fake game test.
- [x] 2.2 Register the menu `laws`, the confirmation dialog, the press and state commands, and the base menu option `on_esc`. Verified by fake game tests.
- [x] 2.3 Remove the law buttons and the laws strip from the tech window, add the line "Laws: open the Laws menu". Verified by `harness/tests/test_fakegame_laws.py` (updated) and `scenarios/tech_tree/widget_laws.py`.

## 3. Widget

- [x] 3.1 Write `mod/InvasionMod/ue/make_laws_widget.py` from `mockups/laws-menu.html` (font Mikadan, dark grey panel, nine pooled cards, filter row, dialog). Verified by a build in a private UE workspace and pak work_dir, and by the real game runs in 4.1.
- [x] 3.2 Build the pak. Verified by the real game runs.

## 4. Real game checks

- [x] 4.1 Write test scenarios `mod/InvasionMod/scenarios/laws_menu/` (`open_close`, `enact_revoke`, `roundtrip` with the guarded `save_game`, `layout`). Run each with `--slot 2`. Verified by `runs/<id>/summary.json` (ids in the pull request).
- [x] 4.2 Capture picture evidence into `evidence/` (no law, two laws, filter Locked, full slots, the dialogs). Listed in `evidence/README.md` with the run ids. At most 1280x720.

## 5. Docs and close

- [x] 5.1 Update `CHANGELOG.md` (Unreleased), the wiki page `invasion-features.md`. Verified by `wiki.py check`.
- [x] 5.2 Run the full test set and `openspec validate add-laws-menu --strict`.
- [ ] 5.3 Archive as the last commit: `openspec archive add-laws-menu --yes`.
- [x] 5.4 Fill the test results table of the implementation pull request.
