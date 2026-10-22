# Design: Spike menu custom textures

## Context
- The menus `raid_widget`, `tech_tree_widget` and `liege_influence` create pak widgets with `WidgetBlueprintLibrary:Create` and `AddToViewport`.
- The repo can cook assets headless in UE 5.5.4 and ship them in a pak (skills `harness-pak-mod` and `harness-meshy`).
- The approved mockup needs: a full screen parchment background, a patterned border, framed cards that stretch, illuminated capitals and a blackletter font.

## Candidates
| # | Way | Good | Risk |
|---|---|---|---|
| 1 | Texture in a mod pak, set from Lua with `Image:SetBrushFromTexture` | Normal UE path; cooked and compressed | Needs the cook step; the texture path must be found at run time (`StaticFindObject` or `LoadAsset`) |
| 2 | PNG loaded at run time with `KismetRenderingLibrary:ImportFileAsTexture2D`, then `SetBrushFromTexture` | No pak; art can change without a cook | The function may be missing in a shipping build; textures are not compressed; file path rules |
| 3 | Widget blueprint in the pak with the textures already placed | Least Lua | Each layout change needs a cook; harder to make one base menu |

## Questions the spike answers
1. Which candidates work in the real game? A screenshot for each one that works.
2. Can a brush draw as Box (9-slice) with margins set from Lua, so a frame stretches without blurred corners?
3. Can a custom font be loaded from a pak and set on a `TextBlock` from Lua?
4. Which way fits the base menu of #308 best (one base, menus add only their content)?

## Safety
- Single-player only. No save function. Back up the save folder before runs.
- Do not pass Lua strings to `FName` parameters of widgets that may lack them (CLAUDE.md, Safety).
- Do not edit game files or game paks.

## Decision
Owner (2026-10-21): candidate 2 is approved. Menus may use PNG images loaded at run time (ImportFileAsTexture2D, SetBrushFromTexture, 9-slice with Brush.DrawAs = 1). Candidate 1 (pak texture) and the custom font stay untried; they need an editor cook. Engine facts are in docs/wiki/concepts/engine-limits.md.
