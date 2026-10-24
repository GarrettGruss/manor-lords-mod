# Tasks

- [x] 1. Spike: find the game call that reads and sets the game speed and the paused state (see #418). Write `notes/game-speed.md`.
- [x] 2. Move the Close button to the bottom middle in `core/menu.lua` (Lua only, no pak rebuild).
- [x] 2b. Spike: find how Esc reaches the game (UE4SS RegisterKeyBind or the game input) and how to stop the game Esc menu from opening on the press that closes a mod menu. Write `notes/esc-key.md`. Then close the open mod menu on Esc in `core/menu.lua`, with tests in `test_fakegame_menu.py` and `menu/base.py`.
- [x] 3. Pause on open and restore on close in `core/menu.lua`, for all close paths. Keep the Begin speed of the settings menu.
- [x] 4. Fake-game tests in `harness/tests/test_fakegame_menu.py` (open pauses, close restores, open while paused stays paused, all close paths).
- [x] 5. Update test scenarios `mod/InvasionMod/scenarios/menu/base.py` and `smoke.py` (position, pause, restore).
- [x] 6. Picture evidence of the Close button in `evidence/`, with `README.md`.
- [x] 7. Update `CHANGELOG.md` and the wiki pages for the menu, then run `wiki.py check`.
- [x] 8. Run the tests and `openspec validate update-mod-menu-close-and-pause --strict`, then archive as the last commit.
