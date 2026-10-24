# Task 1.1: AI opponents in the game setup

`numGenericAILords` is a field of `gameSetup.currentGameSetup`. `mod/shared/HarnessGameSetup` reads it (snapshot field `ai_lords`).
The real game confirmed it: a new game from the 6th template "The Hussites Are Coming" gives `ai_lords` 0 (run 20261024-052548-ea01,
`vassals` 0 in the mod state). The guard reads `ai_lords` through `HarnessGameSetup.game_setup_state()`.

Real runs:

| Run | Case | Result |
|---|---|---|
| 20261024-052227-2274 | fixture `base` (old save, live check, AI lord pawns exist) | `vassals` 1, no warning |
| 20261024-052336-702e | fixture `playtest-noai` (old save, no AI lord pawn) | `vassals` 0, warning |
| 20261024-052548-ea01 | new game from the 6th template (game setup) | `vassals` 0, warning in the start menu |

Not run: a real save and load. `save_game` has not run in the real game yet (CLAUDE.md, Safety). The value is a ModState entry
like the other mod settings, and the fake-game test checks that a load keeps it. The warning line shows in the start menu, which opens in a new game only.
The first line of the warning was shortened to one line, because a second line pushed "Raid size" out of the menu box.
