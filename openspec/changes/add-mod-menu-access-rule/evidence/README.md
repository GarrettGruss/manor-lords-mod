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
