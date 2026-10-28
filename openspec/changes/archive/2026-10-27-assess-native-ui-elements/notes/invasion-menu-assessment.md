# Invasion Mod menu: native or primitive?

Read-only assessment. Paths are relative to the repo root.

## 1. Inventory

| Widget | Class or path | Kind | Where |
|---|---|---|---|
| Bottom bar button (clone) | `/Game/UI/HUD/mainTabButton.mainTabButton_C` | native class | mod/InvasionMod/Scripts/core/menu.lua:23, 442-451 |
| Bottom bar panel (parent) | `main_tabs_HB` in `MainUICPP_C` | native instance (reused) | menu.lua:31, 349-353, 464, 448 |
| Close button | `/Game/UI/Common/menuButton.menuButton_C` | native class | menu.lua:24, 177-188 |
| Game Esc menu (closed again, not drawn) | `mainMenu_widget_C` | native instance (reused) | menu.lua:26, 511-519 |
| Bar label text | `/Script/UMG.TextBlock` | primitive | menu.lua:360 |
| Backdrop / click blocker | `/Script/UMG.UserWidget` + `WidgetTree` + `/Script/UMG.Button` | primitive | menu.lua:137-141 |
| Menu content (all 4 menus) | cooked pak Widget Blueprint `/Game/HarnessMod/WBP_*` | mod asset, built from primitives | raid_widget/init.lua:78; tech_tree_widget/init.lua:238; liege_influence/init.lua:289; scenario_settings/init.lua:495 |
| Content parts: panel, text, layout | `unreal.Border`, `TextBlock`, `VerticalBox`, `HorizontalBox`, `SizeBox`, `CanvasPanel` | primitive | mod/InvasionMod/ue/make_scenario_settings_widget.py:51-91; make_tech_widget.py:42-89; make_liege_widget.py:33-44; make_raid_widget.py:40-55 |
| Content click buttons | `WBP_ClickButton` (mod asset, put into a Border) | mod asset (primitive Button inside) | mod/shared/HarnessClickHooks/HarnessClickHooks.lua:1-10; make_tech_widget.py:48 |
| Seed of the pak widgets | `/MoverExamples/Widgets/ControlsDisplay` (engine sample, only copied as an empty shell) | engine, not a game asset | make_liege_widget.py:7; make_raid_widget.py:8; make_tech_widget.py:7 |
| Scenario settings: seed widget name `StackBox_51` | name of a node in the copy | n/a | make_scenario_settings_widget.py:14 |

Not part of the menu framework, but native reuse elsewhere: the order tooltip clones `/Game/UI/Tooltips/approvalFactorWidget.approvalFactorWidget_C` (mod/InvasionMod/Scripts/features/order_tooltip/widget.lua:5; docs/wiki/concepts/engine-limits.md:118). The scenario settings menu reads `W_HUD_LordPanel_V2_C` (scenario_settings/init.lua:185). Wiki records a spike that cloned the game's option widgets (Spinner, GridPanel) for a template menu (docs/wiki/concepts/engine-limits.md:79), but the shipped menu does not use them.

## 2. Where styling comes from

- Game assets: only through the cloned classes. `mainTabButton_C` keeps its own icon and look (menu.lua:23). `menuButton_C` keeps its serif font and fleur-de-lis (menu.lua:7-8). The label text key `Close` is the game's own text (menu.lua:385-388).
- Hard-coded in Lua:
  - backdrop colour black, alpha 0.55 (menu.lua:20, 142);
  - z-orders 450 / 500 / 510 (menu.lua:18-19, 183);
  - bar label scale 0.5, white colour, centre and bottom alignment (menu.lua:32-33, 365-373);
  - Close anchor (0.5, 0.95) (menu.lua:25, 184-185);
  - disabled tint of click buttons (liege_influence/init.lua:217-229; tech_tree_widget/init.lua:70).
