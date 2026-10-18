# MLUE4SS-zDev

## What it is
A stock RE-UE4SS "zDEV" build. The folder name says `3.0.1-1136-g35d1795d`. The changelog title is `v4.0.0-rc1`. The proxy `dwmapi.dll` is in the root. Everything else is in `ue4ss\`. This is the same "new layout" as our install.

It is not made for Manor Lords. The `CustomGameConfigs` folder has configs for 36 other games (Satisfactory, Abiotic Factor, Vein and others). It has no Manor Lords entry. The `UE4SS-settings.ini` is the generic one. There are no Manor Lords AOB signatures, member variable layouts or mod loader uassets.

The commit text `g35d1795d` is not inside the DLL (searched). The version comes from the folder name only.

## Comparison with our install
Our install: `C:\Program Files (x86)\Steam\steamapps\common\Manor Lords\ManorLords\Binaries\Win64\`.

| item | ours | zDev |
|---|---|---|
| dwmapi.dll | 279,552 B, SHA-256 3f11fad958a959dd7ab78ab0b42be90e33f8ef8e152fbdc3c8e4278cb590e6cc, PE build time 2026-10-09 | 279,552 B, 2bd8edd80335c4cc1a64186b8ac9fb5764e0ff58669584b6c04131fc9f5e3842, 2026-09-14 |
| UE4SS.dll | 20,606,976 B, 87b494191b7bc9bcfd938f54190c09e9aaa01dc354f6927ba661b0a18bad13ee, 2026-10-09 | 20,567,040 B, d936fd2d66ae9287f0b32aec5f698aa81ff20ef744eac43bf62d8475469393df, 2026-09-14 |
| UE4SS.pdb | 156,004,352 B | 135,098,368 B |
| UE4SS-settings.ini | one difference: `EnableAutoReloadingLuaMods = 1` | `= 0` (default) |
| Mods/shared/Types.lua | identical (same SHA-256) | identical |
| bundled mods | same 12 stock mods, plus our Harness* and stand-in mods | the 12 stock mods. `EventViewerMod` and `KismetDebuggerMod` `main.dll` differ (a rebuild) |
| Changelog and Docs | newer | older |

Result: our build is newer than the downloaded one (about 3.5 weeks). Our Changelog has entries that zDev lacks:
- `__eq` metamethod on UObject (compare two objects by pointer with `==`).
- Setting `FWeakObjectProperty` values from Lua (an object, a `FWeakObjectPtr` or `nil`).
- A fix for a crash at engine shutdown.
- A fix for `RegisterCustomProperty` with an unknown property size.
- A fix for a memory leak when Lua calls a UFunction with an `Out` parameter (UE4SS issue 1446).

The other file differences are only `Changelog.md`, `uobject.md`, `fweakobjectptr.md` and the two debug mod DLLs.

## What is useful to us
- Lua types: `Mods/shared/Types.lua` (57 KB, `---@meta`, LuaLS format) is already installed in our game folder and is identical. The repo has no `.luarc.json`. We could add one for editor checks. Value is low: it covers UE4SS built-ins only, not game classes.
- `GenerateLuaTypes()` and the GUI "Dump Lua Bindings" button write types for all reflected classes to `Mods/shared/types` (guide: `Docs/guides/using-custom-lua-bindings.md`). This could give LuaLS names for Manor Lords `BP_*` classes. The guide warns that the language server may fail on a large game. Fix: a `.luarc.json` with `workspace.maxPreload` and `workspace.preloadFileSize`. We do not use it yet (no hit in `mod/` or `harness/`). The call writes into the game folder, so ask the user first.
- Lua API we do not use yet (docs in `Docs/lua-api/global-functions/`): `RegisterCustomProperty`, `RegisterConsoleCommandHandler` and `RegisterConsoleCommandGlobalHandler`, `LoadAsset`, `StaticConstructObject`, `CreateInvalidObject`, `IsKeyBindRegistered`, `RegisterBeginPlayPre/PostHook`, `RegisterInitGameStatePre/PostHook`, `RestartMod`, `UninstallMod`, `RestartCurrentMod`. Classes: `UDataTable` (`classes/udatatable.md`, `devlogs/datatables-in-ue4ss.md`), `TMap`, `TSet`.
  - We already use `LoopAsync`, `ExecuteInGameThread`, `ExecuteWithDelay`, `ExecuteAsync`, `FindAllOf`, `RegisterHook`, `RegisterKeyBind`, `NotifyOnNewObject`, `ForEachUObject`, `DumpJMAP`.
  - The `UDataTable` docs may help spec 10 data table work. Compare with `HarnessDataTable` first.
  - `RegisterConsoleCommandHandler` could add an in-game console control path next to the bridge.
- `MapGenBP` (3 uassets): a sample map generator for the Blueprint mod loader. Not related to Manor Lords.
- `CustomGameConfigs`, `MemberVarLayoutTemplates`, `VTableLayoutTemplates`, `Default_UVTD_Configs`, `UE4SS_SDK_Backends`: for other games and for the C++ SDK generator. Not needed. Our game works with the built-in UE 5.5.4 layout, and the jmap and usmap exist already.

## Risk review
- `dwmapi.dll` is a proxy loader for `ue4ss\UE4SS.dll`. Strings: `UE4SS.dll`, `ue4ss`, `override.txt`, `--disable-ue4ss`. Same as ours.
- `UE4SS.dll` injects into the game process and hooks engine code by design. It was not run. Its 20 MB body was not reviewed for network use. The source is public (GitHub RE-UE4SS). This zip is not from a verified release page. Treat it as untrusted.
- `EventViewerMod` and `KismetDebuggerMod` are native C++ debug mods (DLL and PDB). Not reviewed in depth.
- The Lua mods are the stock ones. They also exist in our install.

## Lessons for us
- Do not switch builds. Ours is newer and has the fixes above.
- Keep `EnableAutoReloadingLuaMods = 1`. It is our deliberate change.
- Test idea, only if we ever try another build: install it in a copy of the game folder, run the existing smoke scenario, and compare `summary.json` and `bridge_status`. Not needed now.
- Follow-up spikes: (1) call `GenerateLuaTypes()` once and judge the output for Manor Lords; (2) try `RegisterConsoleCommandHandler`; (3) read `datatables-in-ue4ss.md` for spec 10 data table work.
