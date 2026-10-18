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
