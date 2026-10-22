# 1.1 New game detection, pause and un-pause

Method: the harness new game (`run.py --scenario scenario-settings-new-game-menu --new-game --pak raidmenu --slot 1`). HarnessBoot opens the
map with the console command `open <map>` while `savefileToLoad` is empty. The game's own new game and Game Setup screens are NOT opened, so the real
`menu.sav` is not touched (the run has a private `LOCALAPPDATA`; the real save folder was compared with the backup at the end, see the report).
Runs (slot 1): `20261022-044520-b8cd`, `20261022-044915-02fb`, `20261022-045052-489b` (found the speed finding below), `20261022-045227-57f0` (pass).

## What the mod sees in a new game

| Read | New game (run 57f0) | Loaded fixture (run ff47) |
|---|---|---|
| `MLGameInstance.savefileToLoad` (FString, `:ToString()`) | `""` | `"saveGame_51"` |
| game day (`TemporalComponent.daysTotal`) | 0 | 205 |
| mod state at pawn ready | empty ("stored version nil, 0 unknown entries") | the saved tags |
| `pawn.currentUIMode` | not 0 while the intro plays, 0 after it | not tested |

- `savefileToLoad` is reliable in both cases here: empty on a new game, the slot name after a harness load (the open question of the design is closed for the harness path).
  A load from the game's own "Continue" button was not tested (the harness loads through the load screen). The rule `kind_of_game` adds the game day as a guard
  (a game with an empty file name and a day over `new_game_max_day`, 10, is an old save), in case the file name is lost after a load (the load bug of 2026-10-11).
- The mod state is loaded (`state.loaded`) at about the same time as the first daily step of the invasion feature. The first run showed that the invasion feature
  then showed the banner "Pick the difficulty" and started the great raid clock on day 0 before the menu. The decision is therefore made inside a hold gate that the
  invasion feature asks before each daily step (`invasion.set_hold_gate`): a new game is held until "Begin the game" (fake game test `test_a_new_game_holds_the_daily_step_until_begin`).
- The menu opens when the pawn exists and the intro is over (`currentUIMode == 0`), or after `intro_wait_s` (60 s).

## Pause and un-pause

- `pawn:pauseGame()` pauses the clock (clock change 0.0 over 3 s while the menu is open; the game shows "Game Paused"). `gameSpeed` is 0 while the menu is open.
- `pawn:unPauseGame()` alone does NOT make a new game run: after it `bIsPlayerPaused` is false, but `gameSpeed` stays 0 and the clock stands still
  (also after the harness `unPauseGame` twice; runs 02fb and 489b). `pawn:changeGameSpeed(1, false)` after it makes the clock run (gameSpeed 1, clock +3.1 s in 3 s).
  The mod therefore calls `unPauseGame` and then `changeGameSpeed(config.begin_speed, false)` on "Begin the game" (run 57f0: gameSpeed 1, clock moves, no harness call).
- Not verified: whether a new game started by the player (without the HarnessBoot pause) also starts at speed 0. In the harness run, HarnessBoot calls `pauseGame` once after the intro
  (at game clock 5.0) before the menu opens, so the mod pause cannot be told from the boot pause. The owner may check this once with a real new game on slot 0.

## Other facts

- The base menu opens a menu with `bar = false` (a new optional field in `core/menu.lua`) without a bottom bar button, so the player cannot reopen the settings menu.
- The Close button of the base menu (top left) closes the menu like "Begin the game": the current choices apply (the game must not stay paused).
- 14 click buttons (`WBP_ClickButton`) in one menu work: all clicks of the test scenario came through the same code as a hook click (`scenario_settings_click`).
  A real mouse click on the buttons was NOT tested in this change (the test scenario uses the named command; the hook path is the one of the raid menu, spec 34).
- Autosave: HarnessBoot already pushes the timer one year away before READY. The mod sends `disable_autosave` again (shared module `HarnessAutosave`) after the intro and after
  Begin. The read back (`autosave_status`, run 57f0): remaining 31535410 s after Begin. Whether the first call after a player's new game is undone (spike #358) cannot be seen
  in a harness run, because the boot step runs first.
- Look: `menu-defaults.png` and `menu-changed.png` in the run folders `runs/20261022-045227-57f0/screenshots/` (slot 1: other windows may cover parts). The PNG images of the mockup
  are not in the pak (see `art.md`).