- Hard-coded in the pak builders: parchment `LinearColor(0.62,0.50,0.30,0.97)`, ink `(0.10,0.06,0.02,1)`, text width 760 (make_scenario_settings_widget.py:17-19, 68-69); panel colour `(0.05,0.04,0.03,0.85)` (make_tech_widget.py:86; make_raid_widget.py:41); transparent border brush `(0,0,0,0)` (make_tech_widget.py:50). The scenario settings header says: "Look: parchment colours (a Border brush colour and dark text). The PNG images of the mockup are not in this pak yet." (make_scenario_settings_widget.py:7).
- No game font, brush, style asset or texture is referenced by the content widgets (grep of `Font`, `Brush`, `/Game/UI` in mod/InvasionMod/ue/make_*.py finds none). Wiki: "Not known: a cooked pak texture and a custom (blackletter) font" (docs/wiki/concepts/engine-limits.md:54). Owner decision: PNG images may be loaded at run time (docs/wiki/concepts/engine-limits.md:55).

## 3. Hooks and parents

- Parent: finds the HUD with `FindFirstOf("MainUICPP_C")` (menu.lua:464), finds `main_tabs_HB` (menu.lua:349-353, depth first search at 331-347), and appends the cloned button with `AddChildToHorizontalBox` (menu.lua:448). Polled every 1000 ms; re-added after a game load (menu.lua:21, 461-498, 611).
- Hooks on the game classes, matched by widget name so only our buttons act: `mainTabButton_C:HandleClicked`, `:HandleHovered` (menu.lua:416-423); `menuButton_C:DoOnReleased`, `:OnMouseEnter` (menu.lua:425-432).
- Menu content, backdrop and Close button go to the viewport with `AddToViewport` (menu.lua:145, 183, 303), not into a game screen.
- Esc: key bind (menu.lua:603); the game's `mainMenu_widget_C` is closed again with `continue()` or `DoCloseAndHideSelf` (menu.lua:518-519).
- Pause: `pauseGame`, `unPauseGame`, `changeGameSpeed` on the player pawn (menu.lua:226, 240-241).

## 4. Constraints recorded in the repo

- `Button.OnClicked:Add` on a run-time Button crashes the game: DANGEROUS_ACTIONS.md:26. Details: openspec/changes/archive/2026-10-21-add-mod-menu-access-rule/notes/menu-findings.md:6 ("Do not bind a delegate on a widget made with `StaticConstructObject`"). This pushed the design to hook game classes (`HandleClicked`, `DoOnReleased`) and to a pak `WBP_ClickButton` whose event is hookable (HarnessClickHooks.lua:3-5; make_tech_widget.py:48 "a Button here is not").
- A cooked Blueprint of ours has no graph, so a Button inside it has no hookable click (HarnessClickHooks.lua:2).
- Click blocking: a full-screen Button blocks a click, a Border does not (menu.lua:5-6; docs/wiki/concepts/engine-limits.md:46). This is why the backdrop is a primitive Button (menu.lua:140).
- Fonts and textures from a pak not tried (docs/wiki/concepts/engine-limits.md:54).
- Clone problems: a cloned bar button has no icon of its own, so a TextBlock label is added (menu.lua:355); a cloned option widget shows only "label" until set up (docs/wiki/concepts/engine-limits.md:79); a preset button made by Lua cannot select a preset (same line).
- Widget class rules: LoadAsset does not load a mod pak asset; the asset registry `GetAsset` does (menu.lua:75-91).
- Game widgets can be fragile: `GetClass` on an unchecked child crashed (DANGEROUS_ACTIONS.md, "Check a widget returned by `GetChildAt`").
- "Only this module makes a mod menu widget" (menu.lua:14; docs/wiki/architecture/invasion-mod.md:38).

## 5. Verdict: mixed

The menu frame is native: the bottom bar button is a clone of `mainTabButton_C` inside the game's own `main_tabs_HB`, and the Close button is the game's `menuButton_C`. The content of every menu, the backdrop and all colours are primitives (Border, TextBlock, boxes, Button) with hard-coded colours, and no game font, brush or texture is used. The crash of `OnClicked:Add` and the missing hookable click on primitives explain why clicks use game-class hooks and a mod `WBP_ClickButton`.
