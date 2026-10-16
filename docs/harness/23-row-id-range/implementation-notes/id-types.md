# Row id types and keys (spec 23, plan step 1, acceptance A1)

Date: 2026-10-15. Static only. The game was not run. No save function was called.
Sources: UAssetGUI JSON under `modtools/work/json/ManorLords/Content/NotStronghold/Data/`
(`buildingStats.json`, `buildingStats.json.vanilla`, `DT_Upgrades.json`, `DT_Items.json`,
`DT_ConstructionBPs.json`, `DT_BuildingMeshPathData.json`, `DT_IndependentBuildingPartAssemblies.json`),
the translation tables under `Content/Translation/HoodedHorse/`, and the UE4SS jmap
(`ue4ss/ManorLords-5.5.4-40574608+++UE5+Release-5.5-5e627997.jmap`). Counts were made with
short read-only scripts in the scratchpad.

## Summary

- In every table studied, the row name is the key. There is no id field in the row struct.
- Row names are text (FName). A numeric id is the text of a number, for example `"72"`.
- Native fields that hold a building type or an upgrade id are `int32` (jmap `IntProperty`).
- No `byte` field holds a building type id. Vanilla already uses ids above 255 (470 to 484).
- The highest vanilla building id is **484**, not 125. Spec 23 README says "the vanilla ids end near 125". That is wrong. 125 is a free id in vanilla, not the end of the range.
- `EBuildingType` has a sentinel `EBuildingType_MAX = 485`. Ids 485 and above are outside the enum. This is a risk (see Risks).

## Per table

### buildingStats (row struct `Stat`, building type table)

| Item | Value |
|---|---|
| Key | Row name (FName), text of the building type id. Example: row `"72"` is the Storehouse. Lua `FindRow("72")` works (`worker-slots.md`, spec 12). |
| Id field in row | None. `Stat` has 75 fields. |
| Row count | 104 vanilla (`buildingStats.json.vanilla`). 105 now (row 125 added by the mod). |
| Vanilla id range | 1 to 484. Largest vanilla ids: 472 to 484 (Manor and siege rows, `BurgagePlot_Lv4` = 484). |
| Gaps | About 380 ids unused in 0 to 484. Free ids near the test range in vanilla: 123, 124, 125, 126, 127, 128, 129 (checked: 125 is free in vanilla). |
| Id type in native fields | `int32` (`IntProperty`): `BuildingDataStruct.bType`, `SavedBuilding.bType`, `SavedCastleModule.bType`, `Region:getBuildingCount(bType)`, `RTSMultiEngineCPP:getBuildingData(buildingID)`, `isBuildingTypeValid(buildingID)`. |
| Enum | `EBuildingType`: 100 names, values 3 to 485. Values 470 to 484 are above 255. Underlying type shown as `UInt32` in two places (`PerkSettings` RuralBuildings and CraftsmenBuildings set keys). Probably this enum, not proven. |
| Byte fields | `pastureSpace`, `stableSpace`, `accidentRate`, `deathRate`, `deathFromCollapseRate` are `Byte`. They are counts and rates, not ids. |
| Upgrade links | `upgrades` is `Array<int32>` of DT_Upgrades row names (18 distinct values; all exist in DT_Upgrades). `upgradedFrom` is `int32` (a buildingStats id; 0 means none). |
| Display name key | `DisplayName` is a Name. The translation table `DT_Translation_BuildingNames` has keys `buildingID_<id>`. 73 of 105 rows have one. `buildingID_125` is missing. `buildingID_97` exists. |
| Real game evidence | Row 125 (clone of row 97, `small_stable`) loads, shows, is placed and built (spec 18). Row 123 (clone of 472) loads and builds (spec 12, `manor-module-pak.md`). |

### DT_Upgrades (row struct `Upgrade`)

| Item | Value |
|---|---|
| Key | Row name (FName), text of the upgrade id, `"0"` to `"116"`. Row `"ext"` is a separator line, not an upgrade. |
| Id field in row | None. |
| Row count | 62 (61 numeric + `ext`). |
| Id range | Max 116. Unused: 1, 3, 46 to 99. Used: 0, 2, 4 to 45, 100 to 116. |
| Link to building | `upgradesInto` is `int32`, a buildingStats row name. Targets: 8, 52, 60, 68, 97, 99, 114, 116, 120, 484. All exist as buildingStats rows. |
| Link from building | `buildingStats.upgrades` (`int32` array) holds DT_Upgrades row names. Example: row 3 (`residentialPlot_lv1`) has `upgrades` [2, 12]. DT_Upgrades row 2 has `upgradesInto` 8. This chain is consistent. |
| Native use | `RTSMultiEngineCPP:getUpgradeData(upgradeID int32)`, `SMBuildingMaster:hasUpgrade(upgradeID)`, `GetUpgradeResourceCost(InUpgradeID)`, `PawnCPP` `UpgradeRequest.upgradeID` (int32). `SavedBuilding.upgradesDone` is an int array. |
| Requires building | `requiresBuilding` is an int array. It is empty in every row. |
| Vanilla copy | None in `modtools/work`. The JSON was extracted on 2026-10-10. Assumed vanilla, not checked. |
| Real game evidence | None yet for a new upgrade row. Plan step 4. |

