## MODIFIED Requirements
<!-- Issue: #505 -->

### Requirement: Mod menus pause the game while open
Every mod menu on the base menu (raid, tech, liege, scenario settings) SHALL pause the game when it opens. When the menu closes, the game SHALL return to the speed that was active before the menu opened. If the game was already paused, it SHALL stay paused after the close. Every way to close SHALL restore the speed. The Begin button of the settings menu keeps `config.begin_speed`.

#### Scenario: Opening a menu pauses the game
- **WHEN** the game runs at a normal speed and a mod menu opens
- **THEN** the game is paused
- Checked by `mod/InvasionMod/scenarios/menu/base.py` (B3), `mod/InvasionMod/scenarios/menu/smoke.py` (S6) and `harness/tests/test_fakegame_menu.py`.

#### Scenario: Closing a menu restores the speed
- **WHEN** a mod menu was opened at a speed above pause, and it closes by the Close button, by the shortcut, or because the game removed the widget
- **THEN** the game runs again at the speed it had before the menu opened
- Checked by `mod/InvasionMod/scenarios/menu/base.py` (B4), `mod/InvasionMod/scenarios/menu/smoke.py` (S6, the Close click) and `harness/tests/test_fakegame_menu.py` (one case for each way to close: Close button, shortcut, widget removed, Esc).

#### Scenario: A menu opened while paused stays paused
- **WHEN** the player paused the game, then opens a mod menu and closes it
- **THEN** the game is still paused after the close
- Checked by `harness/tests/test_fakegame_menu.py` and `mod/InvasionMod/scenarios/menu/smoke.py` (S7). Decided by the owner (2026-10-23).

#### Scenario: The Close button is at the bottom middle
- **WHEN** a picture of an open mod menu is taken
- **THEN** the Close button is at the bottom middle of the screen, in the game's Close label style
- Checked by picture evidence (`evidence/menu-*.jpg`), reviewed by the owner, and by `harness/tests/test_fakegame_menu.py` (anchor 0.5, 0.95).
