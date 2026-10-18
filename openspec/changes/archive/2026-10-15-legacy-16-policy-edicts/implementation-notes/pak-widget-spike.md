# Pak widget spike (issue #60, option c)

Date: 2026-10-13. Result: a cooked Widget Blueprint in a pak was loaded, created and shown in the real game. A screenshot shows it.
Screenshot (run folder, git-ignored, 6 MB): `runs/20261014-003105-d53c/screenshots/policy-menu.png`.
It shows the text "Policy menu" and grey buttons ("Strict fasting" and two more, partly hidden). A Windows firewall pop-up from `EpicGamesLauncher` (started by the UE editor) covers the middle of the picture. It is not from the game or the mod.
Tags: [known] has evidence from this spike. [theory] is not tested.

## Steps and results
1. [known] Project: Blueprint-only UE 5.5.4 project `ManorLords`, in `C:\Users\garre\development\mlm-ue\ManorLords` (outside the repo). Sources in `mod/PolicyMenu/ue/` (`ManorLords.uproject`, `Config/*.ini`, `make_widget.py`). Copy them to the workspace folder to rebuild.
2. [known] Headless editor works: `UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=<file> -unattended -nullrhi`.
3. Widget tree from Python. This was the gate.
   - [known] `WidgetBlueprintFactory` + `AssetTools.create_asset` makes a WidgetBlueprint, but its tree has no root widget.
   - [known] `WidgetTree` is found with `unreal.find_object(bp, "WidgetTree")`. Its `RootWidget` is protected: Python cannot set it. There is no `construct_widget` and no `widget_tree` property.
   - [known] Workaround: duplicate a stock engine widget that already has a root (`/MoverExamples/Widgets/ControlsDisplay`, plugin `MoverExamples` enabled in the .uproject). Find the root as the outer of a child's slot. `clear_children`, `new_object(TextBlock/Button, tree, name)` and `add_child` then work. The widget names have random suffixes (for example `StackBox_51`), found from the name table of the .uasset.
   - [known] The copied graph refers to `StackBox_51`. The seed widget stays in the tree (it holds the menu items), and the EventGraph is removed with `BlueprintEditorLibrary.remove_graph`. Then the compile has no error.
   - [theory] A cleaner source asset (or a C++ helper) would remove the leftover functions of the copy (`GatherInputInfo`; the cooked asset still imports `/Script/EnhancedInput`). The game loaded it without problems.
4. [known] Cook: `UnrealEditor-Cmd.exe <uproject> -run=cook -targetplatform=Windows -unversioned -nopak -skipeditorcontent`. It takes about 8 minutes (it also cooks the plugin content) and prints unrelated "Content is missing from cook" errors for Landmass packages. The result `Saved/Cooked/Windows/ManorLords/Content/HarnessMod/WBP_PolicyMenu.uasset` (7.7 KB) and `.uexp` (9.8 KB). Imports are engine classes only.
5. [known] Pack: copy both files to `modtools/work/policymenu/ManorLords/Content/HarnessMod/`, then `pakmod.py build policymenu` (repak, V11, mount `../../../../../docs/`). The pak is `mod/PolicyMenu/paks/policymenu_P.pak` (18 KB). The AES key is only needed by the tool wrapper. It was never printed or written.
6. Lua (`mod/shared/HarnessPolicyMenu`, commands `menu_pak_show`, `menu_pak_read`, `menu_pak_hide` in `HarnessActions`).
   - [known] `LoadAsset` does not load an asset of a mod pak. It gives no error and `StaticFindObject` still finds nothing. Reason (theory): it needs the asset registry, and the pak has no registry entry.
   - [known] This works: `AssetRegistryHelpers:GetAsset(FAssetData)` with a table `{PackageName, PackagePath, AssetName, AssetClassPath={PackageName=/Script/UMGEditor, AssetName=WidgetBlueprint}}`. Then `StaticFindObject("/Game/HarnessMod/WBP_PolicyMenu.WBP_PolicyMenu_C")` finds the class.
   - [known] `WidgetBlueprintLibrary:Create(controller, class, controller)`, `AddToViewport(500)`, `SetPositionInViewport` work. `IsInViewport` is true.
   - [known] Note: `StaticFindObject` of a package path throws "Name wasn't long". Wrap it in `pcall`.
7. [known] Real game: scenario `probe-policy-menu-pak` (`--fixture base --pak policymenu`). 4 launches: (1) class not found, (2) and (3) diagnostics, (4) pass with the screenshot. No crash. The pak was removed after each run (`~mods` folder gone).

## Not done
- Click wiring (the Blueprint has no click variables, because the graph was removed). [theory] Poll the `Button` state from Lua (`IsPressed`) or bind a Lua hook, then call `Region:setPolicySigned`.
- Policy names are fixed in `make_widget.py` (POLICIES list). Only 3 buttons.
- The deploy script copies `mod/PolicyMenu/ue` and the pak into the game `Mods` folder. It is small. Move the `ue` folder if this matters.
- Editor-only click-by-click steps were not needed.

## Next steps
Make a clean menu (all policies, icons set from Lua, styled), add the click poll, and make it a releasable mod with the pak in `mod.json`.
