# Game speed: read, pause, restore (task 1)

- Read: `RTSMultiEngineCPP.gameSpeed` is the speed factor: 0 paused, 1, 4 or 8 (spec 04, `read_game_speed`). The settings menu run 20261022-045052-489b already showed that a paused game reads 0.
- Pause: `PawnCPP:pauseGame()`. Un-pause and set: `PawnCPP:unPauseGame()`, then `changeGameSpeed(index, false)`. The index is 1, 2 or 3 for the factors 1, 4 and 8 (`timectl.set_speed`). `unPauseGame` must come first, or the game falls back to 1x after about 3 s.
- Restore rule in `core/menu.lua`: the factor read before the pause is stored. On close, a stored 0 (paused before) changes nothing, so the game stays paused. Another factor: `unPauseGame`, then `changeGameSpeed(index)`.
- The settings menu keeps its own speed (`manages_speed = true`): its Begin button sets `config.begin_speed`, and it has the clock guard of #418.
- Real runs: menu-smoke 20261024-001206-171c (speed 4 before, 0 while open, 4 after the Close click for the raid, tech and tribute menus; paused before the open: still 0 after the close).
