# Prep: spike menu custom textures

Prepared on 2026-10-20 without the game. Nothing here ran in the real game. All "reflected" claims are unproven until the first run.

## How the menus build widgets today
- `raid_widget`, `tech_tree_widget` and `liege_influence` find a cooked Widget Blueprint class (`/Game/HarnessMod/WBP_*.WBP_*_C`). If `StaticFindObject` fails, they call `AssetRegistryHelpers:GetAsset` (`LoadAsset` does not load mod pak assets).
- Then `WidgetBlueprintLibrary:Create(controller, class, controller)`, `AddToViewport(z)`, `SetPositionInViewport`.
- The widget tree is made in headless UE with Python (`mod/InvasionMod/ue/make_raid_widget.py`, `make_tech_widget.py`). Lua finds children by name with `FindAllOf` and sets text with `SetText(FText(...))`.
- Clicks use `WBP_ClickButton` (copy of the engine widget `AudioButtonToggle`) and `HarnessClickHooks`.
- Widget classes we ship: `WBP_RaidMenu`, tech tree widget, `WBP_ClickButton`. They use `TextBlock` and `Border`. Their images have no texture (`make_click_button.py` clears the brush). No `Image` with a texture exists in our paks yet.
- The game has other widgets with `Image` (for example `genericAchievement_EventMessage_C`), not checked.
- The wiki has no UI or widget page (`docs/wiki` has only architecture, concepts, integrations, operations, testing, workflows). The spike must add one (task 2.1).
- Old evidence: the archived refugees mod (`openspec/changes/archive/2026-10-15-legacy-13-mod-inspection/implementation-notes/refugees-expanded.md`) says it built a widget with `CanvasPanel`, `Border`, `TextBlock`, `Image` and loaded `assets/refugees_banner.png` through `KismetRenderingLibrary`. This is a third-party mod, read from its code. It is a hint that candidate 2 works in this game, not a proof.

## What is reflected (no dump in the repo)
The repo has no UE4SS object dump or header dump. The `jmap` file named in the refugees notes is outside the repo. So these names are from UE 5.5 source knowledge and must be checked at run time (the probe logs each step; `list_functions` on the bridge can check them in the first minute of a run):
- `KismetRenderingLibrary:ImportFileAsTexture2D(WorldContextObject, Filename)` : `Texture2D`. A BlueprintCallable static function. Filename is an FString, so no FName risk.
- `Image:SetBrushFromTexture(Texture2D, bMatchSize)`, `SetBrushFromSoftTexture`, `SetBrush(SlateBrush)`, `SetDesiredSizeOverride(Vector2D)`: BlueprintCallable on `/Script/UMG.Image`.
- `SlateBrush` fields: `DrawAs` (enum: NoDrawType 0, Box 1, Border 2, Image 3, RoundedBox 4), `Margin` (normalized 0 to 0.5 for a Box brush), `ImageSize`, `ResourceObject`. Writing a nested field (`image.Brush.DrawAs = 1`) may or may not work through UE4SS. The probe tries it and logs the error.
- `Border:SetBrushFromTexture` also exists, and `Border` is already in our widgets. This is the fallback if a new `Image` cannot be built from Lua.
- Not known: is `StaticConstructObject` of `WidgetTree` and `Image` allowed for a `UserWidget` made from the C++ class? A safer way is to add an `Image` to a cooked widget in `make_*_widget.py` (candidate 3 style) and set its brush from Lua. Do this if the probe fails at "construct WidgetTree".

## Risks (CLAUDE.md, Safety)
- No Lua string goes to an FName argument. The probe passes `FName(...)` only to `StaticConstructObject` (object names). If that crashes, stop and use a cooked `Image` instead.
- Do not read struct values with soft object fields (`getItem`, `RowStruct`). `SlateBrush.ResourceObject` is a hard pointer, but the probe never reads the brush. It only writes `DrawAs` and `Margin`.
- Never write a `Tags` array. Not used.
- No save function. The probe does not call one, and `test_save_call_sites.py` passes.
- Run one game at a time. A crash report goes to the real `%LOCALAPPDATA%\ManorLords\Saved\Crashes`; the launcher copies it.
- `ImportFileAsTexture2D` makes an uncompressed texture, with mips off by default in the call? Unknown. Large art (a 4K parchment) would use much memory. Note the size in the result.

