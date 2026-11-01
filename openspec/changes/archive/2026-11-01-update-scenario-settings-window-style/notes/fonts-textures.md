# Fonts and textures for the start screen (task 1.1)

Result of the archived change `update-liege-contracts-window-style` (`notes/fonts-textures.md`), reused as it is:
- Font: the game font `/Game/UWG/fonts/CombinedFont_Mikadan` works for every text block (stub asset in the editor, never shipped in the pak).
- Panel: a flat dark grey colour. `grungeTiling` is too dark. No rough edge and no soft centre light (the background is flat near-black).
- Colours are sRGB values converted with `v ** 2.2`.

What is new here:
- The option texts and the two button texts are text blocks of the widget (`OptText<r>_<c>`, `DefaultsText`, `BeginText`). The click buttons lie on top of them. Lua hides their box and label (`SetBackgroundColor`, `SetBrushColor` on the TextBorder, label colour alpha 0), so the serif font and the colour are under full control.
- The selected option is gold. The underline is a thin Border (`Under<r>_<c>`) that Lua colours gold (selected) or clear. `SetVisibility(Collapsed)` did not hide these Borders in the game (run `20261101-183611-f3a6`), so Lua changes the brush colour instead. A text block of an unused fourth choice gets empty text.
- The flourish of "Begin the game" is the character U+2767 in the game font. It shows in the game.
- Difference from the mockup: no soft centre light and no rough panel edge (as in the liege window); the flourishes are text, not the game's Close button class.

## Traps
- `ipairs` stops at the first nil: a list made of possibly missing widgets must not be walked with `ipairs`.
- Build with a private UE workspace and a private pak `work_dir` (`pakmod.py --config <C:/ path>`); the log line `built ...InvasionMod_P.pak` must appear.

## Runs
- `20261101-183611-f3a6`: first look (underlines of all options visible, "-" in unused cells; fixed).
- `20261101-183855-456c`: final look, pass.
