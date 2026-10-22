# Evidence (spike-new-game-difficulty-setting, issue #358)

Pictures from the game run `spike358-3` (kept open, real main menu, slot 0). Taken with `capture_game_window`, then compressed to 1280 px wide JPEG.

| File | What | How |
|---|---|---|
| `menu-setup.jpg` | Game Setup screen: Template Difficulty, Raider Frequency (Medium), Raider Free Years, bandit camps | `GoToGameSetup` on the main menu widget |
| `menu-setup-clicked.jpg` | Same screen after a real click on the right arrow: Raider Frequency is Frequent | `osinput` click |
| `menu-clone.jpg` | A cloned setting entry added from Lua: the text "label" at the top left of the list | command `game_setup_menu_probe` |
