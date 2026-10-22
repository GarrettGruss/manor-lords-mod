# Bottom bar button spike (task 1.3, issue #308)

## Result
A mod can add a button to the game's bottom bar at run time, from Lua, in the game's own style. One real click runs a Lua callback. A full-screen widget with Visibility Visible does NOT block a click to the world (a `Border`). A button or an input mode may block it. That is not tested (run cap).

## Widgets and paths
- HUD root: `MainUICPP_C` (`/Game/UI/HUD/MainUICPP.MainUICPP_C`), the only `UserWidget` in the viewport (found with `FindAllOf("UserWidget")`, `IsInViewport`).
- Path of the bar: `MainUICPP > CanvasPanel_0 > C_Gameplay > top_and_side_bars (CanvasPanel) > ... > main_tabs_HB`.
- Panel: `main_tabs_HB`, a `HorizontalBox` (desired 360x60) holding `mainTabButton_*` (class `/Game/UI/HUD/mainTabButton.mainTabButton_C`, 60x60 each): `10_Explore` (collapsed), `8_Road`, `1_Construction`, `2_Army`, `3_Map`, `7_wiki_wip`, `5_Settings`. The six visible buttons are the bar.
- Each button holds `Button > Overlay > (CommonLazyImage frame, NamedSlot > Overlay > Icon 42x42, Highlight 56x56, ToolTipAnchor)`.
- Class functions: `HandleClicked`, `HandleHovered`, `switchTab`, `flipRoadMode`, `GetToolTipText`, `PreConstruct`, `InitToolTip`.

## What worked (runs below)
- `WidgetBlueprintLibrary:Create(controller, mainTabButton_C, controller)` makes a new game button. `main_tabs_HB:AddChildToHorizontalBox(widget)` puts it last. No struct reads.
- Style match: the clone has the same frame, size and hover glow as the game buttons, because it is the same class (nothing is copied by hand). `widget:SetColorAndOpacity` tinted it red, so it can be told apart. The icon is the class default (empty); a mod needs its own icon (the texture spike has the way: `Image:SetBrushFromTexture` on the `Icon` child).
- Click: `RegisterHook` on `/Game/UI/HUD/mainTabButton.mainTabButton_C:HandleClicked` fires for our clone (filter by object name). One real mouse click gave one callback, and the game did nothing else (no panel opened). The hook runs for all buttons of the class, so it must filter by name. As in HarnessClickHooks, do the real work in the scheduler tick, not in the hook.
- Hover: `HandleHovered` hook fires for the clone. The tooltip shows the default text `mainTab_0` (`GetToolTipText`; a mod must set a text).
- `Button.OnClicked:Add(function)` was not tried in the final probe (an earlier idea; the hook route works).
- `widget:IsHovered()` on the clone returned false while the mouse was on it. Use the hook for hover, not `IsHovered`.

## Click blocking
- `add_overlay`: `Create` of a `UserWidget`, own `WidgetTree`, `Border` root (brush alpha 0.35), `SetVisibility(0)` (Visible) on the widget and the border, `AddToViewport(50)`, anchors 0..1. The view was dimmed, so the overlay was drawn.
- Control without overlay: a click on a house opened its burgage plot panel (run `20261021-035925-a56f`).
- With the overlay on, the same click opened the same panel (run `20261021-040103-7d5e`). So a Visible `Border` does not block the world. The game takes the click through the player controller, and a Border does not mark the click as handled.
- Not tested: a full-screen `Button` (it handles clicks), `SetInputMode` UI only, or the game's own `developmentPanel` technique (a fullscreen game widget in `big_panels`). Task 2.3a must test one of them. A button that covers the screen is the first thing to try.

## Runs (5 game runs of the 6 allowed, slot 0; one more run `20261021-033825-60df` listed widgets only)
| Run | Result |
|---|---|
| `20261021-033825-60df` | Widget scan: `MainUICPP_C` is the only in-viewport widget. The screenshot was covered by another window. |
| `20261021-035324-7b0a` | Tree dump cut at 500 nodes. Verdict harness_error: the save folder check saw `saveGame_53*` deleted. That slot is not from this run (another agent's fixture slot, in the shared folder). Nothing of this probe saves. |
| `20261021-035510-1ced` | Full tree dump (1842 nodes) found `main_tabs_HB`. |
| `20261021-035731-c446` | Clone added and clicked, callback 1. The block test used a wrong click spot (it hit the wiki button). |
| `20261021-035925-a56f` | Same, the control click hit a house (world click works). |
| `20261021-040103-7d5e` | Overlay then world click: not blocked. Clone and click: callback 1. |

## Risks
- A game update can rename `MainUICPP`, `main_tabs_HB` or `mainTabButton_C`. A mod must find them by name at run time and fail loudly with a log line, then fall back to the own viewport button (`ui-entry-point.md`, option d).
- The HUD widget is built when a game loads. The bar must be found after the load (the probe ran after READY). A reload of the save makes a new `MainUICPP`; add the button again on each load.
- The clone hook fires for all `mainTabButton_C` objects. The click must be matched by name.
- The `main_tabs_HB` box has a desired width of 360 for six buttons. A seventh button grows it; the bar stayed centred with 7 buttons in the picture (no overlap).
- Real mouse clicks near the window edge can scroll the camera.

## Code
`mod/shared/HarnessUiProbe/HarnessUiProbe.lua` (command `ui_probe`, registered in `HarnessActions`), test scenario `harness/scenarios/probe_bottom_bar.py` (hidden, options `--env STAGE=clone WIDGET=MainUICPP PANEL=main_tabs_HB LIMIT=5 BLOCK=1`).
