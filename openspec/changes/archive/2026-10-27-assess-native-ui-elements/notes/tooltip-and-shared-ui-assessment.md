# Tooltip and shared UI assessment

Scope: `order_tooltip`, the other widget features (not `core/menu.lua`), the shared UI modules, and wiki pages. Read only.
The wiki page `docs/wiki/concepts/native-modding.md` has no widget or UI facts (grep for `/Game/UI`, `_C`, widget, UMG, crash: no match).

## 1. Inventory

| Widget | Class or path | Native or primitive | Where |
|---|---|---|---|
| Public Order tooltip (edited, not made) | `BigTooltip_ApprovalAndPublicOrder_C`, hook on `:updateContents` | native, reused instance | `mod/InvasionMod/Scripts/features/order_tooltip/init.lua:12` |
| Tooltip row (made by the mod) | `/Game/UI/Tooltips/approvalFactorWidget.approvalFactorWidget_C`, `WidgetBlueprintLibrary:Create` | native class, new instance | `order_tooltip/widget.lua:5`, `:36-37` |
| Row list `recentFactors_VB`, `pastFactors_VB`, `current_sum_txt`, `none_txt` | members of the native tooltip | native | `widget.lua:40,50-55` |
| Row texts `DescriptionText`, `ValueText` | members of the native row | native | `widget.lua:41-42` |
| Row arrow Image (found by class name `Image`) | native texture `tiny_arrow_triangle_up`, turned with `SetRenderTransformAngle` | native | `widget.lua:25-31,44`; `openspec/changes/archive/2026-10-23-fix-order-tooltip-arrows/notes/arrow.md:9` |
| Value colour (green or red) | `SetColorAndOpacity` with a hard-coded colour | native text block, hand-set colour | `widget.lua:7-14` |
| Banner `genericAchievement_EventMessage_C` | made by `PawnCPP:playEventMessage` | native | `mod/shared/HarnessUi/HarnessUi.lua:3,11` |
| Bottom bar button clone | `/Game/UI/HUD/mainTabButton.mainTabButton_C`, `Create` + `AddChildToHorizontalBox` | native class | `mod/shared/HarnessUiProbe/HarnessUiProbe.lua:181,219-227` |
| Probe overlay: WidgetTree + Border/Button | `/Script/UMG.UserWidget`, `WidgetTree`, `Border`, `Button` via `StaticConstructObject` | primitive | `HarnessUiProbe.lua:271-282` |
| Probe Button + TextBlock (copies style of a game button) | `/Script/UMG.Button`, `TextBlock`; `SetBackgroundColor(template.BackgroundColor)` | primitive, game style copied | `HarnessUiProbe.lua:150-164,159-160` |
| Texture probe: WidgetTree + Image | `/Script/UMG.WidgetTree`, `Image`; PNG loaded at run time | primitive | `mod/shared/HarnessTexProbe/HarnessTexProbe.lua:59-70,90` |
| Game setup row clone | `/Game/UI/Game_Setup/W_Menu_GameSetupSettingEntry.W_Menu_GameSetupSettingEntry_C` | native class | `mod/shared/HarnessGameSetup/HarnessGameSetup.lua:92-97` |
| Game setup screen | `mainMenu_GameSetup_C` (found, not made) | native | `HarnessGameSetup.lua:78` |
| Policy widget probe | `/Game/UI/Development_Tree/policyWidget.policyWidget_C`, `Create` + `AddToViewport` | native class | `mod/shared/HarnessPolicies/HarnessPolicies.lua:223,251-262` |
| Click button (pak widget of the mod) | `/Game/HarnessMod/WBP_ClickButton.WBP_ClickButton_C` (cooked Widget Blueprint in the mod pak) | mod-made asset, not a game asset | `mod/shared/HarnessClickHooks/HarnessClickHooks.lua:9-11,65-70` |
| Telemetry probe dialog | `UserWidget`, `Border`, `VerticalBox`, `TextBlock`, `SizeBox`, `MultiLineEditableTextBox`, `CheckBox`, `HorizontalBox`, `Button` via `StaticConstructObject` | primitive | `mod/shared/HarnessTelemetryProbe/HarnessTelemetryProbe.lua:377,391-425` |
| raid_widget, tech_tree_widget | cooked pak Widget Blueprints (`make_raid_widget.py`, `make_tech_widget.py`); Lua only does `SetText` and `SetColorAndOpacity`; menu shell is `core/menu.lua` (not assessed) | mod-made asset | `features/raid_widget/init.lua:37`; `features/tech_tree_widget/init.lua:30,70,86`; `docs/wiki/architecture/invasion-features.md:96,162` |

