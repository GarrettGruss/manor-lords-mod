# MLUE4SS 229 (UE4SS 3.0.1-1136-g35d1795d, small package) (inspection note)

Date: 2026-10-14. Source: `C:\Users\garre\Downloads\MLUE4SS 229 3.0.1-1136-g35d1795d 2026-09-19T17-09Z VTfcmBr00.zip` (Nexus file id 229, upload 2026-09-19). Local copy (git-ignored): `modtools/example-mods/mlue4ss-229/`. Nothing was run or installed.
Archive: 8,717,962 bytes, SHA-256 `050948bdf6b4aae2ff8d834aaebadbf7535d4cb8478fbb579966a5ca3142f86a`. 20 files. Author: UE4SS-RE team. License: MIT (`ue4ss/LICENSE`, 1,085 bytes).

## What it is
The stock RE-UE4SS runtime for Manor Lords as the ML mod tools distribute it: proxy `dwmapi.dll`, `ue4ss/UE4SS.dll`, `UE4SS-settings.ini`, `UE4SS_SDK_Backends/UE4SS.json`, and default Lua mods (`BPML_GenericFunctions`, `BPModLoaderMod`, `CheatManagerEnablerMod`, `ConsoleCommandsMod`, `ConsoleEnablerMod`, `Keybinds`, `LineTraceMod`, `SplitScreenMod`, shared `UEHelpers`). It is the small "release" form of the build that the earlier note `ml-ue4ss-zdev.md` listed as the 367-file "zDev" package (no PDB, no docs, no `Types.lua`, no C++ mods, no MapGen assets).

## Binary hashes (not run)
| file | size | SHA-256 |
|---|---|---|
| `dwmapi.dll` | 279,552 | `2bd8edd80335c4cc1a64186b8ac9fb5764e0ff58669584b6c04131fc9f5e3842` |
| `ue4ss/UE4SS.dll` | 20,567,040 | `d936fd2d66ae9287f0b32aec5f698aa81ff20ef744eac43bf62d8475469393df` |

Both are byte-equal to the files in the zDev package (same hashes as in `inventory.md`). So there is one build, 3.0.1-1136-g35d1795d, shipped in two packages.

## Comparison with our installed UE4SS
- Ours (`...\Win64`): `dwmapi.dll` `3f11fad958a959dd...`, `UE4SS.dll` `87b494191b7bc9bc...` (file date 2026-10-09). Different from this package, so we run another (newer) build. Do not replace it.
- Our `UE4SS-settings.ini` differs from the package in 7 keys: ours sets `EnableHotReloadSystem=1`, `EnableAutoReloadingLuaMods=1`, `bUseUObjectArrayCache=true`, `ConsoleEnabled=1`, `GuiConsoleEnabled=1`, `GuiConsoleVisible=1`, `MaxMemoryUsageDuringAssetLoading=85`. The package has 0, 0, false, 0, 0, 0, 80 (a quiet default). So the package default does not give a console or hot reload.
- Our Mods folder has all the stock mods plus ours (`HarnessBoot`, `UEBridge`, `RefugeeWaves`, ...). The package `mods.txt` enables `CheatManagerEnablerMod`, `ConsoleCommandsMod`, `ConsoleEnablerMod`, `BPML_GenericFunctions`, `BPModLoaderMod`, `Keybinds`.

## Risk review
Native DLLs from a third party. Signed by nobody. They are the same bytes as the zDev package that was reviewed earlier. We do not install anything from it.

## Lessons for us
- No new feature. Nothing here to adopt; keep our build.
- If a user reports a problem on a clean machine, this is the build the ML community mods (for example MLArmyCampMod, MLHomelessTentMod) target by version family (3.0.1-450 to 3.0.1-942). Our build is newer, so those C++ mods may also fail for ABI reasons.
- Test idea: a check in `harness/deploy.ps1` that records the SHA-256 of our `UE4SS.dll` and `dwmapi.dll` in `runs/<id>/summary.json`, so a run states which UE4SS built it. (Not done; proposal only.)
