# MLArmyCampMod 0.1.1-a.2 (inspection note)

Date: 2026-10-14. Source: `C:\Users\garre\Downloads\MLArmyCampMod var-steam-276-0-1-1-a-2-1773864732.zip` (Nexus file id 276; 1773864732 = 2026-03-18). Local copy (git-ignored): `modtools/example-mods/ml-army-camp/`. Nothing was run. The pak was only listed and read as bytes.
Archive: 654,734 bytes, SHA-256 `9d2ab45811bbb7c7b2d1fe5b4d9bc1b753e9ac4ba1b8d2fbd1ce6c1bf9aeaabf`.
Author: Psiae (`mod_manifest.json`). No license text. The same author made MLModMenu and MLHomelessTentMod; all three share one C++ framework.

## What it does for the player
It adds two squad skills, "Encamp" ("Encamp the squad") and "Decamp" ("Decamp the squad"), with a camping-tent icon. The pak description reads "Allows encamping army". It is a squad command, not a building.

## Mechanism
- Native UE4SS C++ DLL (`dlls/main.dll`, 828,928 bytes) plus a tiny Blueprint pak. No Lua (`Scripts/main.lua` is 0 bytes).
- Files and hashes (the `variant_steam/` copies are byte-equal to the top-level ones):

| file | size | SHA-256 |
|---|---|---|
| `dlls/main.dll` | 828,928 | `f4edd7ba25a0953f19524c58add621548336dc25464cf8a1cd2b512a4f50dc6e` |
| `ae_bp/dev_psiae_MLArmyCampMod.pak` | 12,860 | `22b2c67b04dab09fcf5b2584811edda225d4aadcdff4fb1b3722d78f1dc63e5a` |

- Strings in the DLL (reading printable text only):
  - Console commands `k.armyCamp.ping`, `isInGame`, `printModInfo`.
  - Game classes it wraps: `RTSMultiEngineCPP`, `Squad`, `SMUnit`, `UnitSpawner`, `SMBuildingMaster`, `PawnCPP`, `MLGameInstance`, `ESquadControl`, `ESquadType`, `ERallyingStatus`, `EEquipmentSlot`.
  - UI classes it hooks or reads: `/Game/UI/Army/retinueEditor`, `/Game/UI/Army/skillButton`, `BigTooltipGeneric`, `castlePlanner`, `buildingCardWidget`, `mercenaryScreen`, `MainUICPP`.
  - Property and function names near the camp logic: `camp`, `campLocation`, `rallyingStatus`, `isEngaged`, `commandedSquads`, `activeCommandedSquads`, `selectedSquads`, `getPawnBySetupIndex`, `skills`, `skills_ralliedOnly`, `Update Skill Available And Tooltip`, `buildings`, `building`, `bType`, `demolish`, `button_demolish`.
  - `ProcessEvent` is called to run reflected functions. UE4SS version in the manifest: `3.0.1-942-gc0335505`.

## Camp, garrison and building questions (user focus)
- **Does it make a buildable army or siege camp?** No. Nothing in the pak or the strings creates a new `BM_` class, a `buildingStats` row or a construction Blueprint. The words `buildings`, `bType` and `demolish` appear, but the evidence says they read existing buildings (the tent icon belongs to the squad skill). The mod does not help issue #94 (a buildable siege camp). I could not read the DLL logic; I only read its strings.
- **How does Encamp work?** Most likely it writes the squad properties `camp` and `campLocation` (both are names of `Squad` fields; the baron mods in spec 13 also read `campLocation`) and sets `rallyingStatus`, then adds the skill buttons to `retinueEditor` through `skillButton`. This is an inference from names, not proven.

## Garrison (coordinator question)
- Search result: the word "garrison" does not appear in the DLL. The only close name is `garrisonedIn`, which is a wrapper field list entry for `SMUnit` (a unit property: the building it is garrisoned in). No `garrisonLimit`, no `getModularGarrisonLimit`, no garrison building function, no assignment call.
- So the mod does NOT put squads into the camp, and it does not reuse the manor garrison system (type 57, `getModularGarrisonLimit`, keep `garrisonLimit`; see spec 12 `manor-survey.md` and spec 14 `free-walls.md`).
- What it means for us: a camp here is a squad state (a position and a status). The "garrison" of soldiers is just the squad that stays at `campLocation`. For a buildable camp that holds soldiers we still need the manor garrison route: a `buildingStats` row with `garrisonLimit` and a building class that has a garrison function. Test idea below.

## Game version and staleness
Manifest: game 0.8.065, UE4SS 3.0.1-942. Our game is 0.8.111 (about 46 builds newer). The mod refuses other versions ("Unsupported game version" string). It would not load on 0.8.111 without a rebuild. Names that other notes found stale: `RTSMultiEngineCPP.squads`, `skillButton` and `retinueEditor` widget layout (spec 13 summary: UI rebuilt). Not run, so staleness is by version only.

## Risk review
Native DLL, 829 KB, built from a developer path (`C:\Users\EronG\...`, PDB name only). Imports include file calls (`CreateFileW`, `FindFirstFileW`, `GetModuleFileNameW`) that fit the mod framework (manifest and data folder). No network API names (no `WinHttp`, `socket`) in the strings I read. It is not signed. Do not install. It calls game functions through `ProcessEvent`, so it is also a crash risk on a newer game. The MLToolbox and MLModPresence companions it names are not in the archive.

## Lessons for us
- Squad `camp` and `campLocation` are named fields. We can read them with the bridge (`get_property` on a `Squad`) before and after a baron camps. This is a cheap spike for spec 10 (where the baron army waits).
- Naming pattern: new squad skills are made by adding a button to `skillButton` in `retinueEditor` (UI, DLL). We do not need this.
- It confirms there is no mod-made siege camp, so #94 stays a pak/data job (spec 18 `siege-camp-build.md`).
## Test idea
Spike `squad-camp-fields`: with the bridge, dump `Squad` property list for `camp`, `campLocation`, `rallyingStatus` on the player's squads and on the baron's during a challenge. Assert the fields exist and change when the army stops to camp. No mod install needed.
