# Proposal: Assess native UI elements

Issue: #504.

## Why
The custom menus of this repo may build their look from plain UMG primitives (CanvasPanel, Button, TextBlock) with hand-set styles. Then they do not look like the game. A third-party mod, Shelter Seekers, reuses native game widgets (`MessageFullscreen_C`, `ChoiceTooltip_C`, `RegionDropdown_C`, `mainTabButton_C`). We want to know where we stand and how to move toward native elements.

## What Changes
- Inventory the widgets that our menus, tooltips and shared UI modules create or touch. Mark each one native or primitive.
- Document how Shelter Seekers gets, shows, fills and closes native widgets (decompiled for study only).
- Write a report with a verdict and advice. The advice names follow-up changes; this spike builds nothing.

## Non-goals
- Code changes to menus. They go into follow-up changes.
- Copying third-party code. Check its license first.

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None.

## Impact
Read-only study of `mod/InvasionMod/Scripts/core/menu.lua`, `features/order_tooltip/`, `mod/shared/HarnessUi*` and the wiki. No game run.
