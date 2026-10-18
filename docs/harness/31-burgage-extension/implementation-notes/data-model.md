# Data model of a burgage extension (2026-10-18)

Sources: jmap of the game, exported tables in the git-ignored `modtools/work/json`, the blueprint `BM_SG_Ext_TailorShed`, and the runs in the other notes.

## What an extension is
- A plot is one `SMBuildingMaster` (bType 3). `Extensions[]` holds the yard. Each entry has `Type`, `transf`, `buildings` (its parts) and `dirtPlanes`.
- `Extension.Type` is a number. Its enum is native: `EExtensionType` has 17 values: 0 Clutter, 1 ChickenCoop, 2 AnimalPen, 3 Blacksmith, 4 Bakery, 5 Brewery, 6 Tailor, 7 Cobbler, 8 VegetableGarden, 9 Joiner, 10 Armorer, 11 Bowyer, 12 Orchard, 13 Butcher, 14 Apiary, 15 Cheesemonger, 16 Fishmonger, 17 Count. There is no weaver.
- The weaver exists only as a stand-alone building (`buildingStats` row 33, job 14, shown input flax 11 and wool 23, shown output linen 12 and yarn 148).

## Tables and classes that touch an extension
| Piece | Where | What it holds |
|---|---|---|
| Upgrade row | `DT_Upgrades` row `100 + Type` (`extension6` = row 106) | cost, `regionalWealth`, perks, `minimumHouseLv`, `descr`, icon. Only these. |
| Part list | `DT_IndependentBuildingPartAssemblies` (row `extension_tailorShed`) -> class `BM_SG_Ext_TailorShed` | Blueprint with the parts: `FullBld_162` (the shed mesh), `clutter_*`, `res_<item>_<n>` (goods piles) and `workpos`, `workpos1` (where the worker stands). |
| Mesh | `/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_Ext_TailorShed_Ubeam` | the shed |
| Construction | `DT_ConstructionBPs` row 162 -> `C_SG_Ext_TailorShed_Ubeam` | build animation |
| Job | native `SMBuildingMaster:changeArtisanType(Type)` and `PawnCPP:addArtisanChangeRequest` | `artisanJob`: Tailor (6) gives job 10. The map is in native code. |
| Recipe | `DT_Items`: the row of the product has `Resources` (input), `craftingOutput`, `craftingTool` | vanilla already has yarn 148 = 1 wool 23 -> 1 yarn and linen 12 = 1 flax 11 -> 1 linen (tool 260, distaff). Clothes: items 8 and 34 (yarn or linen -> 149). |
| Enable a recipe | `SMBuildingMaster:EnableRecipe(goodID)` | the player does it in the panel |

The maps "extension number -> part blueprint" and "extension number -> job" are not in any exported table or plot blueprint. The plot blueprint `BM_SG_Cottage_Lv1_A` does not mention the tailor. They are native.

## Plot calls that work without the mouse (verified, spec 15 and this spec)
- `PawnCPP:addExtensionChangeRequest({buildingMaster, upgradeID = <Type>, Slot = 0})`: the plot is rebuilt, `upgradesDone` gets `100 + Type`, the cost is charged (tailor: 6 planks, row 106).
- `PawnCPP:addArtisanChangeRequest({buildingMaster, upgradeID = <Type>, Slot = 0})`: after the extension is built. `artisanJob` becomes 10, `assigned_families` 1, and the cost of row 106 is charged again (6 planks).
- Harness commands: `plot_upgrade` (flags `extension` and `artisan`), `master_artisan` (read), `master_artisan_set` (UNSAFE: `job`, `lv`, `enable_recipe`, `extension_type`).

## Reading limits found
- Arrays that a UFunction returns (`GetAllAvailableRecipes`, `GetActiveRecipes`, `GetAllProducedGoods`) read as empty in Lua, also on a sawpit that makes planks. Do not trust them.
- `StaticMeshComponent0.Bounds.BoxExtent` does not read (empty). Mesh size must come from the cooked asset or from UE.
