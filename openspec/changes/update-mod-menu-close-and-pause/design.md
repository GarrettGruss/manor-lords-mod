# Design

## Close button

The Close button is made in Lua, not in the pak. `make_close_button` in `core/menu.lua` clones the game's bar button class (`mainTabButton_C`) and places it with `SetPositionInViewport({X=24, Y=24})`. The pak widgets (raidmenu, techmenu) do not hold it. So the move needs no pak rebuild.

The new place is the bottom middle: X is half the viewport width minus half the button width, Y is the viewport height minus the button height minus a margin. Use the viewport size and the widget desired size, or an anchor and alignment, whichever the game accepts. The button keeps the game's button format. Check the look against the Scenario Templates panel in a picture.

## Pause

Open: read the current game speed, store it in the menu state, then pause. Close: set the stored speed. One close function serves all close paths (button, shortcut, the game removing the widget), so the restore runs once. A spike must find the game call for the speed (change #418 uses one for `begin_speed`). If the game was already paused at open, the stored speed is "paused", so it stays paused.

## Settings menu

The Begin button sets `config.begin_speed` as it closes the menu. The restore must not overwrite that speed: on a Begin click the stored speed is dropped.
