# Inspection: StorageAndManorUnlock 0.5.0 (for game 0.8.104)

Date: 2026-10-11. Source: `C:\Users\garre\Downloads\StorageAndManorUnlock 0.8.104 389 1 2026-09-23T06-19Z DB1bsWkhV`.
Nothing was run or copied. Line numbers refer to the files in that folder.

## Files
| File | Size (bytes) | SHA-256 |
|---|---|---|
| README.txt | 1417 | 2ccabd2792d6757a02c8ade3aab58521b325dae3f42e25d9bc6d7fa4376d96c3 |
| StorageAndManorUnlock/enabled.txt | 0 | (empty) |
| StorageAndManorUnlock/Scripts/config.lua | 2722 | 8116cb65f68ba4e8303ed28fe8bc4202ac9c818fe53c2044063f2640f6ceb1b6 |
| StorageAndManorUnlock/Scripts/main.lua | 10602 | ef38a640aea0ebfb7e5f97fac44715293341f52cff3b17f6ad00216ff03ce5f8 |

No binary file. No license text. No author name. The README says "v0.5.0 BALANCE TEST ... Manor Lords 0.8.104 + UE4SS 3.0.1 Beta".

## What it does for the player
- Raises the storage limit of about 55 buildings (storehouse, granary, farmhouse, burgage plots, camps, workshops, manor palaces).
- Raises every finite per-region building limit to 99 (`maxInRegion`). The README calls this the "manor/module unlock" (README line 14).
- It replaces an older "integrated PAK" that did the same with a data table. The README says to remove that pak and other storage mods (README line 8).

## How it works
Mechanism: UE4SS Lua. No hook. No UFunction call. It only writes fields of data table rows, from a retry loop.
1. `main.lua:164-171`: `StaticFindObject("/Game/NotStronghold/Data/buildingStats.buildingStats")`. This is the same table that spec 12 (`worker-slots.md`) uses.
2. `main.lua:173-178`: `dt:FindRow(tostring(id))`. The row name is the building type id as text. Same as our note.
3. `main.lua:180-188`: reads and writes row fields with plain Lua (`row[field]`, `row[field] = value`), each in `pcall`.
4. `main.lua:316-343`: `LoopAsync(5000, fn)`. It tries up to `retry_limit` (12) times, every 5 s, until the table is loaded. It stops when at least 25 storage rows and 25 fields were readable and at least one `maxInRegion` was readable.
   It writes from the async loop, not in `ExecuteInGameThread`. This is against our design rule, but it worked for the author (see "Risk review").

Storage writes (`main.lua:214-265`, values in `config.lua`): fields `storageLimitGeneric`, `storageLimitLarge`, `storageLimitPantry` on about 55 rows. Row ids used: 3, 4, 6, 7, 8, 14, 18, 20, 22, 28, 31-33, 35-37, 42, 43, 52, 59-61, 68, 69, 72, 73, 80, 81, 89, 91-93, 98-100, 103, 105, 108, 109, 111, 116-119, 473, 474, 483.
Examples (config.lua): Storehouse (72) generic 2500; Large Storehouse (99) generic 25000; Granary (80) pantry 2500; Large Granary (68) pantry 25000; Farmhouse (69) 1200/1200; Construction Yard (119) generic 3000, large 200; Manor Palace Lv1/2/3 (98, 474, 81) 250/250.
The labels in the Lua file do not always match the names in the 0.8.083 pak (for example the pak names row 68 "Granary" and row 80 "granary_lv1"). Treat the labels as the author's guess. Three rows (22, 73, 109) are "unmapped" in the file itself.

Manor limit unlock (`main.lua:288-311`): for each row id 0 to 500, read `maxInRegion`. If `0 < old < 99`, write 99 (`config.lua:123`, `region_limit_target = 99`).
- 0 is unlimited, so rows with 0 stay 0.
- The rule is blind. It lifts every finite limit, not only manor rows. It does not name the Keep (57), but the Keep has a finite limit, so it is lifted.
- The README says the effect is "confirmed" in game (README line 14). We did not verify this. It is the author's report.

## Target game version and stale signs
- Target 0.8.104. Our game is 0.8.111.
- Names checked against the jmap of 0.8.111 (`/Script/ManorLords.Stat`, 75 properties): `maxInRegion` (offset 744, IntProperty), `storageLimitGeneric` (888), `storageLimitLarge` (892), `storageLimitPantry` (896) all exist. No name is missing.
- The data table object is not in the jmap (the jmap holds classes, not this instance; the key `/Game/NotStronghold/Data/buildingStats.buildingStats` is absent). Our spec 12 note `worker-slots.md` verified live that `/Game/NotStronghold/Data/buildingStats` is loaded and that `FindRow("<id>")` and field writes work in 0.8.111.
- Row ids can move between versions. Rows 22, 73 and 109 are unmapped in the mod. Our 0.8.111 values for rows 57, 68, 72, 80, 99 (50, 2500, 250, 500, 2500) match the values in the older pak (see `manor-limit-99.md`), so those ids look stable. Do not rely on this for other rows.
- Verdict: probably still works on 0.8.111. Not tested in game.

## Risk review
- No file, network, process or registry access. No `os`, no `io`, no `require` of other mods.
- It reads its own `config.lua` with `dofile` from the path of its own script (`main.lua:141-156`). It only loads a file next to itself.
- It writes data table rows in memory. It never saves. It calls no save function. It does not touch saves.
- Writes from `LoopAsync` may run off the game thread. Plain number fields have worked for us from the bridge, so the risk is low. A crash is possible if the table is half loaded.
- It lifts all finite building limits. Side effects are unknown (for example other one-per-region special buildings). Untested.

## Lessons for us
- M1 (storage in the manor): it confirms our method. Storage capacity is a field of the `buildingStats` row, writable from Lua at run time. We already write the Keep row (spec 12 `worker-slots.md`). New idea: the mod sets Manor Palace rows (98, 474, 81) to 250/250 while the Keep is 50 in the base data. We can raise `storageLimitGeneric` of the Keep row the same way.
- M2 (several manors, normal buildings in the manor):
  - The data column `maxInRegion` in `/Script/ManorLords.Stat` is the likely owner of the "one Keep per region" rule. Our spec 12 note says the check "counts buildings of type 57 ... a unique-building rule in C++". A C++ rule can still read a data column. The community mod lifts `maxInRegion` and says it unlocks the manor and modules. This gives a new, cheap test: write `maxInRegion = 99` into row "57" at run time, then place a second Keep. It bears on Q5. It does not show that two manors work (`Region.manor` is one reference).
  - It says nothing about normal buildings inside the manor area (Q4).
  - Fields in the jmap that we have not used: `placedWithin` (int, offset 908), `isModule`, `moduleCategory` (enum, 2 = Manor). `placedWithin` could be a placement link. The older pak (0.8.083) has no value for it (see `manor-limit-99.md`). A spike should read `placedWithin` on all rows.
- Technique: retry with `LoopAsync` until the data table is loaded, then log OK, PAK, MISS or ERROR for each row. We can copy the idea (not the code) for a data helper that reads, writes and reads back a row field with a log line.
- Test idea (harness): scenario `manor-region-limit`. (1) Read `maxInRegion` of row 57 through the bridge. (2) Write 99. (3) Place a Keep, finish it with the shortcut, place a second Keep. (4) Assert 2 buildings of type 57 and record `Region.manor`. Control: without the write, the second click places nothing (known from spec 12). Repeat for a Palace and for the Tax Collector.
