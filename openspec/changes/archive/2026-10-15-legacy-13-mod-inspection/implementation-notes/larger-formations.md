# LargerFormations 1.0.0 (inspection note)

Date: 2026-10-11. Source: `C:\Users\garre\Downloads\LargerFormations 1.0.0 356 1 2026-08-20T15-02Z yiVQ96hxt`. Nothing was run or installed. The pak was unpacked with repak into the session scratchpad (`mods-C/lf-unpack`), not into the repo.

## Files and SHA-256
| File | Size | SHA-256 |
|---|---|---|
| `README.txt` | 1170 | `438e8b1cb66c4fa779b08416bd691de37dc193da0ba75e8704ef1d1a8de36840` |
| `ManorLords/Binaries/Win64/ue4ss/Mods/LargerFormations/enabled.txt` | 0 | (empty) |
| `.../LargerFormations/Scripts/main.lua` | 1298 | `3f24e9811c49f13208e49bdf7a98365bc0970967ac56b935e934d4b35bdb4a32` |
| `.../LargerFormations/dlls/LargerFormationsNative.dll` | 80896 | `13b8b4febe3c215970393087d24281abc4e5f99b7daa70b15b22f05e8dd9b5cf` |
| `ManorLords/Content/Paks/~mods/LargerFormations_P.pak` | 11803 | `a3c2a12be43347d13fa0b09cadf80eefc66ea0c0484cb3682cd29872382a7583` |
Archive: `LargerFormations 1.0.0 356 1 2026-08-20T15-02Z yiVQ96hxt.zip`, 38106 bytes, SHA-256 `b7b3114dde980b08b9355e376dd30a06a2520caf3b37058badd1a8cf92bc242c`.

## What it does for the player
Formations get twice as many soldiers, instead of more cards on the army bar (README.txt):
- normal formations 36 to 72, militia 36 to 72,
- brigand and special formations 18 to 36,
- retinue base limit 12 to 24, upgraded retinue limit 24 to 48.
README: "Tested with Manor Lords 0.8.083".

## How it works
Two parts. Both are needed.
1. **Native patcher (DLL).** `Scripts/main.lua` (lines 1-37) only calls `package.loadlib(<mod>/dlls/LargerFormationsNative.dll, "luaopen_LargerFormationsNative")` and runs the entry. The DLL (strings only, not disassembled):
   - scans the `.text` section of the game exe for six byte signatures with wildcards (`??`). The labels are `Normal formations`, `Militia formations`, `Special / Brigand formations` (also `SquadGeneratorShared`), `Retinue initial limit`, `Retinue garrison base`, `Retinue garrison upgrade`;
   - checks that each target holds the expected vanilla value, then patches the instruction operand in memory with `VirtualProtect` and `FlushInstructionCache`;
   - is transactional: "Validating all six patch targets...", "PATCH SET ABORTED. No Larger Formations patches were applied.", rollback on write error, and a final verification. Success text: "LARGER FORMATIONS ENABLED SUCCESSFULLY ... Normal formations: 36 -> 72";
   - writes a log `dlls/LargerFormationsNative.log` (C++ `ofstream`).
   So the formation size limits are constants in game code (the squad generator, militia squad code, retinue code), not in a data table.
2. **Pak `LargerFormations_P.pak`** (repak `info`: version V8B, not encrypted, no compression, mount `../../../../../docs/`, 2 files): `ManorLords/Content/NotStronghold/Data/DT_UnitTemplates.uasset` and `.uexp`. It replaces the whole unit table (29 rows, same names as the 0.8.111 table in spike S7).
   - The repo tool `pakmod.py tojson` gives a `RawExport` for this asset, which the tool refuses. I decoded the `.uexp` by hand with the jmap row struct `/Script/ManorLords.UnitTemplate` (unversioned properties; script in the scratchpad). The decode ended exactly at the end of the data, so the layout is right.
   - `maxSize` by row: militia rows (`bowMilitia, militiaFoot, spearMilitia, militiaPole, crossbowMilitia, militia, militiaFoot_testing, spearMilitiaTesting`) 32; `retinue_tier1, retinue_tier3, reginaldsRetinue, retinue_tier1_old` 60; `brigands, brigandArchers, brigandPolearms, brigands_old, basket, sherwoodBow, wrong_unit_type` 60; **the five mercenary rows `mercenary_archers, mercenary_heavy_archers, mercenary_spearmen, mercenary_infantry, mercenary_crossbowmen` 72**; `single` 1.
   - Spike S7 read 60 for the mercenary rows in 0.8.111. So the visible change is 60 to 72 on five rows. I did NOT diff against the vanilla asset (it needs the game paks and their key; the instruction was not to touch them). Other fields (item ids in `weapons`, `armours`, `cost`, `minHouseLv`) are 0.8.083 values. They may differ from 0.8.111.

## Game version and signs it is stale
- Target: 0.8.083 (README). This is 28 builds older than 0.8.111.
- Names in 0.8.111: `UnitTemplate` struct has all 27 fields the pak writes (`maxSize` at offset 256 and so on); `Squad.maxSize` exists; row names match S7. No name is stale.
- Stale risk is in the DLL: the signatures target code bytes of the 0.8.083 exe. The author says it aborts if a signature is not unique or a value is not the expected vanilla value. A 0.8.111 exe may match (the code is old), or not. Only a run shows it. The log file tells.
- The pak replaces the full table, so any 0.8.104 to 0.8.111 data change in `DT_UnitTemplates` is lost while it is installed. The pak is version V8B, our `pakmod` builds V11; the game accepts both in principle (not tested here).

## Risk review
- DLL (80 KB, MSVC, imports only `KERNEL32` and the C runtime): `VirtualProtect`, `FlushInstructionCache`, `GetModuleHandleW`, `GetModuleFileNameW`, `QueryPerformanceCounter`, file output through the C runtime. No network library, no process creation, no registry. It changes executable memory of the game process. A wrong patch crashes the game. Not run.
- Lua loader loads a DLL by path (`package.loadlib`), so it runs native code at game start.
- License: none given.

## Lessons for us
- Unit stats and formation size: **two layers.** Spike S7 showed `maxSize` of a row sets the number of units that `spawnArmy` makes, up to a shape limit (60 gave 36 or 18). This mod shows that shape limit is code (six constants) and that a pak also sets row `maxSize`. For our invasion mod: with data only (no DLL), the raid size cap per squad stays at 36 (18 for brigands); more men need more squads. A pak alone changes `maxSize`, which matters only below the code limit.
- Pak lesson: a unit table pak is a full replacement. Edit only what we need and rebuild from the current 0.8.111 table, not from an old copy. The decode method (hand parse with the jmap struct) is a fallback when `tojson` returns a RawExport. Possible follow-up for the pakmod tool.
- Retinue limits 12 and 24 (base and garrison upgrade) are separate constants, so the retinue size is not read from `DT_UnitTemplates.maxSize` (60).
- No steering, no raid or enemy logic here.

## Test idea for the harness
A/B scenario `formation-size`: variant A has no mod, variant B has a pak (built by us from the 0.8.111 table) that sets `mercenary_spearmen.maxSize` to 72 and `spearMilitia.maxSize` to 20. Use `spawn_army` with each template and count units per squad (`units_census`). Assert (range) that the count follows `min(maxSize, shape limit)`: 36 for the mercenary row (the shape limit holds) and 20 for the militia row (below the limit). This confirms the two-layer model before we depend on it.
