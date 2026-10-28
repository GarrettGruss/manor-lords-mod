# Report: do our custom menus use native UI elements?

Issue: #504. Inputs: `invasion-menu-assessment.md`, `tooltip-and-shared-ui-assessment.md`, `shelter-seekers-native-ui.md` (this folder). The main claims were checked against the source.

## Verdict: mixed

| Area | Verdict | Why |
|---|---|---|
| Menu frame (`core/menu.lua`) | Native | Bottom bar button is a copy of `mainTabButton_C` in the game's `main_tabs_HB`. Close is the game's `menuButton_C`. Esc closes the game's `mainMenu_widget_C`. |
| Menu backdrop | Primitive | Run-time `UserWidget` + `Button`, black at alpha 0.55 (`menu.lua:137-142`). Needed: a Border does not block clicks. |
| Menu content (raid, tech tree, liege tribute, scenario settings) | Primitive (pak) | Cooked `WBP_*` widgets from an engine sample shell, built from `Border`, `TextBlock` and boxes. Colors hard-coded in `ue/make_*.py`. No game font, brush or texture. |
| Content buttons | Pak | `WBP_ClickButton` through `HarnessClickHooks`, because of crash #308. |
| Order tooltip | Native | Rows are `approvalFactorWidget_C` in the game's tooltip. Only green and red are hard-coded. |
| Shared modules | Native | `HarnessUi` (`genericAchievement_EventMessage_C`), `HarnessGameSetup` (`W_Menu_GameSetupSettingEntry_C`), `HarnessPolicies` (`policyWidget_C`). Primitives only in probes. |

So the frame and the small UI are native, but the content of every menu, which is what the player reads, is not. That is why the menus do not look like the game.

## Risk found

`mod/InvasionMod/Scripts/features/order_tooltip/widget.lua:28` calls `GetClass` on a `GetChildAt` result with no `IsValid` check. DANGEROUS_ACTIONS.md lists this pattern as a crash (#462). Fix it in a small `fix/` change.

## What Shelter Seekers shows

A third-party mod builds a full event letter, HUD cards, tooltips and a region dropdown from native widgets, with no `Button` built at run time. New for us: `MessageFullscreen_C` as a custom letter, `ChoiceTooltip_C`, `RegionDropdown_C`, `MainUICPP_C.C_Gameplay` as a HUD canvas, `IsDynamicBigPanelVisible`, and a click "trampoline" (`OnReleased:Add(object, FName("nativeFn"))` plus `RegisterHook` on that function). It hooks the save functions but does not call them. Study only: check its license before any code is copied.

## Advice, in order

1. **Fix the `IsValid` risk** in `order_tooltip/widget.lua` (small `fix/` change).
2. **Spike: native widgets in menu content** (`spike-native-menu-widgets`). Answer in the real game:
   - Is `OnReleased:Add(object, FName)` on a native button safe, and is the target function harmless? Try `MessageFullscreen_C` with `setGUIToLetterStyle`.
   - Do `ChoiceTooltip_C` (`SetToolTip`) and `RegionDropdown_C` (poll `GetSelectedIndex`) work in our build?
   - Can native children (`menuButton_C`, `approvalFactorWidget_C`, `W_Menu_GameSetupSettingEntry_C`) be added inside our pak `WBP_*` panels?
   - Dump all `/Game/UI/` widget classes with the bridge into the catalog.
3. **Use native buttons in menus.** If the spike passes, replace `WBP_ClickButton` with `menuButton_C` copies, caught by `RegisterHook` on `DoOnReleased` matched by address (the base menu already does this for Close). This gives the game's font and sound at once.
4. **Use native rows.** Use `W_Menu_GameSetupSettingEntry_C` (spinner rows, spike #416) for the scenario settings menu, and `ChoiceTooltip_C` for hover help on menu buttons.
5. **Use native frames.** Try `MessageFullscreen_C` as the frame for one-choice menus (raid offer, liege tribute) instead of a pak panel.
6. **Take colors from the game.** Until content is native, read the color values of a native panel with the bridge and use them in `ue/make_*.py`, in one shared table.
7. **Keep the pak widgets for layout only**: a pak or run-time container with native children.

Each step after 1 is its own OpenSpec change, and needs screenshots as evidence.

## Docs added by this spike

- `docs/wiki/concepts/native-ui-elements.md`: catalog of game widget classes with status (used, spike, third-party).
- `docs/wiki/workflows/building-mod-ui.md`: how to build a mod menu.