Other features under `Scripts/features/` have no widget code in a grep for `StaticConstructObject`, `WidgetTree`, `AddChild`, `/Game/UI`, `/Script/UMG`. Files with matches: `core/menu.lua` (excluded), `order_tooltip/*`, and the shared modules above.

## 2. Catalog of native widget classes and assets already known

In code:
- `/Game/UI/Tooltips/approvalFactorWidget.approvalFactorWidget_C` - `widget.lua:5`
- `BigTooltip_ApprovalAndPublicOrder_C` (`/Game/UI/Tooltips/BigTooltip_ApprovalAndPublicOrder`) - `order_tooltip/init.lua:12`
- `genericAchievement_EventMessage_C` - `HarnessUi.lua:11`
- `/Game/UI/HUD/mainTabButton.mainTabButton_C` - `HarnessUiProbe.lua:181`
- `/Game/UI/Game_Setup/W_Menu_GameSetupSettingEntry.W_Menu_GameSetupSettingEntry_C` - `HarnessGameSetup.lua:92`
- `mainMenu_GameSetup_C` - `HarnessGameSetup.lua:78`
- `/Game/UI/Development_Tree/policyWidget.policyWidget_C` - `HarnessPolicies.lua:223`

In wiki, specs and notes:
- `MainUICPP_C` (HUD; `main_tabs_HB`; `WidgetTree.WhiteTooltipRT`) - `docs/wiki/concepts/engine-limits.md:42,59`
- `/Game/UI/Common/menuButton.menuButton_C` (Close button, hook `DoOnReleased`) - `docs/wiki/architecture/invasion-features.md:170`; `engine-limits.md:43`
- `mainMenu_widget_C` (`/Game/UI/Main_Menu/mainMenu_widget`, Esc menu) - `engine-limits.md:44`; `openspec/changes/archive/2026-10-24-spike-lua-crash-after-spawn/notes/crash-table.md:139`
- `questMessageElaborate_C` (letter banner) - `engine-limits.md:36-38`
- `popupMessageWidget_C` - `openspec/changes/archive/2026-10-24-spike-militia-corpses-and-camp-removal/notes/q2-camp-removal.md:19`
- `mainMenu_GameSetupPresetButton_C`, `HorizontalRadioSelect_C`, `W_MenuSpinner_C` (over `/Script/AutoSettings.Spinner`), `MLGameSetupSettingWidget`, `MLTextBlock` - `openspec/changes/archive/2026-10-23-spike-scenario-template-menu/notes/menu-widgets.md:7-12`
- Texture `/Game/UWG/ui_textures/tiny_arrow_triangle_up` - `arrow.md:9`
- Data table `DT_GameSetupPresets` (thumbnail soft objects) - `menu-widgets.md`

## 3. Styling sources

- Game assets: the row class (frame, fonts, arrow texture), the tooltip, the bottom bar button (frame, size, hover glow: `engine-limits.md:42`) and the Close button (`menuButton_C`). The style comes with the cloned class.
- Style copied from a game widget at run time: `button:SetBackgroundColor(template.BackgroundColor)`, `SetColorAndOpacity(template.ColorAndOpacity)` - `HarnessUiProbe.lua:159-160`.
- Hard-coded: green `{0.35,0.8,0.3,1}` and red `{0.85,0.25,0.2,1}` - `widget.lua:7-10`. `rows.lua:18` says "as in the game", but the values are not read from a game asset. Probe tint `{1.0,0.6,0.6,1}` - `HarnessUiProbe.lua:231`. Overlay `{0,0,0,0.35}` - `HarnessUiProbe.lua:281-282`.
- Run-time PNG (not a game asset): `ImportFileAsTexture2D`, 9-slice `Brush.DrawAs = 1` - `HarnessTexProbe.lua:90,105-106`; `engine-limits.md` section "Menu pictures". Owner decision 2026-10-21 allows it.
- Fonts: no font is set in the code searched. A custom font was not tried (`engine-limits.md`, "Not known").

