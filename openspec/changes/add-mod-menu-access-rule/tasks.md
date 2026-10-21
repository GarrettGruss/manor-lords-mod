## 1. Spike
- [x] 1.1 Find how a pak or Lua adds a clickable entry point to the game UI (HUD button or a button in an existing game menu). Write `notes/ui-entry-point.md`.
- [x] 1.2 Owner picks the entry point and answers design question 2 (2026-10-20: one button per menu, in the bottom bar after the game's buttons, in the game's format, not hideable).
- [ ] 1.3 Spike: find the bottom bar widget and its panel, add a button after the game's buttons at run time, and copy the game's button style. Write `notes/bottom-bar-spike.md`; verify with a real game run and a picture.

## 2. Build
- [ ] 2.0 Build the extensible base menu `mod/InvasionMod/Scripts/core/menu.lua` (create, open, close, fullscreen, click blocking, bottom bar button, one menu at a time, `register`); verify with fake game tests.
- [ ] 2.0b Add a Python test that only `core/menu.lua` creates mod menu widgets; verify it fails on the old menus and passes after the move.
- [ ] 2.1 Move the raid menu onto the base menu; verify with fake game tests.
- [ ] 2.2 Move the tech tree menu and the tribute menu (`liege_influence`) onto the base menu; verify with fake game tests.
- [ ] 2.3a Make each mod menu fullscreen like the developments menu, and block clicks from reaching the game behind it (no burgage plot or HUD reacts to a menu click); verify with a real game run and a picture.
- [ ] 2.3 One menu smoke test scenario for all menus, plus the base menu test scenario (fullscreen, click blocking, bottom bar). Update the "Checked by" lines. Was: Test scenarios: each root menu opens in at most 2 clicks with no key press. Update the "Checked by" lines.
- [ ] 2.4 Picture evidence of the entry point and both menus in `evidence/`.

## 3. Close
- [ ] 3.1 Update the wiki, `CHANGELOG.md` and the skill for menus if one is affected.
