# Row id persistence results (spike #284, tasks 1.1 to 1.3)

Date: 2026-10-20. Real game, single player, game slot 2, base fixture. Pak `rowid` (made fresh from the game paks with
`harness/tools/s127_make_ids_json.py`): `buildingStats` rows 126, 486, 1000, 2000, 32767, 65536 cloned from row 30 (hitching post),
`DT_Upgrades` rows 117 (offered by 486, `upgradesInto` 126) and 118, and the names `buildingID_<id>`.
Test scenario: `harness/scenarios/probe_row_id_persistence.py` (hidden, real mouse). Save only through `save_game`.

## Runs
| Run id | What | Result |
|---|---|---|
| `rowid-write-a` | place 126, 32767, 65536, 486; build; use upgrade 117; `save_game` (slot saveGame_53) | Placed 126, 32767, 486 and built them. 65536 was blocked at the chosen click spot (a bad spot, not an id problem). Upgrade not finished. |
| `rowid-write-b` | same, better spots | All four ids placed and built. Upgrade request accepted. Save written (saveGame_57). |
| `rowid-read-a` | load saveGame_57, count buildings of each id, watch the upgrade for 40 game days | All four ids load and keep their buildings (see 1.1). |
| `rowid-lord-a` | `probe-lord-village` with the pak, AI lord village, 30 game days | pass, no crash (see 1.3). |

## 1.1 Save and load of a building with a new id: PASS
- Ids 126, 32767 and 65536 (and 486) were built, then saved with the guarded action `save_game`, then loaded.
- After the load each type still has 1 built building (`building_sites` counts), and the row is read (`building_stat` kind 126: `bVisibleInUi` true, `maxHp` 50).
- The game did not crash at save or at load. 1000 and 2000 were not placed (the range 126 to 65536 is covered by 126, 486, 32767, 65536).
- Save guard: `rowid-write-b` reports "the user's save files did not change" and the launcher hash of the user save folder was equal before and after (`user_saves_sha256` ca9f0c74fc54 in `rowid-lord-a`; the write and read runs report the same message). The kept slots were deleted by hand after the check. The save folder was backed up before each saving run (`SaveGames-backup-20261020-224351`, `-225440`, `-230339`).

## 1.2 New upgrade row: PARTLY
- Row read: `upgrade_stat` 117 gives `upgradesInto` 126, `bUseOnlyOnce` true, as in the pak.
- `plot_upgrade` (addUpgradeRequest) on a building of id 486 with upgrade 117 was accepted. The building then shows the cost goods of the new row (2 timber (16) and 6 planks (17)) in `needs`, so the game reads the new row.
- The pending upgrade state survives the save and the load (same `needs` after the load).
- NOT seen: the upgrade finishing (486 turning into 126). 20 game days before the save and 40 game days after the load (stock of planks and timber given): the `needs` stayed and the type stayed 486.
- Cause not found. No control run with a vanilla upgrade on a non-plot building was done, so the cause may be the hitching post clone (no builder work for an upgrade of this building) and not the id. It is not proven that a new upgrade id works to the end. This needs a spike with a control (for example vanilla upgrade 14 on a vanilla stable), or a decision by the user.

## 1.3 AI lord village with the new ids in the pak for 30 game days: PASS
- `rowid-lord-a`: pass, no crash, no new crash folder in the real `Crashes` folder.
- Lord debug logs (`debugLog_AI_construction`, general, tactics) have no error line. The only "failed" lines are `AI_build failed to find place: LoggingCamp, Sawpit, BurgagePlotTool`, which are normal (no place found), not an id error.
- The lord village stayed at 5 buildings and 5 families and made no `AI_build` line in 30 days. No new id was built by the AI: the ids exist in the table, and the AI ignores them. This was not compared with a run without the pak.

## Verdict
No id range failed. Task 2.1 is not needed for the ids. Open: the completion of an upgrade with a new row (1.2).

## Not verified
- Ids 1000 and 2000 in a save, a mesh or blueprint other than the hitching post, and an AI lord that builds a new id.
- A run of the lord village without the pak (control for the build count).

## Tool changes
- `HarnessBuild.MAX_TYPE` and `actions.MAX_BUILDING_TYPE` raised to 70000 (both capped at 600 and 300).

## 1.2 control runs (same fixture, slot 2, no save)
Test scenario phase `ROWID_PHASE=control` (`probe_row_id_persistence.py`); tool `harness/tools/s284_make_upgrade_clone.py` makes pak `rowid2` (upgrade row 119 = clone of vanilla row 14, `upgradesInto` 126, offered by building 486).
| Run id | Building | Upgrade row | Result |
|---|---|---|---|
| `rowid-control-a` | vanilla hitching post 30 | vanilla 14 (4 planks, into stable 97) | Works at once: the post disappears and a stable site appears within 1 game day (goods taken from stock). |
| `rowid-control-b` | new id 486 | new row 119 (same fields as 14, new id) | Does NOT work: after 40 game days the building stays 486, `needs` 4 planks never delivered. |
| `rowid-control-c` | vanilla 30 | new row 119 | Not run: `harness_error` (game window lost the foreground, no input sent). The 3-run cap is used. |
Meaning: the test setup is fine (the vanilla upgrade finishes in 1 day). The new row 119 has the same fields as vanilla row 14, so row 117 failing is not caused by its cloned fields (row 2 settings). The cause is the new upgrade id or the new building id 486 as source. Run c (new upgrade on a vanilla building) would separate them. Not proven yet, so task 1.2 stays unchecked.

### Control c result (runs `rowid-control-d`, `rowid-control-e`)
- `rowid-control-d`: `crash`, the game process ended during boot (before the scenario, no input). `rowid-control-e`: new row 119 on the VANILLA hitching post 30: does NOT work. After 40 game days the post is still type 30 and `needs` 4 planks never change. No focus problem this time.
- So the new building id 486 as the source is not the cause: a new upgrade row fails on a vanilla source too, while vanilla row 14 works on the same building (`rowid-control-a`).
- Row 119 and row 14 differ only in the row id (119, new) and in `upgradesInto` (126, a new building id, instead of 97). So the cause is the new upgrade id OR the new target building id (126). The pending cost is read from the new row, but the request is not carried out.
- Not separated: a control with a new upgrade id into a vanilla target (row 120 = row 14, `upgradesInto` 97), or vanilla row 14 retargeted to 126. The run cap is used. Task 1.2 is NOT checked. Rule for now: do not rely on a new DT_Upgrades row for an upgrade that finishes. Task 2.1 (change the id rule for upgrades) needs the owner.
