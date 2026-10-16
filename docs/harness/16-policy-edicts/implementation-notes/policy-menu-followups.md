# Policy menu follow-ups (issue #60)

Date: 2026-10-14. Real game, fixture `base`, 5 launches (4 fixes, then a pass). No crash. No save function called.
Pass run: `runs/20261014-010118-2dcf` (local, git-ignored). Screenshots in `runs/20261014-010118-2dcf/screenshots/`:
`policy-menu.png` (menu, all grey) and `policy-menu-signed.png` (first policy green with [x]). No pop-up covers them.

## Results
1. Click wiring: works. Lua polls `Button:IsPressed` every 40 ms. A press that ends while `IsHovered` is true is one click, with a 0.4 s debounce. It calls `Region:setPolicySigned` (ManorCore `set_policy_signed`). A real OS click signed policy 2, a second click unsigned it. No Blueprint graph is needed.
2. Real policy list: works. The mod reads `getAllAvailablePolicies` (6 policies in the base village) and the signed list. Names come from the row field `Name` of DT_PolicyTypes (only that field; the Icon soft object is never read). They are the game text ("Hunting grounds", "nightwatch", "Strict fasting"). The widget has 20 slots (button + label); Lua fills them and collapses unused ones. Signed shows "[x]" and a green button.
3. Open/close: F7 (`RegisterKeyBind`) and the commands `PolicyMenu.open/close/toggle/read`. A real F7 key press closed and opened the menu. F7 is not known to be used by the base game (not checked against a key list). Change `CONFIG.toggle_key` if it clashes.
4. `GatherInputInfo` and the EnhancedInput import are gone: `BlueprintEditorLibrary.find_graph` + `remove_graph`, then `remove_unused_variables`. The cooked asset imports only CoreUObject and UMG.
5. Clean screenshot: the editor was closed before the game started; no firewall pop-up.
6. Releasable mod: `mod/PolicyMenu/mod.json`, `CHANGELOG.md`, player-safe code (requires only ManorCore; HarnessCommands is optional through `pcall`). Gate scenario `policy-menu`. `release.py --mod PolicyMenu --dry-run` passes (zip scan clean, pak has no key). Not published.

## Facts
- `bIsVariable` is not exposed to Python, so widgets are not Blueprint variables. Lua finds them with `FindAllOf("Button")` and the names `PolicyButtonN` / `PolicyLabelN`.
- The seed stack box is horizontal. A `VerticalBox` child (made in Python) gives a vertical list.
- `GetPaintSpaceGeometry`, `GetCachedGeometry` and `GetTickSpaceGeometry` return a zero size from Lua, so `PolicyMenu.read` has no screen position. The scenario finds the first button by hover (`IsHovered`) around a position taken from a screenshot (window 2582x1496). Open: a real position source, if more buttons must be clicked.
- Repeated `bring_to_front` calls opened the Windows task switcher. `focus_game` now returns when the game is already in front.
- The mod loads its pak class with `GetAsset`; `LoadAsset` does not work for mod paks.
- The fake tests do not cover the new ManorCore policy functions (real game proof only).

## Changes
`mod/PolicyMenu/` (Scripts/main.lua, ue/make_widget.py, paks, mod.json, CHANGELOG.md); ManorCore policy functions; `osinput.click_at/hover_at/press_key`; `ctx.click_with_mouse/hover_with_mouse/press_key`; the release zip skips the `ue` folder; removed HarnessPolicyMenu, `menu_pak_*` commands and `probe-policy-menu-pak`.
