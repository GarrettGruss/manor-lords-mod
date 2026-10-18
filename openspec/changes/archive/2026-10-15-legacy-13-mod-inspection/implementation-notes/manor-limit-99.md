# Inspection: ManorLimit99 (pak for game 0.8.083)

Date: 2026-10-11. Source: `C:\Users\garre\Downloads\ManorLords 0.8.083 ManorLimit99 343 1 2026-08-02T00-25Z 5VzvODT6J`.
The pak was listed and unpacked with repak into the session scratchpad. Nothing from the folder was run, installed or copied into the repo.

## Files
| File | Size (bytes) | SHA-256 |
|---|---|---|
| ManorLords_0.8.083_ManorLimit99.pak | 18622 | f88ee52ca79c3a1b0f7d7039ea58e793f1fbf5fd9a64d598a6bfaa00289aa2ee |

No readme, no license, no author name. Pak: version V3, zlib compression, index not encrypted, mount point `../../../../../docs/ManorLords/Content/NotStronghold/Data/`, 2 entries:
- `ManorLords/Content/NotStronghold/Data/buildingStats.uasset` (46257 bytes unpacked)
- `ManorLords/Content/NotStronghold/Data/buildingStats.uexp` (37103 bytes unpacked)
The pak is not encrypted, so no key was needed.

## What it does for the player
It raises the per-region limit of the manor buildings to 99. A region can then hold many Keeps, Tax Collectors and Palaces. The pak replaces the whole `buildingStats` table (its only asset).

## How it works
- Mechanism: a pak that overrides the data table `/Game/NotStronghold/Data/buildingStats` (row struct `/Script/ManorLords.Stat`). It is the same table as in spec 12.
- The pak holds the whole table (102 rows), not a patch. Every other row is the 0.8.083 value. On 0.8.111 it would also reset any value that changed after 0.8.083.
- `tojson` (UAssetGUI with our mapping) wrote a RawExport for this asset, so I got no row JSON. I read the rows by hand from the `.uexp` (unversioned properties, 102 rows, row name = type id) and checked the layout against the `Stat` struct in the jmap. See "Confidence".
- Changed value found: the integer **99** at the position of `maxInRegion` in 7 rows. All have `moduleCategory` = 2 (Manor):

  | Row id | Name in pak (DisplayName) |
  |---|---|
  | 57 | manor_keep_lv1 |
  | 475 | manor_keep_lv2 |
  | 83 | manor_keep_lv3 |
  | 58 | Tax Collector |
  | 98 | manor_palace_lv1 |
  | 474 | manor_palace_lv2 |
  | 81 | manor_palace_lv3 |

- Not changed: walls (470, 471, 476, 477, 480-482), gate modules (95, 82, 478), outer towers (472, 479) and all normal buildings hold 0 (unlimited). Row 95 (manor_gate_lv1) holds 2 at that place. I read this as a vanilla limit that the mod did not touch.
- The vanilla `maxInRegion` of the Keep is not in the pak and not in our notes. By inference it is a small number, probably 1. Reasons: our second Keep is refused, and the Lua mod (`storage-and-manor-unlock.md`) lifts only values with `0 < old < 99`.
- Storage fields in the same table equal our 0.8.111 findings: Keep (57) generic 50, Storehouse (72) 250, Storehouse_Lv2 (99) 2500, Granary (80) pantry 500, Granary Lv2 (68) 2500. So the pak does not change storage.
- Table size: 102 rows here, 104 in our game (`worker-slots.md`). The `Stat` struct in the 0.8.111 jmap has 75 properties. The rows in the pak list 73 values. The two last properties in struct order are `placedWithin` and `requiredTech`. They may be new since 0.8.083. This is not proven: trailing zero values can also be left out in this format.

### Confidence
- High: the pak layout, the row set, the DisplayNames, and that only rows 57, 58, 81, 83, 98, 474 and 475 hold 99 at that place.
- Medium: that this 99 is `maxInRegion`. Reasons: the position is the same in all manor rows, it is 0 in the rows of normal buildings, and the Lua mod names `maxInRegion -> 99` with the same effect. (Row 108, clay_furnace, holds a 99 at another place. I treat it as another field.)
- Not done: a full decode to JSON and a diff to the vanilla table. The vanilla table would need the game pak and the key. I did not do this.

## Target game version and stale signs
- Target 0.8.083. Our game is 0.8.111.
- `maxInRegion`, `moduleCategory` (value 2 = Manor) and `isModule` exist in the 0.8.111 jmap (`/Script/ManorLords.Stat`, `/Script/ManorLords.EModuleCategory`). The mechanism has not been renamed.
- Do not install this whole-table pak on 0.8.111. It would replace the 0.8.111 table with the 0.8.083 table (2 rows fewer, older values). Writing only the field from Lua is safer.

## Risk review
- No code. A data table only. No file, network or process access.
- The risk is a stale table in a new game version, because the pak ships the whole table.

## Lessons for us
- Q5 (manors per region): a mod author lifted the manor limit by data, on the manor rows only. The "one Keep per region" check is therefore probably the `maxInRegion` column read by C++. Our note "a unique-building rule in C++" stays true, but a Lua write to the row may be enough. We did not test this.
- Several manors in one region: the pak allows 99 Keeps and 99 Palaces by data. Nothing in the pak or the Lua README proves that the game then runs several manors. `Region.manor` is one reference (spec 12 Q5). This needs a game test.
- M2 (normal buildings inside the manor area): the pak changes no placement rule for normal buildings. It does not solve M2. `placedWithin` (jmap offset 908) is a new field to read on the Keep and on normal rows.
- Technique: when UAssetGUI gives a RawExport, a hand decode of the `.uexp` still works for the end of each row. The row boundary is the row-name FName plus the unversioned header. A cheap compare is to look for one value (here 99) across all rows. Add a diff-to-vanilla command to `harness/tools/pakmod.py` if we need this again.
- Test idea (harness): the same as in `storage-and-manor-unlock.md`. Write `maxInRegion` of row 57 at run time, place two Keeps, assert two type 57 buildings. Then repeat for row 98 (Palace) and row 58 (Tax Collector). Then check what the planner and the bailey do with two Keeps.
