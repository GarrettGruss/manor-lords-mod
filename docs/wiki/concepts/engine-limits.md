---
type: Concept
title: Engine limits found by spikes
description: Things the game does not allow from Lua or data, found by spikes and closed as not possible, with the evidence and the reason. Now holds buildings inside the manor bailey.
tags: [engine, limits, bailey, manor, spike]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-19T00:00:00Z }
sources:
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-17-bailey-buildings/README.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-17-bailey-buildings/implementation-notes/bailey-buildings.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-12-manor-exploration/
---
# Engine limits found by spikes

## Buildings inside the manor bailey: not possible

Closed as not possible by owner decision, 2026-10-19 (issue #68, change `spike-bailey-buildings`). No more tests, no fixture and no pak route will be tried. Criterion M2 (wall in a whole town) stays not verified.

Facts that stay true:

- The mouse path refuses a normal building inside the bailey. The ghost is orange with the text "Road Access obstructed". The same building outside the ring is white and is placed (checked on the fixtures `manor-bailey` and `manor-closed`, a valid Large castle).
- The refusing check is native C++. Nine candidate functions were hooked and gave zero events. No data table holds the rule, and no reflected flag that it reads was found.
- A burgage plot committed without the mouse (`plot_field_place`, `addCommitFieldRequest`) skips the check and makes sites inside the ring. Builders never build them (0 of 4 after 30 game days, while 4 of 4 outside plots were built).
- Not separated: a bailey rule, or no reachable road path because the palisade blocks roads (ring with one gate). A gate-free ring test was never run.

Do not plan a feature that needs buildings inside the bailey.

## Menu pictures: PNG at run time (spike #333)
- A mod menu can show a picture the game does not have, without a pak. `KismetRenderingLibrary:ImportFileAsTexture2D(world, path)` loads a PNG from an absolute path with forward slashes. The texture is not compressed.
- Build the widget in Lua: `WidgetBlueprintLibrary:Create`, then `StaticConstructObject` of `WidgetTree` and `Image`. Use `Image:SetBrushFromTexture(texture, false)`, `AddToViewport` and `SetPositionInViewport`.
- 9-slice: write `image.Brush.DrawAs = 1` (Box) and `image.Brush.Margin = {Left, Top, Right, Bottom}`. Margin is a fraction of the texture (16 px of 256 px is 0.0625). Corners stay sharp at any size when the corner art is inside the margin.
- `SetDesiredSizeOverride` alone did not size a new full screen image (it drew about 24 px). Put the image in a canvas panel with full-screen anchors, or set the override after the brush change.
- Not known: a cooked pak texture and a custom (blackletter) font. Both need an editor cook and were not tried. A shipped mod must deploy its PNG next to its Lua (not tested).
- Owner decision 2026-10-21: menus may use PNG images loaded at run time. Notes: `openspec/changes/archive/2026-10-21-spike-menu-custom-textures/notes/`.
