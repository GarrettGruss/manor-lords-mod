---
type: Workflow
title: Building mod UI
description: How to build a new mod menu or other UI in the Invasion Mod - register with core/menu.lua, choose between a native game widget, a cooked pak widget and a run-time UMG widget, catch clicks safely, style it like the game, avoid the known crashes, and test it with screenshots.
tags: [ui, widget, menu, umg, workflow, native]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-27T00:00:00Z }
sources:
  - resource: repo://mod/InvasionMod/Scripts/core/menu.lua
  - resource: repo://mod/shared/HarnessClickHooks/HarnessClickHooks.lua
  - resource: repo://mod/InvasionMod/ue/
  - resource: repo://mod/InvasionMod/Scripts/features/order_tooltip/widget.lua
  - resource: repo://docs/wiki/concepts/engine-limits.md
  - resource: repo://openspec/changes/assess-native-ui-elements/notes/report.md
---
# Building mod UI

This page says how to add UI to the Invasion Mod. The catalog of game widgets is [Native UI elements of the game](../concepts/native-ui-elements.md). The crash rules are in `DANGEROUS_ACTIONS.md`.

## 1. Start from the base menu

Every mod menu registers with `mod/InvasionMod/Scripts/core/menu.lua` (`menu.register`). The base menu gives you:

- a bottom bar button (a copy of the game's `mainTabButton_C` in `main_tabs_HB`);
- open and close, one menu at a time, and Esc handling;
- a full-screen backdrop that blocks clicks to the game;
- the game's `menuButton_C` as the Close button;
- pause while the menu is open.

Only `core/menu.lua` may create menu widgets (`test_menu_widget_sites.py`). A feature gives the base menu its content widget and reacts to clicks.

## 2. Choose a widget source

Prefer the first source that fits:

1. **A native game widget** (`/Game/UI/..._C`). It has the game's font, frame and sounds. Use it for letters, banners, tooltips, option rows, dropdowns and buttons. Examples in the repo: the order tooltip rows (`approvalFactorWidget_C`), the HUD banner (`genericAchievement_EventMessage_C`).
2. **A cooked pak widget** (`/Game/HarnessMod/WBP_*`, made by `mod/InvasionMod/ue/make_*.py`). Use it for a layout the game has no widget for. Today all four menus use this source. Their parts are plain `Border`, `TextBlock` and boxes with hard-coded colors, so they do not look like the game. See [Pak mods](pak-mods.md) for the build.
3. **A run-time UMG widget** (`StaticConstructObject` of `/Script/UMG.<Type>`). Use it only for layout containers (`CanvasPanel`, `SizeBox`, `ScrollBox`) and for `Image` with a PNG. Never put a click handler on it.

Mixing is fine and expected: a pak or run-time layout container that holds native children (text rows, buttons, tooltips) looks native.

## 3. Create and place a native widget

```lua
local lib = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
local class = StaticFindObject("/Game/UI/Tooltips/approvalFactorWidget.approvalFactorWidget_C")
assert(class and class:IsValid(), "approvalFactorWidget_C is not loaded")
local row = lib:Create(controller, class, controller)
parent:AddChildToVerticalBox(row)        -- add first
row.DescriptionText:SetText(FText("..."))  -- then set the text
```

- Set text after the add. The widget's construct overwrites an earlier `SetText`.
- To put a widget on screen with no parent: `AddToViewport(z)`, `SetAnchorsInViewport`, `SetAlignmentInViewport`. Do not call `SetPositionInViewport` after the anchor.
- To reuse only a part of a game widget: create it as a donor, `RemoveFromParent` the child, add the child to your container, and keep the donor in a Lua table.
- Hide the parts you do not need with `SetVisibility(1)` (collapsed).

## 4. Catch clicks safely

Allowed, best first:

1. Poll state at the menu tick: `GetSelectedIndex`, `GetCurrentIndex`, `IsChecked`. No delegate is needed.
2. `RegisterHook` on a function of a native class (`mainTabButton_C:HandleClicked`, `menuButton_C:DoOnReleased`, a `BndEvt__...` event). The hook fires for every instance. Match your widget by name or `GetAddress()`.
3. `WBP_ClickButton` from our pak, through `HarnessClickHooks`.

Forbidden: `OnClicked:Add(luaFunction)` on a Button from `StaticConstructObject` (crash #308).

Not checked yet: binding a button delegate to a native function (`OnReleased:Add(object, FName("fn"))`) and hooking that function. A third-party mod does this. Run a spike first.

Hooks run on the game thread, but key binds do not. Queue the work with `ExecuteInGameThread`.

## 5. Style it like the game

- Native widgets bring their own font and look. This is the main reason to use them.
- For pak widgets, do not invent colors. Copy the color values of a native widget (read them with the bridge `inspect_object`), and keep them in one place.
- Custom pictures: load a PNG at run time with `KismetRenderingLibrary:ImportFileAsTexture2D` and `Image:SetBrushFromTexture` (spike #333; owner decision 2026-10-21). Keep a Lua reference to the texture.
- A cooked font or texture in our pak is not tried yet.

## 6. Avoid the known crashes

- Check `IsValid` on every widget from `GetChildAt`, `FindAllOf` or a named child before a method call. `pcall` does not catch an access violation.
- Do not read the building list at each menu refresh. Cache it.
- A full-screen `Border` does not block clicks. Use the base menu backdrop.
- Opening the game's setup screen writes the real `menu.sav`.

## 7. Test it

- Fake game kit tests for the logic (`test_fakegame_*.py`).
- A real test scenario that opens the menu, clicks with `osinput`, and takes `ctx.screenshot(name)`. UI changes need picture evidence in the change (CONTRIBUTING.md, "Picture evidence").
