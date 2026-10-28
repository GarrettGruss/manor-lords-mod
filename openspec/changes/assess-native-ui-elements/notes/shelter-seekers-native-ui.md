# Shelter Seekers: how it reuses native game UI

Source note: Shelter Seekers is a third-party mod. We read a decompiled copy for study only. Check its license before you copy any code. Copy the technique, not the code. The decompiled names (`L0_1` and so on) are generated; the pseudo-code below uses readable names.

Safety note: the mod hooks the save functions `IoHandler:SaveGameToSlot` and `PawnCPP:requestSaveFile` (and `onSavingFinished`) in `event.lua:2522-2600`. In the decompiled files I found these as `RegisterHook` paths only, with no direct call. It also uses a "checkpoint" idea around saves and writes under `/ManorLords/Saved/SaveGames/` (`event.lua:203`). Save calls are forbidden for us (DANGEROUS_ACTIONS.md). Do not copy that part.

File refs are to the decompiled folder `shelter_seekers_decompiled`. Line numbers are from the decompiled text and may be a few lines off.

## 0. Common helpers

- `isValid(obj)`: `pcall(obj:IsValid())`, true only if the call worked and returned `true` (`ui.lua:~25-40`, `notifications.lua:~10-30`). Used before nearly every widget call. Compare with our rule: check `IsValid` before a method call on a child widget.
- Widget identity: compares `GetAddress()` of the hook `self` with the stored widget, so a hook only reacts to its own widget (`ui.lua:~710-760`).
- Game-thread hand-off: the click handler disables the button, then runs the real work in `ExecuteInGameThread` (`notifications.lua:~640-700`).
- Every `Create` and `StaticFindObject` result is asserted with `isValid` and a clear message ("vanilla widget class or factory is not loaded").

## 1. Create a native widget: MessageFullscreen / MessageTutorialFullscreen

Element: `/Game/UI/Elements/MessageFullscreen.MessageFullscreen_C` (the tutorial variant is only checked, not created).

Steps:
1. Get the class: `StaticFindObject("/Game/UI/Elements/<Name>.<Name>_C")`. Get the factory: `StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")` (`ui.lua:1086-1100`).
2. Guard: the game must be loaded and paused. The code first looks for any live `MessageFullscreen_C` or `MessageTutorialFullscreen_C` with `FindAllOf` and `IsInViewport`. It refuses to open if a vanilla one is on screen (`ui.lua:1040-1080`). It also checks pause menu and big panel state.
3. Remember input state (`isUsingUI`, cursor, mouse-over) so it can restore it later (`ui.lua:1150-1165`).
4. Create with `factory:Create(player, class, playerController)`, then `SetIsEnabled(false)`.
5. Clear data fields so the widget does not run its quest logic: `Quest.ID = -1`, `tutorial = false`, `isLetter = false` (for the tutorial variant: `header_key` and `descr_key` set to `FName("None")`).
6. `widget:AddToViewport(2000)` (`ui.lua:~1204`).
7. Set text and art (sections 3 and 4), hide unused parts (`objectives_sb`, `rewards_HB`, `signature_HB`, `timeLeft_HB`, `Time_VB`, `tutorial_options`, `checkbox_SkipTutorials`) with `SetVisibility` (`ui.lua:1380-1540`).
8. Take over input: `player:setIsUsingUI(true)`, `controller.bShowMouseCursor = true`, `SetInputMode_UIOnlyEx` (`ui.lua:~880-890`). Enable the buttons.

Pseudo-code:
```
cls     = StaticFindObject(widgetPath)
factory = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
w = factory:Create(player, cls, controller)
w:SetIsEnabled(false)
w.Quest.ID = -1; w.tutorial = false; w.isLetter = false
w:AddToViewport(2000)
hideUnusedParts(w); setTexts(w); bindButtons(w)
controller:SetInputMode_UIOnlyEx(...)
```

