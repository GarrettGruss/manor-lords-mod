# Policy menu options

## (a) Reuse the game's own panel
- The development panel is the widget `developmentPanelTree_C` (in the main UI, `MainUICPP`). `PawnCPP:toggleDevelopmentPanel()` opens and closes it (verified live, callable from the bridge).
  While it is open the game clock stops.
- It holds 20 `policyWidget_C` children (`policyWidget` to `policyWidget_20`) with `policyID`, `policyTier`, `wip`, `Region`. A mod can call the release handler of a child
  (`BndEvt__policyWidget_Button_22_..._OnButtonReleasedEvent`, no arguments). It signed policy 12 (`policiesSigned` = [12]).
- Limit: the panel shows only the game's policies. A new policy needs a new row in `DT_PolicyTypes`, and it has no effect code.

## (b) Lua-made widget
- Verified live: `WidgetBlueprintLibrary:Create(pawn, policyWidget_C class, controller)` makes a new policy card. `AddToViewport(500)` and `SetPositionInViewport` place it
  (command `menu_probe_show`; screenshot `runs/s16-b/screenshots/probe1.png` showed the card of policy 12 at the chosen position; `in_viewport` true; no crash).
- It reuses game art, the tooltip (`BigTooltipPolicy_C`) and the click handler of the game. The button state can be polled with `Button_22:IsPressed()` and `IsHovered()` (both read false when idle).
- A delegate such as `OnClicked` cannot be bound from Lua. Use polling in a `LoopAsync`. A fully new layout needs a `UserWidget` with a `WidgetTree` made in Lua. This was not tried.
- The click itself was not tested. It needs the real mouse (spec 07 real-mouse input). The machine has a monitor (the screenshot works), so a click test is possible next.

## (c) Pak widget
- A new UMG asset (WidgetBlueprint) in a `_P.pak`, made with `Create` from Lua. This gives full layout control and bound events in the Blueprint graph.
  It needs UAssetGUI work on a widget asset. This repo has proven only DataTables. Editing a Blueprint graph in JSON is hard.
- Not tested (no pak build in this spike).

## Recommendation
Start with (b): reuse `policyWidget_C` cards in a mod-owned screen, with polled click state, and let the mod apply the effect (sign policy 12 and unsign it with a Lua timer).
Use (a) only to show the normal panel. Consider (c) later for a custom layout.
