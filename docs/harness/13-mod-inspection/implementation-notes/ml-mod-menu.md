# MLModMenu

## What it is
An in-game "Mod Menu" for Manor Lords by Psiae (`dev.psiae.manorlordsmods.MLModMenuMod`, display name "Mod Menu"), version `0.1.0-alpha.1`. It adds a Mods entry to the main menu and entries to the pause menu. Other mods register with it and get a settings page.

Files: `dlls/main.dll` (5.5 MB, a UE4SS C++ mod, internal name `MLModMenuMod.dll`), `ae_bp/MLModMenuMod.pak` (18 MB, 122 entries), two manifest JSON files, an empty `enabled.txt`. No license text.

## How it works
- The DLL is a RE-UE4SS C++ mod (class `mod::MLModMenuMod`, with `onUnrealInit` and `onInitialize`). It hooks `InitGameState`, the game viewport tick, load map callbacks and the process console exec callback. It hooks Blueprint functions of the pak: `BP_API_StaticFunctions:RegisterMod`, `RequireApiVersion`, `IsApiVersionCompatible`, `BP_API_ModApi:RegisterMainMenu`, `RegisterPauseMenu`, and `WBP_MainMenuScreen:OnModEntryClicked`.
- It reads game classes: `BP_MLGameInstance_C`, `MLCheatManager_C`, `AMenuPawn_C`, `AMyPawnCPP_BP3_C`, `mainMenu_widget_c`, `MainUICPP_C` and others. It checks that the owning pawn is `AMenuPawn_C` or `AMyPawnCPP_BP3_C`. It adds a menu button (`WBP_MenuButtonExtend`) to the game's main menu widget.
- The pak mounts at `../../../ManorLords/Content/Mods/MLModMenuMod/` (pak version V11, Oodle compression, index not encrypted). Contents by listing:
  - `API/BP_API_*` (Mod, ModApi, ModBinder, MainMenu_Mod, MainMenu_ModApi, MainMenu_Screen, PauseMenu_Mod, RegisterModResult, StaticBroadcasts, StaticFunctions, Screen, ObjectBase): the Blueprint API that other mods call.
  - `BP_MainMenu`, `BP_PauseMenu`, `BP_ModActor`, `ModActor`, `BP_GameMenu`, and helper bases.
  - `UI/`: `WBP_MainMenuScreen`, `WBP_ModEntryWidget`, `WBP_ModInstancePage`, `WBP_DefaultCheckbox`, `WBP_DefaultSlider`, `UI/BasicUI/WBP_ModPage_BasicAutoBlock*` (auto-built settings blocks with a checkbox and a slider widget), key art and two screenshots.
  - `Game/`: a few copies of Manor Lords UI textures and sounds (paper texture, button sounds).
- Link between DLL and pak: a version check. Error text: "linking error, version mismatch between CPP and BP". A mod can require an API version (`RequireApiVersion`).
- Dependency: the DLL also looks for a second mod `MLModPresence` (`/Game/Mods/MLModPresenceMod/API/...`, hook on `OnRegisterModReady`, text "Incompatible Mod, require 'MLModPresence' api version"). That companion mod is not in this download. The menu may not work alone.
- "JSON config": only metadata manifests for a separate mod manager (`dev.psiae.ModManifest`, `manifestVersion 0.1.0-alpha.1`). They list a `ue4ss` mod loader dependency (UE4SS `3.0.1-450-1033902`, timestamp 2025-08-03) and a stub `MLToolBox`. There is no settings file format in the download. Settings values are probably kept in memory or saved by each mod.

## Pak unpack
`repak info` worked (not encrypted). `repak unpack` failed: "Oodle loader error: Oodle initialization failed previously". It wrote 31 of the entries, all empty or tiny, and could not read the Blueprint assets. That folder was deleted. I did not install Oodle. The Blueprint function parameters of `RegisterMod` and `RegisterModSimple` are therefore unknown. They need the uassets (after an Oodle-capable repak) or the author's docs.

## Target game version
Not stated. Manifest time 2025-09-01 (main.dll PE time 2025-09-01 15:13 UTC) and UE4SS 3.0.1-450 (2025-08) say it was built for the game as of late summer 2025. That is far before 0.8.111. The class names it needs (`AMenuPawn_C`, `AMyPawnCPP_BP3_C`, `/Game/UI/Main_Menu/mainMenu_widget`) should be checked in our jmap before any test. Old UE4SS C++ API (it imports `UE4SS.dll` symbols from a 3.0.1 build) may not link with our newer UE4SS 4.0.0-rc1 build.

## Risk review
- `main.dll` imports only `KERNEL32`, `USER32`, `UE4SS.dll`, MSVC runtime and CRT. No WinHTTP, WinINet or socket library. No URL strings found. Strings show no process start, no registry use and no file path other than game asset paths. Only `CreateFileW` appears (normal for CRT).
- It hooks game functions and adds widgets. It does not call save functions (no `SaveGame` strings found; not exhaustive).
- The pak replaces no game asset (all paths are under `Mods/MLModMenuMod`). It contains copies of some game textures and sounds under its own folder.
- Not run, not loaded.

## Lessons for us
- Can the invasion mod use it? Not now. It targets a game build from 2025, needs a missing companion mod, and its API is for Blueprint mods (BP calls `RegisterMod`). A Lua mod could in theory call those UFunctions, but only with the pak loaded, which means the harness would need `--pak` support for a third-party pak, and the parameters are unknown. Our invasion options (difficulty, raid size) can use named commands (`HarnessCommands`) and, for the player, key binds or the game's own options. Skip the menu.
- Design idea worth keeping: a registry API with `RequireApiVersion` and a CPP/BP version check. It is a good pattern if we ever expose options to the player.
- Check against our jmap/usmap (done): `MenuPawn_C`, `MyPawnCPP_BP3_C`, `mainMenu_widget_C`, `MLCheatManager_C` and `MainUICPP_C` all exist in 0.8.111. So the class names are not stale. The open risk is the C++ ABI against our newer UE4SS and the missing companion mod.
- Test idea: an A/B check that the pak and DLL load in the harness is a later step with the user's approval. Pre-check: search our jmap for `AMenuPawn_C`, `AMyPawnCPP_BP3_C`, `mainMenu_widget_C`, `MLCheatManager_C`. If a name is missing, the menu is stale.
- Tooling lesson: our `repak` build cannot unpack Oodle-compressed paks without the Oodle library. If we need to read this pak, ask the user before installing anything.
