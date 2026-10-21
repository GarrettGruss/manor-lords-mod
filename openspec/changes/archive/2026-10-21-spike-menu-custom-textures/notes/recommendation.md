# Recommendation (task 1.5)

Use candidate 2: PNG files loaded at run time (`KismetRenderingLibrary:ImportFileAsTexture2D`) and set on `Image` widgets made from Lua (`StaticConstructObject`, `SetBrushFromTexture`). It works in the real game (runs 20261021-033203-e2bb, 20261021-032756-0e6f) and needs no editor cook and no pak, so art can change without a rebuild.

- Frames: draw as Box (`Brush.DrawAs = 1`) with `Brush.Margin`; corners stay sharp at any size. Keep corner art inside the margin.
- Full screen: `SetDesiredSizeOverride` alone did not size the image (it drew about 24 px). The base menu must place images in a canvas panel with full-screen anchors. To check in the base menu task of #308.
- Files: a shipped mod needs the PNGs deployed next to its Lua and a path built from the mod folder, not a repo path.
- Font: a custom blackletter font needs an editor cook (not tried). Until then, use the game's fonts.
- Pak textures (candidate 1) stay a fallback if run-time import is ever missing.

Owner decision (2026-10-21): approved.
