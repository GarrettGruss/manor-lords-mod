# Proposal: update-mod-menu-close-and-pause

Issue: #420.

## Why

The owner asked for two changes to the mod menus (2026-10-23):

1. The Close button is at the top left. It SHALL be at the bottom middle of the screen, in the game's Close label style. The style reference is the Close label of the game's Diplomacy screen (`reference/diplomacy-close.jpg`): a plain white serif text "Close" with a small fleur-de-lis on each side, no frame or box, centered at the very bottom (about 95% of the screen height) over a dark band. The game shows "Game Paused" on that screen.
2. A fullscreen mod menu SHALL pause the game while it is open.

## What changes

- The Close button of every mod menu moves to the bottom middle of the screen. It stays a clone of the game's bar button (made in Lua, see `design.md`).
- The base menu (`core/menu.lua`) pauses the game when a menu opens and restores the game speed when it closes. This holds for every menu on the base menu: raid, tech, liege and tribute, scenario settings.
- Close by the Close button, by the F8 or F9 shortcut, or by the game removing the widget all restore the speed.

## Decided by the owner (2026-10-23)

If the game was already paused when a mod menu opened, it stays paused after the menu closes. The restore puts back the speed that was active before the open.

## Overlap with other changes

- `fix-settings-menu-pause` (#418, PR #419) keeps the scenario settings menu paused through the intro cinematic. This change sets the general rule for all menus. The two do not conflict: the settings menu Begin button keeps its own begin speed (`config.begin_speed`), and that speed replaces the saved speed on a Begin click. Whichever change merges second adapts its tasks to the first.

## Impact

- Spec: `mod/core` (modified requirement "Mod menus are fullscreen and block clicks to the game", new requirement "Mod menus pause the game while open").
- Code: `mod/InvasionMod/Scripts/core/menu.lua`, tests `harness/tests/test_fakegame_menu.py`, test scenarios `mod/InvasionMod/scenarios/menu/base.py` and `smoke.py`.
- Picture evidence of the Close button position.
