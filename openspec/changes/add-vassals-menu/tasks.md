## 1. Spec

- [x] 1.1 The owner answers the open questions in `design.md` (or accepts the defaults). Verified by review of the spec pull request.

## 2. View and commands (fake game)

- [x] 2.1 Add `features/vassals_menu/view.lua` (header, card model, status mapping, tribute text, hints) and `InvasionMod.vassals_menu_view`. Verified by `harness/tests/test_fakegame_vassals_menu.py`.
- [x] 2.2 Add the click handlers for policy and restore that call the existing commands, with refusal text. Verified by `harness/tests/test_fakegame_vassals_menu.py`.
- [x] 2.3 Register the menu `vassals` in the bottom bar (`core/menu.lua`). Verified by `harness/tests/test_fakegame_vassals_menu.py`.

## 3. Widget

- [x] 3.1 Write `mod/InvasionMod/ue/make_vassals_widget.py` from the mockup, build it in a private UE workspace and a private pak work_dir, and add it to the pak. Verified by a build run and the real game test scenario.

## 4. Real game

- [x] 4.1 Write `mod/InvasionMod/scenarios/vassals_menu/window.py`: open from the bar, read the view, set a policy, restore a wiped village, close. Verified by a real game run on slot 1 or 2 (pass the slot number, never `--slot auto`).
- [x] 4.2 Take pictures with `ctx.screenshot` for each status and the header into `evidence/` with `README.md` (run ids). Verified by review of the pull request.

## 5. Close

- [x] 5.1 Update `CHANGELOG.md` (Added), the wiki and the skills that the change affects (menu list). Verified by `wiki.py check`.
- [x] 5.2 Run the full test set and `openspec validate add-vassals-menu --strict`.
- [ ] 5.3 Archive as the last commit: `openspec archive add-vassals-menu --yes`.
- [ ] 5.4 Fill the test results table of the implementation pull request.
