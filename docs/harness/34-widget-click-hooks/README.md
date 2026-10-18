# Spec 34: widget click hooks

Issue: #254. Branch: `feat/34-widget-click-hooks`.

## Goal
A button of a mod menu reports a click as an event. The mod does not poll `Button:IsPressed()` any more.
Reason: polling missed short clicks, so the user had to press a button twice.

## Non-goals
- A new menu layout. The menus keep their layout.
- Hover, tooltips and keyboard focus.

## Result
Route 1 works. Details: `implementation-notes/click-hook-method.md`.
- The UE 5.5 editor Python cannot create graph nodes. So a graph is copied from an engine widget that already has one:
  `/AudioWidgets/AudioButtonToggle/AudioButtonToggle`. Its root `Button01` has an `OnClicked` event.
- The copy is `WBP_ClickButton` (`mod/shared/HarnessClickHooks/ue/make_click_button.py`). The compiled event is the UFunction
  `WBP_ClickButton_C:BndEvt__Button01_K2Node_ComponentBoundEvent_0_OnButtonClickedEvent__DelegateSignature`.
  The game calls it through ProcessEvent, so `RegisterHook` sees it.
- Shared module `mod/shared/HarnessClickHooks`: `attach(border, controller, tag)`, `bind_texts`, `set_text`, `set_visible`, `drain(owner)`, `release`.
- The menu pak holds a `Border` where a button belongs. Lua puts a click button into the Border.

## Acceptance criteria
- 10 real single clicks (OS mouse, 1 s apart) give exactly 10 click events: scenario `tech-tree-widget-clicks`.
- The tech tree menu and the raid menu take real clicks (`tech-tree-widget`, `invasion-raid-widget`).
- The Lua state stays alive for 5 minutes with the menu open (see the finding about the 50 ms tick).

## Open questions
- PolicyMenu was ported (see the note "PolicyMenu port"). No open mod still polls.
- The click button has a leftover graph with compile errors in the copy (`Can't connect pins`). The event works. A cleaner source would be better.

## Evidence (2026-10-18)
- Probe, 10 real clicks, 10 hook events: run `20261018-163733-ec87`.
- PolicyMenu, 10 real clicks, 10 counted: `policy-menu-clicks` runs `20261018-201957-b8f7` and `20261018-202107-d682`; `policy-menu` run `20261018-201834-1aad`.
- Tech tree menu, 10 real clicks on a law button, 10 counted: runs `20261018-180342-674d` and `20261018-180458-603f`.
- `tech-tree-widget` (real clicks on a path and a node): `20261018-180609-de2e`. `invasion-raid-widget` (real click picks the difficulty): `20261018-164406-1404` (first build) and `20261018-181534-1047` (final build).
- Tech menu open for 300 s with the state read twice a second: `20261018-173614-d910` (pass). Same test on the old polling code crashed: `20261018-173210-49ed`.
- Not measured: the old 50 ms poll against the hook with the same clicks (the old code crashes in the same test, so a long run is not possible). The old poll missed clicks according to the user.