Close (`ui.lua:~55-120`): `widget:RemoveFromParent()` (if valid), then restore `setIsUsingUI(old)` and `SetInputMode_GameAndUIEx(...)`, each in its own `pcall`, errors collected and logged.

Risks: it touches input mode and pause state; a wrong restore can lock input. It relies on private widget field names (`Quest`, `isLetter`, `graphic`). Game updates can rename them. No crash-list item is hit here, but `FindAllOf` results are used only after `IsValid`.

## 2. Catch clicks without a Lua closure on the button (the "trampoline")

Elements: `Button_Accept`, `Button_Decline`, `MD_NaviAutoButton_Accept`, `MD_NaviAutoButton_Decline` on MessageFullscreen; `MainButton` on questMessageElaborate; the arrival `mainTabButton`.

Steps:
1. For each of `OnClicked`, `OnPressed`, `OnReleased` (and hovered events on some buttons): `delegate:Clear()`, then `GetBindings()` and assert it is empty (`ui.lua:830-860`, `notifications.lua:~490-515`).
2. Bind the delegate to an existing native UFunction by name, not to a Lua function: `button.OnReleased:Add(targetObject, FName("switchToEventGUIStyle"))` (`ui.lua:~655-670`, helper `bindNativeFunction`). Then `GetBindings()` must be non-nil.
   - Accept uses the native function `switchToEventGUIStyle`; Decline uses `setGUIToLetterStyle` (`ui.lua:795-815`).
   - Notification and arrival buttons use `MainUICPP:updateTranslation` (OnPressed) and `MainUICPP:updateOnScreenTextVisibility` (OnReleased), with the live `MainUICPP` as target (`notifications.lua:~830-850`, `arrival_panel.lua:~1100-1150`).
3. Catch the call with `RegisterHook("/Game/UI/Elements/MessageFullscreen.MessageFullscreen_C:<fn>", cb)`. In `cb`: `self = ctx:get()`, check `isValid(self)` and the address equals our widget, check our `ready` flag (`ui.lua:~700-790`).
4. For HUD buttons the hook is on `MainUICPP_C:updateTranslation` and `...:updateOnScreenTextVisibility`. Press is detected when `button:IsHovered()` and `button:IsPressed()`; release counts as a click only if the button is no longer pressed but still hovered (`notifications.lua:~530-700`).
5. In the callback: set `ready=false`, `SetIsEnabled(false)`, then `ExecuteInGameThread(function() pcall(userCallback) end)`. On failure the button is re-enabled.

Pseudo-code:
```
for each ev in {OnClicked, OnPressed, OnReleased}: button[ev]:Clear()
button.OnReleased:Add(widget, FName("setGUIToLetterStyle"))   -- native no-op target
RegisterHook(cls..":setGUIToLetterStyle", function(ctx)
  local w = ctx:get()
  if isValid(w) and addr(w)==addr(ourWidget) and ready then
    ready=false; w:SetIsEnabled(false)
    ExecuteInGameThread(function() onChoice("REJECT") end)
  end end)
```

Why it seems to work this way: the delegate is bound with `(object, FName)` of a real UFunction. This is the engine-native form. It avoids `Button.OnClicked:Add(luaFunction)`, which is on our crash list for run-time buttons. The buttons here are children of a widget made by `Create`, not buttons made with `StaticConstructObject`.

Risks:
- The native target functions (`switchToEventGUIStyle`, `setGUIToLetterStyle`, `updateTranslation`, `updateOnScreenTextVisibility`) still run their own game code when the delegate fires. The mod depends on that being harmless. `updateTranslation` and `updateOnScreenTextVisibility` can be called by the game at other times, so the hook must check the button state (it does).
- A hook on a shared class function runs for every instance. The address check is required.
- DANGEROUS_ACTIONS: `Button.OnClicked:Add` is never called with a Lua function in this code (I found only `Clear`, `GetBindings` and `Add(object, FName)`). This is the main point to copy. Needs a spike to confirm that `Add(object, FName)` itself is safe in our game build.

## 3. Set text on native widgets

