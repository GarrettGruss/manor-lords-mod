# UI entry point for mod menus (task 1.1, issue #308)

## Result
A mod can add a clickable button to the game screen from Lua. One click reaches the root menu, with no hotkey. Proven in a real game run.

## Proof
- Run `20261020-024642-6426` (test scenario `spike-ui-entry-button`, `--pak raidmenu`): verdict pass.
- A `WBP_ClickButton` (pak widget of `HarnessClickHooks`) was created with `WidgetBlueprintLibrary:Create`, labeled "Mods", and put in the viewport with `AddToViewport` and `SetPositionInViewport` (100, 100). It shows at the top left of the HUD.
- A real mouse click (`ctx.click_with_mouse`, position found by hover) was counted once by the click hook, and the raid menu opened.
- Screenshots: `runs/20261020-024642-6426/screenshots/entry-button-before.png` and `entry-button-after-click.png`.
- Spike code: `HarnessClickHooks.create_standalone` (new), commands `InvasionMod.spike_entry_open` and `spike_entry_state` in `raid_widget/init.lua`, scenario `spike_ui_entry_button.py` (removed from the harness: it named the mod; see git history of commit 8320540^).

## Options
| Option | Works | Risk | Effort |
|---|---|---|---|
| (d) Our own button added to the viewport from Lua (proven) | Yes | Low. No game widget is touched, so a game update cannot break it. Needs the click button pak. It does not follow the HUD layout. | Small. The click hook code exists. |
| (a) A button added into an existing game HUD widget at run time | Not tried (run cap, time) | Medium. Needs the HUD class name and a panel with `AddChild`. A game update can rename it. | Medium. |
| (b) A button inside an existing game menu (pause menu, building panel) | Not tried | Medium to high. The menu must be open first, so the root menu is click 2 at best. | Medium. |
| (c) A pak replacement of a HUD widget | Not tried | High. Replaces a game asset. Breaks on game updates and conflicts with other paks. | High. |

## Notes
- Hover scanning near the window edge scrolled the game camera (the picture after the click shows a different view). Scan away from the edges.
- The click is handled in the scheduler tick, as for the other menus. No game call runs in the hook.
- Several menus need one more widget: a small list opened by click 1. Click 2 opens the menu.

## Recommendation for design question 2
Use one shared "Mods" button (option d). Click 1 opens a small list of mod menus, click 2 opens the menu. This uses one screen spot, scales to new menus (tribute, tech tree, raid) and stays inside the 2-click rule. One button per menu crowds the HUD with each new menu. If only one menu exists, the button may open it directly.

## Open questions
- Is the position (top left, under the window edge) acceptable, and should the player be able to hide the button?
- Options (a) to (c) were not run. Try them only if the owner wants the button inside the game HUD.
