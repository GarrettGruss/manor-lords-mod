# Inventory of the inspected mods

Source: `C:\Users\garre\Downloads` (extracted by the user, 2026-10-11). 15 items. Nothing was run or installed.
SHA-256 values of binary files are in each mod note.

## Group A: manor and storage


| mod | version | target game version | type | files | size | author | license text |
|---|---|---|---|---|---|---|---|
| StorageAndManorUnlock | 0.5.0 "BALANCE TEST" (folder name: 0.8.104 389 1) | 0.8.104 (UE4SS 3.0.1 Beta) | Lua | README.txt, StorageAndManorUnlock/enabled.txt, Scripts/config.lua, Scripts/main.lua | 14741 bytes (1417 + 0 + 2722 + 10602) | not given | none given |
| ManorLimit99 | not given (folder name: 0.8.083 343 1) | 0.8.083 | pak (data table `buildingStats`, 2 assets) | ManorLords_0.8.083_ManorLimit99.pak | 18622 bytes (pak) | not given | none given |

SHA-256 values are in the two mod notes.

## Group B: population, loot, nature


Sizes are the total of the extracted folder. Author means a name given in the files; none of the four gives a personal name.

| mod | version | target game version | type | files | size | author | license text |
|---|---|---|---|---|---|---|---|
| RefugeesExpanded | 1.9.1 (Nexus 388) | 0.8.104, UE4SS 3.0.1 | Lua + DLL (native bridge, C++ source included) | 16: `Scripts/main.lua`, `Scripts/config.lua`, `native_bridge/RefugeesPopulationBridge.dll`, `.lib`, `native_src/*.cpp, .def, .obj, .lib, build and readme notes`, `assets/refugees_banner.png`, readmes, changelog, `enabled.txt` | 3,039,291 bytes (zip 2,967,276) | none given (a comment mentions "Psiae's 0.8.104 backend") | none given |
| Battlefield Loot And Bandit Loot (folder `UnifiedLoot`) | 1.2.0 (Nexus 390) | 0.8.104 | Lua | 9: `Scripts/main.lua`, `Scripts/config.lua`, readmes (EN, CN), changelog, money and test notes (CN), install note (CN), `enabled.txt` | 75,078 bytes (zip 21,290) | none given | none given |
| AllYearOrchards 60Day SpringToAutumn (folder `TLAYOrch`) | 0.4.5 (Nexus 387) | 0.8.104 | Lua + DLL (two MLTweaks patch templates) | 6: `Scripts/main.lua`, `native/templates/HarvestPulseOn.dll`, `HarvestPulseOff.dll`, `README_中文.txt`, `CREDITS.txt`, `enabled.txt` | 490,891 bytes (zip 240,364) | "TL" tag only; native part derived from MLTweaks by miu0007 | `CREDITS.txt`: "The upstream package explicitly permits modification, reuse and redistribution." (MLTweaks is MIT per another mod's notice). No license for the Lua |
| TreeRegeneration | 1.0.0 (Nexus 407) | 0.8.111, UE4SS 3.0.1 rev f6d5f942 | Lua + DLL (no source) | 20: 14 Lua files in `scripts/`, `native/TreeRegenerationNative.dll`, `native/NOTICE.txt`, `PERMISSIONS.txt`, `README.md`, `CHANGELOG.md`, `enabled.txt` | 563,947 bytes (zip 221,150) | none given | `PERMISSIONS.txt`: personal use allowed; redistribution, re-upload, modpack inclusion and public modified versions need prior permission of the author |

## Binary files

| mod | file | size | SHA-256 |
|---|---|---|---|
| RefugeesExpanded | `native_bridge/RefugeesPopulationBridge.dll` | 5,632 | `e702e80f2a31e4b1745e12171b58e2d707073eea081b4a220f84a8543d7622a7` |
| RefugeesExpanded | `native_bridge/RefugeesPopulationBridge.lib` | 1,696 | `9ea85ffe097aa486620eb9eba7be71fe0dae2dd714a7a113e57b65d54b0212a1` |
| RefugeesExpanded | `native_src/bridge.obj` | 6,735 | `1f3686f32ed865e776d798b500881080ba9b262aa57d2f126e7d0744df96f527` |
| RefugeesExpanded | `native_src/kernel32.lib` | 2,496 | `ddc610aec6f6c7eeca8716a400a305d42a198c3fe37384c86df1738ec2b680da` |
| RefugeesExpanded | `assets/refugees_banner.png` | 2,932,406 | `375e75880fdb702ac094a9ee94488760a340337404dd9dbb10f303db6495e2cf` |
| AllYearOrchards | `native/templates/HarvestPulseOff.dll` | 239,104 | `52c1fde44bc087b9287cab76446260e495a3b0ffd08a11e68c6e70a598c2e1e` |
| AllYearOrchards | `native/templates/HarvestPulseOn.dll` | 239,104 | `7067853387dc67fed0bcc35115f560456d7e86f2b618d42da8f7e144983a3cb8` |
| TreeRegeneration | `native/TreeRegenerationNative.dll` | 411,136 | `d6134d58e90fdca9a72c011ec3e834e912817dcb44dbdf220139592802eb4cc6` |

## Group C: military, enemies, AI


Sizes are the total of the extracted folder (the archive size is in brackets). "Author" means a name given in the files. None of the seven gives a name. None gives a license text. Nexus file ids come from the folder names.

| mod | version | target game version | type | files | size | author | license text |
|---|---|---|---|---|---|---|---|
| AdaptiveEnemies | 1.1 (Nexus 369) | 0.8.104 | Lua | 4: `README.txt`, `scripts/config.lua`, `scripts/main.lua`, `enabled.txt` | 29,602 bytes (zip 11,011) | none given | none given ("100% original standalone code" in README) |
| AdaptiveMilitia | 1.1 (Nexus 370; README and header say 1.0) | 0.8.104 | Lua | 4: `README.txt`, `scripts/config.lua`, `scripts/main.lua`, `enabled.txt` | 10,698 bytes (zip 4,920) | none given | none given ("Standalone original code" in README) |
| AdaptiveOrigins | 1.1 (Nexus 368) | 0.8.104 | Lua | 4: `README.txt`, `scripts/config.lua`, `scripts/main.lua`, `enabled.txt` | 25,618 bytes (zip 10,682) | none given | none given ("100% original standalone code" in README) |
| AdaptiveRetinueManager (EN) | v2.6 in the load message, v2.5.2 in the header (Nexus 381) | 0.8.104 | Lua + DLL (no source) | 4: `scripts/main.lua` (4,057 lines), `scripts/config.lua`, `native_bridge/AdaptiveRetinueNativeBridge.dll`, `enabled.txt`. No README | 193,869 bytes (zip 46,991) | none given | none given |
| BetterBattlefieldMod | v2.3 (Nexus 306) | not stated (file date 2026-04-09) | Lua | 2: `Scripts/main.lua`, `Enabled.txt`. No README | 10,285 bytes (zip 3,494) | none given | none given |
| LargerFormations | 1.0.0 (Nexus 356) | 0.8.083 (README: "Tested with") | pak + DLL + Lua loader | 5: `README.txt`, `ue4ss/Mods/LargerFormations/Scripts/main.lua`, `.../dlls/LargerFormationsNative.dll`, `.../enabled.txt`, `Content/Paks/~mods/LargerFormations_P.pak` | 95,167 bytes (zip 38,106) | none given | none given |
| ML Battle Scenarios 1 (0.2) | 0.2 (Nexus 316) | 0.8.065 (read from `saveGame_68_descr.sav`) | save (2 `.sav`) + 6 PNG | 8: `saveGame_68.sav`, `saveGame_68_descr.sav`, `saveGame_68.png`, `saveGame_68_coat_0..4.png`. No README | 4,839,662 bytes (7z 4,526,370) | none given | none given |

## Archive SHA-256
| archive | SHA-256 |
|---|---|
| AdaptiveEnemies ... .zip | `4e63d95cf80f3c7bb940333c5f33bec31a5075e97acbd8b919600799fe59fbda` |
| AdaptiveMilitia ... .zip | `890c0ffb63d7cb6926ac2dfbcddfa73d875bb74eaa6800cdbfc3fee472f5dc22` |
| AdaptiveOrigins ... .zip | `b8ea3d00367e3055523429515dc60d96c5b0600ababaf73482c7780687e1f33f` |
| AdaptiveRetinueManager ... .zip | `d48f32efbce6d0b3e82ed1b0d996f6eb0585b9758f72084a0efff20a445a2f22` |
| BetterBattlefieldMod ... .zip | `56654178f64d5c2180be221e77f220b0f256dfa98c871b3c705cc294642bad6b` |
| LargerFormations ... .zip | `b7b3114dde980b08b9355e376dd30a06a2520caf3b37058badd1a8cf92bc242c` |
| ML Battle Scenarios ... .7z | `e3b343b510d414bdc43a569d3d8f95a1bfd49ee5995c8d2f06c6ff1404f18979` |

## Binary files (not run; hashes and sizes only)
| file | size | SHA-256 |
|---|---|---|
| `AdaptiveRetinueManager/native_bridge/AdaptiveRetinueNativeBridge.dll` | 12,800 | `803d67c42e36ada4f501c5b83b354e011b3804acfffd37533c47d99d594be1d5` |
| `LargerFormations/dlls/LargerFormationsNative.dll` | 80,896 | `13b8b4febe3c215970393087d24281abc4e5f99b7daa70b15b22f05e8dd9b5cf` |
| `LargerFormations_P.pak` | 11,803 | `a3c2a12be43347d13fa0b09cadf80eefc66ea0c0484cb3682cd29872382a7583` |
| `saveGame_68.sav` | 3,530,885 | `ba2a660c97825747fd5794018ac1a037490f80ba056ae613c9e1ffedd5dce8e0` |
| `saveGame_68_descr.sav` | 2,169 | `5fcb8be20b3358bf1bb8a699131091300c3aeb011e56bc1e6d028152812d0abe` |
Hashes for the PNG files are in `ml-battle-scenarios.md`. The Retinue Manager Lua hashes are in `adaptive-retinue-manager.md`.

## Stale check against the 0.8.111 jmap (short)
| mod | result |
|---|---|
| AdaptiveEnemies | all names found; baron name unchanged per baron-model.md |
| AdaptiveMilitia | `addMilitiaSquad` found; **hooked UI objects `addSquadCard`, `skillButton` and property `MainUICPP.unitCards` not found** (UI rebuilt) |
| AdaptiveOrigins | all names found |
| AdaptiveRetinueManager | **`RTSMultiEngineCPP.squads`, `updateSquadEquipmentStats`, `PawnCPP.addRetinueSquad`, `getAllSquads` not found**; selection, delete and editor names found |
| BetterBattlefieldMod | `initChallenge` (3 arguments), `battlefield_BP_C`, `Region.manor` found (the mod writes `Manor`) |
| LargerFormations | row struct and names fit; DLL signatures target 0.8.083 code and cannot be checked from the jmap |
| ML Battle Scenarios | save from 0.8.065; not checkable |

## Group D: tools


| mod | version | target game version | type | files | size | author | license text |
|---|---|---|---|---|---|---|---|
| MLModMenu (folder `MLModMenuMod`) | 0.1.0-alpha.1 (built 2025-09-01) | not stated; built long before 0.8.111 (by date) | DLL (UE4SS C++ mod) + pak | 5: `dlls/main.dll`, `ae_bp/MLModMenuMod.pak` (122 entries), `modManifest.json`, `modManifests/ue4ss/modManifest.json`, `enabled.txt` (empty) | main.dll 5,538,304 B; pak 18,288,690 B; about 23.8 MB | Psiae (`dev.psiae`) | none given |
| MLUE4SS-zDev | 3.0.1-1136-g35d1795d (changelog title v4.0.0-rc1; DLL compiled 2026-09-14) | any UE game (UE 4.7 to 5.8); no Manor Lords parts | UE4SS build (proxy dwmapi.dll, UE4SS.dll, docs, templates, Lua, 2 DLL mods, 3 uassets) | 367 files | 176 MB extracted (zip 46,599,228 B) | UE4SS-RE team (RE-UE4SS) | MIT, "Copyright (c) 2022 Narknon" (`ue4ss/LICENSE`) |

Hashes (SHA-256):

| file | size | SHA-256 |
|---|---|---|
| MLModMenu `dlls/main.dll` | 5,538,304 | e47e724c2dfd5027bd1630c749f9d02e01072a97e09ee46197f99e41a58a84cf |
| MLModMenu `ae_bp/MLModMenuMod.pak` | 18,288,690 | 51bb045845b1993056e213f853c83532f02cca5f2d2b63d9f1953a2b3529f567 |
| zDev `dwmapi.dll` | 279,552 | 2bd8edd80335c4cc1a64186b8ac9fb5764e0ff58669584b6c04131fc9f5e3842 |
| zDev `ue4ss/UE4SS.dll` | 20,567,040 | d936fd2d66ae9287f0b32aec5f698aa81ff20ef744eac43bf62d8475469393df |
| zDev `ue4ss/UE4SS.pdb` | 135,098,368 | dd2058e9b096484672d1b7708bb36759393c05baef4573913dd19d94d8c51880 |
| zDev `Mods/EventViewerMod/dlls/main.dll` | 607,744 | c8e37b212fb999572d54a9cb8b9b14ca6f66d7b6e8fc61db84728ec12626c3b1 |
| zDev `Mods/KismetDebuggerMod/dlls/main.dll` | 726,016 | 647552d6f7dd0e641ce146a1dbbf2261a6832f8f6629aedfec793973413c8392 |
| zDev `MapGenBP/Content/MapGen/MapCreator.uasset` | 120,715 | 18fe5a4f7ed094c90345fc7f6fcc63926e3f20c380291a21be6b08b1182b4f22 |
| zDev `MapGenBP/Content/MapGen/MapSpawnStruct.uasset` | 5,734 | 2f5977ca8e0db41a044019147b1138de4f78f8ebd9743ff9707c26f52e09462e |
| zDev `MapGenBP/Content/MapGen/MeshStruct.uasset` | 3,796 | 074c41907987bd49289f3e54ffbdb24b39103fa9d4021a1965eb92ce93c32593 |
| zDev `Mods/shared/Types.lua` | 57,252 | d246b8b26ee7ee38e8cd12bd7530e60b318dfd45e05260b8d75ea35bdb482a9b (same as ours) |
