# M12 iteration 05: laws in the tech menu

Branch: `feat/M12-tech_tree-05-laws-menu`. Issue: #236.

## Goal
The tech tree menu (iteration 02) lists the laws of iteration 04 and lets the player enact and repeal them.

## Changes
- `make_tech_widget.py` adds a `LawsLine0` text and a row of 3 buttons (`LawButton0..2`, `LawLabel0..2`). The pak `techmenu_P.pak` is rebuilt (spec 16 method).
- `tech_tree.view()` returns `laws` (the laws of the chosen path with status enacted, available or locked) and `max_laws`.
- The widget shows the line "Laws: N of 2 in force" and one button for each law of the path. A button says "Enact X", "[in force] X (repeal)" or "X (closed)". A click calls `tech_tree.enact_law` or `repeal_law`, the same functions as the commands.
- The click handlers are named functions (`press_path`, `press_node`, `press_law`). The command `tech_tree_widget_press {kind, index}` calls them without the mouse.

## Acceptance criteria
- W1 to W6 of scenario `tech-tree-widget-laws` (needs `--pak techmenu`): the line and labels equal the tech_tree state before and after each press; presses enact, repeal and refuse as the commands do.
- Real mouse clicks on the law buttons are NOT tested here. They stay open in #203.

## Result
PASS in the real game (2026-10-18). Runs `20261018-141510-3570` and `20261018-141610-8fda`. Real clicks: open (#203).

## Fix after release: F9 key crash (#245)
The real F9 key crashed the game (key callback ran Lua on the input thread). The callback now sets a flag and the scheduler tick toggles the menu. See implementation-notes/f9-key-crash.md. Scenario `tech-tree-widget-key`: runs 20261018-154213-0a49 and 20261018-154331-093d pass.
