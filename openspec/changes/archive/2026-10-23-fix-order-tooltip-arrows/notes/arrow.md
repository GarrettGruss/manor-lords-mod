# How the row picks its arrow

Question: why does a mod row show a red down arrow, also for a positive value?

Method: a game kept open (run `uparrow-spike2`), real mouse hover on the order icon, then read the live `approvalFactorWidget_C` rows with raw Lua eval (`allow_eval` switched on in the game folder for the spike, switched off again after).

Findings:
- The widget tree is `CanvasPanel_0 > HorizontalBox_24 > [Image_45, SizeBox_1 > DescriptionText (RichTextBlock), SizeBox_2 > ValueText (TextBlock)]`.
- `Image_45` always has the brush texture `/Game/UWG/ui_textures/tiny_arrow_triangle_up`. The game does not change the brush. It changes `RenderTransform.Angle`: 0 for a native row `+10%`, 180 for a native row `-10%`.
- A new row has angle 180 (the default of the widget), so a mod row always showed a down arrow.

Options:
1. A native field that drives the arrow: not needed. The arrow is set from the row value in the widget graph, and the row was built before the mod writes its text.
2. Copy the brush or load a texture: not needed. The texture is already the up arrow.
3. Rotate the image: WORKS. `Image:SetRenderTransformAngle(0.0)` for a positive row and `180.0` for a negative row, after `AddChildToVerticalBox`. No tint was needed: the game arrow is the same dark red for both signs.

Result: run `uparrow-rows` (pass), picture `evidence/tooltip-up-arrow.jpg` shows `Manor +10` with an up arrow.

Not verified: a negative row in a picture (`Homeless families`, needs homeless families in the fixture); the fake-game test checks angle 180 for it.
