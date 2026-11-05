## 1. Rules and state

- [ ] 1.1 Add `law_extra_slots`, `laws_unlocked`, `laws_sources` to mod state. Slots = `max_active_laws` + extra. Verified by `harness/tests/test_fakegame_laws_menu.py`.
- [ ] 1.2 Add `laws_unlock(id, source)`, `laws_add_slot()` and the commands `InvasionMod.laws_unlock`, `laws_add_slot`. Verified by the same test (unknown id, repeat call, new slot total).
- [ ] 1.3 Let the tech tree enact rule accept a contract-unlocked law and the extra slots. Verified by `harness/tests/test_fakegame_laws.py` (updated) and the new test.

## 2. Feature `laws_menu`

- [ ] 2.1 Write `laws_view(state)` (header, nine cards, filter, effect signs, disabled text). Verified by a fake game test.
- [ ] 2.2 Register the menu `laws`, the press and state commands. Verified by a fake game test.
- [ ] 2.3 Remove the law buttons and the laws strip from the tech window, add the line "Laws: open the Laws menu" (after the owner answers Q1). Verified by `harness/tests/test_fakegame_laws.py` (updated).

## 3. Widget

- [ ] 3.1 Write `mod/InvasionMod/ue/make_laws_widget.py` from `mockups/laws-menu.html` (font Mikadan, dark grey panel, nine pooled cards, filter row). Verified by a build in a private UE workspace and pak work_dir, and by the real game run in 4.1.
- [ ] 3.2 Build the pak and deploy with `harness\deploy.ps1`. Verified by the real game run.

## 4. Real game checks

- [ ] 4.1 Write test scenarios `mod/InvasionMod/scenarios/laws_menu/` (`open_close`, `enact_revoke`, `roundtrip` with the guarded `save_game`, `layout`). Run each with `--slot 1` or `--slot 2` (never `--slot auto`). Verified by `runs/<id>/summary.json`.
- [ ] 4.2 Capture picture evidence with `ctx.screenshot(name)` into `evidence/` (no law, two laws, filter Locked, full slots). List each in `evidence/README.md` with its run id. At most 1280x720.

## 5. Docs and close

- [ ] 5.1 Update `CHANGELOG.md` (Unreleased), the wiki pages for the menus and the tech tree, and the skills that the change affects. Verified by `wiki.py check`.
- [ ] 5.2 Run the full test set and `openspec validate add-laws-menu --strict`.
- [ ] 5.3 Archive as the last commit: `openspec archive add-laws-menu --yes`.
- [ ] 5.4 Fill the test results table of the implementation pull request.
