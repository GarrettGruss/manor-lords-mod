# Hover route (task 1.1)

- Route chosen: the UMG function `SetToolTipText(FText)` on the `Border` that holds each click button. Lua only. No pak rebuild.
- Set in `tech_tree_widget/init.lua` (`set_tooltip`) on each refresh. It sets the text again only when the text changes. A hidden button gets "".
- Run `20261023-223841-d686` (scenario `tech-tree-widget-tooltip`, slot 0, `--pak techmenu`): reading `Border.ToolTipText` back through `tech_tree_widget_state` returned the expected text for all 8 node buttons and the law buttons (checks T1 to T4 passed). `SetToolTipText` raised no error.
- Not proven by that run: that the game draws the tooltip on a real hover (the child click button may take the hover), and that it draws while the game is paused. See the evidence README for the real hover attempt.
- The fallbacks (`ToolTipWidget`, an `OnHovered` text block) were not needed to set the text, so they were not tried.

# Decision (task 1.3)

Lua only. `techmenu_P.pak` and `make_tech_widget.py` do not change.
