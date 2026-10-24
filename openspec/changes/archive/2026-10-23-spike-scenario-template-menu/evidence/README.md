# Evidence

Pictures are JPEG, at most 1280x720, taken from hold runs (a scratch test scenario that keeps the game open; not committed) with `runlib.screenshot.capture_game_window`. Fixture `base`, main menu opened with the console command `open /Game/NotStronghold/Maps/MainMenu`, then `GoToGameSetup`.

| File | What it shows | Run id |
|---|---|---|
| `m1-setup-screen.jpg` | The game's New Game "Game Setup" screen: 5 scenario templates, Template Difficulty, settings rows | `menu-h-185800` |
| `m2-rows-hidden.jpg` | Run-time Lua: AI Aggressiveness, Off Map Adversary and both bandit camp rows collapsed; a 6th template button added (Lua, slot size Fill) | `menu-h-185800` |
| `m3-row-added.jpg` | Run-time Lua: a cloned row "Hussite raid level" with own choices (value Harsh) at the bottom of the list | `menu-h-185800` |
| `m4-sixth-button.jpg` | Run-time Lua: a 6th template button (no thumbnail data) in the template bar | `menu-h-185800` |
| `m5-pak-sixth-template.jpg` | Pak route: row `hussites_are_coming` in `DT_GameSetupPresets` gives a 6th template button. Windows of other programs cover the left edge. | `menu-p-190638` |
| `m6-click-sixth-template.jpg` | After a real click on the 6th template: End Goal Domination, AI Opponents 0, Off Map Adversary Present (the values of the cloned `baron` row) | `menu-q-191928` |