### DT_Items (row struct `Item`, not a building table; checked for overlap only)

| Item | Value |
|---|---|
| Key | Row name, text of the item id, `"-1"` to `"358"`. |
| Id type | `int32` in `craftingTool`, `Item.upgradesRequiredToCraft` (int array). |
| Gaps | 147 unused ids in -1 to 358. |
| Overlap | Ids 255 and 256 exist as item rows. They are a different id space from buildings. |

### Other keyed tables (all key = row name, text)

| Table | Rows | Key range | Note |
|---|---|---|---|
| `DT_ConstructionBPs` | 186 (183 numeric) | 20 to 1001 | Keys 200 and 1001 exist. 156 keys have no buildingStats row. Keys are the `MainBld_<key>` names used by modules (spec 12). Non-numeric keys: `443_cheapFence`, `below_are_gate_wall_and_stone_wall`, `walls_end`. |
| `DT_BuildingMeshPathData` | 72 | 20 to 543 | Keys 255 and 256 exist. The mesh path of a new building id reads this row (`getBuildingMeshForID`). |
| `DT_IndependentBuildingPartAssemblies` | 73 (22 numeric) | 20 to 540 | Key 200 exists. Non-numeric keys are section lines. |
| `DT_Translation_BuildingNames` | 91 | `buildingID_<id>` | Text table. Max numeric key 484. No key for 125. |
| `DT_Translation_BuildingDescriptions` | 76 | `buildingID_<id>_descr` | Text table. Max 484. |

## Free ids for the test candidates (plan step 2)

Checked against: buildingStats (current), DT_Upgrades, DT_ConstructionBPs, DT_BuildingMeshPathData, DT_IndependentBuildingPartAssemblies, DT_Items.

| Candidate id | buildingStats | DT_ConstructionBPs | DT_BuildingMeshPathData | Other | Status |
|---|---|---|---|---|---|
| 126 | free | free | free | free | free in all checked tables. Below 485. |
| 200 | free | **used** (key 200) | free | IndependentAssemblies **used** | Construction key exists. Clone may reuse it. |
| 255 | free | free | **used** | DT_Items **used** (item id) | Mesh row exists. Test with care. |
| 256 | free | free | **used** | DT_Items **used** (item id) | Mesh row exists. Test with care. |
| 1000 | free | free | free | free | Free. Above 484 (enum MAX 485 is above it). |
| 2000 | free | free | free | free | Free. Above enum range. |
| 32767 | free | free | free | free | Free. int16 max. |
| 65536 | free | free | free | free | Free. Above uint16. |

Note: 125 and 126 to 128 are free in vanilla buildingStats. Id 125 is the mod's current test row.

## Risks for large ids

1. **Enum range.** `EBuildingType_MAX` is 485. Native code may size an array with it, or index an array by building type. Ids 485 and above could then read or write outside the array. This is the main risk for ids 1000 and above. No native array sized by the id was found in the jmap, so this stays open (plan step 3 search could not prove it). Test ids below 485 first.
2. **Text keys.** Display names use `buildingID_<id>` in the text table. A new id with no key may show a missing-text label. Not tested.
3. **Mesh and construction rows.** A new building id reads `DT_BuildingMeshPathData` and `DT_ConstructionBPs` by the same number. Ids 200, 255, 256 and 1001 already have rows there. A new building may show the wrong mesh.
4. **int32 holds all candidates.** Every candidate fits in int32. A native 16-bit copy of the id would fail above 32767 or 65535. Not seen in the jmap.
5. **Native map keyed by int.** `BuildingSettings.BuildingPartData` is `TMap<int32, BuildingPartData>`. The meaning of its key is not known. It may be keyed by building type. Check in the real game or with a reader of its use.
6. **Row name text.** A row name must be plain digits (`"126"`). `"0126"` is a different name. Use the same text as the id.
7. **Int arrays of ids.** `MLBuildingCategory.BuildingTypes` (TArray<int32>), `AI_buildingTypes` (TArray<int32>) and `RTSMultiEngineCPP` lists hold building ids. A new id must be added to the right list (for example the AI build list) or the AI will not use it. Not checked in this step.

## Ids the real-game step should test (input for plan steps 2 to 4)

- buildingStats: 126 (free, below 485), 200 (construction key exists), 255 (mesh row exists), 256 (mesh row exists), 1000 (above enum MAX), 2000, 32767, 65536. The plan's list fits. Order: 126 first, then 255 and 200 (collision cases), then the high ids.
- DT_Upgrades: 2 new upgrade rows. Use free upgrade row names above 116 (for example 117 and 118) that point to the new building id (for example 126 and 1000). Check that `buildingStats.upgrades` of the source building lists the new upgrade id.
- Check the text key `buildingID_<id>` for each new building id. Add the key only in a separate test, so the effect of the missing key is seen.

## Open questions (not answered by static reads)

- Does native code index an array with the building id, or with the enum value? (Q2)
- Is `BuildingPartData` keyed by building id? (Q2)
- Is `EBuildingType` really `uint32`? Shown only for the sets in `PerkSettings`.
- Does the save file store the id as int32 with no other limit? (Save test is out of scope for spec 23.)
