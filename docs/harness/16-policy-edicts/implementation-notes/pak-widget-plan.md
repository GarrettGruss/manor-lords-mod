# Pak widget plan (option c, issue #60)

Date: 2026-10-13. Research only. The game was not started. Nothing was installed.
Tags: [known] has evidence in the repo. [theory] is not tested.

## Question 1: can the widget be made without the editor?
Answer: no, not in a way that fits the criteria. Reasons:
- [known] The repo pipeline (repak, UAssetGUI, `.usmap`) is proven only for one DataTable (`pak-spike-findings.md`). Its open questions list strings, new rows and soft object fields as untested.
- [known] No UE editor is on this PC (`C:\Program Files\Epic Games` is missing).
- [theory] A WidgetBlueprint has a `WidgetTree`, slots, a generated class and a function graph. Writing one by hand as UAssetGUI JSON means hundreds of linked exports and Kismet bytecode. The result would be fragile, and a bad mapping fails silently (see "Traps" in the pak skill). Not recommended.
- [theory] Editing an existing cooked widget (for example `policyWidget`) in UAssetGUI could change texts, colors or sizes. It cannot add a new menu layout. It would also replace the game's own widget for every user of it.

Alternative that needs no editor: a widget built in pure Lua (a `UserWidget` with a `WidgetTree` made in Lua).
- [known] Game cards made in Lua work and a screenshot shows them (`policy-menu.md`, `policy-followups.md`).
- [theory] A new `WidgetTree` with new panels and buttons built in Lua is not tried. It is the cheapest path to "a custom menu in the game plus a screenshot". It is not option c, so it is the user's call.
- A pak data change alongside (for example a new `DT_PolicyTypes` row) is possible with the current pipeline. It adds data only, not layout.

Conclusion: the pak widget (option c) needs the UE 5.5 editor. The user approved it. The editor is not installed, so issue #60 is blocked on the user.

