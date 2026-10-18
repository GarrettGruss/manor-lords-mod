# RefugeesExpanded v1.9.1 (Nexus 388)

Source: `Downloads\RefugeesExpanded 0.8.104 EN 388 1 2026-09-22T14-19Z 3akjNUoJE\RefugeesExpanded\`.
Target: Manor Lords 0.8.104, UE4SS 3.0.1 Beta (`README_EN.txt:17`). Nothing was run.

## What it does for the player
- Every 1.5 to 2.5 game years a modal window pauses the game (`CHANGELOG.txt:2`, `Scripts/config.lua:6-8`).
- The player rejects the refugees or accepts 5, 10 or 15 families, and picks a player region.
- Ctrl+Shift+F opens the event by hand (`main.lua:2030`).
- Accepted families arrive at the next month start. They are extra: normal growth does not use them up (`CHANGELOG.txt:5`).

## How it adds people (the answer for criterion P3)
The mod adds no new type of person. It calls the game's own growth function again and again.

1. Function: `/Script/ManorLords.Region:growPopulation` (`main.lua:742`). It has no parameters (guard at `main.lua:991-996` refuses to run if a parameter appears).
2. The call is made by a small native DLL, not by Lua. The DLL gets the Region address and the UFunction address from a text file written by Lua (`native_population.cfg`: `region=0x..`, `func=0x..`, `repeat=N`; `main.lua:833-835`, `RefugeesPopulationBridge.cpp:60-81`).
3. The DLL resolves the export `?ProcessEvent@UObject@Unreal@RC@@QEAAXPEAVUFunction@23@PEAX@Z` in `UE4SS.dll` and calls `ProcessEvent(region, func, nullptr)` N times, N from 1 to 32 (`RefugeesPopulationBridge.cpp:92-102`). It patches no game bytes (`BUILD_CLANGCL.txt:8`).
4. Lua checks the result with `Region:getTotalNumFamilies()` before and after, in the same game tick (`main.lua:998-1024`). It counts only the rise it sees (`credit_batch_growth`, `main.lua:922`).
5. Timing rule. The mod only calls on the first day of a month (`dayOfTheMonth == 1`, `main.lua:1090`, `1047`, `1113`). Comments call it the "valid immigration window" and "the game's month-start gate" (`main.lua:1043`, `1092`). If the game accepts only part of the group, the rest waits for the next month start (`CHANGELOG.txt:9`). If the player accepts at another day, the families wait for the next month start (`main.lua:1095-1101`).
6. Region choice: `PawnCPP:getAllCommandedRegions()`, with a fallback of `FindAllOf("Region")` and `region.ownerPawn` (`main.lua:553-587`).

Why was native code needed? The code does not say. Facts from its comments (`main.lua:729-740`):
- Version 1.5 hooked `growPopulation` with `RegisterHook`. A full September to October rollover gave zero ProcessEvent calls to it. So the game calls the function in native code, not through the reflection path. A Lua hook cannot see it, and waiting for the game to call it does not work.
- The mod therefore calls it itself. A plain Lua call (`region:growPopulation()`) is not used anywhere in the file. We do not know if the author tried it and failed. The DLL only does what a Lua call also does (ProcessEvent), so the DLL may not be needed. This is a question for our spike, not a fact.

Other game objects it reads (all guarded with `pcall`):
- `WeatherMaster` (`daysTotal`, `day`, `month`, `dayOfTheMonth`; `main.lua:272-417`). Fallback: `RTSMultiEngineCPP:getDaysTotal`, `getMonth`, `getDayOfTheMonth`.
- `PawnCPP`: `isMainPlayer`, `isAI`, `playEventMessage`, `playPopupMessageGUI`, `getAllCommandedRegions`. `Region`: `regionName`, `workerFamilies`, `ownerPawn`.
- UI: builds a UMG widget with `WidgetBlueprintLibrary`, `CanvasPanel`, `Border`, `TextBlock`, `Image`, loads `assets/refugees_banner.png` through `KismetRenderingLibrary`, pauses with `GameplayStatics:SetGamePaused` or `PlayerController:SetPause` (`main.lua:1257-1650`).
- Mouse clicks use screen hitboxes with `RegisterKeyBind(Key.LEFT_MOUSE_BUTTON)` (`main.lua:2065`).
- Timers: `LoopAsync(750)` poll, `ExecuteWithDelay`, `ExecuteInGameThread` (`main.lua:2116`).
- Schedule: a fixed pseudo-random gap from the absolute game day. No data goes into the save (`main.lua:295-347`).

## Version and signs of staleness
Checked against the 0.8.111 jmap (`ManorLords-5.5.4-40574608...jmap`, script `scratchpad\mods-B\chk*.py`).

| Name | In 0.8.111 jmap |
|---|---|
| `Region:growPopulation` | yes. `FUNC_Final \| FUNC_Native \| FUNC_BlueprintCallable`, no parameters |
| `Region:getTotalNumFamilies`, `workerFamilies`, `regionName`, `ownerPawn` | yes |
| `PawnCPP:getAllCommandedRegions`, `playEventMessage`, `playPopupMessageGUI`, `isMainPlayer` | yes |
| `RTSMultiEngineCPP:getDaysTotal` | yes |
| `RTSMultiEngineCPP:getMonth`, `getDayOfTheMonth` | no (`getMonthsTotal` exists) |
| class `WeatherMaster` | no class with "Weather" in its name. The fields `day`, `daysTotal`, `dayOfTheMonth`, `month`, `monthsTotal` are now on `/Script/ManorLords.TemporalComponent` |
| `MyRTSMultiEngineCPP_BP_C`, `MyPawnCPP_BP3_C` | yes |

Effect: the calendar read (`FindFirstOf("WeatherMaster")`) probably returns nothing on 0.8.111. The mod then falls back to `getDaysTotal`, which still works, but it loses `dayOfTheMonth`. It then uses a 30-day fallback (`main.lua:1123-1130`) and the month-start rule may not fire. The core call (`growPopulation`) is not stale. The mod needs a small fix before it can work on 0.8.111. This is a prediction from names only; a game test is needed.

## Risk review
- Native code: `RefugeesPopulationBridge.dll` (5,632 bytes). Source and strings agree: only KERNEL32 imports (`CreateFileW`, `ReadFile`, `WriteFile`, `GetModuleFileNameW`, `GetModuleHandleW`, `GetProcAddress`) and the UE4SS export above. No network, no process creation, no code patching. It reads `native_population.cfg` next to itself and writes `native_population.status`.
- Danger: it calls a UFunction by raw pointers from a text file, with no check that the pointers are valid. A bad file can crash the game. The Lua side writes the file, so the risk is low if we write it ourselves.
- It runs inside the game process. The game thread rule is kept (`ExecuteInGameThread`).
- Lua file access: reads and writes only in its own folder. It uses `package.loadlib` to load the DLL (`main.lua:803`).

Binary files:

| File | Size | SHA-256 |
|---|---|---|
| `native_bridge/RefugeesPopulationBridge.dll` | 5,632 | `e702e80f2a31e4b1745e12171b58e2d707073eea081b4a220f84a8543d7622a7` |
| `native_bridge/RefugeesPopulationBridge.lib` | 1,696 | `9ea85ffe097aa486620eb9eba7be71fe0dae2dd714a7a113e57b65d54b0212a1` |
| `native_src/bridge.obj` | 6,735 | `1f3686f32ed865e776d798b500881080ba9b262aa57d2f126e7d0744df96f527` |
| `native_src/kernel32.lib` | 2,496 | `ddc610aec6f6c7eeca8716a400a305d42a198c3fe37384c86df1738ec2b680da` |
| `assets/refugees_banner.png` | 2,932,406 | `375e75880fdb702ac094a9ee94488760a340337404dd9dbb10f303db6495e2cf` |

License: none given. The files name no author and no license.

## Lessons for us
Method for P3: yes, and it changes our spike result.
- Our spike called `growPopulation()` on all regions on random days and saw no change (`spike-P3.md`). We guessed the cause was missing housing. This mod suggests a second cause: the call has an effect only on the first day of a month. The mod never checks housing, but it does see that the game can accept only part of a group, so housing may still cap it. Neither point is proven.
- The mod's effect is one family per call, up to 32 calls per window, verified by `getTotalNumFamilies` before and after.
- New fact from the jmap, not used by this mod: `Region` also has `AddNewFamily(familyMembers: array)` returning an int, `AddNewFamilyMember(familyID, newMember: object)`, `accomodateHomelessFamilies(ignoreBuilding)` and `removeWorkerFamilyAt`. The P3 spike listed other `Region` functions but not these. They may allow a direct refugee, but they need unit objects, and the spike warned about fake families.
- Lua test needs no DLL at first: `region:growPopulation()` is a normal reflected UFunction and the bridge can call it with `call_function`.

Test idea for the harness (spike, needs a developed village):
1. Load a fixture where `getAvailableLivingSpace` shows free housing, or build burgage plots first.
2. Use the time controller to stop on a day with `TemporalComponent.dayOfTheMonth == 1`.
3. Read `getTotalNumFamilies`, `getNumTotalPopulation`. Call `growPopulation()` once on the game thread. Read again.
4. Repeat on day 15 as a control. If only day 1 works, record the gate in the spec 10 P3 notes.
5. If the Lua call fails and only a native ProcessEvent call works, that is the reason for the DLL. Record it.
Assert ranges, not exact values. Do not call any save function.
