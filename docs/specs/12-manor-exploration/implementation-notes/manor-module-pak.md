# Manor module added by a pak (issue #65)

Date: 2026-10-13. Game 0.8.111. Fixture `manor-bailey` (1 family, 5 residents, built palace). Run `s65-1` (1 game launch).
The AES key was read from the environment only. No save function was called. Autosave was set one year away (`disable_autosave`) and checked.

## Short answer
- A pak CAN add a new manor module row. The game loaded it and a mod-planned blueprint of the new type was committed and handled by the builders.
- The planner list is NOT data. It is a fixed list of `buildingWidget` entries in the widget Blueprint `castlePlanner`. A pak can change it.
- Not finished: whether the planner shows the new card, and whether the new module is finished by builders. See "Open".

## How the planner lists modules
- `ManorModules` is only a folder of `BM_SG_Manor_*` Blueprints (empty mesh actors). There is no data asset of that name (the earlier note was wrong).
- `buildingStats` has 19 rows with `moduleCategory` Manor: 57, 58, 81, 82, 83, 95, 98, 470, 471, 472, 474 to 482. Unused type ids below 484: 2, 9, 11, 12, 15 to 17, 19, 23, 24, 27, 29, 38, 41, 44, 47 to 49, 51, 54 to 56, 63 to 67, 70, 71, 74, 90, 94, 96, 101, 123 and up.
- `castlePlanner` (UI/Castle_Planner) holds 10 `buildingWidget` entries with a fixed `ID`: 98, 57, 58, 83, 81, 81, 95, 50, 57, 472. Some are `Collapsed` (the game shows them by level). The cards use `card_keep_lv1`, `card_sg_Gatehouse`, `card_tax_collector`, `card_tower_lv1`. So a new module needs a new or retargeted widget entry. The row alone is not enough.

## Pak method (works)
1. `roundtrip` of `buildingStats` and `castlePlanner` is byte-equal.
2. New row: clone row 472 (outer tower) as row `123` (script `harness/tools/s65_edit_json.py stats`). The name `123` MUST be added to `NameMap` too. Without it UAssetGUI 1.1.0 exits 0 and writes no file.
3. Planner: `s65_edit_json.py planner` sets `ID` 123 on the collapsed widget `buildingWidget_5` and removes its `Visibility`.
4. Two paks: `mm123data` (row only, 86 KB) and `mm123ui` (planner only, 117 KB). Both were installed. The game started and loaded the save without error.

## Results (run s65-1)
| Check | Result |
|---|---|
| `building_stat type=123` | row exists, `name` manor_outertower_lv1, `maxInRegion` 0 (new row read by the game) |
| `manor_blueprint_add type=123` (new `mesh` argument) | blueprint actor tagged `bType_123` added to the manor (`blueprints` 5 to 6) |
| Commit (`convertBlueprintsToBuildings`) | accepted, no crash. Manor became "under construction". Parts 90 to 98 (the 3 old plans plus mine) |
| Builders | the manor panel shows transported goods (timber 4/12, rubble 5/24 then 12/24 after about 25 game days). The carrier works slowly: the village had 1 family of 2 working people |
| Planner card for 123 | NOT checked: the manor cannot open the planner while it is under construction |
| Finished module | NOT reached |

Mesh limit: the tower mesh path from the row (`SM_MERGED_C_SG_Manor_Tower_Lv1_00`) was not loaded and `LoadAsset` found nothing, so the test used the loaded gatehouse and palace meshes. A mod-made blueprint can use only a mesh the game has loaded.
Side effect to know: committing a module makes a finished manor a construction site again. Hunger pop-ups stopped the simulation once (200 fish fixed it).

## Open
- Open the planner on a finished manor and see if card 123 shows (needs a finished manor: unsafe `construction_complete` or a healthy village). A request to start the game with the unsafe flag was denied in this session, so the second launch was not done.
- Check that a finished type 123 module is an `SMBuilding` part like the tower.
- Behaviour is native: a new id has no special effect. Reusing an existing id with changed data was not needed.

## Changes in the game folder
- `Paks\~mods\mm123data_P.pak` and `mm123ui_P.pak` installed by `run.py`, removed after the test (`pakmod.py remove --all`; `~mods` removed). Deploy copied the mod `HarnessWalls` into `ue4ss\Mods` (normal deploy).
