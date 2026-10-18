# M12 iteration 02: pak-ui notes

- A pak asset is fixed, the tree is data. So the Widget Blueprint has a pool of 16 node buttons on a `CanvasPanel` inside a `SizeBox` (760 x 240). Lua shows only the buttons that it needs.
- `CanvasPanel.add_child_to_canvas` returns a `CanvasPanelSlot` in the editor Python; `set_position` and `set_size` work. In the game, `button.Slot:SetPosition({X, Y})` from Lua works and `Slot:GetPosition()` reads back the same values (runs 20261018-075817-9c43, 20261018-083344-5edb). So layout data in the JSON moves the buttons at run time.
- `Button:SetBackgroundColor` is called inside `pcall`. Its effect on the screen was not checked (a screenshot exists in the run folders `screenshots/tech-tree-widget.png`).
- Build: editor script `make_tech_widget.py` (copy it into the UE workspace `C:\Users\garre\development\mlm-ue\ManorLords`; this was done on this PC), cook, copy `WBP_TechTreeMenu.uasset` and `.uexp` (14.9 KB, 3.3 KB) to `modtools/work/techmenu/ManorLords/Content/HarnessMod/`, `pakmod.py build techmenu` (18.8 KB). The key was set in the environment for that one command only. A grep of the diff and of the pak for the key found nothing.
- Real mouse runs need the PC free of other games. See the iteration file for the failed runs.
- The raid widget keeps its own copies of `find_class`, `make_widget` and `find_named`. A shared helper module is a clean-up for later.
