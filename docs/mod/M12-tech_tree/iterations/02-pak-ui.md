# M12 iteration 02: pak-ui

Branch: `feat/M12-tech_tree-02-pak-ui`. Issue: #203. Stacked on PR #198 (iterations 01 and 03).

## Goal
A pak menu for the tech tree (key F9). It shows the path, the free node slots and the effects. The player picks a path and unlocks nodes with the mouse. The tree is data driven: the menu is built from `data/tech_tree/tree.json`, including the layout data.

## Design
- A pak asset is fixed, but the tree is data. So the Widget Blueprint `/Game/HarnessMod/WBP_TechTreeMenu` (made by `mod/InvasionMod/ue/make_tech_widget.py`, same method as the raid widget) holds a POOL of 16 node buttons (`NodeButton0..15`, labels `NodeLabel0..15`) on a `CanvasPanel` (`TreeCanvas`), two path buttons (`PathButton0..1`) and three text lines (`TechLine0..2`).
- Lua (`features/tech_tree_widget`) shows one button for each node of the tree, sets its label and colour (unlocked green, available white, locked grey, other path dark red) and moves it with `Slot:SetPosition` to `layout x/y` times `step_x/step_y` (config, 180 and 60 pixels).
- A tree with more than 16 nodes fails loudly when the menu opens.
- Clicks use the rule of PolicyMenu and the raid widget (a press that ends while hovered). A click calls `tech_tree.choose_path` or `tech_tree.unlock`. Refusals are logged and shown in `last_error`.
- `tech_tree.view()` (new export) gives the menu everything it shows, so the menu has no tree rules of its own.
- Commands `tech_tree_widget_open`, `tech_tree_widget_close`, `tech_tree_widget_state`. Config `tech_tree_widget`. Key F9 (F7 policy menu, F8 raid menu).
- Pak `techmenu_P.pak` in `mod/InvasionMod/paks/`. Build: editor script, cook, copy `WBP_TechTreeMenu.uasset/.uexp` to `modtools/work/techmenu/ManorLords/Content/HarnessMod/`, `pakmod.py build techmenu`. The AES key was loaded from the key file into `MANORLORDS_AES_KEY` for that one command only.

## Acceptance criteria
- U1: the widget opens and is in the viewport.
- U2: the three shown lines equal the wanted lines of the tech tree state.
- U3: the number of visible node buttons equals the number of nodes in the data.
- U4: every visible node button stands at `layout x * 180`, `layout y * 60`.
- U5: a real mouse click on a path button chooses that path.
- U6: a real mouse click on the first node of the path unlocks it; its label shows the mark `[x]`.

## Scenarios
- Fake game: `harness/tests/test_fakegame_tech_tree.py` (text rules, wanted lines, message without the pak).
- Real game: `tech-tree-widget --pak techmenu` (EXCLUSIVE: real mouse; no other game window).

## Result
not started