## 4. Recorded constraints that limit native reuse

- `Button.OnClicked:Add` on a Button made with `StaticConstructObject` crashes (access violation `0x70`): `docs/wiki/concepts/engine-limits.md` (menu section); `DANGEROUS_ACTIONS.md` ("Never call `Button.OnClicked:Add` on a Button made at run time"). This is why `WBP_ClickButton` exists (`HarnessClickHooks.lua:1-5`).
- A cooked mod widget has no graph, so its Button has no hookable click: `HarnessClickHooks.lua:2`.
- Check a `GetChildAt` result with `IsValid` before a call: `DANGEROUS_ACTIONS.md` (change `fix-order-tooltip-arrows`, #462). `widget.lua:26-29` calls `GetClass` on a `GetChildAt` child with no `IsValid`. This is a possible crash risk to review.
- Reads of Brush and soft-object structs can crash: `HarnessTexProbe.lua:5`, `HarnessUiProbe.lua:5`; `DANGEROUS_ACTIONS.md` (soft object fields).
- A Lua error inside a UObject call can crash UE4SS (#323, #327): `HarnessClickHooks.lua:22-24`.
- Texts of a cloned row are overwritten by its defaults if written before the add: `widget.lua:39`; `engine-limits.md` (spike #422).
- A new row shows a down arrow until the angle is set: `widget.lua:23-24`.
- Post callbacks of Blueprint hooks never fired. Use a pre hook and a delay: `engine-limits.md` (spike #422).
- The tooltip list is rebuilt on every open, so the apply must repeat: `engine-limits.md` (spike #422); `invasion-features.md:126`.
- Blueprint classes load late: `order_tooltip/init.lua:48`.
- A mod pak asset needs the asset registry call to load: `HarnessClickHooks.lua:30-31`.
- `SetPositionInViewport` after an anchor sends a widget top left: `engine-limits.md:43`.
- `SetDesiredSizeOverride` alone did not size a new image: `engine-limits.md` (menu pictures).
- Custom texture from a pak and custom font: not tried (`engine-limits.md`).
- A pre hook cannot cancel a native UFunction: `engine-limits.md:36`.

## 5. Verdict per area

| Area | Verdict | Reason |
|---|---|---|
| `order_tooltip` | native | Reuses the native tooltip and makes native row instances. Only the green and red colours are hand-set (`widget.lua:7-10`). No primitive is built. |
| `HarnessUi` (banner) | native | Native banner class through `playEventMessage` (`HarnessUi.lua:3`). |
| `HarnessGameSetup`, `HarnessPolicies` | native | Create game classes (`HarnessGameSetup.lua:92`, `HarnessPolicies.lua:251`). |
| `HarnessUiProbe` | mixed | Clone of `mainTabButton_C` (native) plus overlay and button from UMG primitives (`:150-164,271-282`). |
| `HarnessTexProbe`, `HarnessTelemetryProbe` | primitive | Only `/Script/UMG.*` classes (`HarnessTexProbe.lua:59-70`; `HarnessTelemetryProbe.lua:391-425`). Both are probe code. |
| `HarnessClickHooks`, `raid_widget`, `tech_tree_widget` | mod-made cooked widgets | Not native and not run-time primitives. They are cooked assets of the mod pak. What they use inside was not checked here. Their shell (`core/menu.lua`) is assessed by another agent. |

Summary: outside the menu shell, the shipped feature UI that edits a game screen (`order_tooltip`) is native. Run-time primitives appear only in probes. The mod menus use cooked mod widgets.
