# OS mouse regression (issue #115)

Real-mouse clicks stopped reaching the game world around run s90f (2026-10-15).
`PawnCPP:getMouse3d` returned Z -100000 for every cursor position. No ghost followed the cursor. Hover tooltips still worked.

## Cause (strong evidence, not toggled)

Windows reports no mouse device on this PC now.

- `GetSystemMetrics(SM_MOUSEPRESENT)` is 0 (`uv run python harness/tools/s115_input_env.py`).
- `Get-PnpDevice -Class Mouse -PresentOnly` and `-Class Keyboard -PresentOnly` find nothing. All Razer DeathAdder and HID mouse entries have status Unknown (not connected).
- The session is not remote (`SM_REMOTESESSION` 0). One monitor.
- Unreal Engine reads the mouse position for the world trace only when a mouse is attached. The engine code (from memory, not checked in this repo): `UGameViewportClient::GetMousePosition` returns false when `FSlateApplication::IsMouseAttached()` is false. Slate hover still works, because it uses the window messages.
- This fits every symptom: ground trace fails, ghost does not follow, UI hover works.

What was ruled out (working run s21a-1 against failing runs s104g-1, s90f-1, s90e-5):

- Same private `GameUserSettings.ini` (2560x1440, `FullscreenMode=1`, `WindowPos` -1), same fixture hash, same game build.
- Same click path (`SetCursorPos` plus `mouse_event`). `osinput.py` and `focus_game` were not the cause. The `focus_game` early return only skips a redundant focus call.
- In run s115-1 the game window had the focus (rect 629,285 - 3211,1781) and the cursor was inside. `getMouse3d` was still Z -100000 at three spots (0.5,0.5), (0.43,0.27), (0.65,0.65), also in plain building mode of a hitching post (30) without any pak.

I did not toggle the cause: no mouse could be plugged in from here. A mouse in Windows is the proof still open.

## Fix

- `osinput.check_mouse_present` raises `InputError` ("no mouse device ... no input sent"). `focus_game` calls it, so every helper (`place_with_mouse`, `order_with_mouse`, `click_at`, `hover_at`, `press_key`, scenario `click_with_mouse`, `hover_with_mouse`) fails at the first call. This saves launches and clicks.
- `Win32Input.mouse_present` reads `SM_MOUSEPRESENT`. Fake test: `FocusTest.test_no_mouse_device_is_an_error_before_any_input`.
- Skill `harness-game-spike` has the rule.
- Tools: `harness/tools/s115_input_env.py` (read Windows input facts), `harness/tools/s115_probe.py` (read `getMouse3d` at three spots, skips the check on purpose).

## Proof

- Run s115-1 (`place-building` on fixture `base`): the scenario stopped with the new `InputError` message. This proves the check.
- `s115_probe.py s115-1`: `mouse_present False`, game in the foreground, `getMouse3d` Z -100000 at three spots.
- The vanilla placement proof (white ghost, building count +1) was NOT done. It needs a mouse device. 1 launch used. The game was closed.

## Next step

Plug a mouse into the PC (or install a virtual HID mouse driver; that is outside this repo and needs the user). Restart the game. Run `uv run python harness/tools/s115_input_env.py` (expect `SM_MOUSEPRESENT 1`), then `uv run python harness\run.py --scenario place-building --keep-open`.

## Housekeeping

Run s115-1 used `--keep-open` and left the fixture slot `saveGame_46*` (8 files) in the real save folder. The permission checker refused to delete it. The user or the next harness run should remove it.
