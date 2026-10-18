# Row id results (spec 23, plan steps 2 to 5)

Date: 2026-10-16. Real game, single player, save `saveGame_48` of the base fixture. No save function was called.
Pak `ids` (not committed, made again with `harness/tools/s127_make_ids_json.py`, then `pakmod.py fromjson --to ids` and `build ids`):
buildingStats rows 126, 486, 1000, 2000, 32767, 65536 cloned from row 30 (hitching post), all `bVisibleInUi` true;
text rows `buildingID_<id>` ("Test <id>") in `DT_Translation_BuildingNames` (the tools support it); DT_Upgrades rows
117 (upgradesInto 126, offered by row 486) and 118 (upgradesInto 1000, offered by row 2000), cloned from upgrade 2.

## Runs
- `s127-ids-a`: harness_error, the fixture files were missing in the worktree (copied from the main checkout).
- `s127-ids-b`: game started, rows read. `building_stat` refused ids above 600 (`MAX_TYPE`), and raw eval is off. The game was stopped by hand.
- `s127-ids-c`: the real test. Limit raised to 70000, new read command `upgrade_stat`. All results below. Runs b and c ended with `harness_error` at `paks-remove` only because `--keep-open` leaves the game running. The pak was removed by hand after the game was stopped.
Run folders: `runs/s127-ids-c/` (git-ignored). Screenshots: `menu2.png`, `tab2.png` (7 hitching post cards), `placed_<id>.png`.

## Result table (buildingStats)

| id | load (row read) | show in build menu | place (real click) | build | 30 days | crash |
|---|---|---|---|---|---|---|
| 126 | yes | yes | yes | yes (within 15 days) | yes | no |
| 486 | yes | yes | yes | yes | yes | no |
| 1000 | yes | yes | yes | yes | yes | no |
| 2000 | yes | yes | yes (3rd click point; two buildings placed by mistake) | yes | yes | no |
| 32767 | yes | yes | yes | yes | yes | no |
| 65536 | yes | yes | yes | yes | yes | no |

Method: row read with `building_stat` (number fields only). Menu: Logistics tab shows 7 hitching post cards (1 vanilla + 6 new). Place: `s94_drive.py place` at window fractions (0.35, 0.3) and nearby points. A master of the type appeared each time. Then 15 days at speed 3 (all `constructed`), then 30 more days at speed 3 (45 days in total). The game stayed alive, no new crash report (real `%LOCALAPPDATA%\ManorLords\Saved\Crashes` has no new folder). A crash report copy was not needed.

## Result table (DT_Upgrades)

| upgrade id | upgradesInto | load (row read) | use in game |
|---|---|---|---|
| 117 | 126 | yes | not tested |
| 118 | 1000 | yes | not tested |

The rows load and the link number is read back. The upgrade was not started in the game, because the clone is a hitching post and has no upgrade button path that was tested. The upgrade flow of a new row stays open.

## Not tested
- Ids 200, 255, 256 (other tables use them) were not in the task list. Keep them out of the mod range.
- Ids 487 to 999 and gaps (Q4): the ids 126 to 485 gap and 486 to 65535 gaps caused no problem.
- Save and load of a new id (a save function is forbidden).
- Rows with a new mesh or a new blueprint. All clones use the hitching post blueprint. A new building id also reads `DT_BuildingMeshPathData` and `DT_ConstructionBPs` by number.
- The AI build lists.

## Answers
- Q2: no crash at 486, 1000, 2000, 32767, 65536. No array index problem was seen in 45 game days.
- Q3: all six ids pass every step for buildingStats.
- Q4: gaps are fine.

## Tool changes
- `HarnessHousing.MAX_TYPE` raised from 600 to 70000.
- New read command `upgrade_stat` (`HarnessActions` version 50).
- `s127_make_ids_json.py` makes the edited JSON of the `ids` pak.
