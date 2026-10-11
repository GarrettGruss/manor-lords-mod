# TreeRegeneration v1.0.0 (Nexus 407)

Source: `Downloads\TreeRegeneration 407 1 2026-10-10T08-00Z p6DC7o36X\TreeRegeneration\`.
Target: Manor Lords 0.8.111 and UE4SS 3.0.1 Beta, revision f6d5f942 (`README.md:12-13`). The DLL prints `READY game=0.8.111 ...`. This is the only mod in group B made for our game version. Nothing was run.

## What it does for the player
It plants young trees near adult trees at forest edges and clearings, in all regions (player, neutral, AI). The trees use the game's own growth and save system. At most one tree per region per game day. Chance per region per day is `DailyPlantingChance` (default 0.5). Seed distance 6.5 to 14 m from an adult. Trunks keep 4.75 m apart. Buildings, roads, water and ponds are avoided (`README.md:42-62`, `scripts/config.lua`).

## How
Lua (14 files in `scripts/`) finds a place and adds the visual tree. A native DLL then registers the tree with the game's growth data.

Scheduling (`regeneration.lua`):
- `NotifyOnNewObject("/Script/ManorLords.RTSMultiEngineCPP", ...)` starts the worker when the engine object appears (`regeneration.lua:281`). `RegisterLoadMapPreHook` stops it (`:288`).
- `LoopInGameThreadWithDelay(50, ...)` is the worker (`:249`). Each tick does one small job. Day from `engine:getDaysTotal()`; pause test from `player:getGameSpeed() <= 0` (`:163-176`). It rolls `random() < DailyPlantingChance` once per region per day (`:219`).
- Index: it builds a candidate list in small steps (even when paused) and rebuilds it every 30 game days (`index_builder.lua`, `edge_index.lua`; samples 8 per adult, capacity 4096 per region).
- `ModRef:GetSharedVariable` is used as a generation counter, so a reload stops the old worker (`:46-58`).
- Console command `tr_status` via `RegisterConsoleCommandHandler` (`:264`).

Game objects and properties (`game_api.lua`, `planting.lua`):
- `RTSMultiEngineCPP`: `regions`, `pawns`, `treeMeshes`, `youngTreeMeshes`, `treeMeshesTriggeringForestBiome`, `getDaysTotal`, `getRegionByPos(Pos, skipBoundCheck)`.
- `Region.regionalFoliage`: array of instanced static mesh components. Trees are instances in these. The young-tree component is found by mesh name containing `stc_oak_photog_babya` (`game_api.lua:92-105`).
- `InstancedStaticMeshComponent`: `AddInstanceWorldSpace`, `RemoveInstance`, `GetInstanceCount`, `GetInstanceTransform`, `GetInstancesOverlappingSphere`.
- `SMBuildingMaster` (`FindAllOf`, `GetActorBounds`), `Road` (`Spline`, `roadWidth`, `FindLocationClosestToWorldLocation`), `MLWaterBodyRiver`, `/Script/Water.*` classes, `KismetSystemLibrary:LineTraceSingle`, `CapsuleOverlapComponents`, `GetComponentBounds`.
- Signature guard: `checkSignature(path, {param = PropertyType})` compares the parameter list of each function and stops the mod if it differs (`unreal.lua:44-56`, `game_api.lua:10-45`). A good pattern.

Planting step (`planting.lua:473-502`):
1. `baby:AddInstanceWorldSpace(transform)` adds the visible young tree to the region's component. Scale 1.75 to 2.0.
2. `bridge.register(region, baby, transform, day)` asks the DLL to register the tree as a growing tree. If the DLL refuses, Lua removes the instance again (`RemoveInstance`).
3. The DLL answers `OK id=... growing=N->M`. Lua checks the id and stops on any unknown result.

Lua to DLL channel (`native_bridge.lua`): `package.loadlib(dll, "NTR_Init")` and `"NTR_Process"`. Lua writes `native-request.txt` (`NTR1`, `id`, `region=<hex address>`, `component=<hex address>`, `day`, rotation, translation, scale), calls `NTR_Process`, then reads `native-response.txt` and `native-status.txt`.

## Why a DLL is needed
The visual tree alone would not grow and would not be saved. The game keeps a separate list of "growing" foliage. No reflected UFunction adds to it. The DLL finds the game's own planting routine by a byte signature in the exe and calls it with the region, the component, the transform and the day (strings: `ready: 0.8.111 planting path at exe+0x%llX`, `UNSUPPORTED planting signature matches=%zu`, `registered: growing foliage %d -> %d`). The README says it "checks the game's planting signature and constructor" and stops when they do not match (`README.md:16-18`). The exact byte pattern is not readable as text in the DLL (it is probably stored as bytes). The author says the DLL follows the "signature-scanning and fail-closed approach" of ML-Tweaks (`native/NOTICE.txt`).

## Version and signs of staleness
Not stale. Checked in the 0.8.111 jmap: `Region.regionalFoliage`, `RTSMultiEngineCPP.regions/treeMeshes/youngTreeMeshes/treeMeshesTriggeringForestBiome`, `getDaysTotal`, `getRegionByPos`, `PawnCPP:getGameSpeed`, `Road.Spline/roadWidth`, `MLWaterBodyRiver`, `EBuildingType` all exist. `RTSMultiEngineCPP.pawns` was not found as a property; the mod uses it only as a fallback after `FindFirstOf("MyPawnCPP_BP3_C")` (`game_api.lua:51-54`). It does not use `WeatherMaster`. The DLL refuses to run on another game build.

## Risk review
- Native code: `native/TreeRegenerationNative.dll`, 411,136 bytes, compiled C++ with the standard library (strings: `NaturalTreeRegenerationNative.dll` and `.pdb`, `VirtualProtect`, `VirtualQuery`, Itanium demangler text). Imports only KERNEL32 and the C runtime. No network or process-creation API names were found. It reads and writes `native-request.txt`, `native-response.txt`, `native-status.txt` in the mod folder, and `native-log.txt`.
- `VirtualProtect` in the strings means it can change memory protection of game code. The README says it registers growth; whether it patches code was not found by reading strings. No source is included. Treat it as a binary that edits the running game. Review needs a disassembler before installation.
- Writes live game state (foliage instances and growth registration) every game day, in all regions. A wrong call can corrupt a save. The author reports tests of save/load, but only for their own setup.
- Lua writes log files in the mod folder (`regeneration-log.txt`, `native-log.txt`). It also creates `TextRenderActor` markers when marker options are on (off by default).
- License (`PERMISSIONS.txt`): personal use only. Redistribution, re-upload, modpack inclusion and public modified versions need the author's permission. `native/NOTICE.txt`: approach informed by MIT-licensed ML-Tweaks; no code from the "All Rights Reserved" Grow More Berry Bush mod. So we must not copy code from it. Ideas and the described method are fine to study.

| File | Size | SHA-256 |
|---|---|---|
| `native/TreeRegenerationNative.dll` | 411,136 | `d6134d58e90fdca9a72c011ec3e834e912817dcb44dbdf220139592802eb4cc6` |

## Lessons for us
- Not relevant to P3 or R3 directly.
- Proof that a mod can add world objects (foliage) in game 0.8.111 only by combining a reflected visual call (`AddInstanceWorldSpace`) with a native registration call. This is the same shape as refugees: the reflected function set is not enough for some state changes. Keep in mind for any "spawn a new thing and make it real" question (outposts, camps).
- Techniques we can use without any DLL:
  - `checkSignature` guard: fail loud at startup if a function's parameter names or types changed (our rule "Fail loudly").
  - Game-thread worker with `LoopInGameThreadWithDelay` and a small job per tick, with a generation counter in `ModRef` shared variables to stop old workers after a reload.
  - Day-change detection with `getDaysTotal` and pause detection with `getGameSpeed <= 0`.
  - Region lookup by position: `getRegionByPos`.
  - Request and response files with a unique id (matches our design rule "unique request IDs").
- Test idea: a read-only check that `Region.regionalFoliage` has a young-tree component and read `GetInstanceCount()` before and after N game days with the mod installed in a private copy, asserting a range (planting is random). Do this only after the DLL has been reviewed and the user approves.
