# Click blocking spike (task 2.3a, issue #308)

## Question
A full-screen `Border` does not stop a click from reaching the game (see `bottom-bar-spike.md`). What does?

## Method
Test scenario `probe-bottom-bar` (`STAGE=clone BLOCK=1`, options `MODE=border|button`, `INPUT=none|uionly|gameandui`). Command `ui_probe` (`HarnessUiProbe`):
1. `focus`: move the player `PawnCPP` onto the first `SMBuilding`. The camera then centres on it (it was the Wooden Church).
2. `add_overlay`: full-screen widget, 35% black, Visible, `AddToViewport(50)`.
3. Real mouse: hover and click at the screen centre.
4. `close`, then the same click as a control.

Check: a building panel opens when the click reaches the game. The first attempt (run `20261021-125240-51b5`) had no building under the click, so it proved nothing.

## Results
| Run | Overlay root | Input mode | Click on the church with overlay | Control click after close |
|---|---|---|---|---|
| `20261021-125505-cc2a` | `Button` | none | Blocked (no panel, only the hover label) | Panel opens |
| `20261021-125652-7ac4` | `Border` | UIOnly call failed (wrong parameter count) | Not blocked (panel opens) | Panel opens |
| `20261021-125839-bc53` | `Border` | `SetInputMode_UIOnlyEx(pc, widget, 0, true)` | Blocked (no panel, only the hover label) | Panel opens (input restored with `SetInputMode_GameAndUIEx(pc, nil, 0, false, true)`) |

Not tested: `GameAndUI` with the widget focused (run cap).

## Decision
- Use a full-screen `Button` as the root of the blocking layer. It needs no input mode, so nothing has to be restored when a menu closes or when a load happens with the menu open.
- `UIOnly` also works, but it changes the input for the whole game (keys, camera) and must be restored on every close path. Keep it as the fallback.
- The game still shows the hover label of the building under the cursor. It is cosmetic; no panel opens.
- Parameter counts that UE4SS needs: `SetInputMode_UIOnlyEx` 4 (controller, widget, lock mode, flush input), `SetInputMode_GameAndUIEx` 5 (controller, widget, lock mode, hide cursor, flush input).
- Not checked: the menu content above the Button still gets its own clicks. Put the content in the same widget tree as a sibling above the Button in `core/menu.lua`, and check it in the base menu test scenario (task 2.3).
- Not checked: a click on the HUD (top bar, bottom bar) while the menu is open. The layer is at z-order 50 over the whole viewport, so it should cover them; check in task 2.3.