## Plan per candidate
### Candidate 2: runtime PNG (probe is ready)
1. `uv run python openspec/changes/spike-menu-custom-textures/tools/make_test_png.py` (already run; writes `assets/test_frame.png`, 256x256, parchment, 16 px dark border, red 32 px marker top left).
2. Deploy: `harness\deploy.ps1` (the new shared module `HarnessTexProbe` is picked up from `mod/shared`).
3. Run: `MSYS_NO_PATHCONV=1 uv run python harness\run.py --scenario probe-menu-texture` (hidden; `--list-scenarios --include-test-scenarios` shows it). Option `PNG_PATH` sets another file. Back up the save folder first.
4. Read `runs/<id>/summary.json`, the log lines tagged `HarnessTexProbe` (each step: ok or the error) and the screenshots `png-fullscreen`, `box-small`, `box-wide`.
5. Pass: `png-fullscreen` shows the parchment with a dark border and a red marker top left. For Box: at 200x200 and 600x300 the 16 px border keeps the same thickness and the corners stay square.
6. The path must be absolute and readable by the game process. Does the game find a file under `runs/` or the repo? The probe passes the repo path. A final mod would ship the PNG next to its Lua (`ue4ss/Mods/<Mod>/assets/`); check that deploy copies it.

### Candidate 1: texture in a pak (not built; needs the editor, so not done in this prep)
1. Copy the PNG to the UE workspace (`C:\Users\garre\development\mlm-ue\ManorLords`).
2. A UE Python script (new, `-ExecutePythonScript`, same pattern as `make_click_button.py`; set `MSYS_NO_PATHCONV=1`) imports it with `unreal.AssetImportTask` (`destination_path=/Game/HarnessMod`, `destination_name=T_TestFrame`, `automated=True`, `save=True`).
3. Then set on the `Texture2D`: `mip_gen_settings = TMGS_NO_MIPMAPS`, `lod_group = TEXTUREGROUP_UI` (UserInterface2D), `compression_settings = TC_EDITOR_ICON` (UserInterface2D, sRGB) and `never_stream = True`; save. This keeps the UI sharp.
4. Cook: `-run=cook -targetplatform=Windows -unversioned -nopak -skipeditorcontent`. Copy `T_TestFrame.uasset`, `.uexp` (and `.ubulk` if made) into the pak work folder under `ManorLords/Content/HarnessMod/`. Build with `pakmod.py build <name>`; install; run with `--pak <name>`. Never write the AES key anywhere.
5. Lua: load like the widget classes. `StaticFindObject("/Game/HarnessMod/T_TestFrame.T_TestFrame")`; if invalid, call `AssetRegistryHelpers:GetAsset` with `AssetClassPath = { PackageName = FName("/Script/Engine"), AssetName = FName("Texture2D") }` (same shape as `find_class` in `raid_widget`). Then `image:SetBrushFromTexture(texture, false)`.
6. The probe module can take a second action for this (`load_asset`); add it after candidate 2 shows that the widget build works. If `SetBrushFromTexture` works in the probe, only the load step differs.
7. For a Box brush, also set `Brush.DrawAs = Box` and `Brush.Margin` in Lua, or set them in the editor script on an `Image` in a cooked widget (`brush.set_editor_property("draw_as", unreal.SlateBrushDrawType.BOX)`, `margin`). The editor way avoids writing struct fields from Lua.

## Probe
- Lua: `mod/shared/HarnessTexProbe/HarnessTexProbe.lua`. Command `texture_probe` with `action` = `load_png` (field `path`), `show` (`width`, `height`), `box` (`margin`, `width`, `height`), `close`. Registered in `mod/HarnessActions/Scripts/main.lua`. Every risky call is in a `pcall` step that logs through `HarnessLog` and returns the step list in the answer. It validates the path (ends with `.png`, no `..`).
- Scenario: `harness/scenarios/probe_menu_texture.py`, name `probe-menu-texture`, `HIDDEN = True`, limit 180 s.
- Test PNG tool: `openspec/changes/spike-menu-custom-textures/tools/make_test_png.py`.

## Open questions
- Does `StaticConstructObject` of `WidgetTree` and `Image` work from Lua? If not, use a cooked widget with an `Image` (small `make_*` script).
- Is `HarnessActions` command list documented in a skill or the wiki that must list `texture_probe`? Add it when the spike ends (the spike may delete the probe).
- The probe adds a shared module to the harness. If the spike result is "no", remove it in the close task.
