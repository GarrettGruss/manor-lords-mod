# 1.5 Menu with a text box and a check box

## Question

Can a mod menu show a text box for the tester's description and a check box (default ticked)?

## Method

Probe `menu_open` in `HarnessTelemetryProbe`, test scenario `probe_playtest_menu.py`, run ptt-menu-1 (slot 2). The widget is built at run time from C++ UMG classes, with no pak widget:

- `WidgetBlueprintLibrary:Create` (a `UserWidget`), a `WidgetTree` made with `StaticConstructObject`, then `Border` > `VerticalBox` > `TextBlock` title, `SizeBox` (640 x 180) > `MultiLineEditableTextBox` with a hint text, `HorizontalBox` with `CheckBox` and a label, `Button` with a `TextBlock`.
- Texts are set with `FText("...")`. No Lua string goes to an FName argument of a widget function.
- The menu framework of #308 (`core/menu.lua`) is not on `main`, so the probe does not use it.

## Result

- Every step returned ok. The widget is in the viewport (`IsInViewport` true) and renders.
- The check box is ticked by default (`SetIsChecked(true)`, read back with `IsChecked()`), and `SetIsChecked(false)` unticks it.
- The text box shows text set by Lua (`SetText`, read back with `GetText():ToString()`).
- Typing: `SetKeyboardFocus()` gave `HasKeyboardFocus` true. `WM_CHAR` messages posted to the game window then reached the text box (" +typed" was inserted at the caret). So the text box takes real character input and needs no pak widget.
- No mouse was used: a click on the check box or the button was not tested.

## Pictures

`evidence/menu-typed.png` and `evidence/menu-unticked.png` (see `evidence/README.md`). The run was on slot 2, so other windows (a UE4SS console of another slot) cover part of the game. Clean pictures need slot 0 later.

## Not verified

- A click on the check box and the button (the click hooks of `HarnessClickHooks` attach to Border widgets; a Button was not tried).
- Game hotkeys while the text box has focus. The game may use letter keys for camera and speed, so typing could trigger them. Needs a spike with a real keyboard, or an input mode switch (`SetInputMode_UIOnly`) when the menu opens.
- Copy and paste, the cursor in the box, a non-English keyboard layout or IME.
- Look: default Slate styling (grey box, white check). A themed look needs brushes from a pak or the texture method of `spike-menu-custom-textures`.
- A text box inside the menu framework of #308 (not merged).
