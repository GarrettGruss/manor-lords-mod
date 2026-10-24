## Context

- Effects are data. `tech_tree/tree.lua` reads each node and law with a list `effects`, each `{ kind, value, min_garrison_squads? }`. `tree.EFFECT_KINDS` maps a kind to `"add"` or `"percent"`.
- Menu buttons are `WBP_ClickButton` objects of the shared module `HarnessClickHooks`, put into a pool of `Border` widgets of the pak `techmenu_P.pak`. Text is set from Lua. The pak is built by `mod/InvasionMod/ue/make_tech_widget.py`.
- The owner's mouse is not connected now. A real hover cannot be tested until it is.

## Decisions

1. One source of truth. A function `lines.effect_lines(source, tree)` in `tech_tree_widget/lines.lua` builds the tooltip text from `source.effects` (a node or a law) and `tree.policy_gates`. Names of kinds are in one table `KIND_TEXT`. This is a design choice, not a spec requirement.
2. One line for each numerical effect, in data order, joined with a newline. Then one line for each vassal policy that the node opens.
3. Mapping of the 8 existing effect kinds:

   | Kind | Type | Tooltip line (value in data) |
   |---|---|---|
   | `public_order` | add | "Public Order +10" (10) |
   | `approval` | add | "Approval -3" (-3) |
   | `buy_back_price` | percent | "Buy-back price -25%" (-0.25) |
   | `militia_attack` | percent | "Militia attack +10%" (0.10) |
   | `militia_defence` | percent | "Militia defence +10%" (0.10) |
   | `retinue_capacity` | add | "Retinue capacity +12" (12) |
   | `tribute_share` | percent | "Tribute share +25%" (0.25) |
   | `manor_storage` | add | "Manor storage capacity +200" (200) |

   - A percent value v shows as the signed whole percent of v x 100. A value that is not a whole percent shows one decimal ("+2.5%").
   - An add value shows as a signed integer.
   - `min_garrison_squads` n adds " (needs at least n garrison squads)".
   - A node with a gate in `policy_gates` adds "Opens vassal policy <policy>". This line is optional (the spec says MAY). A future non-statistic effect kind gets a sentence in `KIND_TEXT` and shows as that sentence without a number.
4. Hover route. Preferred: the UMG property `ToolTipText` of the button's `Border`, set from Lua when the menu refreshes. UMG shows it on mouse over with no event hook. Fallback: set `ToolTipWidget` to a small text widget, or use a hover event (`OnHovered` of the click button) that fills a fixed text block of the menu. The spike task decides. It first reads the property from the live widget (no mouse needed), then asks the owner to hover once.
5. Pak or Lua. If `ToolTipText` works on the existing Border from Lua, no pak rebuild is needed (Lua only). If a tooltip text block is needed in the widget, `make_tech_widget.py` changes and the pak `techmenu_P.pak` is rebuilt. The spike says which.
6. Test split. The text builder is pure Lua and has a fake-game test. The tooltip property is read by a test scenario through `tech_tree_widget_state` (the state lists the tooltip text of each shown button). The real hover needs the owner for the picture.

## Open questions

- Owner example "Storage capacity +20%": the data has `manor_storage` as a flat +200 units, not a factor. This spec shows "+200". If the owner wants a percentage, the data must change to a factor, or the builder needs the base capacity. Answered by spike task 1.2. Ask the owner at the spec review.
- Does the game show `ToolTipText` of a `Border` when the mouse is over a child `WBP_ClickButton`? Answered by spike task 1.1.
- Does the tooltip show while the menu is open and the game is paused? Answered by spike task 1.1.