- MessageFullscreen: `widget.Title1`, `widget.message_txt` (or `messageTxt`), `choiceA`, `choiceB` take `SetText(FText(str))` (`ui.lua:1380-1420`). Text is only set after the widget is created and before it is enabled.
- ChoiceTooltip: `tooltip.localizedTextBox_C_1.TextBlock_16:SetText(FText(str))` and `SetAutoWrapText(true)` (`ui.lua:~370-400`).
- questMessageElaborate: `contractAvailable_txt`, `numMsgs_txt` (`notifications.lua:~430-450`).
- genericAchievement_EventMessage: `main_txt:SetText`, `bottomTxt:SetText`, `bottomTxt:SetAutoWrapText(true)`, `bottomTxt.WrapTextAt = 880` (`notifications.lua:~180-200`).
- Always `FText("...")`, and always after an `isValid` assert on the text control.

Risks: field names are private to the widget blueprint. Assert them with a clear message so a game update fails loudly.

## 4. Custom art with ImportFileAsTexture2D

Used in `ui.lua:1229-1300` and `arrival_panel.lua:~860-900`.

Steps:
1. `lib = StaticFindObject("/Script/Engine.Default__KismetRenderingLibrary")`, assert valid.
2. `tex = lib:ImportFileAsTexture2D(worldContext, filePath)`, assert `isValid(tex)` ("check path and JPEG decoding").
3. Store the texture on the widget (`widget.mainGraphicTexture = tex`) so it is not garbage collected.
4. `image:SetBrushFromTexture(tex, false)`, `image:SetColorAndOpacity({R=1,G=1,B=1,A=1})`, `image:SetVisibility(...)`.
5. All of it is inside two nested `pcall`s. A failed import logs "ARTWORK unavailable; offer continues" and the UI still opens.
- Files are loaded from a mod folder (`../UIAssets/arrival-status/panel-background-v1.png`, `family-emblem-64.png`) and from a per-offer `artwork_path` (JPEG).
- The native control receiving the art is `widget.graphic` on MessageFullscreen.

Risks: world context must be a valid object. Big files cost memory and time on the game thread. The texture needs a strong reference.

## 5. Reuse a native widget as a piece of art or layout: HUD notifications

### 5a. genericAchievement_EventMessage (status banner)
Steps (`notifications.lua:115-260`): get `mainUI.C_Gameplay` (the HUD canvas); `factory:Create(player, class, controller)` for `/Game/UI/Elements/genericAchievement_EventMessage.genericAchievement_EventMessage_C`; take only `ribbon_border` out of the created widget; set `main_txt` and `bottomTxt`; `ribbon_border:RemoveFromParent()`; `SetVisibility(3)`, `SetRenderOpacity(1)`; `C_Gameplay:AddChildToCanvas(ribbon_border)`; then `SetAnchors`, `SetAlignment`, `SetPosition`, `SetSize`, `SetAutoSize(false)` on the returned canvas slot. The "donor" widget is kept in the mod state so its children stay alive (the border is re-parented out of it).

### 5b. questMessageElaborate (clickable notification card)
Steps (`notifications.lua:400-960`): `Create` the class `/Game/UI/Elements/questMessageElaborate.questMessageElaborate_C` as donor. Take `MainButton` and `contractAvailable_txt`. Assert both share one parent. Strip decoration by `RemoveFromParent` on `numMsgs_txt`, `MD_NaviAutoButton`, `flareA`, `flareB`. Detach the parent panel, `SetVisibility(4)` (hit-test invisible) for the panel and `3` for the button. Set `SetToolTipText`. `button:GetChildAt(0):SetVisibility(3)`. Bind clicks as in section 2. Wrap the panel in a `SizeBox` (805.7 x 204) made with `StaticConstructObject(SizeBox class, donor)`, `SetContent(panel)`, and add to `C_Gameplay` with canvas anchors at top-center.

