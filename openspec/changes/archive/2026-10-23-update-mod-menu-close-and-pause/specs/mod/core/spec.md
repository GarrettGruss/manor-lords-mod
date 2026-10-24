## MODIFIED Requirements
<!-- Issue: #420 -->

### Requirement: Mod menus are fullscreen and block clicks to the game
Each mod menu SHALL cover the full screen, like the game's developments menu. While a mod menu is open, a mouse click SHALL NOT reach the game world or the game HUD behind the menu. A click on the menu SHALL act only on the menu, also a click on the empty background of the menu content. A mod menu SHALL have a Close button that the player can click with the mouse (a click on the backdrop does nothing). Its place and style are in the scenarios below.

#### Scenario: A click on the menu does not reach the world
- **WHEN** a mod menu is open over a burgage plot, and the player clicks a menu button at the place of the plot
- **THEN** the menu button acts
- **AND** the plot is not selected and no game panel opens
- Checked by `mod/InvasionMod/scenarios/menu/base.py` (test scenario `menu-base`) and `evidence/world-click-blocked-by-menu.jpg` with the control `world-click-control-no-menu.jpg`.

#### Scenario: A click on the menu background does not reach the world
- **WHEN** a mod menu is open over a building, and the player clicks the empty background of the menu content at the place of the building
- **THEN** no game panel opens
- Checked by `mod/InvasionMod/scenarios/menu/base.py` and `evidence/world-click-blocked-by-menu.jpg` (before the fix: `content-click-leaked-before-fix.jpg`).

#### Scenario: The Close button closes the menu
- **WHEN** a mod menu is open
- **THEN** its Close button is at the bottom middle of the screen
- **WHEN** the player clicks the Close button
- **THEN** the menu and its backdrop are gone
- **AND** the game speed is restored (see "Mod menus pause the game while open")
- Checked by `mod/InvasionMod/scenarios/menu/smoke.py` (click and un-pause), `harness/tests/test_fakegame_menu.py` (position) and picture evidence of the Close button position.

#### Scenario: A menu covers the full screen
- **WHEN** a mod menu is open
- **THEN** it covers the full screen, like the developments menu
- Checked by picture evidence (`evidence/menu-raid.jpg`, `menu-tech.jpg`, `menu-liege-tribute.jpg`). The dimmed backdrop covers the full screen including the HUD; the menu content keeps the size and place of its pak layout.

## ADDED Requirements

### Requirement: Mod menus pause the game while open
Every mod menu on the base menu (raid, tech, liege and tribute, scenario settings) SHALL pause the game when it opens. When the menu closes, the game SHALL return to the speed that was active before the menu opened. If the game was already paused, it SHALL stay paused after the close. Every way to close SHALL restore the speed. The Begin button of the settings menu keeps `config.begin_speed`.

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

### Requirement: The Esc key closes an open mod menu
While a mod menu is open, a press of the Esc key SHALL close it, like the Close button, and the pause rule applies. The game's own Esc menu SHALL NOT open on that press. With no mod menu open, Esc SHALL work as before.

#### Scenario: Esc closes the menu and restores the speed
- **WHEN** a mod menu is open and the player presses Esc
- **THEN** the menu and its backdrop are gone, and the game speed is restored
- **AND** the game's own Esc menu is not open
- Checked by `mod/InvasionMod/scenarios/menu/smoke.py` (checks E1 to E3) and `harness/tests/test_fakegame_menu.py`. How Esc reaches the game: `notes/esc-key.md`. The game's Esc menu opens on the same press and the mod closes it again within 1.5 s (it can show for a few frames).

#### Scenario: Esc with no mod menu open opens the game menu
- **WHEN** no mod menu is open and the player presses Esc
- **THEN** the game's own Esc menu opens as before
- Checked by `mod/InvasionMod/scenarios/menu/smoke.py` (checks E4 and E5).
