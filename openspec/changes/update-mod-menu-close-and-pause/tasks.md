# Tasks

- [ ] 1. Spike: find the game call that reads and sets the game speed and the paused state (see #418). Write `notes/game-speed.md`.
- [ ] 2. Move the Close button to the bottom middle in `core/menu.lua` (Lua only, no pak rebuild).
- [ ] 3. Pause on open and restore on close in `core/menu.lua`, for all close paths. Keep the Begin speed of the settings menu.
- [ ] 4. Fake-game tests in `harness/tests/test_fakegame_menu.py` (open pauses, close restores, open while paused stays paused, all close paths).
- [ ] 5. Update test scenarios `mod/InvasionMod/scenarios/menu/base.py` and `smoke.py` (position, pause, restore).
- [ ] 6. Picture evidence of the Close button in `evidence/`, with `README.md`.
- [ ] 7. Update `CHANGELOG.md` and the wiki pages for the menu, then run `wiki.py check`.
- [ ] 8. Run the tests and `openspec validate update-mod-menu-close-and-pause --strict`, then archive as the last commit.
