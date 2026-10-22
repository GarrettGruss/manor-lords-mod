# Evidence

Pictures of the bottom bar spike (task 1.3). Run ids are in `notes/bottom-bar-spike.md`.

| File | Test scenario | Run id | Shows |
|---|---|---|---|
| `bottom-bar-before.jpg` | `probe-bottom-bar` | `20261021-035510-1ced` | The game's bottom bar: six square buttons at the bottom centre. |
| `bottom-bar-clone-hover.jpg` | `probe-bottom-bar` | `20261021-040103-7d5e` | A seventh button (red tint) after the game's buttons, same frame and size, with the hover tooltip. |
| `overlay-world-click-not-blocked.jpg` | `probe-bottom-bar` | `20261021-040103-7d5e` | A full-screen Border (Visible) is on screen (dimmed view), and a click still opened the burgage plot panel behind it. |

The game window was in front in these pictures (the probe raises it). No other window covers them.


Click blocking pictures (task 2.3a, slot 0; the camera was moved over a building).

| File | Test scenario | Run id | Shows |
|---|---|---|---|
| `button-overlay-blocks-world-click.jpg` | `probe-bottom-bar` (`MODE=button`) | `20261021-125505-cc2a` | Task 2.3a. A full-screen Button (Visible) is on screen. A click on the Wooden Church opened no panel (only the hover label). |
| `control-click-opens-building-panel.jpg` | `probe-bottom-bar` | `20261021-125505-cc2a` | The same click after the overlay was closed: the church panel opens. |
| `border-uionly-blocks-world-click.jpg` | `probe-bottom-bar` (`MODE=border INPUT=uionly`) | `20261021-125839-bc53` | A Border plus UI-only input mode. The click opened no panel. |


Base menu pictures (tasks 2.3 and 2.4, slot 0, final code unless noted). Findings in `notes/menu-findings.md`. The spike pictures above were recompressed to 800 px.

| File | Test scenario | Run id | Shows |
|---|---|---|---|
| `bar-with-mod-buttons.jpg` | `menu-smoke` | `20261022-035031-bc8c` | The bottom bar: the game's six buttons, then Raid, Tech and Liege, same frame and size (the labels are small text under the default icon). |
| `bar-button-hover.jpg` | `menu-smoke` | `20261022-035031-bc8c` | The Raid button with the game's hover glow. |
| `menu-raid.jpg` | `menu-smoke` | `20261022-035031-bc8c` | The raid menu opened by one click: dimmed full-screen backdrop over the HUD, the menu content, the Close button at the top left. |
| `menu-tech.jpg` | `menu-smoke` | `20261022-035031-bc8c` | The tech tree menu, opened by one click on its button. |
| `menu-liege-tribute.jpg` | `menu-smoke` | `20261022-035031-bc8c` | The tribute menu (button label "Liege"), opened by one click. |
| `menu-liege-after-click.jpg` | `menu-smoke` | `20261022-035031-bc8c` | A real click on "Send tribute" in the content acted: influence 20, silver 800. |
| `world-click-blocked-by-menu.jpg` | `menu-base` | `20261022-034841-c6a7` | The camera is over the Wooden Church. With the menu open, a real click at the screen centre (on the menu background) opened no panel (only the hover label). |
| `world-click-control-no-menu.jpg` | `menu-base` | `20261022-034841-c6a7` | The same click with the menu closed opens the church panel. |
| `content-click-leaked-before-fix.jpg` | `menu-base` | `20261022-034616-e668` | Before the fix (content Borders Visible): the same click on the menu background opened the church panel behind the menu. |

The game window was brought to the front before each picture. No other window covers them.
