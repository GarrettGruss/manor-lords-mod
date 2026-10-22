# Base menu findings (tasks 2.0 to 2.4, issue #308)

Built `mod/InvasionMod/Scripts/core/menu.lua` and moved the raid menu, the tech tree menu and the tribute menu (`liege_influence`) onto it. Real game runs on slot 0, fixture `base`.

## Engine facts
- **`Button.OnClicked:Add(fn)` on a Button made at run time crashes the game.** Run `20261022-033050-8596`: access violation at `0x70` in `XMulticastDelegateProperty::setup_member_functions` (stack of the Lua call). Do not bind a delegate on a widget made with `StaticConstructObject`. The click of a game bar button clone is seen with the hook on `mainTabButton_C:HandleClicked` (safe, see `bottom-bar-spike.md`).
- **A click on a Visible `Border` of the menu content reaches the game.** Run `20261022-034616-e668`: with the backdrop Button below the content, a click on the empty background of the menu opened the Wooden Church panel (`evidence/content-click-leaked-before-fix.jpg`). Slate hands a click to the widgets under the cursor from the top; a Border does not handle it, and the backdrop Button below the content is not in that path.
  - Fix: every Border of the menu content and the content widget get visibility `SelfHitTestInvisible` (4). A click on a content button still acts (the button is a child). A click on empty content falls to the backdrop Button, which blocks it. Run `20261022-034841-c6a7`: no panel opens, only the hover label (`evidence/world-click-blocked-by-menu.jpg`), and the same click without the menu opens it (`evidence/world-click-control-no-menu.jpg`). Run `20261022-035031-bc8c`: a real click on `TributeButton` of the content sends one tribute (silver 1000 to 800, influence 20).
- The backdrop dims the HUD too (z-order 450, above the HUD). The bottom bar is then under the backdrop, so the bar button cannot close the menu. The base menu adds a Close button for this: a clone of `mainTabButton_C` added to the viewport at z-order 510, position (24, 24), label "Close". Its click is the same `HandleClicked` hook (the hover hook names it `__close`). The backdrop itself has no click callback (see the crash above).
- A bar clone has a default icon (a map). The label is a `TextBlock` added to the clone's `Overlay` (`AddChildToOverlay`): `SetRenderScale` 0.5 (the default font is larger than the 60 px button), centred, bottom aligned. `SetColorAndOpacity` on the text is optional (the call may fail; the default is white).
  - A label wider than the button makes the button wider (render scale does not change the layout size). "Tribute" made its button wider, so the label of the tribute menu is "Liege" (the menu title is "Liege").
- The tooltip of a clone showed the default text `mainTab_0` (run `20261022-033605-5436`, the Close button). `SetToolTipText(FText)` is called on each clone since then and raised no error, but no picture shows a tooltip after it (the tooltip needs a longer hover than the scenario waits), so it is not proven whether the text changed. Open point, cosmetic.
- The HUD widget `MainUICPP_C` is found with `FindFirstOf` each second; a new HUD (a load) gets the buttons again. Run `20261022-033828-dcfb` found no HUD and added no button in 44 s while another agent's game window covered this one (log: nothing from the menu). The scenarios now bring the game window to the front first. The cause is not proven (a covered window may throttle the game thread). The base menu logs the poll count (`bar_polls`, `hud_found` in `menu_state`).
- Parameter counts and facts of the spike notes still hold (`click-blocking.md`).

## Decisions that changed
- Design decision "a full-screen Button under the menu content blocks clicks" is not enough: the content Borders must be `SelfHitTestInvisible` too. Design and delta spec updated (the click-blocking line and the new Close button).
- The click on the backdrop does not close the menu (no safe click callback). A Close button, a key (F8, F9) or the bar button when the HUD is not covered do.
- The fullscreen requirement is met by the backdrop (a full-screen dim layer that covers the HUD). The menu content keeps its size and place from the pak (position 300, 150). The owner may want the content itself to fill the screen like the developments menu; that needs a new layout in the pak (open question).

## Runs (slot 0, 10 of 10)
| Run | Scenario | Verdict | Note |
|---|---|---|---|
| `20261022-032938-c7d4` | `menu-smoke` | harness_error | Scenario bug: a missing key (`bar_error` is dropped from the JSON when nil). Bar buttons were added (log). |
| `20261022-033050-8596` | `menu-smoke` | crash | `OnClicked:Add` on the backdrop Button (see above). |
| `20261022-033331-5f59` | `menu-smoke` | harness_error | Close button off screen test point (y too near the window edge). Raid menu and bar pictures were good. |
| `20261022-033605-5436` | `menu-smoke` | fail | Raid menu passed. Tech: stale hover id, the close click missed the button edge. |
| `20261022-033828-dcfb` | `menu-smoke` | fail | No HUD found, no bar buttons (window covered). |
| `20261022-034159-a9ae` | `menu-smoke` | fail | Same stale hover point as run 5. |
| `20261022-034418-8753` | `menu-smoke` | pass | All three menus open with one real click and close with the Close button. |
| `20261022-034616-e668` | `menu-base` | pass | Passed, but the picture shows the content click leak (the scenario does not assert the panel). |
| `20261022-034841-c6a7` | `menu-base` | pass | After the fix: the world click is blocked, the control click opens the panel. |
| `20261022-035031-bc8c` | `menu-smoke` | pass | Final: also a real click on a content button. |

The two passing `menu-base` runs do not assert the building panel (no state in Lua tells it). The pictures show it, and the owner reviews them.

## Checks
- `harness/tests/test_fakegame_menu.py` (19 tests, the real `core/menu.lua` with widget stand-ins): the buttons come after the game's buttons with labels, one click opens, a game button click is ignored, hover, one menu at a time, a failed open leaves no widget, a duplicate id is refused, a new HUD gets the buttons again, a missing panel is reported, the key goes through the base menu, a removed widget closes the menu, the Close button, pass-through of content Borders, and no click callback on the backdrop.
- `harness/tests/test_menu_widget_sites.py` (task 2.0b): only `core/menu.lua` calls `AddToViewport` or `WidgetBlueprintLibrary`. Before the move it found 10 sites in `liege_influence`, `raid_widget` (including the spike "Mods" button) and `tech_tree_widget`; after the move it finds none.
- The spike "Mods" entry button and its commands (`spike_entry_open`, `spike_entry_state`) are removed from `raid_widget`. `HarnessClickHooks.create_standalone` stays in the shared module but nothing uses it now.