Risks: `GetChildAt(0)` is called here after an `isValid` assert on the button, but there is no `IsValid` check on the returned child before `SetVisibility` (`notifications.lua:~820`). This matches the crash-list item for unchecked `GetChildAt`. We must check the child first. Re-parenting a child out of a native widget can leave the donor in a half-built state. Layout numbers are copied from the native widget.

## 6. ChoiceTooltip as a custom tooltip

Element: `/Game/UI/Tooltips/ChoiceTooltip.ChoiceTooltip_C` (`ui.lua:365-640`, also `arrival_panel.lua:~945`).

Steps:
1. `cls = StaticFindObject(path)`; per button `tip = factory:Create(controller/world, cls, player)`; assert valid.
2. Remember `tip:GetAddress()` in a table with the tooltip text.
3. Set text: `tip.localizedTextBox_C_1.TextBlock_16:SetText(FText(t))`, `SetAutoWrapText(true)`. Hide `objectives_VB`, `Time_VB`, `timeLeft_HB`, `questTimeRemaining`, `focus-txt_1`.
4. `button:SetToolTip(tip)`; assert `button.ToolTipWidget` is still valid. Fallback: `button:SetToolTipText(FText(...))` if creation fails.
5. `RegisterHook("...ChoiceTooltip_C:Construct", cb)`: the game rebuilds the tooltip on hover, so the hook sets the text again for known addresses (`ui.lua:~475-540`). The refresh is inside `pcall`.
- Cleanup walk (`ui.lua:~280-364`): a recursive function visits `GetChildrenCount`/`GetChildAt` of a widget and clears quest content. It uses the `isValid` helper on `WidgetTree` and `RootWidget`.

Risks: the Construct hook fires for all tooltips in the game, so filter by address. The recursive `GetChildAt` walk: check `isValid` on each child (this code does it through the `isValid` helper at the top of the recursion).

## 7. RegionDropdown as a destination picker

Element: `/Game/UI/Common/RegionDropdown.RegionDropdown_C` (`region_selector.lua:200-340`).

Steps:
1. `StaticFindObject(path)`; if invalid, `LoadAsset(path)` then find again.
2. `dd = factory:Create(...)`; assert `dd.RegionComboBox` valid.
3. Clear native behavior: `OnSelectionChanged:Clear()`, `OnOpening:Clear()`, `OnGenerateWidgetEvent = nil`, `ClearOptions()`.
4. For each row: `AddOption(label)`; remember the index of the default. `RefreshOptions()`, `SetSelectedIndex(i)`.
5. `dd:RemoveFromParent()`; `SetVisibility(0)`; `SetIsEnabled(true)`.
6. Add into a native container: `message_txt:GetParent():AddChild(dd)` (the parent of the message text block of the MessageFullscreen). Set slot padding 24/12. `SetToolTipText`.
7. Read the choice by polling: `combo:GetSelectedIndex()` inside `Refresh`/`Read` when the user presses Accept (`region_selector.lua:~90-150`). No change event is bound. Accept is disabled when the selected row is not allowed.
8. Close: `combo:RemoveFromParent()` if valid.

Risks: `LoadAsset` may block on the game thread. `GetParent()` result is asserted valid before use. Polling avoids a delegate bind on a run-time widget. This is the safest part to copy.

## 8. mainTabButton and W_HUD_MercenaryCompanyV2 as HUD pieces

Element: `/Game/UI/HUD/mainTabButton.mainTabButton_C` and `/Game/UI/HUD/W_HUD_MercenaryCompanyV2.W_HUD_MercenaryCompanyV2_C` (`arrival_panel.lua:1080-1260`).

