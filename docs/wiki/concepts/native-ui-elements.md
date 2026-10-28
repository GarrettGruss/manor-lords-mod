---
type: Concept
title: Native UI elements of the game
description: Catalog of the game's own widget classes that a Lua mod can find, create, fill, hook or reuse (HUD, bottom bar, buttons, letters, banners, tooltips, dropdowns, option rows), with paths, named children, hookable functions, the safe ways to catch a click, and which ones are checked in this repo or only seen in a third-party mod.
tags: [ui, widget, umg, menu, native, hud]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-27T00:00:00Z }
sources:
  - resource: repo://mod/InvasionMod/Scripts/core/menu.lua
  - resource: repo://mod/InvasionMod/Scripts/features/order_tooltip/widget.lua
  - resource: repo://mod/shared/HarnessUi/HarnessUi.lua
  - resource: repo://mod/shared/HarnessGameSetup/HarnessGameSetup.lua
  - resource: repo://mod/shared/HarnessPolicies/HarnessPolicies.lua
  - resource: repo://mod/HarnessActions/Scripts/main.lua
  - resource: repo://docs/wiki/concepts/engine-limits.md
  - resource: repo://openspec/changes/assess-native-ui-elements/notes/shelter-seekers-native-ui.md
---
# Native UI elements of the game

A "native element" is a widget Blueprint class of the game (a path under `/Game/UI/...`, class name ending in `_C`), or a live instance of one. A native element has the game's font, frame, colors and sounds. A widget that a mod builds from `/Script/UMG.*` types (Border, TextBlock, Button) has none of these unless the mod sets them by hand.

To build a new menu with these elements, see [Building mod UI](../workflows/building-mod-ui.md).

## Status labels

- **Used**: shipped code in this repo uses it.
- **Spike**: a spike in this repo checked it. Shipped code does not use it.
- **Third-party**: seen only in the decompiled Shelter Seekers mod (`openspec/changes/assess-native-ui-elements/notes/shelter-seekers-native-ui.md`). Not checked in our build. Run a spike before you rely on it.

## How to get an instance

- **Create a new one:** `StaticFindObject("/Game/UI/<Dir>/<Name>.<Name>_C")` for the class. Then call `Create(player, class, controller)` on `StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")`. If the class is not loaded yet, `LoadAsset(path)` first. A mod pak class needs the asset registry `GetAsset`, not `LoadAsset` (`core/menu.lua:75-91`).
- **Find the live one:** `FindFirstOf("<Name>_C")` or `FindAllOf`. Check `IsValid` on every result.
- **Reuse a part:** create a "donor" widget, take one child (`RemoveFromParent`), and add it somewhere else. Keep the donor in a Lua table so the engine does not collect it.

## Catalog

### HUD and bottom bar

| Class | Path | Named children / functions | Status |
|---|---|---|---|
| `MainUICPP_C` | `/Game/UI/HUD/MainUICPP` | `main_tabs_HB` (bottom bar), `C_Gameplay` (HUD canvas), `WhiteTooltipRT`, `IsDynamicBigPanelVisible()`, `updateTranslation`, `updateOnScreenTextVisibility` | Used (`main_tabs_HB`). Third-party (`C_Gameplay`, `IsDynamicBigPanelVisible`, the two update functions) |
| `mainTabButton_C` | `/Game/UI/HUD/mainTabButton` | hooks `HandleClicked`, `HandleHovered`. No own icon: add a label | Used (`core/menu.lua:23`) |
| `W_HUD_LordPanel_V2_C` | `/Game/UI/HUD/` | read for position | Used (`liege_influence/init.lua:33`) |
| `W_HUD_MercenaryCompanyV2_C` | `/Game/UI/HUD/W_HUD_MercenaryCompanyV2` | `Image_58` (background art) | Third-party |
| `W_HUD_ArmySkillButtonV2_C` | `/Game/UI/HUD/` | — | Named in the repo only |

### Buttons and menus

| Class | Path | Named children / functions | Status |
|---|---|---|---|
| `menuButton_C` | `/Game/UI/Common/menuButton` | serif font, fleur-de-lis. Text: property `TextKey`, then `updateText`. Hooks `DoOnReleased`, `OnMouseEnter` (no `HandleClicked`) | Used (`core/menu.lua:24`) |
| `mainMenu_widget_C` | game Esc menu | `continue()` closes it and restores the HUD | Used (`core/menu.lua:511-519`) |
| `popupMessageWidget_C` | popup | `Button_Accept`; event `BndEvt__popupMessageWidget_Button_Accept_..._OnButtonReleasedEvent__DelegateSignature` | Used by the harness (`HarnessActions/Scripts/main.lua:392`) |
| `RegionDropdown_C` | `/Game/UI/Common/RegionDropdown` | `RegionComboBox`: `ClearOptions`, `AddOption`, `RefreshOptions`, `SetSelectedIndex`, `GetSelectedIndex`. Clear `OnSelectionChanged`, `OnOpening` first | Third-party |

