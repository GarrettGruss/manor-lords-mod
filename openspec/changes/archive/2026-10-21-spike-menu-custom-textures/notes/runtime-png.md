# Runtime PNG and Box (9-slice) result

Spike tasks 1.1 and 1.3. Test scenario `probe-menu-texture` (probe module `mod/shared/HarnessTexProbe`). Game runs used: 6 of 6.

## Result
Both work in the real game.

- Run `20261021-033203-e2bb` (pass): load PNG, show in an `Image`, Box at 200x200 and 600x300. Pictures in `../evidence/`. Run `20261021-032756-0e6f` (pass) gave the same step answers; its pictures have another window in front of the game.
- Functions and steps that worked (every step in the probe answer was `ok`):
  - `KismetRenderingLibrary:ImportFileAsTexture2D(world context, path)` with an absolute path with forward slashes (a repo path under the worktree worked). `Texture2D:GetSizeX` and `GetSizeY` returned 256 and 256.
  - `WidgetBlueprintLibrary:Create(controller, UserWidget class, controller)`, then `StaticConstructObject` of `WidgetTree` and of `Image`, set `widget.WidgetTree` and `WidgetTree.RootWidget`. No cooked Widget Blueprint is needed.
  - `Image:SetBrushFromTexture(texture, false)`, `Image:SetDesiredSizeOverride({X, Y})`, `AddToViewport`, `SetPositionInViewport`, `IsInViewport` (true).
  - Writing the nested struct fields `image.Brush.DrawAs = 1` (Box) and `image.Brush.Margin = {Left, Top, Right, Bottom}` worked, with no crash. No game crash in any run.
- Box (9-slice): `Margin` is a fraction of the texture (16 px of 256 px = 0.0625). At 200x200 and 600x300 the border keeps the same thickness (about 13 px on screen) and the corners stay sharp and square. The red 32 px marker in the corner is larger than the 16 px margin, so it stretches in x at 600 wide. Art for a frame must keep all corner detail inside the margin.

## Findings and problems
- First `SetDesiredSizeOverride(1280, 720)` on a new `Image` did not give a full screen image: the picture drew only about 24 px at the top left, even with a 1 s wait in run `20261021-033301-2498` (that picture had another window in front, so it is not proof). The Box calls (override set again after the brush change, plus `SetPositionInViewport`) sized the image correctly. Next try: set the override after `AddToViewport`, or put the Image in a sized `SizeBox`.
- `HarnessActions` parses only fixed request keys. A new command must read its own fields from the raw request text (second handler argument). The probe does this (`parseOwn`).
- `ctx.expect.record` needs a string `rule`.
- The harness screenshot copies screen pixels. A user window in front of the game ends up in the picture. The probe scenario raises the game window to topmost without focus (`raise_game_window`); it worked in run `20261021-033203-e2bb` and failed in `20261021-033301-2498`. A harness fix is outside this spike.
- Memory: `ImportFileAsTexture2D` gives an uncompressed texture. Not measured for large art.
- The PNG is read from an absolute path. A shipped mod needs the PNG next to its Lua (`ue4ss/Mods/<Mod>/assets/`); not tested whether deploy copies a PNG.
