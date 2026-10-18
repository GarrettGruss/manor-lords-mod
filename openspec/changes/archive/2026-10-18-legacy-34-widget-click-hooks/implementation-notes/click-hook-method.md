# Click hook method (spec 34)

Date: 2026-10-18. Tags: [known] has evidence in a run. [theory] is not tested.

## Routes tried, in order
1. Give our widget a graph. WORKS (below).
2. Reuse a game button class: not needed.
3. Slate or UMG hook on mouse down: not needed.

## Route 1 facts
- [known] UE 5.5 editor Python has `K2Node` and `EdGraph` types, but no way to create nodes. `BlueprintEditorLibrary` can only add or remove graphs and variables.
  `K2Node_CustomEvent` and `K2Node_ComponentBoundEvent` are not exposed.
- [known] Method: duplicate an engine widget whose graph already has a bound button event. Search: `grep -l OnButtonClickedEvent__DelegateSignature` in
  the engine `Content` and `Plugins` folders. The best source is `/AudioWidgets/AudioButtonToggle/AudioButtonToggle` (runtime plugin, engine classes only).
- [known] `duplicate_asset` compiles the copy. It prints `Can't connect pins Self and Button` errors (the graph is typed for the old class). The compiled bound event still exists.
  The cooked asset keeps the function `BndEvt__Button01_K2Node_ComponentBoundEvent_0_OnButtonClickedEvent__DelegateSignature`.
- [known] The copy imports a texture of the source plugin. The 8 `Image` widgets get no brush resource, so the cooked package needs no plugin asset. The game loads it.
- [known] `RegisterHook("/Game/HarnessMod/WBP_ClickButton.WBP_ClickButton_C:BndEvt__Button01_...")` works after the class is loaded
  (class load: asset registry `GetAsset`, same as every pak widget). The hook gets the widget instance as `self`.
- [known] Probe run `20261018-163733-ec87`: 10 real clicks (OS mouse, 1 s apart) gave 10 hook events. Event times were 1.5 s apart (the click gap).
- [known] The label is `ValueText` (a TextBlock inside `TextBorder`). Python cannot make it a variable (`bIsVariable` is not exposed). Lua walks
  `widget.Button01:GetContent():GetChildAt(1):GetContent()`. A scan with `FindAllOf("TextBlock")` for each of 21 buttons crashed the game
  (luaH_getint in `auto_construct_object`).
- [known] The menu paks hold a `Border` (clear brush, else it paints white) where a button was. Lua calls `Border:SetContent(clickButton)`.
  A canvas slot of the Border still moves the button (`Border.Slot:SetPosition`). `UserWidget:SetColorAndOpacity` tints the button.

## Where the hook callback runs
[theory] On the game thread: Slate calls the OnClicked delegate during input handling, and the Blueprint event goes through ProcessEvent.
Not proven by a thread id (Lua has none). The module keeps the callback minimal: it pushes `{name, time}` into a queue and does no game call.
The scheduler tick (game thread) drains the queue.

## Finding: the 50 ms tick breaks the Lua state
Runs with the tech menu open and the harness reading its state twice a second:
- Old code (polling) on origin/main, 50 ms tick: crash after about 160 s (`luaH_getshortstr` in `push_enumproperty`), run `20261018-173210-49ed`.
- New code with 50 ms tick: crash or JSON garbage (`attempt to compare number with function`) after 100 to 250 s, runs `20261018-164721-aefb`, `-165450-c9ee`, `-172159-771e`, `-172912-2d86`.
- New code with `TICK_MS = 100`, labels refreshed every 500 ms and only when changed: pass for 300 s, run `20261018-173614-d910`.
Cause [theory]: the async loop thread and the game thread both run Lua in one state (known: issue #163, PR #166). A faster tick and a refresh that touches many objects each tick raise the chance.
The click hook makes the 50 ms tick unneeded. So `TICK_MS` is back at 100 ms.

## PolicyMenu port (2026-10-18)
The mod PolicyMenu (F7, `mod/PolicyMenu/`) uses the same pattern as the tech tree menu. Issue: see the PR of branch `fix/policymenu-click-hooks`.
- [known] The pak `policymenu_P.pak` holds 20 `Border` widgets named `PolicyButton<N>` (clear brush) and the title. The old `Button` and `TextBlock` pairs are gone.
  The pak also holds `WBP_ClickButton` (same cooked files as `techmenu_P.pak`). `make_widget.py` makes the menu, the cook copies both assets into `modtools/work/policymenu`.
- [known] Lua: `attachSlots` finds the Borders by name, calls `clickhooks.attach` for each, then one `bind_texts`. The colour uses `SetColorAndOpacity`, set only when the signed state changes.
- [known] The key callback only sets a flag. The existing `LoopAsync` (`tick_ms = 100`, was `poll_ms = 40`) drains the click queue on the game thread. No new loop.
  The hook callback only queues. A click on a policy calls `ManorCore.set_policy_signed`, then the menu refreshes.
- [known] New command `PolicyMenu.press {index}` calls the click handler without the mouse. `PolicyMenu.read` reports `hovered` and `visibility` of the click button (no `pressed`).
- [known] Layout change: the click button is smaller than the old Button. The first button is at about 25 % and 57 % of the screenshot. Both scenarios start the hover scan there.
- [known] Real runs (all pass): `policy-menu` `20261018-201834-1aad` and `20261018-202221-89ac`. New scenario `policy-menu-clicks` (10 real clicks, 10 counted, EXCLUSIVE): `20261018-201957-b8f7` and `20261018-202107-d682`.
- [theory] Not soaked for 5 minutes with the menu open (the tech menu was, run `20261018-173614-d910`). The tick is 100 ms and the labels change only when the state changes, as there.