### Letters, banners and messages

| Class | Path | Named children / functions | Status |
|---|---|---|---|
| `genericAchievement_EventMessage_C` | `/Game/UI/Elements/genericAchievement_EventMessage` | `main_txt`, `bottomTxt`, `ribbon_border` | Used (`HarnessUi.lua:11`) |
| `questMessageElaborate_C` | `/Game/UI/Elements/questMessageElaborate` | `MainButton`, `contractAvailable_txt`, `numMsgs_txt`, `flareA`, `flareB` | Used (hide the bandit banner, `HarnessBandits.lua:212`). Third-party (as a clickable card) |
| `MessageFullscreen_C` | `/Game/UI/Elements/MessageFullscreen` | `Title1`, `message_txt`, `choiceA`, `choiceB`, `graphic`, `Button_Accept`, `Button_Decline`, `MD_NaviAutoButton_Accept`, `MD_NaviAutoButton_Decline`; fields `Quest`, `isLetter`, `tutorial`; functions `switchToEventGUIStyle`, `setGUIToLetterStyle` | Third-party (as a custom event letter). An old note of another mod hooks its `BndEvt__Button_ChoiceA/B` events |
| `MessageTutorialFullscreen_C` | `/Game/UI/Elements/` | `header_key`, `descr_key` | Third-party (checked only) |

### Tooltips

| Class | Path | Named children / functions | Status |
|---|---|---|---|
| `BigTooltip_ApprovalAndPublicOrder_C` | public order tooltip | `recentFactors_VB`; hook `updateContents` (pre) | Used |
| `approvalFactorWidget_C` | `/Game/UI/Tooltips/approvalFactorWidget` | `DescriptionText`, `ValueText`, arrow `Image_45` (texture `tiny_arrow_triangle_up`) | Used (`order_tooltip/widget.lua:5`) |
| `ChoiceTooltip_C` | `/Game/UI/Tooltips/ChoiceTooltip` | `localizedTextBox_C_1.TextBlock_16`. Attach with `Button:SetToolTip(tip)`. The game rebuilds it: hook `Construct` and set the text again | Third-party |

### Settings and development tree

| Class | Path | Named children / functions | Status |
|---|---|---|---|
| `W_Menu_GameSetupSettingEntry_C` | `/Game/UI/Game_Setup/W_Menu_GameSetupSettingEntry` | `Text`, `Spinner` (`UpdateOptions` with `SettingOption {Label, Value}`, `GetCurrentIndex`). Rows go in a `GridPanel` (`AddChildToGrid`) | Spike (#416) |
| `mainMenu_GameSetup_C`, `mainMenu_GameSetupPresetButton_C` | game setup screen | opening it writes the real `menu.sav` | Spike |
| `policyWidget_C` | `/Game/UI/Development_Tree/policyWidget` | — | Used by the harness (`HarnessPolicies.lua`) |

## Catching a click

| Way | Status | Notes |
|---|---|---|
| `RegisterHook` on a function of the game class (`HandleClicked`, `DoOnReleased`, a `BndEvt__...` event). Match `self` by name or by `GetAddress()` | Used | Fires for every instance of the class. Filter for your own widget. |
| `WBP_ClickButton` from our pak (`HarnessClickHooks`) | Used | Our cooked Blueprints have no graph, so a Button inside them has no hookable click. This button does. |
| Poll the state: `GetSelectedIndex`, `IsPressed`, `IsHovered` | Third-party | Binds no delegate. This is the safest choice. |
| `button.OnReleased:Add(object, FName("nativeFunction"))`, then `RegisterHook` on that native function | Third-party | Binds a native function, not a Lua function. The target function still runs its own code. **Not checked in our build.** |
| `button.OnClicked:Add(luaFunction)` on a Button from `StaticConstructObject` | **Crashes** | DANGEROUS_ACTIONS.md, #308. |

## Rules

- Check `IsValid` on every widget from `GetChildAt`, `FindAllOf` or a named child, before any method call. `pcall` does not catch a native access violation (#462).
- Child names (`TextBlock_16`, `Image_58`) and fields (`Quest`, `isLetter`) are private to the game Blueprint. A game update can rename them. Fail loudly with a clear message if one is missing.
- Set the text of a created row after you add it to its parent. A `SetText` before the add is overwritten by the default text (`approvalFactorWidget_C`).
- Touch widgets only on the game thread. A key bind callback must queue the work with `ExecuteInGameThread`.

## Not known yet

- Whether `Add(object, FName)` on a button delegate is safe in our build.
- Whether a font or a texture cooked into our pak works. PNG files loaded at run time do work (`ImportFileAsTexture2D`, spike #333).
- A full list of `/Game/UI/` classes. Dump them with the bridge (`list_subclasses` of `UserWidget`) in a spike.
