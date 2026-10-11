# AllYearOrchards 60Day SpringToAutumn (TLAYOrch v0.4.5, Nexus 387)

Source: `Downloads\AllYearOrchards 60Day SpringToAutumn 387 1 2026-09-21T15-53Z Leir1xqRT\TLAYOrch\`.
Target: Manor Lords 0.8.104 + UE4SS (`Scripts/main.lua:2`, `README_中文.txt:2`). Nothing was run.

## What it does for the player
- Apple, pear and quince trees can be harvested from 1 March to 30 November (game day 60 to 334). Winter (December to February) is dormant.
- A mature tree gets a new batch of fruit about every 60 game days. A picked tree does not refill the next day.
- Base yield and tree growth speed are not changed. Other crops keep the vanilla season (`README_中文.txt:4-15`).
- Ctrl+Alt+Y arms one refresh by hand. It is refused in winter (`main.lua:362-374`).

## How
Two parts: a Lua data change and a native pulse.

1. Season data (Lua, no DLL). `StaticFindObject("/Script/ManorLords.Default__CropSettings")` finds the class default object (`main.lua:157`). Property `HarvestSeason` is an array of 16 `IntPoint` values, one per crop type (jmap: `array_dim` 16, struct `/Script/CoreUObject.IntPoint`). Lua writes the text `(X=60,Y=334)` into the entries for crop indices 9, 13, 14 (apple, pear, quince) with `prop:ContainerPtrToValuePtr(owner, index)` and `prop:ImportText(...)` (`main.lua:172-209`, `FRUIT` at line 21). It repeats this at startup and at each map load (`RegisterLoadMapPostHook`, `main.lua:350`).
2. Fruit refill (native). The base game recomputes crop yield each day. The mod needs it to recompute only once per 60 days. It does so by loading a native patch DLL for one game day, then loading a second DLL that restores the code. `HarvestPulseOn.dll` and `HarvestPulseOff.dll` differ in a few bytes of a code descriptor (`HarvestAllYear`): in the Off file a jump `75 0B` is present, in the On file it is `90 90` (a no-op). Lua copies the template to `native/runtime_NNN_ON.dll`, writes `native.cfg`, loads it with `package.loadlib(runtime, "MLTweaks_Init")` and calls it (`main.lua:95-132`).
3. Clock. Reads `WeatherMaster.daysTotal`, `day`, `month`, `dayOfTheMonth` every 250 ms (`pollDay`, `main.lua:266-324`). The header comment says `daysSinceLastRaid` is not a day clock (`main.lua:6-9`). When 59 days passed in the fruit season, it turns the pulse on; on the next day change it turns it off (`main.lua:303-322`). If the clock jumps by 0 or more than 120 days it rebaselines (`main.lua:284-292`).

## Why a DLL is needed
The yield refill is in the game's compiled code (a daily crop-yield routine). It has no reflected UFunction to call. The DLL patches the code in memory: it finds byte patterns in the game exe, changes memory protection with `VirtualProtect`, and writes new bytes. The strings show 5 other features from the upstream tool (carry capacity, free upgrade, wildlife cap, per-crop yield, crop settings); they stay off because `native.cfg` sets them to 0 (`main.lua:59-78`).

## Version and signs of staleness
- The DLL logs "signature found N times - SKIPPED (game version changed?)" when a pattern does not match. On a new build the patch does nothing, safely. It has no check for game version.
- `WeatherMaster` is not a class in the 0.8.111 jmap (see `refugees-expanded.md`). The fields it reads now sit on `TemporalComponent` (`day`, `daysTotal` as Int64, `month`, `dayOfTheMonth`, `Year`, `Season`, `isWinter`). So the clock read probably fails on 0.8.111 and the pulse would never arm. The `HarvestSeason` write itself is still valid.
- Jmap check: `CropSettings.HarvestSeason` exists as `IntPoint[16]`; `HarvestGrowthThreshold`, `WinterGardenGrowthMultiplier`, `BaseDailyGrowthRate[16]` and `BaseYieldPer100Plants[16]` exist too. The default object in the jmap shows `(244,273)` for all 16 entries, so the dump does not give the real per-crop values (the real values come from a Blueprint subclass or data). Do not rely on it.

## Risk review
- Native code: two DLLs of 239,104 bytes each, built from MLTweaks by miu0007 (strings: `Source: https://github.com/miu0007/LM-Tweaks`, `MLTweaksNative`). Imports: `KERNEL32` only, plus `GetProcAddress` and `LoadLibraryExW`. No network imports were found. Strings include `VirtualProtect`, `VirtualAlloc`, `CreateFileW`, `CreateThread`: the DLL starts a thread, patches game code in memory and reads `native.cfg`, writes `native_log.txt` and `crop_settings.txt` in `ue4ss\Mods\TLAYOrch\`.
- It patches executable code. A wrong match could crash the game; the DLL counts pattern hits and skips if the count is not 1.
- The Lua copies a DLL to a new file and loads the copy many times (one load per pulse). Loaded copies are never unloaded. It deletes up to 500 old copies at startup with `os.remove` (`main.lua:334-337`).
- Paths are hard-coded `ue4ss/Mods/TLAYOrch/` relative to the game folder (`main.lua:16`).

| File | Size | SHA-256 |
|---|---|---|
| `native/templates/HarvestPulseOff.dll` | 239,104 | `52c1fde44bc087b9287cab76446260e495a3b0ffd08a11e68c6e70a598c2e1e` |
| `native/templates/HarvestPulseOn.dll` | 239,104 | `7067853387dc67fed0bcc35115f560456d7e86f2b618d42da8f7e144983a3cb8` |

License: `CREDITS.txt` says the native templates come from MLTweaks 1.1.0 and "the upstream package explicitly permits modification, reuse and redistribution". The notice in the tree-regeneration mod says MLTweaks is MIT. The orchard Lua itself has no license text. Author tag: "TL" (no name).

## Lessons for us
- Not relevant to P3 or R3.
- Technique 1: write a reflected array property of a class default object from Lua with `Reflection():GetProperty(name)`, `ContainerPtrToValuePtr`, `ImportText`. This changes data tables (for example `CropSettings`) without a pak. It could change other `Default__` data tables in our tests. This is worth a note for spec 12 style balance tests.
- Technique 2: a pulse model for a native toggle (on for one tick, then off) for a daily routine that has no UFunction.
- Technique 3: use a monotonic day counter (`daysTotal`) as a clock and rebaseline when it jumps; reject `daysSinceLastRaid` as a clock.
- Test idea: read `Default__CropSettings.HarvestSeason[9]` before and after the mod's Lua write to confirm that ImportText works on 0.8.111, then read the value back. Needs no DLL, and it is a cheap check of the season-edit technique.
