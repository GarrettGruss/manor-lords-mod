# Hover tooltip of the item boxes (design, "Tooltips")

Each objective and reward item is a Border. The mod sets `SetToolTipText` on it with the name and the description. In the real game (run 20261028-030940-20a7 and later; picture `evidence/window-tooltip.jpg`) no hover tooltip is drawn over the window, although the property is set (`liege_menu_state.tooltips`).

Fallback of the design: the mod reads `IsHovered` of the visible item Borders every refresh (500 ms) and shows the text of the hovered item in the footer line (`FooterText`) of the window. The scenario `liege-contracts-window` checks it (assert W8b: the footer holds "Wood" while the mouse is over the wood item).

Other finding: `SetVisibility(Collapsed)` on a Border in the first refresh after the open did not hold for the card Borders and the active panel (`GetVisibility` read 4 afterwards), while the item Borders collapsed. The window writes the visibility once more 1.5 s after the open. Scenario assert W3b reads `GetVisibility` of the first card in the empty state.