## Question 2: UE 5.5 steps
### A. Facts about the target
- [known] Engine 5.5.4, build `UE5+Release-5.5` (usmap file name in `pak-spike-findings.md`).
- [known] The game paks are `pakchunk0*-Windows.pak`, V11, mount `../../../`, encrypted. There are no `.utoc` or `.ucas` files in `Content\Paks`. So the game uses legacy pak files, not IoStore.
- [known] A plain, unencrypted, uncompressed `<name>_P.pak` in `Paks\~mods\` is loaded by the game, and its assets replace the originals.
- [known] Game asset paths start with `ManorLords/Content/...`. So the project name and the mount point are `ManorLords`, and in-game package paths are `/Game/...`.
- [known] The widgets `policyWidget_C` and `developmentPanelTree_C` exist. A `LogicMods` folder exists in `Paks`.

### B. Project setup
1. [theory] Install UE 5.5.4 (exact version 5.5.4). A Blueprint-only project needs no Visual Studio. Install the Windows target only.
2. [theory] Create a Blank, Blueprint-only project named `ManorLords` (no starter content, no raytracing). The name makes the cooked package paths `/Game/...` map to `ManorLords/Content/...` in the pak.
3. [theory] Put the new asset in a unique folder, for example `/Game/HarnessMod/WBP_PolicyMenu`. A new path does not replace any game asset.

### C. Stub assets
- [theory] Prefer no game references. Use plain `UserWidget`, `Button`, `TextBlock`, `Border`, `VerticalBox`. Then no stub is needed.
- [theory] Clicks do not call game functions in the Blueprint. The Blueprint stores the click in variables (`LastClickedPolicyId`, int, and `ClickCounter`, int). Lua polls them, then calls `Region:setPolicySigned(id, true)`. This is the proven path (`policy-followups.md`). It keeps game classes out of the cook.
- [theory] For game art (policy icons), let Lua set the brush at run time. Do not stub game textures.
- [theory] If a game parent class is wanted (for example `policyWidget_C`), make a stub Blueprint at the same path with the same parent and variables. Exclude the stub from the pak. Risk: signatures must match, else the load fails.

### D. Make the WBP
1. [theory] New Widget Blueprint, parent `UserWidget`, name `WBP_PolicyMenu`.
2. [theory] Layout: root `CanvasPanel`, a `Border`, a title `TextBlock`, a `VerticalBox` with N rows (`Button` + `TextBlock`), one per policy. Name the widgets and tick "Is Variable" so Lua can find them.
3. [theory] Graph: each button `OnClicked` sets `LastClickedPolicyId` and increments `ClickCounter`.
4. [theory] Compile, save, and test with Play in the editor.

### E. Cook and pack
- [theory] Project Settings, Packaging: "Use Io Store" OFF, "Use Pak File" ON, "Generate Chunks" OFF, compression OFF, encryption OFF, signing OFF. Target Windows, Development or Shipping.
- [theory] Cook (File, Cook Content for Windows, or `UnrealEditor-Cmd.exe <uproject> -run=cook -targetplatform=Windows`). Take `Saved\Cooked\Windows\ManorLords\Content\HarnessMod\WBP_PolicyMenu.uasset` and `.uexp` (and `.ubulk` if it appears).
- [theory] Check the cook with UAssetGUI and the game `.usmap` (`pakmod.py tojson`). It must open as a real WidgetBlueprint, not "RawExport".
- [theory] Version risk: the cooked package must match the game's engine version. Use 5.5.4.
- [known] Pack: files under `<work>/ManorLords/Content/HarnessMod/`, then `repak pack --mount-point ../../../ --version V11 <folder> policymenu_P.pak`. The output is unencrypted and goes to `Paks\~mods\`.
- [theory] `pakmod.py build` packs only `fromjson` output today. A small addition (`build --from-folder`) with tests is needed for cooked files.

### F. Deploy and test
- [known] `run.py --scenario <name> --pak policymenu` installs the pak, runs and removes it. Do not copy by hand.
- [known] The launcher hashes the user's saves before and after each run.

### G. Show it from Lua
All [theory] until a spike runs.
1. Find the class: `StaticFindObject("/Game/HarnessMod/WBP_PolicyMenu.WBP_PolicyMenu_C")`. If nil, `LoadAsset("/Game/HarnessMod/WBP_PolicyMenu")`, then find again.
2. Create: `WidgetBlueprintLibrary:Create(pawn, class, controller)`, then `AddToViewport(500)` and `SetPositionInViewport`. [known] These calls work on the game card.
3. Read the Blueprint variables `LastClickedPolicyId` and `ClickCounter`.
4. Click wiring: [known] `OnClicked` cannot be bound from Lua. So a `LoopAsync` poll sees `ClickCounter` change. Lua then calls `Region:setPolicySigned(id, true)` inside `HarnessLog.try`, on the game thread.
5. Add named commands in `HarnessPolicies` (`menu_show`, `menu_state`), so scenarios do not need eval.

### H. Screenshot
- [known] The tool is `ctx.screenshot(name)` in a scenario. It calls `take_screenshot` in `harness/runlib/phases.py` and writes `runs/<id>/screenshots/<name>.png`. The MCP tool `list_screenshots` lists them. Model: scenario `ui-countdown`.
- New scenario `policy-menu-pak`: run with `--pak policymenu`, call `menu_show`, wait, `ctx.screenshot("menu")`, assert `in_viewport` is true. Optional: a real click (spec 07) and assert `policiesSigned`.

## Risks
1. A cooked Blueprint may crash the game at load (version, mapping, dependencies). A crash is a result with logs.
2. `LoadAsset` on a pak-only path is not proven. Fallback: `NotifyOnNewObject`.
3. Legacy pak vs IoStore: the file list says legacy. It is not confirmed by loading a cooked asset.
4. Fonts and styles: use engine default content only.
5. The editor is a large manual install by the user.

## Next steps
1. The user installs UE 5.5.4 and gives the path.
2. Make the project and the WBP (B to D).
3. Spike: load one trivial cooked widget (a button and a text) from a pak, show it, take the screenshot. This answers risks 1 to 3 with the smallest asset.
4. Then the policy menu and the click wiring.
Optional cheap path (user decision): build the layout in pure Lua first, to meet "custom menu plus screenshot" without the editor.