Steps:
1. `Create` both with the factory (class from `StaticFindObject`), keep them in a `donors` list. Assert the button valid, and `Image_58` valid on the mercenary widget.
2. Button: `SetIsEnabled`, clear `OnClicked/OnPressed/OnReleased/OnHovered/OnUnhovered`, assert no bindings. Bind `OnPressed` to `MainUICPP:updateTranslation` and `OnReleased` to `MainUICPP:updateOnScreenTextVisibility`, then verify binding count (same trampoline as section 2).
3. Mercenary widget: only `Image_58` (a background image) is used. It is re-parented into the mod's own `CanvasPanel` with `AddChildToCanvas`, set to 224x72, white color. The rest of the native widget is not shown.
4. The arrival panel position is computed from the real mercenary panel, to avoid overlap: it reads `hud.MercenaryPanelV2_VisibilityBox`, `GetChildrenCount`, `GetChildAt(0)`, `.MercenaryContainer` (`arrival_panel.lua:380-470`). Each step is checked by `Valid` and a layout test. Fallback: a fixed `280` offset. It uses `SlateBlueprintLibrary` and `WidgetLayoutLibrary` for screen positions.
5. Open-UI check (`arrival_panel.lua:205-250`): panel hides when the pause menu or `IsDynamicBigPanelVisible` is true, or any live `MessageFullscreen_C`, `MessageTutorialFullscreen_C` or `mercenaryScreen_C` is in the viewport (`FindAllOf` + `IsInViewport`).

Risks: this reads private HUD layout. `GetChildAt(0)` is guarded by `Valid` and a layout-parent check. `Image_58` may change in a game update.

## 9. What it still builds from primitives, and why

- `StaticConstructObject(StaticFindObject("/Script/UMG.<Type>"), owner, FName("ShelterArrival_<n>"))` for `CanvasPanel`, `Image`, `ScrollBox`, and `SizeBox` (`arrival_panel.lua:820-840`, `notifications.lua:865-880`). Types seen: `CanvasPanel`, `Image`, `ScrollBox`, `SizeBox`. A `Spacer` is a native child of questMessageElaborate that is hidden, not built.
- They fill gaps the native widgets cannot cover: a free-position root panel, a mod-art background and emblem (imported textures), a scrolling body for the arrival list, and fixed-size wrapping around a re-parented native card.
- No `Button` is made from primitives. All buttons are native (cloned by `Create`). This is probably on purpose: it avoids `OnClicked:Add` on a run-time button, which crashes our game.
- Text uses the native typography: the arrival text blocks are taken from a created ChoiceTooltip (`arrival_panel.lua:~940-960`, "native arrival typography unavailable"), so fonts match the game style.

Risks: `StaticConstructObject` on UMG types is safe in this mod's usage but is not on our crash list; test it in a spike. Pass a valid outer object (the donor or HUD) and give unique `FName`s.

## 10. Summary table

| Technique | Instance source | Added to screen | Click catch |
|---|---|---|---|
| MessageFullscreen | `WidgetBlueprintLibrary:Create` | `AddToViewport(2000)` | `Add(obj, FName)` to native fn + `RegisterHook` on it |
| questMessageElaborate | `Create`, re-parent `MainButton` panel | `C_Gameplay:AddChildToCanvas` | MainUICPP trampoline + `IsHovered/IsPressed` |
| genericAchievement_EventMessage | `Create`, take `ribbon_border` | `C_Gameplay:AddChildToCanvas` | none (display only) |
| ChoiceTooltip | `Create` per button | `Button:SetToolTip` | `RegisterHook ...:Construct` to refresh text |
| RegionDropdown | `StaticFindObject` / `LoadAsset` + `Create` | `AddChild` into message parent | poll `GetSelectedIndex` |
| mainTabButton / MercenaryCompanyV2 | `Create`, use button and `Image_58` | `AddChildToCanvas` in own CanvasPanel | MainUICPP trampoline |

## 11. Ideas to test in our own spike

- Is `Button.OnReleased:Add(obj, FName("nativeFn"))` safe in our build, and does the target function do anything bad when called?
- Do the hooks on `MainUICPP:updateTranslation` and `updateOnScreenTextVisibility` fire on button press/release as the mod assumes?
- Prefer polling (`GetSelectedIndex`, `IsPressed`) over new delegates on run-time widgets.
- Always `IsValid` any widget returned by `GetChildAt` (the mod misses this once, see section 5b).
- Do not copy anything that touches save hooks.
