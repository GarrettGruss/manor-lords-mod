# Opening the tooltip without the owner (task 1.2)

## Verdict

**It works with the harness OS mouse tooling.** On 2026-10-23 `harness/tools/s115_input_env.py` reported `SM_MOUSEPRESENT 1`, so a real cursor move works. No widget call was needed, and no step needs the owner.

## Method

- Hold run (a scratch test scenario that keeps the game open) on fixture `base`, slot 2, run `ord-h-193058`. Picture steps: `runlib.osinput.hover_at(api, hwnd, 0.718, 0.090)` under the OS input lock (`runs/.input.lock`), then `capture_game_window`.
- The order icon (scale with the percentage) is the third item of the top right group: 0.718 of the window width, 0.090 of the height (window of 1302x776 pixels). The tooltip opens about 1 s after the move and stays while the cursor stays. Moving the cursor away (for example to 0.9, 0.6) and back opens it again and runs `updateContents` again.
- The tooltip works with the game paused.
- Cautions: the camera drifts when the cursor sits near the screen edge, so after some minutes the camera region differs from the village. The tooltip shows the factors of the player's home region, not of the camera region. Windows of other agents can cover the window in a picture: retake it.
- The widget is one object that the game keeps: `BigTooltip_ApprovalAndPublicOrder_C` owned by the game instance (`FindAllOf` finds exactly one, and its `recentFactors_VB` holds the rows).
- Not needed here, so not tried: calling a widget function to show the tooltip from Lua.
